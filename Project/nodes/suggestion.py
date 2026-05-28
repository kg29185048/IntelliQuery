"""
Suggestion Agent — generates alternative query suggestions after a failure.

Refactored to use ChatPromptTemplate + JsonOutputParser LCEL chain.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import get_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LCEL chain
# ---------------------------------------------------------------------------
_SYSTEM = """You are a MongoDB expert assistant.

A user asked a question that could not be answered — either the query could not
be generated, or it was invalid for the database.

Database Schema: {schema}
Error that occurred: {error}

Suggest 4 alternative natural language questions that ARE valid for this schema
and would work correctly. Make them specific, clear, and directly usable.

CRITICAL RULES:
1. Do NOT hallucinate or invent collections or fields. 
2. ONLY use the exact collection names and field names listed in the Database Schema above.
3. If the schema is empty or you are unsure, provide generic suggestions like "Show all documents".

Return ONLY valid JSON:
{{"suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"]}}"""

_HUMAN = "Failed user query: {user_query}"

_suggestion_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human",  _HUMAN),
])
_suggestion_chain = _suggestion_prompt | get_llm(json_mode=True) | JsonOutputParser()

_FALLBACK = [
    "Show all documents in the collection",
    "Count total records",
    "Find top 5 results by a field",
    "Search by name or ID",
    "None of these (I will rephrase)",
]


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def generate_suggestions(user_query: str, schema, error: str) -> list:
    """
    Given a failed query + schema + error message, return 4 suggestion strings
    plus a 'None of these' fallback. Never raises.
    """
    import json as _json
    schema_str = _json.dumps(schema) if not isinstance(schema, str) else schema

    try:
        result      = _suggestion_chain.invoke({"user_query": user_query, "schema": schema_str, "error": error})
        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        suggestions = suggestions[:4]
        suggestions.append("None of these (I will rephrase)")
        return suggestions
    except Exception as exc:
        logger.error("[SuggestionAgent] Failed: %s", exc)
        return _FALLBACK
