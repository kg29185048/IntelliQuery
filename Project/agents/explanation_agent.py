from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY
from prompts.explanation_prompt import EXPLAIN_PROMPT


llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
)

def explain_query(query):
    prompt = EXPLAIN_PROMPT.format(query=query)

    response = llm.invoke(prompt)

    return response.content   # 🔥 IMPORTANT