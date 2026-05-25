# IntelliQuery Backend API

FastAPI backend for IntelliQuery - Natural Language to MongoDB and SQL Query System.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python api/main.py
```
Or using uvicorn directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`

---

## API Documentation

The backend is structured into Core API, Authentication (`/auth`), and Workspaces (`/workspaces`). Most Core and Workspace endpoints require JWT Authentication and an `X-Workspace-Id` header.

### Core Endpoints

- **`GET /health`** - Check API health status.
- **`GET /schema`** - Retrieve the database schema (tables/collections and fields) for the active workspace.
- **`POST /query`** - Process a natural language query and return the generated DB query, explanation, and query results.
- **`POST /extract-intent`** - Extract structured intent from a natural-language query before execution (Phase 1).
- **`POST /visualize`** - Generate an optimal chart configuration (recharts) based on query results data.
- **`POST /install-mcp`** - Install the IntelliQuery MCP server into the Claude Desktop configuration.

### Authentication (`/auth`)

- **`POST /auth/send-signup-otp`** - Generate and send an OTP to email for user registration.
- **`POST /auth/signup`** - Verify OTP and register a new user.
- **`POST /auth/login`** - Authenticate with email/password and return a JWT.
- **`POST /auth/forgot-password`** - Send OTP for password reset.
- **`POST /auth/reset-password`** - Verify OTP and reset password.
- **`POST /auth/google`** - Authenticate or register using a Google OAuth JWT token.

### Workspaces (`/workspaces`)

- **`POST /workspaces/`** - Create a new workspace (MongoDB or SQL).
- **`GET /workspaces/`** - List all workspaces the current user belongs to.
- **`POST /workspaces/join`** - Join a workspace using a 6-character join code.
- **`GET /workspaces/{workspace_id}/members`** - Get all members of a workspace (Admin only).
- **`PUT /workspaces/{workspace_id}/members/{user_id}`** - Update a member's permissions (`read_only` or `read_write`).
- **`DELETE /workspaces/{workspace_id}`** - Delete a workspace entirely (Admin only).
- **`DELETE /workspaces/{workspace_id}/members/{user_id}`** - Remove a member or leave the workspace.

---

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:5173` (Vite frontend)
- `http://localhost:3000` (Alternative frontend)
- `https://intelliquery-five.vercel.app` (Live Demo)

