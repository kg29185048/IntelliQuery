# agents/schema_agent.py

from database.schema_extractor import extract_full_schema

def get_schema(db):
    full_schema = extract_full_schema(db)

    # 🔥 FUTURE: intelligent filtering (for now return all)
    return full_schema