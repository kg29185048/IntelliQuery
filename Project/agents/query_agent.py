
import json
from langchain_groq import ChatGroq
from utils.parser import extract_mongo_query
from prompts.query_prompt import QUERY_PROMPT
from app.config import GROQ_API_KEY

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"}) # <-- THIS IS THE MAGIC BULLET


def _is_spurious_condition(value) -> bool:
    """Return True if a field value is a bare \\d{4} regex — always a hallucination."""
    if not isinstance(value, dict):
        return False
    regex = value.get("$regex", "")
    return regex in (r"\d{4}", r"\\d{4}")


def _get_regex_value(condition: dict) -> str:
    """Extract the $regex string from a single-field condition dict, or '' if none."""
    if not isinstance(condition, dict):
        return ""
    for val in condition.values():
        if isinstance(val, dict) and "$regex" in val:
            return val["$regex"]
    return ""


def _is_contaminated_by(cond_a: dict, cond_b: dict) -> bool:
    """
    Return True if cond_a's regex is an alternation that contains cond_b's regex
    as one of its terms — meaning a proper noun from cond_b leaked into cond_a.
    Example: cond_a genres regex "roberta|romantic|romance", cond_b title regex "roberta"
    → cond_a is contaminated.
    """
    regex_a = _get_regex_value(cond_a)
    regex_b = _get_regex_value(cond_b)
    if not regex_a or not regex_b or "|" not in regex_a:
        return False
    # cond_b must be a simple term (no alternation — it's a proper noun / identifier)
    if "|" in regex_b:
        return False
    terms_a = [t.strip().lower() for t in regex_a.split("|")]
    return regex_b.strip().lower() in terms_a


def _strip_spurious(d: dict) -> dict:
    """Remove any top-level key whose value is a spurious condition."""
    return {k: v for k, v in d.items() if not _is_spurious_condition(v)}


def _cleanup_filter(filter_dict: dict) -> dict:
    """
    Strip hallucinated conditions from LLM-generated filters.
    1. Removes bare \\d{4} regex conditions (top-level and inside $and).
    2. Removes any condition whose alternation regex is contaminated by a proper noun
       that also appears as a simpler regex in another condition (e.g. genres leaking title).
    """
    if not isinstance(filter_dict, dict):
        return filter_dict

    if "$and" in filter_dict:
        conditions = [
            _strip_spurious(c) if isinstance(c, dict) else c
            for c in filter_dict["$and"]
        ]
        conditions = [c for c in conditions if c]  # drop empties

        # Detect which conditions are contaminated by a proper noun from another condition
        to_remove = set()
        for i, cond_a in enumerate(conditions):
            for j, cond_b in enumerate(conditions):
                if i != j and _is_contaminated_by(cond_a, cond_b):
                    to_remove.add(i)

        conditions = [c for idx, c in enumerate(conditions) if idx not in to_remove]

        if len(conditions) == 0:
            return {}
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    # Top-level: remove any key whose value matches the spurious pattern
    return _strip_spurious(filter_dict)

def generate_query(user_query, schema, feedback=None, history=None):
    if feedback:
        user_query = f"{user_query}\n\n[Previous attempt failed: {feedback}. Fix the query and try again.]"
    history_text = ""
    if history:
        history_text = "\n".join(
            f"User: {turn['user']}\nGenerated Query: {turn['query']}" for turn in history
        )
    prompt = QUERY_PROMPT.format(schema=schema, user_query=user_query, history=history_text)
    
    # Get the response
    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    print("\n" + "="*50)
    print("RAW LLM OUTPUT:")
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

    # Strip hallucinated conditions (e.g. spurious released: {$regex: \d{4}})
    if isinstance(clean_query, dict) and "filter" in clean_query:
        clean_query["filter"] = _cleanup_filter(clean_query["filter"])

    print(f"Final Cleaned Query: {clean_query}")
    return clean_query