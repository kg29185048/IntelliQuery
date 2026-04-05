import json
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"})

def check_relevance(user_query: str, schema) -> tuple[bool, str]:
    """
    Checks whether the user's question can be meaningfully answered
    by the given database schema.

    Returns:
        (is_relevant: bool, reason: str)
    Defaults to True on any failure so valid queries are never blocked.
    """
    schema_str = json.dumps(schema) if not isinstance(schema, str) else schema

    prompt = f"""You are a strict database query gatekeeper.

A user has asked a question. Your job is to decide whether the user's question
is asking about data that genuinely exists in the provided database schema.

User Question: {user_query}
Database Schema: {schema_str}

Rules — read carefully:
1. Match on DOMAIN, not on creative field reuse.
   - "show me medical data" against a movies DB → FALSE. The user wants medical records; the DB has movies.
   - "show me action movies" against a movies DB → TRUE.
2. Do NOT invent indirect mappings. If the user asks for X and X is not a collection,
   a field, or the primary purpose of any collection, answer false.
3. The user's INTENT must match the database's purpose.
   - A movies DB cannot answer questions about medical patients, financial transactions,
     employee records, weather data, etc., even if a text field could theoretically contain such words.
4. Only answer true if the question is directly and naturally answerable from the schema as-is.

Return ONLY valid JSON:
{{"is_relevant": true_or_false, "reason": "one short sentence explaining the decision"}}
"""
    try:
        response = llm.invoke(prompt)
        data = json.loads(response.content)
        is_relevant = bool(data.get("is_relevant", True))
        reason = data.get("reason", "")
        print(f"[RelevanceAgent] relevant={is_relevant} | {reason}")
        return is_relevant, reason
    except Exception as e:
        print(f"[RelevanceAgent] Check failed ({e}), defaulting to relevant")
        return True, ""
