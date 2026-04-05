from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, List, Optional
import sys
import os
import traceback
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.mongo_client import get_db, get_db_from_uri
from database.sql_client import get_sql_engine
from database.sql_schema_extractor import extract_sql_schema
from agents.router_agent import run_pipeline
from agents.sql_agent import run_sql_pipeline
from agents.schema_agent import get_schema
from agents.visualization_agent import generate_visualization_config

app = FastAPI(title="IntelliQuery API", version="1.0.0")

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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

class QueryResponse(BaseModel):
    query: Any
    explanation: str
    result: Any

class VisualizeRequest(BaseModel):
    user_query: str
    result_data: List[Any]

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "IntelliQuery API is running"}

@app.get("/schema")
async def get_db_schema(
    x_mongo_uri: Optional[str] = Header(default=None),
    x_mongo_db:  Optional[str] = Header(default=None),
    x_sql_uri:   Optional[str] = Header(default=None),
    x_db_type:   Optional[str] = Header(default="mongodb"),
):
    """Return the database schema: tables/collections and their fields"""
    try:
        if x_db_type == "sql" and x_sql_uri:
            engine = get_sql_engine(x_sql_uri)
            schema = extract_sql_schema(engine)
        else:
            db = get_db_from_uri(x_mongo_uri, x_mongo_db) if x_mongo_uri else get_db()
            schema = get_schema(db)
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    x_mongo_uri: Optional[str] = Header(default=None),
    x_mongo_db:  Optional[str] = Header(default=None),
    x_sql_uri:   Optional[str] = Header(default=None),
    x_db_type:   Optional[str] = Header(default="mongodb"),
):
    """Process natural language query and return query, explanation, and results"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        history = [{"user": h.user, "query": h.query} for h in (request.history or [])]

        if x_db_type == "sql" and x_sql_uri:
            engine = get_sql_engine(x_sql_uri)
            schema = extract_sql_schema(engine)
            response = run_sql_pipeline(engine, request.query, schema, history=history)
        else:
            db = get_db_from_uri(x_mongo_uri, x_mongo_db) if x_mongo_uri else get_db()
            response = run_pipeline(db, request.query, history=history)

        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
