import re
import json

def extract_mongo_query(llm_output):
    # 1. Try to find content inside find(...)
    # This regex looks for find( and grabs everything until the last )
    match = re.search(r"\.find\(\s*(\{.*?\})\s*\)", llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 2. If not found, try to find any JSON block { ... }
    json_match = re.search(r"(\{.*\})", llm_output, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()

    return "{}" # Fallback to empty filter string