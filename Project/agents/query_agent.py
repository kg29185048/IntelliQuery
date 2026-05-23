"""
Query Agent — Phase 2 of the two-phase query flow.

Receives a CONFIRMED intent dict (already validated/edited by the user
via the IntentCard) and routes to the correct per-operation LangChain
chain to generate precise MongoDB syntax.

The old hallucination-scrubbing heuristics (_cleanup_filter, _is_spurious_condition,
etc.) are removed — they addressed symptoms of open-ended prompting. With structured
intent as input, the LLM receives confirmed field names and values so those artifacts
no longer occur.
"""

import json
import logging
from prompts.query_prompt import get_query_chain

logger = logging.getLogger(__name__)


def _build_chain_inputs(confirmed_intent: dict, schema: dict) -> dict:
    """
    Convert the confirmed intent dict into keyword arguments expected by the chain.
    All chains share the same base keys; each ignores keys it doesn't use.
    """
    collection   = confirmed_intent.get("collection", "")
    schema_fields = json.dumps(schema.get(collection, []))

    # Serialise filters list for prompt injection
    filters_text = ""
    filters = confirmed_intent.get("filters") or []
    if filters:
        lines = []
        for f in filters:
            lines.append(
                f"  - {f.get('field', '?')} {f.get('operator', 'eq')} {f.get('value', '?')}"
            )
        filters_text = "\n".join(lines)
    else:
        filters_text = "  (none)"

    # Serialise projection
    projection_list = confirmed_intent.get("projection") or []
    projection_text = ", ".join(projection_list) if projection_list else "(all fields)"

    # Serialise sort
    sort_info = confirmed_intent.get("sort") or {}
    sort_text = (
        f"{sort_info.get('field')} {sort_info.get('direction', 'asc')}"
        if sort_info and sort_info.get("field")
        else "(none)"
    )

    # Serialise aggregate stages
    agg_stages = confirmed_intent.get("aggregate_stages") or []
    agg_stages_text = ", ".join(agg_stages) if agg_stages else "(none)"

    return {
        "collection":       collection,
        "schema_fields":    schema_fields,
        "goal":             confirmed_intent.get("goal", ""),
        "filters":          filters_text,
        "projection":       projection_text,
        "sort":             sort_text,
        "limit":            confirmed_intent.get("limit") or "(none)",
        "aggregate_stages": agg_stages_text,
    }


def generate_query(confirmed_intent: dict, schema: dict) -> dict:
    """
    Generate a MongoDB query dict from a confirmed intent.

    Args:
        confirmed_intent: The structured intent dict returned by extract_intent()
                          and potentially edited by the user via the IntentCard.
        schema:           Full DB schema dict {collection: [fields]}.

    Returns:
        A MongoDB query dict ready for validation and execution.
        Returns {"error": "..."} on failure — never raises.
    """
    operation = confirmed_intent.get("operation", "find")

    try:
        chain  = get_query_chain(operation)
        inputs = _build_chain_inputs(confirmed_intent, schema)
        result = chain.invoke(inputs)

        if not isinstance(result, dict):
            logger.error("[QueryAgent] LLM returned non-dict: %r", result)
            return {"error": "LLM output was not a valid JSON object."}

        logger.info("[QueryAgent] op=%s collection=%s", operation, result.get("collection"))
        return result

    except ValueError as ve:
        # Unknown operation
        logger.error("[QueryAgent] %s", ve)
        return {"error": str(ve)}
    except Exception as exc:
        logger.error("[QueryAgent] generation failed: %s", exc)
        return {"error": f"Query generation failed: {exc}"}