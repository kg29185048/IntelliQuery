# from agents.schema_agent import get_schema
# from agents.query_agent import generate_query
# from agents.validation_agent import validate_query
# from agents.execution_agent import execute_query
# from agents.explanation_agent import explain_query

# def run_pipeline(db, user_query):
#     schema = get_schema(db)

#     query = generate_query(user_query, schema)

#     print("Generated Query:", query, type(query))  # ✅ debug

#     valid, msg = validate_query(query)
#     if not valid:
#         return {"error": msg}

#     result = execute_query(db, query)
#     explanation = explain_query(query)
#     print("Generated Query:", query, type(query))
#     return {
#         "query": query,
#         "explanation": explanation,
#         "result": result
#     }
from agents.query_agent import generate_query
from agents.validation_agent import validate_query
# from agents.explanation_agent import explain_query # If you have one

def run_pipeline(db, user_query):
    try:
        # 1. Get the Schema (Ensure this function exists in your db logic)
        schema = "Collection: users, Fields: [name, email, age]" 

        # 2. Generate the Query (Returns a DICT)
        query_dict = generate_query(user_query, schema)

        # 3. Validate (Expects a DICT)
        is_valid, msg = validate_query(query_dict)
        if not is_valid:
            return {"error": msg}

        # 4. Execute Query
        # If user asks for "names", we should project 'name'
        # For now, let's fetch the data based on the generated filter
        collection = db['users'] 
        
        # We use .find(query_dict) because it's a dictionary now!
        cursor = collection.find(query_dict, {"name": 1, "_id": 0})
        results = list(cursor)

        # 5. Format results for Streamlit
        if not results:
            result_display = "No users found."
        else:
            # Extract just the names into a clean list
            result_display = [doc.get("name") for doc in results if "name" in doc]

        return {
            "query": query_dict, 
            "explanation": "Searching for documents matching your criteria...",
            "result": result_display
        }

    except Exception as e:
        return {"error": str(e)}