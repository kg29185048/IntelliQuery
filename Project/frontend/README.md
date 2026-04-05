# IntelliQuery Frontend

Modern React UI for IntelliQuery - Natural Language to MongoDB Query System

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build

```bash
npm run build
```

## Features

- 🧠 Natural language query input
- 🔍 MongoDB query visualization
- 💡 Query explanation
- 📊 Results display with table/list views
- 📜 Query history
- 🎨 Modern Bootstrap UI
- ⚡ Fast Vite development server

## API Endpoints

The frontend connects to a FastAPI backend at `http://localhost:8000`:

- `GET /health` - Health check
- `POST /query` - Process natural language query
- `POST /explain` - Get explanation for a query

## Project Structure

```
src/
├── components/
│   ├── QueryInput.jsx      - Query input form
│   ├── QueryResult.jsx     - Query result display
│   └── ResultsDisplay.jsx  - Results table/list
├── App.jsx                 - Main app component
├── App.css                 - App styles
└── main.jsx               - Entry point
```
