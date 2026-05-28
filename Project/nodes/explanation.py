"""
Explanation Agent — generates a plain-English explanation of a MongoDB query.

Refactored to use ChatPromptTemplate + StrOutputParser LCEL chain.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LCEL chain
# ---------------------------------------------------------------------------
_SYSTEM = """You are a MongoDB query explainer. Your job is to explain a MongoDB query
in simple, plain English that a non-technical user can understand.

Rules:
- Avoid technical jargon. Focus on the intuition behind the query logic.
- ALWAYS explain the role of $and when present, and how it combines conditions.
- If the query filter is empty ({{}}) explain it means "selecting ALL documents with no filtering".
- ALWAYS explain regex conditions: they enable partial, case-insensitive text matching.
- If the query includes a projection, explain which fields are returned and why.
- Explain aggregation pipeline stages in order (what each stage does to the data).
- Keep the explanation concise but complete — 2 to 5 sentences."""

_HUMAN = "Explain this MongoDB query:\n{query}"

_explanation_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human",  _HUMAN),
])
_explanation_chain = _explanation_prompt | get_llm(json_mode=False) | StrOutputParser()


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def explain_query(query: str) -> str:
    """
    Returns a plain-English explanation of the query string.
    Falls back to a generic message on failure.
    """
    try:
        return _explanation_chain.invoke({"query": query})
    except Exception as exc:
        logger.error("[ExplanationAgent] Failed: %s", exc)
        return "Could not generate an explanation for this query."