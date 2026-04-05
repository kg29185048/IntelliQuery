import json
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"})

def generate_suggestions(user_query: str, schema, error: str) -> list:
    """
    Given a failed user query, the DB schema, and the error message,
    ask the LLM to suggest 4 alternative, valid natural language queries.
    Always appends a 'None of these' fallback option.
    """
    prompt = f"""
You are a MongoDB expert assistant. A user asked a question that could not be answered because the query could not be generated or was invalid.

User Query: {user_query}
Database Schema: {json.dumps(schema) if not isinstance(schema, str) else schema}
Error: {error}

Suggest 4 alternative natural language questions that ARE valid for this schema and would work correctly.
Make them specific, clear, and directly usable.

Return ONLY valid JSON in this exact format:
{{"suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"]}}
"""
    try:
        response = llm.invoke(prompt)
        data = json.loads(response.content)
        suggestions = data.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        # Trim to max 4, then add the fallback
        suggestions = suggestions[:4]
        suggestions.append("None of these (I will rephrase)")
        return suggestions
    except Exception as e:
        print(f"[SuggestionAgent] Failed: {e}")
        return [
            "Show all documents in the collection",
            "Count total records",
            "Find top 5 results by a field",
            "Search by name or ID",
            "None of these (I will rephrase)",
        ]
