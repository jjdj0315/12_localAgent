@echo off
echo ====================================
echo Local LLM Web Application
echo Development Environment Startup
echo ====================================
echo.

echo This script will start all services for local development:
echo 1. Mock LLM Service (port 8001)
echo 2. Backend API (port 8000)
echo 3. Frontend Web UI (port 3000)
echo.
echo Press Ctrl+C to stop all services
echo.
pause

echo.
echo Starting Mock LLM Service...
start "Mock LLM Service" cmd /k "cd llm-service && python mock_server.py"
timeout /t 3

echo Starting Backend API...
start "Backend API" cmd /k "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5

echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3

echo.
echo ====================================
echo All services started!
echo ====================================
echo.
echo Access the application:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Mock LLM: http://localhost:8001
echo.
echo Login credentials:
echo - Create admin user: cd backend ^&^& python -m scripts.create_admin
echo.
echo Press any key to open the application in browser...
pause
start http://localhost:3000
