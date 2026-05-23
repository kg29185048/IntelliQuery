import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


@lru_cache(maxsize=1)
def get_llm(json_mode: bool = False):
    """
    Returns a cached ChatGroq instance.
    Using lru_cache ensures only one LLM client is created per process.
    Set json_mode=True to force JSON-only output (for agents that parse JSON).
    """
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
    )
    if json_mode:
        return llm.bind(response_format={"type": "json_object"})
    return llm