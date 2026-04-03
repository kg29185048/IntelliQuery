from agents.query_agent import generate_query
from agents.validation_agent import validate_query

def run_pipeline(db, user_query):
    try:
        # 1. Schema (you can improve later)
        schema = "Collection: users, Fields: [name, email, age]" 

        # 2. Generate query
        query_dict = generate_query(user_query, schema)

        # 3. Validate
        is_valid, msg = validate_query(query_dict)
        if not is_valid:
            return {"error": msg}

        # =========================================================
        # 🔥 INSERT SUPPORT (NEW CODE ADDED)
        # =========================================================
        if isinstance(query_dict, dict) and query_dict.get("operation") == "insert":
            collection_name = query_dict.get("collection", "users")
            collection = db[collection_name]

            data = query_dict.get("data", {})

            if not data:
                return {"error": "No data provided for insert"}

            try:
                result = collection.insert_one(data)

                return {
                    "query": query_dict,
                    "explanation": f"Inserted into {collection_name}",
                    "result": f"✅ Document added with ID: {str(result.inserted_id)}"
                }

            except Exception as e:
                error_msg = str(e)
                print("INSERT ERROR:", error_msg)

                # 🔥 HANDLE DUPLICATE KEY ERROR
                if "E11000" in error_msg:
                    return {
                        "query": query_dict,
                        "explanation": "Insert failed",
                        "result": "❌ Duplicate value error (unique field already exists)"
                    }

                return {
                    "query": query_dict,
                    "explanation": "Insert failed",
                    "result": f"❌ Error: {error_msg}"
                }

        # =========================================================
        # ✅ EXISTING READ LOGIC (UNCHANGED)
        # =========================================================
        collection = db['users'] 
        
        filter_query = query_dict.get("filter", {})
        projection_query = query_dict.get("projection", {})

        cursor = collection.find(filter_query, projection_query)
        results = list(cursor)

        # Format results
        if not results:
            result_display = "No users found."
        else:
            result_display = [doc.get("name") for doc in results if "name" in doc]

        return {
            "query": query_dict, 
            "explanation": "Searching for documents matching your criteria...",
            "result": result_display
        }

    except Exception as e:
        return {"error": str(e)}