import re

# Words banned inside the generated query dict
FORBIDDEN_WORDS = ["delete", "drop", "remove", "$out", "$merge"]

# Patterns that flag a destructive intent in the raw user question
_DESTRUCTIVE_PATTERNS = re.compile(
    r"\b(delete|drop|remove|truncate|wipe|purge|erase|clear all|destroy|merge into|insert into|\$merge|\$out)\b",
    re.IGNORECASE
)


def check_destructive_intent(user_query: str):
    """Check the raw natural-language query for destructive intent.
    Returns (is_safe: bool, message: str).
    """
    match = _DESTRUCTIVE_PATTERNS.search(user_query)
    if match:
        word = match.group(1)
        return False, (
            f"\u26a0\ufe0f Unsafe query detected: '{word}' operations are not permitted. "
            "IntelliQuery is a read-only interface — it supports SELECT / find / aggregate queries only. "
            "Destructive operations (delete, drop, remove, merge, etc.) are blocked to protect your data."
        )
    return True, "Safe"


def validate_query(query):
    print("Validation Input:", query, type(query))

    if not isinstance(query, dict):
        return False, "Invalid query format: Expected a dictionary"

    # Convert dict to string for a quick security scan
    query_str = str(query).lower()
    for word in FORBIDDEN_WORDS:
        if word in query_str:
            return False, (
                f"\u26a0\ufe0f Unsafe query blocked: '{word}' operations are not permitted. "
                "IntelliQuery only allows read queries (find / aggregate). "
                "Destructive operations are disabled to protect your data."
            )

    return True, "Valid query"