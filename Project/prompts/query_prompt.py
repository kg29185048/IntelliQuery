"""
Per-operation query generation prompts — Phase 2 of the two-phase query flow.

Each chain receives ONLY the variables it needs (already confirmed by the user
via the IntentCard). The LLM's job is narrowed to writing valid MongoDB syntax
for one specific operation — it no longer has to guess intent, collection, or fields.

All chains follow the LCEL pattern:  prompt | llm | JsonOutputParser()

Exported chains:
    find_chain        — for find operations
    aggregate_chain   — for aggregate operations
    insert_chain      — for insert operations
    update_chain      — for update operations
    get_query_chain() — router that picks the right chain by operation name
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import get_llm

_llm_json = get_llm(json_mode=True)
_parser   = JsonOutputParser()

# ===========================================================================
# FIND CHAIN
# ===========================================================================
_FIND_SYSTEM = """You are a MongoDB query generator. Generate a find query in valid JSON.

Collection: {collection}
Available fields in this collection: {schema_fields}
Goal: {goal}

Confirmed filters (convert these to MongoDB filter syntax):
{filters}

Projection fields (empty means return all):
{projection}

Sort: {sort}
Limit: {limit}

STRICT RULES:
1. Return ONLY a JSON object — no explanation, no markdown.
2. For text/category fields, use {{"$regex": "...", "$options": "i"}} for case-insensitive matching.
3. For genre/category synonyms, use alternation: "sci.fi|science.fiction".
4. NEVER add conditions not present in the confirmed filters above.
5. If multiple filters, combine with $and.
6. Include "projection" key only if projection fields are provided (exclude _id with 0).
7. Include "sort" key only if sort is specified.
8. Include "limit" key only if limit is specified.

Return format:
{{
  "operation": "find",
  "collection": "{collection}",
  "filter": {{}},
  "projection": {{}},
  "sort": {{}},
  "limit": <integer>
}}
"""

find_prompt = ChatPromptTemplate.from_messages([
    ("system", _FIND_SYSTEM),
    ("human",  "Generate the MongoDB find query now."),
])
find_chain = find_prompt | _llm_json | _parser


# ===========================================================================
# AGGREGATE CHAIN
# ===========================================================================
_AGGREGATE_SYSTEM = """You are a MongoDB aggregation pipeline generator.

Collection: {collection}
Available fields in this collection: {schema_fields}
Goal: {goal}

Required pipeline stages (in order): {aggregate_stages}

Pre-match filters to apply in $match (if any):
{filters}

STRICT RULES:
1. Return ONLY a JSON object — no explanation, no markdown.
2. Build the pipeline using ONLY the stages listed in "Required pipeline stages".
3. If "$match" is in the stages and filters are provided, add a $match stage first.
4. For "$group", always include "_id" and at least one accumulator ($sum, $avg, $max, $min, $count).
5. For "$sort", sort descending on the primary computed field unless goal says otherwise.
6. Use field names that exist in the collection schema above.
7. If a stage doesn't make sense for the goal, omit it rather than hallucinating.

Return format:
{{
  "operation": "aggregate",
  "collection": "{collection}",
  "pipeline": [
    {{"$match": {{}}}},
    {{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}},
    {{"$sort": {{"count": -1}}}}
  ]
}}
"""

aggregate_prompt = ChatPromptTemplate.from_messages([
    ("system", _AGGREGATE_SYSTEM),
    ("human",  "Generate the MongoDB aggregation pipeline now."),
])
aggregate_chain = aggregate_prompt | _llm_json | _parser


# ===========================================================================
# INSERT CHAIN
# ===========================================================================
_INSERT_SYSTEM = """You are a MongoDB document generator. Generate an insert document in valid JSON.

Collection: {collection}
Available fields in this collection: {schema_fields}
Goal: {goal}

STRICT RULES:
1. Return ONLY a JSON object — no explanation, no markdown.
2. Use ONLY fields that exist in the collection schema above.
3. Infer field values from the goal description.
4. Do not add an "_id" field — MongoDB generates it automatically.

Return format:
{{
  "operation": "insert",
  "collection": "{collection}",
  "data": {{
    "field1": "value1",
    "field2": "value2"
  }}
}}
"""

insert_prompt = ChatPromptTemplate.from_messages([
    ("system", _INSERT_SYSTEM),
    ("human",  "Generate the MongoDB insert document now."),
])
insert_chain = insert_prompt | _llm_json | _parser


# ===========================================================================
# UPDATE CHAIN
# ===========================================================================
_UPDATE_SYSTEM = """You are a MongoDB update query generator.

Collection: {collection}
Available fields in this collection: {schema_fields}
Goal: {goal}

Confirmed filters (documents to update — convert to MongoDB filter syntax):
{filters}

STRICT RULES:
1. Return ONLY a JSON object — no explanation, no markdown.
2. Use $set for updates unless goal implies $inc, $push, $pull, or $unset.
3. NEVER use $out, $merge, delete, or drop — these are forbidden.
4. The "update_data" must include a MongoDB update operator ($set, $inc, etc.).

Return format:
{{
  "operation": "update",
  "collection": "{collection}",
  "filter": {{}},
  "update_data": {{
    "$set": {{
      "field": "new_value"
    }}
  }}
}}
"""

update_prompt = ChatPromptTemplate.from_messages([
    ("system", _UPDATE_SYSTEM),
    ("human",  "Generate the MongoDB update query now."),
])
update_chain = update_prompt | _llm_json | _parser


# ===========================================================================
# CHAIN ROUTER
# ===========================================================================
_CHAIN_MAP = {
    "find":      find_chain,
    "aggregate": aggregate_chain,
    "insert":    insert_chain,
    "update":    update_chain,
}


def get_query_chain(operation: str):
    """Return the appropriate LCEL chain for the given operation name."""
    chain = _CHAIN_MAP.get(operation)
    if chain is None:
        raise ValueError(
            f"Unsupported operation: '{operation}'. "
            f"Expected one of: {list(_CHAIN_MAP.keys())}"
        )
    return chain
