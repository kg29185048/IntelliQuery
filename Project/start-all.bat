@echo off
REM Start IntelliQuery - Backend and Frontend

echo.
echo =====================================
echo   IntelliQuery - Full Stack Startup
echo =====================================
echo.

REM Check if Python and Node are installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    exit /b 1
)

echo ✓ Python found: 
python --version

echo ✓ Node.js found: 
node --version
echo.

REM Start Backend
echo Starting FastAPI Backend on http://localhost:8000...
start cmd /k "python api/main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start Frontend
echo Starting React Frontend on http://localhost:5173...
cd frontend
start cmd /k "npm run dev"

echo.
echo =====================================
echo   Startup Complete!
echo =====================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Press Ctrl+C in each terminal to stop
echo.
pause
