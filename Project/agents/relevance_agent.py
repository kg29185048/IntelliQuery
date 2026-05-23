"""
Relevance Agent — checks whether a user's query is meaningful for the DB schema.

Refactored to use ChatPromptTemplate + JsonOutputParser LCEL chain.
"""

import re
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import get_llm

logger = logging.getLogger(__name__)

_DESTRUCTIVE_RE = re.compile(
    r"\b(delete|drop|remove|truncate|wipe|purge|erase|destroy|merge)\b",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# LCEL chain
# ---------------------------------------------------------------------------
_SYSTEM = """You are a strict database query gatekeeper.

A user has asked a question. Decide whether the user's question is asking about
data that genuinely exists in the provided database schema.

Database Schema: {schema}

Rules:
1. Domain Alignment: The intent must match the schema's purpose.
2. Direct Mapping: Return true only if the requested entities or fields exist in the schema.
3. No Creative Stretching: Do not assume the DB can answer questions outside its primary domain.
4. Do NOT block destructive operations (delete, drop, etc.) — the validation agent handles those.
5. If partially answerable, return true.

Return ONLY valid JSON — no extra text:
{{"is_relevant": true_or_false, "reason": "one short sentence"}}"""

_HUMAN = "User question: {user_query}"

_relevance_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human",  _HUMAN),
])
_relevance_chain = _relevance_prompt | get_llm(json_mode=True) | JsonOutputParser()


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def check_relevance(user_query: str, schema) -> tuple[bool, str]:
    """
    Returns (is_relevant: bool, reason: str).
    Defaults to True on any failure so valid queries are never blocked.
    """
    import json as _json
    schema_str = _json.dumps(schema) if not isinstance(schema, str) else schema

    # Bypass LLM entirely for destructive queries — validation agent handles blocking.
    if _DESTRUCTIVE_RE.search(user_query):
        logger.info("[RelevanceAgent] Destructive keyword — skipping LLM, marking relevant=True")
        return True, "Destructive operation detected; deferred to validation agent."

    try:
        result = _relevance_chain.invoke({"user_query": user_query, "schema": schema_str})
        is_relevant = bool(result.get("is_relevant", True))
        reason      = result.get("reason", "")
        logger.info("[RelevanceAgent] relevant=%s | %s", is_relevant, reason)
        return is_relevant, reason
    except Exception as exc:
        logger.warning("[RelevanceAgent] Check failed (%s), defaulting to relevant", exc)
        return True, ""
