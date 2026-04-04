# IntelliQuery - Full Stack Setup Guide

Complete step-by-step guide to set up and run the IntelliQuery application with React frontend and FastAPI backend.

## Project Structure

```
Project/
├── app/                    # Core application
│   ├── main.py
│   ├── config.py
│   └── ...
├── agents/                 # AI agents
│   ├── router_agent.py
│   ├── query_agent.py
│   └── ...
├── database/               # MongoDB integration
│   ├── mongo_client.py
│   ├── schema_extractor.py
│   └── ...
├── prompts/                # Agent prompts
│   └── ...
├── api/                    # FastAPI Backend (NEW)
│   └── main.py
├── frontend/               # React Frontend (NEW)
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── ...
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── requirements.txt        # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB running (for database operations)

## Backend Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or with conda:
```bash
conda create -n intelliquery python=3.10
conda activate intelliquery
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=intelliquery
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Start the FastAPI Backend

```bash
python api/main.py
```

Or with uvicorn:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Endpoint:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Node Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at **http://localhost:5173**

## Usage

1. **Open your browser** and go to http://localhost:5173
2. **Enter your query** in natural language (e.g., "Show me all active users")
3. **Click "Submit Query"** to process
4. **View results:**
   - 🔍 Generated MongoDB query
   - 💡 Explanation of what the query does
   - 📊 Results displayed in table or list format

## Features

### Frontend Features
- ✨ Modern React UI with Bootstrap styling
- 🎨 Gradient design with smooth animations
- 📜 Query history sidebar (last 10 queries)
- 📊 Smart results display (tables, lists, JSON)
- ⚡ Real-time query processing
- 📱 Fully responsive design

### Backend Features
- 🧠 Advanced NLP using LangChain
- 🔄 Multi-agent orchestration with LangGraph
- 🗄️ MongoDB integration
- 🛡️ CORS-enabled API
- 📝 Interactive API documentation
- ✅ Error handling and validation

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Process Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all users with status active"}'
```

### Response Structure
```json
{
  "query": {
    "find": "users",
    "filter": { "status": "active" }
  },
  "explanation": "This query retrieves all user documents where the status field equals 'active'.",
  "result": [...]
}
```

## Build for Production

### Frontend Build
```bash
cd frontend
npm run build
```

Output will be in `frontend/dist/`

### Backend Production
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### Issue: Frontend can't connect to backend
- Check if FastAPI is running on `http://localhost:8000`
- Verify CORS configuration in [api/main.py](api/main.py)
- Check browser console for error details

### Issue: MongoDB connection fails
- Ensure MongoDB is running: `mongod`
- Check `MONGODB_URI` in `.env` file
- Verify MongoDB credentials

### Issue: Slow API responses
- Check AI model availability (Groq API)
- Verify `GROQ_API_KEY` in `.env`
- Check MongoDB indexing on frequently queried fields

### Issue: Frontend won't start
- Clear `node_modules`: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 16+)
- Check port 5173 availability

## Development Tips

### Frontend
- Styles use CSS modules with Bootstrap
- Components: QueryInput, QueryResult, ResultsDisplay
- Modify [frontend/src/App.css](frontend/src/App.css) for theme changes
- Add new components in [frontend/src/components/](frontend/src/components/)

### Backend
- Main API in [api/main.py](api/main.py)
- Agents in [agents/](agents/)
- Database client in [database/mongo_client.py](database/mongo_client.py)
- Modify CORS allowed origins in api/main.py for different deployments

## Deployment

### Docker (Optional)
Create `Dockerfile` and `docker-compose.yml` for containerized deployment.

### Environment Variables
Make sure to set these for production:
- `MONGODB_URI` - Production MongoDB connection
- `GROQ_API_KEY` - Your Groq API key
- `ENVIRONMENT` - Set to "production"

## Support & Documentation

- **Frontend Docs:** [frontend/README.md](frontend/README.md)
- **API Docs:** [API.md](API.md)
- **Swagger UI:** http://localhost:8000/docs (when backend is running)

---

**Created:** 2026-04-04 | **Version:** 1.0.0
