# 'update' is removed. Destructive commands are kept to prevent data loss.
FORBIDDEN_WORDS = ["delete", "drop", "remove", "$out", "$merge"]

def validate_query(query):
    print("Validation Input:", query, type(query))

    if not isinstance(query, dict):
        return False, "Invalid query format: Expected a dictionary"

    # Convert dict to string for a quick security scan
    query_str = str(query).lower()
    for word in FORBIDDEN_WORDS:
        if word in query_str:
            return False, f"Security Violation: '{word}' is not allowed. Deletions are forbidden."

    return True, "Valid query"