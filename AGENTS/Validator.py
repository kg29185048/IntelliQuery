FORBIDDEN_OPERATORS = {"$unset", "$out", "$merge"}
FORBIDDEN_KEYWORDS = {"delete", "drop", "update", "remove"}


def validate_query(query: dict, schema: dict) -> dict:
    """
    Validates MongoDB query for:
    - structure
    - safety
    - schema correctness
    """

    # =========================
    # 1. Basic Structure Check
    # =========================
    if not isinstance(query, dict):
        return fail("Query must be a dictionary")

    if not query:
        return fail("Empty query not allowed")

    # =========================
    # 2. Deep Scan (recursive)
    # =========================
    def scan(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():

                # 🚫 Forbidden Mongo operators
                if key in FORBIDDEN_OPERATORS:
                    return f"Forbidden operator used: {key}"

                # 🚫 Forbidden keywords
                if isinstance(key, str) and key.lower() in FORBIDDEN_KEYWORDS:
                    return f"Forbidden keyword detected: {key}"

                # ✅ Validate field names
                if not key.startswith("$"):  # not an operator
                    if key not in schema_fields:
                        return f"Unknown field: {key}"

                # 🔁 Recurse
                res = scan(value)
                if res:
                    return res

        elif isinstance(obj, list):
            for item in obj:
                res = scan(item)
                if res:
                    return res

        return None

    # Flatten schema fields
    schema_fields = set()
    for col in schema:
        schema_fields.update(schema[col])

    # Run scan
    error = scan(query)
    if error:
        return fail(error)

    # =========================
    # 3. Logical Checks
    # =========================
    # Full scan detection
    if query == {}:
        return fail("Full collection scan not allowed")

    return {
        "status": "pass",
        "query": query,
        "confidence": 0.9
    }


def fail(msg: str) -> dict:
    return {
        "status": "fail",
        "query": {},
        "error": msg,
        "confidence": 0.0
    }