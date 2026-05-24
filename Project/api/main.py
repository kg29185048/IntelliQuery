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

app = FastAPI(title="IntelliQuery API", version="1.0.0")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])

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


class McpInstallRequest(BaseModel):
    groq_api_key: str
    mongo_uri: str


@app.post("/install-mcp")
async def install_mcp(request: McpInstallRequest):
    """Write the IntelliQuery MCP server entry into the Claude Desktop config file."""
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

        # Locate the venv Python relative to this api/ file's parent (project root)
        project_dir = Path(os.path.dirname(__file__)).parent
        if system == "Windows":
            venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
        else:
            venv_python = project_dir / ".venv" / "bin" / "python"

        python_exec = str(venv_python) if venv_python.exists() else sys.executable
        mcp_server_script = str(project_dir / "mcp_server.py")

        mcp_config = {
            "command": python_exec,
            "args": [mcp_server_script],
            "env": {
                "GROQ_API_KEY": request.groq_api_key,
                "MONGO_URI": request.mongo_uri,
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
