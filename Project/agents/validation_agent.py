FORBIDDEN = ["$unset", "$out", "$merge"] # MongoDB specific forbidden operators

def validate_query(query):
    print("Validation Input:", query, type(query))

    if not isinstance(query, dict):
        return False, "Invalid query format: Expected a dictionary"

    # Convert dict to string just for a quick security scan
    query_str = str(query).lower()
    for word in ["delete", "drop", "update", "remove"]:
        if word in query_str:
            return False, f"Security Violation: {word} is not allowed"

    return True, "Valid query"