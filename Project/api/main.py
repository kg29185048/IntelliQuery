from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, List, Optional
import sys
import os
import json
import platform
import traceback
from pathlib import Path

# Add project root to sys.path so we can import from 'api', 'database', 'agents', etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from api.routes.auth import router as auth_router
from api.routes.workspaces import router as workspaces_router
from api.dependencies import get_current_user
from api.utils.encryption import decrypt_uri
from bson import ObjectId



load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database.mongo_client import get_db, get_db_from_uri
from database.sql_client import get_sql_engine
from database.sql_schema_extractor import extract_sql_schema
from agents.router_agent import run_pipeline, extract_intent_pipeline
from agents.sql_agent import run_sql_pipeline
from agents.schema_agent import get_schema
from agents.visualization_agent import generate_visualization_config
from mcp_server import mcp, set_current_mcp_user
from api.utils.jwt_handler import verify_token, create_access_token

app = FastAPI(title="IntelliQuery API", version="1.0.0")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])

# ── JWT Auth Middleware for MCP SSE endpoint ──
# Wraps the MCP SSE Starlette app with auth so that every MCP tool
# invocation knows which user is calling.
from starlette.types import ASGIApp, Scope, Receive, Send

class McpAuthMiddleware:
    """ASGI middleware that validates JWT from the Authorization header
    and injects the authenticated user into mcp_server's thread-local context."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            # Extract Authorization header
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("utf-8")

            user = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload = verify_token(token)
                    user_id = payload.get("user_id")
                    if user_id:
                        app_db = get_db()
                        user_doc = app_db["users"].find_one({"_id": ObjectId(user_id)})
                        if user_doc:
                            user_doc["id"] = str(user_doc["_id"])
                            user = user_doc
                except Exception:
                    pass  # Invalid token — user stays None, tools return auth error

            set_current_mcp_user(user)

        await self.app(scope, receive, send)

# Mount FastMCP SSE Transport with JWT auth middleware
_mcp_sse = mcp.sse_app()
app.mount("/mcp", McpAuthMiddleware(_mcp_sse))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error"},
    )

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://intelliquery-five.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class HistoryItem(BaseModel):
    user: str
    query: str

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[HistoryItem]] = []
    confirmed: bool = False
    confirmed_intent: Optional[Any] = None   # Structured intent confirmed via IntentCard

class QueryResponse(BaseModel):
    query: Any
    explanation: str
    result: Any
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None
    requires_confirmation: Optional[bool] = None

class VisualizeRequest(BaseModel):
    user_query: str
    result_data: List[Any]

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "IntelliQuery API is running"}

@app.get("/schema")
async def get_db_schema(
    x_workspace_id: str = Header(..., alias="X-Workspace-Id"),
    current_user: dict = Depends(get_current_user)
):
    """Return the database schema: tables/collections and their fields"""
    try:
        app_db = get_db()
        
        # Verify workspace access
        member = app_db["workspace_members"].find_one({
            "workspace_id": x_workspace_id,
            "user_id": current_user["id"]
        })
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
            
        workspace = app_db["workspaces"].find_one({"_id": ObjectId(x_workspace_id)})
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        db_type = workspace.get("db_type", "mongodb")
        db_uri = decrypt_uri(workspace["db_uri"])
        db_name = workspace.get("db_name")

        if db_type == "sql" and db_uri:
            engine = get_sql_engine(db_uri)
            schema = extract_sql_schema(engine)
        else:
            db = get_db_from_uri(db_uri, db_name) if db_uri else app_db
            schema = get_schema(db)
        return {"schema": schema}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id"),
    current_user: dict = Depends(get_current_user)
):
    """Process natural language query and return query, explanation, and results"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        app_db = get_db()
        
        # Verify workspace access and permission
        member = app_db["workspace_members"].find_one({
            "workspace_id": x_workspace_id,
            "user_id": current_user["id"]
        })
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
            
        permission_level = member.get("permission", "read_only")
            
        workspace = app_db["workspaces"].find_one({"_id": ObjectId(x_workspace_id)})
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        history = [{"user": h.user, "query": h.query} for h in (request.history or [])]
        
        db_type = workspace.get("db_type", "mongodb")
        db_uri = decrypt_uri(workspace["db_uri"])
        db_name = workspace.get("db_name")

        if db_type == "sql" and db_uri:
            engine = get_sql_engine(db_uri)
            schema = extract_sql_schema(engine)
            response = run_sql_pipeline(engine, request.query, schema, history=history, permission_level=permission_level)
        else:
            db = get_db_from_uri(db_uri, db_name) if db_uri else app_db

            response = run_pipeline(
                db,
                request.query,
                history=history,
                confirmed=request.confirmed,
                confirmed_intent=request.confirmed_intent,
                permission_level=permission_level,
            )
        if response.get("requires_confirmation"):
            return {
                "query": response.get("query"),
                "explanation": response.get("explanation", ""),
                "result": [],
                "requires_confirmation": True,
            }

        if "error" in response:
            # Soft failure with suggestions — return 200 so the frontend can show chips
            if "suggestions" in response:
                return {
                    "query": None,
                    "explanation": "",
                    "result": [],
                    "error": response["error"],
                    "suggestions": response["suggestions"],
                }
            # Hard error (safety block, validation failure) — return 200 so frontend shows the message
            return {
                "query": None,
                "explanation": "",
                "result": [],
                "error": response["error"],
            }

        return {
            "query": response.get("query", {}),
            "explanation": response.get("explanation", ""),
            "result": response.get("result", [])
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/visualize")
async def get_visualization(request: VisualizeRequest):
    """Ask AI for the best chart config for the given data"""
    try:
        config = generate_visualization_config(request.user_query, request.result_data)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExtractIntentRequest(BaseModel):
    query: str
    history: Optional[List[HistoryItem]] = []


@app.post("/extract-intent")
async def extract_intent_endpoint(
    request: ExtractIntentRequest,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id"),
    current_user: dict = Depends(get_current_user),
):
    """
    Phase 1 — extract structured intent from a natural-language query.
    Returns an extracted_intent dict for the frontend IntentCard,
    or an error + suggestions if the query is irrelevant to the schema.
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        app_db = get_db()

        # Verify workspace access
        member = app_db["workspace_members"].find_one({
            "workspace_id": x_workspace_id,
            "user_id": current_user["id"]
        })
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")

        workspace = app_db["workspaces"].find_one({"_id": ObjectId(x_workspace_id)})
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        db_type = workspace.get("db_type", "mongodb")
        if db_type == "sql":
            raise HTTPException(status_code=400, detail="Intent extraction is only supported for MongoDB.")

        db_uri = decrypt_uri(workspace["db_uri"])
        db_name = workspace.get("db_name")
        db = get_db_from_uri(db_uri, db_name) if db_uri else app_db

        history = [{"user": h.user, "query": h.query} for h in (request.history or [])]
        response = extract_intent_pipeline(db, request.query, history=history)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── MCP Token Generation ──
# Long-lived tokens for MCP (30 days) so users don't have to
# refresh constantly. Regular web JWT expires in 60 min.
import jwt as pyjwt
from datetime import datetime, timedelta

MCP_TOKEN_EXPIRE_DAYS = 30


@app.post("/mcp-token")
async def generate_mcp_token(current_user: dict = Depends(get_current_user)):
    """Generate a long-lived JWT token specifically for MCP / Claude Desktop use."""
    from api.utils.jwt_handler import SECRET_KEY, ALGORITHM
    payload = {
        "user_id": current_user["id"],
        "purpose": "mcp",
        "exp": datetime.utcnow() + timedelta(days=MCP_TOKEN_EXPIRE_DAYS),
    }
    token = pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "token": token,
        "expires_in_days": MCP_TOKEN_EXPIRE_DAYS,
        "usage": "Add this token to your Claude Desktop MCP config as an Authorization header.",
    }


class McpInstallRequest(BaseModel):
    mcp_token: str


@app.post("/install-mcp")
async def install_mcp(request: Request, body: McpInstallRequest):
    """Write the IntelliQuery remote MCP server entry into the Claude Desktop config file.
    Uses a URL-based config with JWT auth header instead of a local command."""
    try:
        system = platform.system()
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            if not appdata:
                raise HTTPException(status_code=500, detail="APPDATA environment variable not found")
            config_path = Path(appdata) / "Claude" / "claude_desktop_config.json"
        elif system == "Darwin":
            config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            raise HTTPException(status_code=400, detail="Unsupported OS. Claude Desktop supports Windows and macOS only.")

        # Build remote MCP config — URL-based with auth header
        server_base = "https://intelliquery.onrender.com"
        mcp_config = {
            "url": f"{server_base}/mcp/sse",
            "headers": {
                "Authorization": f"Bearer {body.mcp_token}"
            }
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                config_data = {}

        config_data.setdefault("mcpServers", {})
        config_data["mcpServers"]["intelliquery-agent"] = mcp_config

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        return {"success": True, "config_path": str(config_path)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
