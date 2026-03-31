import re

MAX_LIMIT = 50


def execute_query(db, query_data: dict) -> dict:
    try:
        # =========================
        # 1. Validate input
        # =========================
        if not isinstance(query_data, dict):
            return fail("Invalid query format")

        collection_name = query_data.get("collection")
        query = query_data.get("query", {})
        sort = query_data.get("sort", {})
        limit = query_data.get("limit", 10)

        # =========================
        # 2. Collection validation
        # =========================
        if not collection_name:
            return fail("Collection not specified")

        if collection_name not in db.list_collection_names():
            return fail(f"Collection '{collection_name}' does not exist")

        collection = db[collection_name]

        # =========================
        # 3. Safety limit
        # =========================
        if not isinstance(limit, int) or limit <= 0:
            limit = 10

        limit = min(limit, MAX_LIMIT)

        # =========================
        # 4. Execute query
        # =========================
        cursor = collection.find(query)

        # =========================
        # 5. Apply sorting
        # =========================
        if isinstance(sort, dict) and sort:
            cursor = cursor.sort(list(sort.items()))

        cursor = cursor.limit(limit)

        result = list(cursor)

        # =========================
        # 6. Empty result handling
        # =========================
        if not result:
            return {
                "status": "success",
                "data": [],
                "message": "No matching records found"
            }

        # =========================
        # 7. Convert ObjectId
        # =========================
        for doc in result:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        return fail(str(e))


def fail(msg: str) -> dict:
    return {
        "status": "error",
        "error": msg
    }