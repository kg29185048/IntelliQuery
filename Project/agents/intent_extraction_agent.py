"""
Intent Extraction Agent — Phase 1 of the two-phase query flow.

Calls the intent_chain to extract structured intent from a natural-language
user query. Returns an ExtractedIntent dict. All errors fall back gracefully
so the pipeline never silently fails.
"""

import json
import logging
from app.config import get_llm
from prompts.intent_prompt import intent_prompt
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LCEL chain: intent_prompt | llm (json_mode) | JsonOutputParser
# ---------------------------------------------------------------------------
_intent_chain = intent_prompt | get_llm(json_mode=True) | JsonOutputParser()


# ---------------------------------------------------------------------------
# Defaults used when the LLM omits optional fields
# ---------------------------------------------------------------------------
_INTENT_DEFAULTS = {
    "operation":        "find",
    "collection":       "",
    "goal":             "",
    "filters":          [],
    "projection":       [],
    "sort":             None,
    "limit":            None,
    "aggregate_stages": [],
}


def extract_intent(user_query: str, schema: dict, history: list = None) -> dict:
    """
    Run the intent extraction chain.

    Args:
        user_query: Raw natural-language input from the user.
        schema:     Dict mapping collection names → list of field names.
        history:    List of past {user, query} turns for multi-turn support.

    Returns:
        A dict conforming to the ExtractedIntent shape. Never raises —
        falls back to safe defaults on any LLM or parse failure.
    """
    schema_str = json.dumps(schema) if not isinstance(schema, str) else schema
    history_text = ""
    if history:
        history_text = "\n".join(
            f"User: {turn['user']}\nGenerated Query: {turn['query']}"
            for turn in history
        )

    try:
        result = _intent_chain.invoke({
            "user_query": user_query,
            "schema":     schema_str,
            "history":    history_text,
        })

        # Merge with defaults so the frontend always gets all keys
        intent = {**_INTENT_DEFAULTS, **result}

        # Normalise types — LLM sometimes returns strings for limit
        if intent["limit"] is not None:
            try:
                intent["limit"] = int(intent["limit"])
            except (TypeError, ValueError):
                intent["limit"] = None

        # Ensure lists are actually lists
        for list_field in ("filters", "projection", "aggregate_stages"):
            if not isinstance(intent[list_field], list):
                intent[list_field] = []

        logger.info(
            "[IntentAgent] op=%s collection=%s filters=%d goal=%r",
            intent["operation"], intent["collection"],
            len(intent["filters"]), intent["goal"]
        )
        return intent

    except Exception as exc:
        logger.error("[IntentAgent] extraction failed: %s", exc)
        # Return a minimal safe fallback so the UI can still show the card
        return {
            **_INTENT_DEFAULTS,
            "goal": user_query,   # Show the raw query so user can edit it
            "_extraction_error": str(exc),
        }
