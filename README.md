# IntelliQuery

# 🚀 Natural Language → MongoDB Query System

A multi-agent AI system that allows users to query MongoDB databases using plain English. The application translates natural language into executable MongoDB queries, validates them, executes them, explains the results, and optionally visualizes the output.

---

## 📌 Overview

Non-technical users often struggle with database querying due to the need for syntax knowledge. Even developers spend time writing repetitive queries.

This project solves that by enabling:

- 🧠 Natural language querying  
- ⚙️ Automated query generation  
- 🔒 Built-in query validation  
- 📊 Smart visualization suggestions  
- 💬 Human-readable explanations  

---


### 🔁 Flow Summary

1. User enters query in Streamlit UI  
2. `router_agent` orchestrates the pipeline  
3. `schema_agent` extracts database structure  
4. `query_agent` converts NL → MongoDB query  
5. `validation_agent` ensures safety  
6. Query is executed on MongoDB  
7. `explanation_agent` explains results  
8. `visualization_agent` generates charts (optional)  
9. Results displayed in UI  


---

## 🤖 Multi-Agent System

### 🔹 `router_agent`
- Central orchestrator
- Controls flow between all agents

### 🔹 `schema_agent`
- Extracts MongoDB schema dynamically
- Provides collection + field metadata

### 🔹 `query_agent`
- Converts natural language → structured JSON query
- Uses **Groq LLM (Llama 3.1 8B Instant)**

### 🔹 `validation_agent`
- Ensures query safety
- Blocks dangerous operations:
  - `delete`
  - `drop`
  - `remove`
  - `$out`
  - `$merge`

### 🔹 `execution_agent`
- Executes query on MongoDB
- Mostly handled inline within router

### 🔹 `explanation_agent`
- Converts query → plain English explanation
- Improves interpretability

### 🔹 `visualization_agent`
- Suggests best chart type using LLM
- Supports:
  - Bar charts
  - Line charts
  - Scatter plots

---

## ⚡ Supported Operations

- `find` → Retrieve documents  
- `insert` → Add new data  
- `update` → Modify existing data  
- `aggregate` → Perform analytics (grouping, counting, etc.)

---

## 🔄 Example Workflow

**User Input:**
Show me all users with gmail emails

**Generated Query:**
```json
{
  "operation": "find",
  "collection": "users",
  "filter": {
    "email": { "$regex": "gmail" }
  }
}
```

**Explanation:**
This query finds all users whose email contains 'gmail'

## 🧰 Tech Stack

| Component | Technology |
|----------|-----------|
| LLM | Groq API (Llama 3.1 8B Instant) |
| Backend | Python |
| Database | MongoDB Atlas (`sample_mflix`) |
| DB Driver | `pymongo` |
| LLM Framework | `langchain_groq` |
| UI | Streamlit |
| Config | `.env` (API keys & URI) |
