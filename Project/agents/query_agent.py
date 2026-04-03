import json
from langchain_groq import ChatGroq
from utils.parser import extract_mongo_query
from prompts.query_prompt import QUERY_PROMPT

llm = ChatGroq(model_name="llama-3.1-8b-instant")

def generate_query(user_query, schema):

    # 🔥 STEP 1: detect INSERT
    if "add" in user_query.lower() or "insert" in user_query.lower():
        prompt = f"""
Convert the user query into STRICT JSON.

Return ONLY JSON.

Format:
{{
  "operation": "insert",
  "collection": "<collection_name>",
  "data": {{ full document }}
}}

User Query:
{user_query}
"""

        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        try:
            query_dict = json.loads(raw_output)
        except Exception as e:
            print("JSON ERROR:", e)
            return {}

        print("INSERT QUERY:", query_dict)
        return query_dict

    # 🔥 EXISTING READ LOGIC (UNCHANGED)
    prompt = QUERY_PROMPT.format(schema=schema, user_query=user_query)
    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    query_string = extract_mongo_query(raw_output)

    try:
        clean_query = json.loads(query_string)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        clean_query = {}

    print(f"Final Query: {clean_query} | Type: {type(clean_query)}")

    return {
        "filter": {},
        "projection": clean_query
    }