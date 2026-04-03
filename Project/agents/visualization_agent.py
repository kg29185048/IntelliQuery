import json
from langchain_groq import ChatGroq
from prompts.visualization_prompt import VISUALIZATION_PROMPT
from app.config import GROQ_API_KEY # Adjust import based on your config location

# Force JSON mode to prevent free-text responses
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant"
).bind(response_format={"type": "json_object"})

def generate_visualization_config(user_query, data):
    # Pass only the first 5 records to save tokens and context window
    data_sample = data[:5] if isinstance(data, list) else data
    
    prompt = VISUALIZATION_PROMPT.format(
        user_query=user_query, 
        data=json.dumps(data_sample, default=str) # default=str handles remaining ObjectIds
    )
    
    response = llm.invoke(prompt)
    raw_output = response.content.strip()
    
    # Clean the output to ensure we just get the JSON
    try:
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
        config = json.loads(raw_output)
        return config
    except Exception as e:
        print(f"Viz Parse Error: {e}")
        return {"visualizable": False, "error": "Failed to parse visualization config"}