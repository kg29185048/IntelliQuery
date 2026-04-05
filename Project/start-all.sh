#!/bin/bash
# Start IntelliQuery - Backend and Frontend

echo ""
echo "====================================="
echo "  IntelliQuery - Full Stack Startup"
echo "====================================="
echo ""

# Check if Python and Node are installed
if ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    exit 1
fi

echo "✓ Python found: $(python --version)"
echo "✓ Node.js found: $(node --version)"
echo ""

# Start Backend in background
echo "Starting FastAPI Backend on http://localhost:8000..."
python api/main.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start Frontend
echo "Starting React Frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "====================================="
echo "  Startup Complete!"
echo "====================================="
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
