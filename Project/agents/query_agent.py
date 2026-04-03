# import json
# from langchain_groq import ChatGroq
# from utils.parser import extract_mongo_query
# from prompts.query_prompt import QUERY_PROMPT

# llm = ChatGroq(model_name="llama-3.1-8b-instant")

# def generate_query(user_query, schema):
#     prompt = QUERY_PROMPT.format(schema=schema, user_query=user_query)
#     response = llm.invoke(prompt)
#     raw_output = response.content.strip()

#     # Get the string version of the query from parser
#     query_string = extract_mongo_query(raw_output)

#     try:
#         # Convert the string "{...}" into a real Python dict
#         clean_query = json.loads(query_string)
#     except Exception as e:
#         print(f"JSON Parse Error: {e}")
#         clean_query = {} 

#     print(f"Final Query: {clean_query} | Type: {type(clean_query)}")
#     return clean_query

import json
from langchain_groq import ChatGroq
from utils.parser import extract_mongo_query
from prompts.query_prompt import QUERY_PROMPT
from app.config import GROQ_API_KEY

# ✅ Bind the model to STRICT JSON MODE
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"}) # <-- THIS IS THE MAGIC BULLET

def generate_query(user_query, schema, feedback=None):
    if feedback:
        user_query = f"{user_query}\n\n[Previous attempt failed: {feedback}. Fix the query and try again.]"
    prompt = QUERY_PROMPT.format(schema=schema, user_query=user_query)
    
    # Get the response
    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    # ==========================================
    # 🐛 DEBUGGING: Print EXACTLY what Groq said
    # ==========================================
    print("\n" + "="*50)
    print("🤖 RAW LLM OUTPUT:")
    print(raw_output)
    print("="*50 + "\n")

    # Get the string version of the query from parser
    query_string = extract_mongo_query(raw_output)

    try:
        # Convert the string into a real Python dict
        clean_query = json.loads(query_string)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        clean_query = {} 

    print(f"Final Cleaned Query: {clean_query}")
    return clean_query