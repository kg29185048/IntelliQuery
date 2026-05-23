"""
Router Agent — LangGraph orchestration for the two-phase query pipeline.

Phase 1 (intent extraction):
  schema → relevance → intent_node  →  [PAUSE: frontend shows IntentCard]

Phase 2 (query generation, triggered when confirmed_intent is present):
  schema → relevance → query_node (uses confirmed_intent) → validate → explain → execute → END
                           ↓ (on error)
                       suggest → END
"""

import logging
from typing import Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

from agents.query_agent          import generate_query
from agents.validation_agent     import validate_query, check_destructive_intent
from agents.explanation_agent    import explain_query
from agents.schema_agent         import get_schema
from agents.suggestion_agent     import generate_suggestions
from agents.relevance_agent      import check_relevance
from agents.intent_extraction_agent import extract_intent

import datetime
from bson import ObjectId, Decimal128

logger = logging.getLogger(__name__)


# ===========================================================================
# BSON SANITISER
# ===========================================================================
def _sanitize(value):
    """Recursively convert BSON / non-JSON-serializable types to plain Python."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def sanitize_doc(doc: dict) -> dict:
    return _sanitize(doc)


# ===========================================================================
# PIPELINE STATE
# ===========================================================================
class PipelineState(TypedDict):
    db:                  Any
    user_query:          str
    history:             Optional[list]
    schema:              Optional[Any]
    # Phase 1 outputs
    extracted_intent:    Optional[dict]
    # Phase 2 inputs
    confirmed_intent:    Optional[dict]   # Set by caller when user confirms
    intent_confirmed:    Optional[bool]   # True → skip intent_node, run query_node
    # Pipeline outputs
    query_dict:          Optional[dict]
    is_valid:            Optional[bool]
    validation_msg:      Optional[str]
    explanation:         Optional[str]
    result:              Optional[Any]
    error:               Optional[str]
    suggestions:         Optional[list]
    is_relevant:         Optional[bool]
    relevance_reason:    Optional[str]
    confirmed:           Optional[bool]   # Legacy: update confirmation
    requires_confirmation: Optional[bool]
    permission_level: Optional[str]


# ===========================================================================
# NODE 1 — Schema
# ===========================================================================
def schema_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] schema_node")
    try:
        schema = get_schema(state["db"])
    except Exception:
        schema = {"users": ["name", "email", "age"], "movies": ["title", "genre", "rating"]}
    return {**state, "schema": schema}


# ===========================================================================
# NODE 2 — Relevance
# ===========================================================================
def relevance_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] relevance_node")
    is_relevant, reason = check_relevance(state["user_query"], state["schema"])
    return {**state, "is_relevant": is_relevant, "relevance_reason": reason}


# ===========================================================================
# NODE 3a — Intent Extraction (Phase 1)
# ===========================================================================
def intent_node(state: PipelineState) -> PipelineState:
    """
    Phase 1: extract structured intent from the raw user query.
    Sets extracted_intent and signals the API to pause and return to the frontend.
    """
    logger.debug("[LangGraph] intent_node")
    extracted = extract_intent(
        user_query=state["user_query"],
        schema=state["schema"],
        history=state.get("history") or [],
    )
    return {**state, "extracted_intent": extracted}


# ===========================================================================
# NODE 3b — Query Generation (Phase 2)
# ===========================================================================
def query_node(state: PipelineState) -> PipelineState:
    """
    Phase 2: generate MongoDB query from confirmed intent.
    Runs ONLY when confirmed_intent is provided by the caller.
    """
    logger.debug("[LangGraph] query_node")

    confirmed_intent = state.get("confirmed_intent") or {}

    # Safety check on the raw user query before generating anything
    is_safe, safety_msg = check_destructive_intent(state["user_query"])
    if not is_safe:
        logger.warning("[QueryNode] Destructive query blocked: %r", state["user_query"])
        return {**state, "error": safety_msg, "is_valid": False, "validation_msg": safety_msg}

    result = generate_query(confirmed_intent, state["schema"])

    if "error" in result:
        return {**state, "error": result["error"]}

    logger.info("[QueryNode] Generated: %s", result)
    return {**state, "query_dict": result, "error": None}


# ===========================================================================
# NODE 4 — Validation
# ===========================================================================
def validation_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] validation_node")
    is_valid, msg = validate_query(state["query_dict"])
    return {**state, "is_valid": is_valid, "validation_msg": msg}


# ===========================================================================
# NODE 5 — Explanation
# ===========================================================================
def explanation_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] explanation_node")
    try:
        explanation = explain_query(str(state["query_dict"]))
        return {**state, "explanation": explanation}
    except Exception as exc:
        return {**state, "explanation": f"Could not generate explanation: {exc}"}


# ===========================================================================
# NODE 6 — Execution
# ===========================================================================
def execution_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] execution_node")
    query_dict = state["query_dict"]
    db         = state["db"]
    operation  = query_dict.get("operation")

    collection_name = query_dict.get("collection")
    if not collection_name:
        return {**state, "error": "No collection specified in the generated query"}

    collection = db[collection_name]

    try:
        # Permission check
        if operation in ["insert", "update", "delete", "drop"] and state.get("permission_level") == "read_only":
            return {**state, "error": "Permission Denied: You have read-only access to this workspace. Modifying the database is not allowed."}

        if operation == "insert":
            data = query_dict.get("data", {})
            if not data:
                return {**state, "error": "No data provided for insert operation"}
            result = collection.insert_one(data)
            return {**state, "result": f"✅ Document added with ID: {str(result.inserted_id)}"}

        elif operation == "find":
            filter_query     = query_dict.get("filter", {})
            projection_query = query_dict.get("projection") or None
            sort_spec        = query_dict.get("sort") or None
            limit            = query_dict.get("limit") or 0

            cursor = collection.find(filter_query, projection_query) if projection_query else collection.find(filter_query)
            if sort_spec:
                # sort_spec: {"field": "x", "direction": "asc"/"desc"} or raw pymongo format
                if isinstance(sort_spec, dict) and "field" in sort_spec:
                    direction = -1 if sort_spec.get("direction") == "desc" else 1
                    cursor = cursor.sort(sort_spec["field"], direction)
                elif isinstance(sort_spec, list):
                    cursor = cursor.sort(sort_spec)
            if limit:
                cursor = cursor.limit(int(limit))
            else:
                cursor = cursor.limit(200)   # Hard safety cap

            results = list(cursor)
            cleaned = [sanitize_doc(doc) for doc in results]
            return {**state, "result": cleaned}

        elif operation == "aggregate":
            pipeline = query_dict.get("pipeline", [])
            if not pipeline:
                return {**state, "error": "No pipeline provided for aggregation"}
            results = list(collection.aggregate(pipeline))
            cleaned = [sanitize_doc(doc) for doc in results]
            return {**state, "result": cleaned}

        elif operation == "update":
            if not state.get("confirmed"):
                return {**state, "requires_confirmation": True}
            filter_query = query_dict.get("filter", {})
            update_data  = query_dict.get("update_data", {})
            if not update_data:
                return {**state, "error": "No update data provided (e.g., missing $set)"}
            result = collection.update_many(filter_query, update_data)
            return {**state, "result": f"✅ Update successful. Modified {result.modified_count} document(s)."}

        else:
            return {**state, "error": f"Unsupported operation: {operation}"}

    except Exception as exc:
        return {**state, "error": f"Execution failed: {exc}"}


# ===========================================================================
# NODE 7 — Suggestion
# ===========================================================================
def suggestion_node(state: PipelineState) -> PipelineState:
    logger.debug("[LangGraph] suggestion_node")
    if state.get("is_relevant") is False:
        error_msg = f"Your question doesn't seem to match this database. {state.get('relevance_reason', '')}".strip()
    else:
        error_msg = state.get("error") or state.get("validation_msg") or "Unknown error"

    suggestions = generate_suggestions(
        state["user_query"],
        state.get("schema") or {},
        error_msg,
    )
    return {**state, "suggestions": suggestions, "error": error_msg}


# ===========================================================================
# CONDITIONAL EDGE FUNCTIONS
# ===========================================================================
def after_relevance(state: PipelineState) -> str:
    """
    If irrelevant → suggest.
    If intent not yet confirmed (Phase 1) → intent.
    If intent confirmed (Phase 2) → query.
    """
    if not state.get("is_relevant", True):
        return "suggest"
    if state.get("intent_confirmed"):
        return "query"
    return "intent"


def after_query(state: PipelineState) -> str:
    if state.get("error"):
        if state.get("is_valid") is False:
            return "end"      # Destructive — no suggestions
        return "suggest"
    return "validate"


def after_validation(state: PipelineState) -> str:
    if not state.get("is_valid"):
        return "end"          # Unsafe query — return error, no suggestions
    return "explain"


# ===========================================================================
# BUILD LANGGRAPH WORKFLOW
# ===========================================================================
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("schema",    schema_node)
    graph.add_node("relevance", relevance_node)
    graph.add_node("intent",    intent_node)
    graph.add_node("query",     query_node)
    graph.add_node("validate",  validation_node)
    graph.add_node("explain",   explanation_node)
    graph.add_node("execute",   execution_node)
    graph.add_node("suggest",   suggestion_node)

    graph.set_entry_point("schema")
    graph.add_edge("schema", "relevance")
    graph.add_conditional_edges("relevance", after_relevance, {
        "intent":  "intent",
        "query":   "query",
        "suggest": "suggest",
    })
    graph.add_edge("intent", END)   # Phase 1 always stops here; Phase 2 re-enters at query
    graph.add_conditional_edges("query", after_query, {
        "validate": "validate",
        "suggest":  "suggest",
        "end":      END,
    })
    graph.add_conditional_edges("validate", after_validation, {
        "explain": "explain",
        "end":     END,
    })
    graph.add_edge("explain",  "execute")
    graph.add_edge("execute",  END)
    graph.add_edge("suggest",  END)

    return graph.compile()


_compiled_graph = build_graph()


# ===========================================================================
# PUBLIC API
# ===========================================================================
def extract_intent_pipeline(db, user_query: str, history: list = None) -> dict:
    """
    Phase 1: run schema → relevance → intent_node.
    Returns {"extracted_intent": {...}} or {"error": "...", "suggestions": [...]}
    """
    initial_state: PipelineState = {
        "db":                  db,
        "user_query":          user_query,
        "history":             history,
        "schema":              None,
        "extracted_intent":    None,
        "confirmed_intent":    None,
        "intent_confirmed":    False,   # ← Phase 1
        "query_dict":          None,
        "is_valid":            None,
        "validation_msg":      None,
        "explanation":         None,
        "result":              None,
        "error":               None,
        "suggestions":         None,
        "is_relevant":         None,
        "relevance_reason":    None,
        "confirmed":           False,
        "requires_confirmation": None,
    }

    final = _compiled_graph.invoke(initial_state)

    if final.get("suggestions"):
        if final.get("is_relevant") is False:
            error_msg = f"Your question doesn't seem to match this database. {final.get('relevance_reason', '')}".strip()
        else:
            error_msg = final.get("error") or "Query could not be processed."
        return {"error": error_msg, "suggestions": final["suggestions"]}

    if final.get("error"):
        return {"error": final["error"]}

    return {"extracted_intent": final.get("extracted_intent", {})}


def run_pipeline(
    db,
    user_query:       str,
    history:          list = None,
    confirmed:        bool = False,
    confirmed_intent: dict = None,
    permission_level: str  = "read_only",
) -> dict:
    """
    Phase 2: run the full pipeline using a confirmed intent.

    Args:
        db:               MongoDB database object.
        user_query:       Original NL query (used for destructive checks & suggestions).
        history:          Conversation history.
        confirmed:        True if user confirmed an update operation (legacy flag).
        confirmed_intent: The structured intent dict from the IntentCard.

    Returns:
        dict with keys: query, explanation, result — or error/suggestions/requires_confirmation.
    """
    initial_state: PipelineState = {
        "db":                  db,
        "user_query":          user_query,
        "history":             history,
        "schema":              None,
        "extracted_intent":    None,
        "confirmed_intent":    confirmed_intent,
        "intent_confirmed":    True,    # ← Phase 2
        "query_dict":          None,
        "is_valid":            None,
        "validation_msg":      None,
        "explanation":         None,
        "result":              None,
        "error":               None,
        "suggestions":         None,
        "is_relevant":         None,
        "relevance_reason":    None,
        "confirmed":           confirmed,
        "requires_confirmation": None,
        "permission_level": permission_level,
    }

    final = _compiled_graph.invoke(initial_state)

    if final.get("suggestions"):
        if final.get("is_relevant") is False:
            error_msg = f"Your question doesn't seem to match this database. {final.get('relevance_reason', '')}".strip()
        else:
            error_msg = final.get("error") or final.get("validation_msg") or "Query could not be generated."
        return {"error": error_msg, "suggestions": final["suggestions"]}

    if final.get("requires_confirmation"):
        return {
            "requires_confirmation": True,
            "query":       final["query_dict"],
            "explanation": final["explanation"],
        }

    if final.get("error"):
        return {"error": final["error"]}
    if final.get("validation_msg") and not final.get("is_valid"):
        return {"error": f"Validation Failed: {final['validation_msg']}"}

    return {
        "query":       final["query_dict"],
        "explanation": final["explanation"],
        "result":      final["result"] if final["result"] is not None else [],
    }




