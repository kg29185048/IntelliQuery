# # ui/streamlit_app.py

# import streamlit as st
# from database.mongo_client import get_db
# from agents.router_agent import run_pipeline

# st.title("🧠 NL → MongoDB Query System")

# query = st.text_input("Ask your question")

# if st.button("Run"):
#     db = get_db()
#     response = run_pipeline(db, query)

#     if "error" in response:
#         st.error(response["error"])
#     else:
#         st.subheader("Generated Query")
#         st.code(response["query"])

#         st.subheader("Explanation")
#         st.write(response["explanation"])

#         st.subheader("Result")
#         st.write(response["result"])
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
from bson import ObjectId
from database.mongo_client import get_db
from agents.router_agent import run_pipeline

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

st.set_page_config(page_title="Mongo Query AI", page_icon="🧠")
st.title("🧠 NL → MongoDB Query System")

query = st.text_input("Ask your question", placeholder="e.g. Show me all user names")

if st.button("Run"):
    if not query:
        st.warning("Please enter a question first!")
    else:
        db = get_db()
        response = run_pipeline(db, query)

        if "error" in response:
            st.error(f"Error: {response['error']}")
        else:
            # Displaying the Query
            st.subheader("Generated Query")
            # Convert dict to pretty JSON string for display
            query_json = json.dumps(response["query"], indent=4, cls=MongoJSONEncoder)
            st.code(query_json, language="json")

            # Displaying the Explanation
            st.subheader("Explanation")
            st.info(response["explanation"])

            # Displaying the Results
            st.subheader("Result")
            if isinstance(response["result"], list):
                # If it's a list of names, show them clearly
                for item in response["result"]:
                    st.write(f"- {item}")
            else:
                st.write(response["result"])