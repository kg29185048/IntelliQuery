# from dotenv import load_dotenv
# import os
# from google import genai
# from Project.agents.schema_agent import get_schema

# load_dotenv()

# # Initialize client
# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# # 🔹 Load your prompt from file
# import os

# def load_prompt():
#     try:
#         # Get current file directory (agent/)
#         current_dir = os.path.dirname(__file__)

#         # Go one level up → project_root/
#         base_dir = os.path.abspath(os.path.join(current_dir, ".."))

#         # Build path to Prompt/QueryGen.txt
#         prompt_path = os.path.join(base_dir, "Prompts", "QueryGen.txt")

#         with open(prompt_path, "r") as f:
#             return f.read()

#     except Exception as e:
#         raise Exception(f"Error loading prompt: {e}")




# # 🔹 Query Generator Function
# def generate_query(user_query, db):
#     base_prompt = load_prompt()
    
#     # 🔥 Get real schema from schema agent
#     schema = get_schema(db)

#     final_prompt = f"""
# {base_prompt}

# ### Database Schema:
# {schema}

# ### User Query:
# {user_query}
# """

#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=final_prompt
#     )

#     return response.text


import json
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from Project.agents.schema_agent import get_schema
from Prompts.QueryGen import QUERY_PROMPT

# 🔹 Load environment variables
load_dotenv()

# 🔹 Initialize LLM (once)
llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# ============================================================
# 🔹 JSON Extraction + Safe Parsing
# ============================================================

def extract_json(text: str) -> str:
    """
    Extract JSON object from text if extra text is present.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text
    except Exception:
        return text


def safe_json_loads(text: str):
    """
    Safely parse JSON. Attempts repair if needed.
    """
    try:
        return json.loads(text)
    except Exception:
        try:
            cleaned = extract_json(text)
            return json.loads(cleaned)
        except Exception:
            return None


# ============================================================
# 🔹 Output Validation
# ============================================================

def fail(msg: str) -> dict:
    return {
        "status": "error",
        "collection": None,
        "query": {},
        "explanation": "",
        "clarification_question": "",
        "confidence": 0.0,
        "error": msg
    }


def validate_output(result: dict) -> dict:
    """
    Ensure LLM output follows strict schema.
    """

    required_keys = [
        "status",
        "query",
        "explanation",
        "clarification_question",
        "confidence"
    ]

    for key in required_keys:
        if key not in result:
            return fail(f"Missing key: {key}")

    status = result.get("status")

    # ✅ SUCCESS CASE
    if status == "success":
        if not isinstance(result["query"], dict):
            return fail("Query must be a dictionary")

    # ✅ AMBIGUOUS CASE
    elif status == "ambiguous":
        if not result["clarification_question"]:
            return fail("Clarification question missing")

        result["query"] = {}  # enforce consistency

    # ✅ ERROR CASE
    elif status == "error":
        result["query"] = {}
        if not result.get("error"):
            result["error"] = "Unknown error"

    else:
        return fail("Invalid status value")

    return result


# ============================================================
# 🔹 Main Query Generator
# ============================================================

def generate_query(user_query: str, db, retries: int = 2) -> dict:
    """
    Generate MongoDB query from natural language.

    Returns structured output:
    {
        status: "success | ambiguous | error",
        query: {},
        explanation: "",
        clarification_question: "",
        confidence: float,
        error: ""
    }
    """

    # 🔹 Get schema once
    schema = get_schema(db)

    for attempt in range(retries + 1):
        try:
            prompt = QUERY_PROMPT.format(
                schema=schema,
                user_query=user_query
            )

            response = llm.invoke(prompt)
            raw_output = response.content.strip()

            # 🔥 Safe parse
            result = safe_json_loads(raw_output)

            if result is None:
                raise ValueError("Invalid JSON from LLM")

            validated = validate_output(result)

            # ✅ Accept success OR ambiguity
            if validated["status"] in ["success", "ambiguous"]:
                return validated

        except Exception as e:
            print(f"[Retry {attempt}] Error: {e}")

    # ❌ Final fallback
    return {
        "status": "error",
        "collection": None,
        "query": {},
        "explanation": "",
        "clarification_question": "",
        "confidence": 0.0,
        "error": "Failed to generate valid response after retries"
    }