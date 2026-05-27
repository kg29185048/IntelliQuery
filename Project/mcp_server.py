"""
MCP Server — Remote SSE tool definitions for IntelliQuery.

This module is imported by api/main.py and mounted as an SSE endpoint.
It exposes two tools to Claude Desktop:
  1. list_workspaces  — discover available workspaces for the authenticated user
  2. ask_database     — query a specific workspace's database via natural language
"""

import sys
import os
import json
import threading

# UTF-8 encoding fix for Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure Python can find the project modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from mcp.server.fastmcp import FastMCP
from database.mongo_client import get_db, get_db_from_uri
from database.sql_client import get_sql_engine
from database.sql_schema_extractor import extract_sql_schema
from agents.router_agent import run_pipeline
from agents.sql_agent import run_sql_pipeline
from api.utils.encryption import decrypt_uri
from bson import ObjectId

# ──────────────────────────────────────────────────────────────
# Thread-local storage for authenticated user context.
# The auth middleware in api/main.py sets this before each
# MCP tool invocation so tools know WHO is calling.
# ──────────────────────────────────────────────────────────────
_user_context = threading.local()


def set_current_mcp_user(user: dict | None):
    """Called by the auth middleware to inject the authenticated user."""
    _user_context.user = user


def get_current_mcp_user() -> dict | None:
    """Retrieve the authenticated user inside MCP tools."""
    return getattr(_user_context, "user", None)


# ──────────────────────────────────────────────────────────────
# Initialize the MCP Server
# ──────────────────────────────────────────────────────────────
mcp = FastMCP("IntelliQuery LangGraph Engine")


# ──────────────────────────────────────────────────────────────
# Tool 1: List Workspaces
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def list_workspaces() -> str:
    """
    List all database workspaces the authenticated user has access to.
    Returns workspace names, IDs, database types, permissions,
    and available collections/tables to help pick the right one for a query.
    """
    user = get_current_mcp_user()
    if not user:
        return "❌ Authentication required. Please configure your JWT token in Claude Desktop."

    user_id = user.get("id") or str(user.get("_id", ""))
    app_db = get_db()

    # Find all workspace memberships for this user
    memberships = list(app_db["workspace_members"].find({"user_id": user_id}))
    if not memberships:
        return "📭 You don't have access to any workspaces yet. Create or join one in the IntelliQuery web app."

    workspace_ids = [ObjectId(m["workspace_id"]) for m in memberships]
    workspaces = list(app_db["workspaces"].find({"_id": {"$in": workspace_ids}}))

    results = []
    for ws in workspaces:
        ws_id = str(ws["_id"])
        member = next((m for m in memberships if m["workspace_id"] == ws_id), None)
        if not member:
            continue

        entry = {
            "workspace_id": ws_id,
            "name": ws.get("name", "Unnamed"),
            "db_type": ws.get("db_type", "mongodb"),
            "your_role": member.get("role", "user"),
            "your_permission": member.get("permission", "read_only"),
        }

        # Fetch schema preview (collections/tables) for smarter routing
        try:
            db_uri = decrypt_uri(ws["db_uri"])
            db_type = ws.get("db_type", "mongodb")

            if db_type == "sql" and db_uri:
                engine = get_sql_engine(db_uri)
                schema = extract_sql_schema(engine)
                entry["tables"] = list(schema.keys())[:20]
            else:
                db_name = ws.get("db_name")
                target_db = get_db_from_uri(db_uri, db_name)
                collections = target_db.list_collection_names()
                entry["collections"] = [c for c in collections if not c.startswith("system.")][:20]
        except Exception:
            entry["schema_preview"] = "Unable to fetch — check workspace DB connection"

        results.append(entry)

    return json.dumps(results, indent=2, default=str)


# ──────────────────────────────────────────────────────────────
# Tool 2: Ask Database
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def ask_database(workspace_id: str, user_query: str) -> str:
    """
    Query a specific workspace's database using natural language.
    Call list_workspaces first to get the workspace_id.

    This triggers a multi-agent LangGraph pipeline that automatically
    fetches the schema, generates a safe query, validates it,
    executes it, and returns the results.

    Args:
        workspace_id: The ID of the workspace to query (from list_workspaces).
        user_query: Your natural language question about the database.
    """
    user = get_current_mcp_user()
    if not user:
        return "❌ Authentication required. Please configure your JWT token in Claude Desktop."

    user_id = user.get("id") or str(user.get("_id", ""))
    app_db = get_db()

    # ── Verify workspace exists ──
    try:
        workspace = app_db["workspaces"].find_one({"_id": ObjectId(workspace_id)})
    except Exception:
        return f"❌ Invalid workspace ID: {workspace_id}"

    if not workspace:
        return f"❌ Workspace not found: {workspace_id}"

    # ── Verify user membership & get permission ──
    member = app_db["workspace_members"].find_one({
        "workspace_id": workspace_id,
        "user_id": user_id,
    })
    if not member:
        return f"❌ Access denied. You are not a member of workspace '{workspace.get('name', workspace_id)}'."

    permission_level = member.get("permission", "read_only")
    db_type = workspace.get("db_type", "mongodb")

    print(f"\n[MCP] User '{user.get('name', user_id)}' querying workspace '{workspace.get('name')}': {user_query}", file=sys.stderr)

    # ── Resolve database connection (uses cached singleton) ──
    try:
        db_uri = decrypt_uri(workspace["db_uri"])
    except Exception as e:
        return f"❌ Failed to decrypt database URI: {e}"

    # ── Run the appropriate pipeline ──
    try:
        if db_type == "sql" and db_uri:
            engine = get_sql_engine(db_uri)
            schema = extract_sql_schema(engine)
            pipeline_state = run_sql_pipeline(
                engine, user_query, schema,
                history=None,
                permission_level=permission_level,
            )
        else:
            db_name = workspace.get("db_name")
            target_db = get_db_from_uri(db_uri, db_name)
            pipeline_state = run_pipeline(
                target_db,
                user_query=user_query,
                history=None,
                permission_level=permission_level,
            )
    except Exception as e:
        print(f"[MCP] Pipeline error: {e}", file=sys.stderr)
        return f"❌ Pipeline Error:\n{str(e)}"

    # ── Handle errors ──
    if "error" in pipeline_state:
        print(f"[MCP] Pipeline failed: {pipeline_state['error']}", file=sys.stderr)
        error_msg = f"❌ Pipeline Error:\n{pipeline_state['error']}"
        if pipeline_state.get("suggestions"):
            error_msg += "\n\n💡 Suggestions:\n" + "\n".join(f"  • {s}" for s in pipeline_state["suggestions"])
        return error_msg

    # ── Format successful output ──
    query_data = pipeline_state.get("query", {})
    query_str = json.dumps(query_data, indent=2, default=str) if isinstance(query_data, dict) else str(query_data)

    results_data = pipeline_state.get("result", [])
    results_str = json.dumps(results_data, indent=2, default=str)

    formatted_output = (
        f"✅ Query Executed Successfully\n"
        f"📂 Workspace: {workspace.get('name', workspace_id)}\n\n"
        f"--- Generated {'SQL' if db_type == 'sql' else 'MongoDB'} Query ---\n"
        f"{query_str}\n\n"
        f"--- Agent Explanation ---\n"
        f"{pipeline_state.get('explanation', 'No explanation generated.')}\n\n"
        f"--- Execution Results ---\n"
        f"{results_str}"
    )

    return formatted_output