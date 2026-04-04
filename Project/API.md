# IntelliQuery Backend API

FastAPI backend for IntelliQuery - Natural Language to MongoDB Query System

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

## API Documentation

### Health Check
- **Endpoint:** `GET /health`
- **Response:** `{"status": "ok", "message": "IntelliQuery API is running"}`

### Process Query
- **Endpoint:** `POST /query`
- **Request:** `{"query": "Show me all active users"}`
- **Response:**
  ```json
  {
    "query": { /* MongoDB query object */ },
    "explanation": "This query finds all documents...",
    "result": [ /* Query results */ ]
  }
  ```

### Explain Query
- **Endpoint:** `POST /explain`
- **Request:** `{"query": "Show me all active users"}`
- **Response:**
  ```json
  {
    "explanation": "This query finds all documents...",
    "query": { /* MongoDB query object */ }
  }
  ```

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:5173` (Vite frontend)
- `http://localhost:3000` (Alternative frontend)
