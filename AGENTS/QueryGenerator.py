# from dotenv import load_dotenv
# import os
# from google import genai

# load_dotenv()

# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Explain OOP in simple terms"
# )

# print(response.text)

from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

# Initialize client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 🔹 Load your prompt from file
import os

def load_prompt():
    try:
        # Get current file directory (agent/)
        current_dir = os.path.dirname(__file__)

        # Go one level up → project_root/
        base_dir = os.path.abspath(os.path.join(current_dir, ".."))

        # Build path to Prompt/QueryGen.txt
        prompt_path = os.path.join(base_dir, "Prompts", "QueryGen.txt")

        with open(prompt_path, "r") as f:
            return f.read()

    except Exception as e:
        raise Exception(f"Error loading prompt: {e}")

# 🔹 Example schema (later this will come from your Schema Agent)
def get_schema():
    return """
Collection: students
Fields:
- name (string)
- marks (int)
- subject (string)
"""

# 🔹 Query Generator Function
def generate_query(user_query):
    base_prompt = load_prompt()
    schema = get_schema()

    # Inject schema + user query into prompt
    final_prompt = f"""
{base_prompt}

### Database Schema:
{schema}

### User Query:
{user_query}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt
    )

    return response.text


# 🔹 Run
if __name__ == "__main__":
    user_query = "Show top 5 students with marks > 80 in DBMS"
    result = generate_query(user_query)
    print(result)