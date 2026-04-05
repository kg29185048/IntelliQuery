import sys
import os
import json

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure Python can find your app/database/agents folders
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from mcp.server.fastmcp import FastMCP
from database.mongo_client import get_db

# Import your LangGraph entry point
from agents.router_agent import run_pipeline

# 1. Initialize the Server
mcp = FastMCP("IntelliQuery LangGraph Engine")

# 2. Connect to the Database once when the server boots
print("Initializing Database Connection for MCP...", file=sys.stderr)
db = get_db()

# 3. Define the single tool that triggers your graph
@mcp.tool()
def ask_database(user_query: str) -> str:
    """
    Ask a natural language question about the database. 
    This triggers a multi-agent LangGraph pipeline that automatically fetches the schema, 
    generates a safe MongoDB query, validates it, executes it, and returns the results.
    """
    print(f"\n[MCP] Claude triggered pipeline with: {user_query}", file=sys.stderr)
    
    # Run your compiled LangGraph pipeline
    # We pass 'history=None' since Claude manages its own conversation history
    pipeline_state = run_pipeline(db, user_query=user_query, history=None)
    
    # Handle Pipeline Errors (Validation failures, Execution failures, Retry limits hit)
    if "error" in pipeline_state:
        print(f"[MCP] Pipeline failed: {pipeline_state['error']}", file=sys.stderr)
        return f"❌ Pipeline Error:\n{pipeline_state['error']}"
        
    # Safely format the JSON query
    query_data = pipeline_state.get('query', {})
    query_str = json.dumps(query_data, indent=2) if isinstance(query_data, dict) else str(query_data)
    
    # Safely format the results (handling potential ObjectIds if they slipped through)
    results_data = pipeline_state.get('result', [])
    results_str = json.dumps(results_data, indent=2, default=str)
    
    # Format the final output to send back to Claude
    formatted_output = (
        f"✅ Query Executed Successfully\n\n"
        f"--- Generated MongoDB Query ---\n"
        f"{query_str}\n\n"
        f"--- Agent Explanation ---\n"
        f"{pipeline_state.get('explanation', 'No explanation generated.')}\n\n"
        f"--- Execution Results ---\n"
        f"{results_str}"
    )
    
    return formatted_output

if __name__ == "__main__":
    # Start the server using standard input/output
    mcp.run()