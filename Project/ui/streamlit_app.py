
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# import streamlit as st
# import json
# from bson import ObjectId
# from database.mongo_client import get_db
# from agents.router_agent import run_pipeline

# class MongoJSONEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, ObjectId):
#             return str(obj)
#         return super().default(obj)

# st.set_page_config(page_title="Mongo Query AI", page_icon="🧠")
# st.title("🧠 NL → MongoDB Query System")

# query = st.text_input("Ask your question", placeholder="e.g. Show me all user names")

# if st.button("Run"):
#     if not query:
#         st.warning("Please enter a question first!")
#     else:
#         db = get_db()
#         response = run_pipeline(db, query)

#         if "error" in response:
#             st.error(f"Error: {response['error']}")
#         else:
#             # Displaying the Query
#             st.subheader("Generated Query")
#             # Convert dict to pretty JSON string for display
#             query_json = json.dumps(response["query"], indent=4, cls=MongoJSONEncoder)
#             st.code(query_json, language="json")

#             # Displaying the Explanation
#             st.subheader("Explanation")
#             st.info(response["explanation"])

#             # Displaying the Results
#             st.subheader("Result")
#             if isinstance(response["result"], list):
#                 # If it's a list of names, show them clearly
#                 for item in response["result"]:
#                     st.write(f"- {item}")
#             else:
#                 st.write(response["result"])

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
import pandas as pd
from bson import ObjectId

from database.mongo_client import get_db
from agents.router_agent import run_pipeline
from agents.visualization_agent import generate_visualization_config
from agents.schema_agent import get_schema

# Custom JSON encoder to handle MongoDB ObjectIds
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# --- App Config ---
st.set_page_config(page_title="Mongo Query AI", page_icon="🧠", layout="wide")
st.title("🧠 NL → MongoDB Query System")
st.markdown("Ask a natural language question to search, insert, or visualize your MongoDB data.")

# ==========================================
# INITIALIZE SESSION STATE MEMORY
# ==========================================
if "response" not in st.session_state:
    st.session_state.response = None
if "current_query" not in st.session_state:
    st.session_state.current_query = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {user, query, explanation, result}

# ==========================================
# SIDEBAR: DATABASE SCHEMA EXPLORER
# ==========================================
with st.sidebar:
    st.header("🗄️ Database Schema")
    st.caption("All available collections and their fields.")
    try:
        db = get_db()
        schema = get_schema(db)
        if schema:
            for collection, fields in schema.items():
                with st.expander(f"📁 {collection} ({len(fields)} fields)"):
                    for field in sorted(fields):
                        st.markdown(f"- `{field}`")
        else:
            st.info("No collections found in the database.")
    except Exception as e:
        st.error(f"Could not load schema: {e}")

    st.divider()
    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        st.session_state.response = None
        st.session_state.current_query = ""
        st.rerun()

# --- Chat History Display ---
for turn in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.markdown(f"**Explanation:** {turn['explanation']}")
        if isinstance(turn["result"], list):
            if len(turn["result"]) > 0:
                st.dataframe(pd.DataFrame(turn["result"]), use_container_width=True)
            else:
                st.write("No matching documents found.")
        else:
            st.write(turn["result"])

# --- User Input ---
query = st.chat_input("Ask your question (e.g. Show me sci-fi movies, then: make it after 2010)")

# 1. Fetch data and save it to memory
if query:
    with st.chat_message("user"):
        st.write(query)

    with st.spinner("Processing request..."):
        # Build history list for the LLM (last 5 turns to avoid token overflow)
        history_for_llm = [
            {"user": t["user"], "query": json.dumps(t.get("query", {}), cls=MongoJSONEncoder)}
            for t in st.session_state.chat_history[-5:]
        ]
        response = run_pipeline(db, query, history=history_for_llm)
        st.session_state.response = response
        st.session_state.current_query = query

        # Append to chat history
        st.session_state.chat_history.append({
            "user": query,
            "query": response.get("query", {}),
            "explanation": response.get("explanation", ""),
            "result": response.get("result", []),
        })

# 2. Render latest response
if st.session_state.response:
    response = st.session_state.response
    saved_query = st.session_state.current_query

    if "error" in response:
        st.error(f"Error: {response['error']}")
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("⚙️ Generated Query")
            query_json = json.dumps(response["query"], indent=4, cls=MongoJSONEncoder)
            st.code(query_json, language="json")

        with col2:
            st.subheader("💡 Explanation")
            st.info(response["explanation"])

        st.divider()

        st.subheader("📋 Result")
        result_data = response["result"]
        
        if isinstance(result_data, list) and len(result_data) > 0:
            df = pd.DataFrame(result_data)
            st.dataframe(df, use_container_width=True)
        elif isinstance(result_data, list) and len(result_data) == 0:
            st.write("No matching documents found.")
        else:
            st.write(result_data)

        # =========================================================
        # ON-DEMAND VISUALIZATION
        # =========================================================
        operation = response.get("query", {}).get("operation")
        is_visualizable_query = operation in ("find", "aggregate")
        
        if is_visualizable_query and isinstance(result_data, list) and len(result_data) > 0:
            
            st.write("") 
            
            # Because this is outside the "Run" button block, clicking it won't erase the screen!
            if st.button("📊 Generate Visualization"):
                with st.spinner("Analyzing data for the best chart..."):
                    
                    viz_config = generate_visualization_config(saved_query, result_data)
                    
                    if viz_config.get("visualizable"):
                        st.subheader(viz_config.get("title", "Data Chart"))
                        
                        chart_type = viz_config.get("chart_type")
                        x_col = viz_config.get("x_axis")
                        y_col = viz_config.get("y_axis")
                        
                        try:
                            if x_col in df.columns and y_col in df.columns:
                                if chart_type == "bar":
                                    st.bar_chart(df, x=x_col, y=y_col)
                                elif chart_type == "line":
                                    st.line_chart(df, x=x_col, y=y_col)
                                elif chart_type == "scatter":
                                    st.scatter_chart(df, x=x_col, y=y_col)
                                else:
                                    st.warning(f"AI requested an unsupported chart type: {chart_type}")
                            else:
                                st.error(f"The AI tried to plot X='{x_col}' and Y='{y_col}', but those columns aren't in the dataset.")
                        except Exception as e:
                            st.error(f"Chart render failed. Error: {e}")
                    else:
                        st.info("The AI determined this specific dataset isn't suitable for charting (e.g., missing numeric Y-axis values).")