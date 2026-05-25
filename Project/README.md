# IntelliQuery

🚀 **Live Demo:** [https://intelliquery-five.vercel.app/](https://intelliquery-five.vercel.app/)

**IntelliQuery** is a powerful, full-stack application designed to translate natural language into structured MongoDB queries using advanced AI agents. By bridging the gap between human language and database syntax, IntelliQuery empowers users to easily explore, query, and understand their data without needing to write complex database commands.

## Overview

IntelliQuery leverages a modern technology stack to deliver a seamless and intelligent data querying experience:
- **Backend:** A robust API built with FastAPI, integrating LangChain and LangGraph for advanced multi-agent orchestration. It supports multiple database engines including **MongoDB** and **SQL** databases.
- **Frontend:** A dynamic, responsive React interface powered by Vite and Bootstrap, ensuring a fast and intuitive user experience.
- **AI Core:** Employs advanced NLP models (via Groq API) across specialized agents (Router, Intent Extraction, SQL, Visualization, etc.) to accurately interpret user intent, validate safety, and generate precise database operations along with human-readable explanations.
- **Security & Multi-Tenancy:** Features robust authentication and a workspace model with member permission controls, making it enterprise-ready.

## Features

- **Natural Language to Query (Mongo & SQL):** Simply type what you want to know, and the system generates the precise query, automatically routing to the correct SQL or NoSQL database.
- **Interactive Intent Confirmation:** Smartly extracts query intents and allows users to confirm them before execution.
- **Query Explanation & Suggestions:** Transparent insights into how the generated query works and intelligent follow-up suggestions.
- **Smart Results & Visualization:** View database results in tabular or list formats, and automatically generate optimal chart configurations for data visualization.
- **Multi-Tenant Workspaces:** Securely manage access via workspaces, encrypting database URIs and enforcing member-specific permissions.
- **Claude Desktop Integration:** Includes an MCP server for seamless integration with Claude Desktop.
- **Modern & Responsive UI:** A premium interface with query history tracking that works beautifully across all devices.

## Tech Stack

- **Frontend:** React, Vite, Bootstrap, CSS Modules
- **Backend:** Python, FastAPI, Pydantic
- **AI & Orchestration:** LangChain, LangGraph, Groq API
- **Databases:** MongoDB, SQL (via SQLAlchemy engines)
- **Security & Auth:** JWT, Google OAuth, Bcrypt, Cryptography (Fernet)
- **Integration:** Model Context Protocol (MCP)

---

## Local Initialization

Follow these steps to get the project running on your local machine.

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **MongoDB** (Running locally on default port `27017` or configured via URI)

### 1. Environment Configuration

Create a `.env` file in the root directory and configure the following variables:
```env
# AI Model Configuration
GROQ_API_KEY=your_groq_api_key_here

# Main Application Database (Workspaces, Users, History)
MONGO_URI=mongodb://localhost:27017/intelliquery

# Authentication & Encryption
JWT_SECRET=your_super_secret_jwt_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id

# Email configuration (Optional, for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 2. Backend Setup

Open a terminal in the root directory and install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend server:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
*The API will be available at `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`).*

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install the Node.js dependencies and start the development server:

```bash
npm install
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

---

## Further Documentation

- For a detailed, comprehensive setup guide, please refer to [SETUP.md](./SETUP.md).
- For API endpoints and backend specifics, see [API.md](./API.md).
- For frontend details, visit the [Frontend README](./frontend/README.md).
