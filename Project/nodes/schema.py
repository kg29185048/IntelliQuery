# agents/schema_agent.py

from database.schema_extractor import extract_full_schema
from api.utils.cache_utils import ttl_cache

@ttl_cache(ttl_seconds=300)
def get_schema(db):
    full_schema = extract_full_schema(db)
    return full_schema