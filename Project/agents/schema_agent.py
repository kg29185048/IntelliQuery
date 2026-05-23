# agents/schema_agent.py

from database.schema_extractor import extract_full_schema

def get_schema(db):
    full_schema = extract_full_schema(db)
    return full_schema