import json
from langchain_groq import ChatGroq
from utils.parser import extract_mongo_query
from prompts.query_prompt import QUERY_PROMPT

llm = ChatGroq(model_name="llama-3.1-8b-instant")

def generate_query(user_query, schema):
    prompt = QUERY_PROMPT.format(schema=schema, user_query=user_query)
    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    # Get the string version of the query from parser
    query_string = extract_mongo_query(raw_output)

    try:
        # Convert the string "{...}" into a real Python dict
        clean_query = json.loads(query_string)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        clean_query = {} 

    print(f"Final Query: {clean_query} | Type: {type(clean_query)}")
    return clean_query