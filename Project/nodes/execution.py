# agents/execution_agent.py

import re

def execute_query(db, query):
    try:
        match = re.search(r"db\.(\w+)\.find", query)
        if not match:
            return "Invalid query format"

        collection = match.group(1)
        return list(db[collection].find().limit(10))

    except Exception as e:
        return str(e)