"""
Intent Extraction Prompt — Phase 1 of the two-phase query flow.

The intent_chain takes a natural-language user query + schema + history
and returns a structured ExtractedIntent dict. The LLM does NOT write
any MongoDB syntax here — it only identifies WHAT the user wants.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------
_SYSTEM = """You are a database query intent extractor.

Your ONLY job is to understand what the user wants and return it as structured JSON.
Do NOT generate any MongoDB query syntax. Do NOT write pipelines or filter objects.
Just extract the intent — the actual query generation happens separately.

The database schema (collections and their fields) is:
{schema}

Conversation history (most recent last):
{history}

Return ONLY this JSON structure — no extra text, no markdown:
{{
  "operation": "find | insert | update | aggregate",
  "collection": "<exact collection name from schema>",
  "goal": "<plain English description of exactly what the user wants — be specific, include field names>",
  "filters": [
    {{ "field": "<field_name>", "operator": "eq|ne|gt|gte|lt|lte|regex|in|nin", "value": "<value>" }}
  ],
  "projection": ["<field1>", "<field2>"],
  "sort": {{ "field": "<field_name>", "direction": "asc|desc" }},
  "limit": <integer or null>,
  "aggregate_stages": ["$match", "$group", "$sort", "$limit", "$unwind", "$project", "$lookup"]
}}

Rules:
- "collection" MUST be one of the collections in the schema above. Pick the best match.
- "filters" should only contain conditions the user EXPLICITLY mentioned.
- "projection" is only set when the user asks for specific fields.
- "sort" is only set when the user implies ordering (top, highest, recent, etc.).
- "limit" is only set when the user says a number (top 5, first 10, etc.).
- "aggregate_stages" is only for aggregate operations. List only the stages actually needed.
  Example: "count by genre" needs ["$group", "$sort"]; "average rating per year" needs ["$group", "$sort"].
- For multi-turn queries (e.g. "now filter those by rating"), merge with the previous intent from history.
- If the query is ambiguous, make the best reasonable guess — do not return an error.
"""

_HUMAN = "User query: {user_query}"

# ---------------------------------------------------------------------------
# Build the LCEL chain: prompt | llm | parser
# ---------------------------------------------------------------------------
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human",  _HUMAN),
])
