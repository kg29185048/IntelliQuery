# agents/sql_agent.py
#
# Handles the full SQL pipeline:
#   1. Generate a SQL SELECT from natural language
#   2. Execute it
#   3. Explain it
#
# Returns the same shape as run_pipeline() so api/main.py needs no extra branching.

import json
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY
from database.sql_client import execute_sql

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
)

# ---------------------------------------------------------------------------
# Prompt — SQL generation
# ---------------------------------------------------------------------------
SQL_QUERY_PROMPT = """\
You are an expert SQL query generator.

The database has the following schema (table → columns):
{schema}

Conversation history (most recent last):
{history}

Current user question:
{user_query}

RULES:
1. Return ONLY a valid JSON object with exactly two keys:
   - "sql": a single, complete, safe SELECT statement (no DDL, no DML other than SELECT)
   - "table": the primary table being queried
2. Do NOT use markdown fences, no explanation, no extra text.
3. Use ILIKE (Postgres/SQLite LIKE) for case-insensitive text matching.
4. If the user refers to a previous result, incorporate previous filters into the WHERE clause.

Examples:

User: Show all customers
Output: {{"sql": "SELECT * FROM customers LIMIT 100", "table": "customers"}}

User: Find orders over $500
Output: {{"sql": "SELECT * FROM orders WHERE total > 500", "table": "orders"}}

Now generate the query:
"""

# ---------------------------------------------------------------------------
# Prompt — SQL explanation
# ---------------------------------------------------------------------------
SQL_EXPLAIN_PROMPT = """\
Explain this SQL query in plain English in 2-4 sentences. Be concise and clear.

{sql}
"""


def _schema_to_text(schema: dict) -> str:
    lines = []
    for table, cols in schema.items():
        lines.append(f"- {table}: {', '.join(cols)}")
    return "\n".join(lines)


def run_sql_pipeline(engine, user_query: str, schema: dict, history: list = None) -> dict:
    """
    Full SQL pipeline. Returns:
      {"query": {"sql": ..., "table": ...}, "explanation": ..., "result": [...]}
    or {"error": "..."}
    """
    history = history or []
    history_text = "\n".join(
        f"User: {t['user']}\nGenerated SQL: {t['query']}" for t in history
    )

    # 1. Generate SQL
    prompt = SQL_QUERY_PROMPT.format(
        schema=_schema_to_text(schema),
        history=history_text,
        user_query=user_query,
    )

    try:
        raw = llm.invoke(prompt).content.strip()
        # Strip markdown fences if model disobeys
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        query_dict = json.loads(raw)
    except Exception as e:
        return {"error": f"Failed to generate SQL: {e}"}

    sql = query_dict.get("sql", "").strip()
    if not sql:
        return {"error": "LLM returned an empty SQL string."}

    # 2. Execute SQL
    try:
        rows = execute_sql(engine, sql)
    except Exception as e:
        return {"error": f"SQL execution error: {e}"}

    # 3. Explain
    try:
        explanation = llm.invoke(
            SQL_EXPLAIN_PROMPT.format(sql=sql)
        ).content.strip()
    except Exception:
        explanation = "Query executed successfully."

    return {
        "query": query_dict,
        "explanation": explanation,
        "result": rows,
    }
