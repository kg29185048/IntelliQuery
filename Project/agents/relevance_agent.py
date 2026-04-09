import json
import re
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"})

# Destructive keywords — relevance check is bypassed for these;
# the validation agent is solely responsible for blocking them.
_DESTRUCTIVE_RE = re.compile(
    r"\b(delete|drop|remove|truncate|wipe|purge|erase|destroy|merge)\b",
    re.IGNORECASE
)

def check_relevance(user_query: str, schema) -> tuple[bool, str]:
    """
    Checks whether the user's question can be meaningfully answered
    by the given database schema.

    Returns:
        (is_relevant: bool, reason: str)
    Defaults to True on any failure so valid queries are never blocked.
    """
    schema_str = json.dumps(schema) if not isinstance(schema, str) else schema

    # Bypass LLM entirely for destructive queries — validation agent handles blocking.
    if _DESTRUCTIVE_RE.search(user_query):
        print("[RelevanceAgent] Destructive keyword detected — skipping LLM, marking relevant=True")
        return True, "Destructive operation detected; deferred to validation agent."

    prompt = f"""You are a strict database query gatekeeper.

A user has asked a question. Your job is to decide whether the user's question
is asking about data that genuinely exists in the provided database schema.

User Question: {user_query}
Database Schema: {schema_str}

### Rules:
1. **Domain Alignment**: The intent of the question must match the purpose of the schema. (e.g., medical questions are irrelevant to a financial database).
2. **Direct Mapping**: Only return true if the requested data points (or entities) exist as collections, tables, or fields.
3. **No Creative Stretching**: Do not assume the database can answer questions outside its primary domain just because a text field *could* contain that info.
4. **Operations**: Do NOT block destructive operations (delete, drop, etc.). If the target entity exists in the schema, the request is relevant.
5. **Ambiguity**: If a query is partially answerable, mark as true.

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
