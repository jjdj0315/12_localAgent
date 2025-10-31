@echo off
REM Local LLM Web Application - Quick Start Script
REM Use docker-compose.yml for production deployment

echo ========================================
echo Local LLM Web Application
echo ========================================
echo.

echo [1/4] Starting Docker containers...
docker-compose up --build -d
if errorlevel 1 (
    echo ERROR: Failed to start containers
    echo Please check if Docker Desktop is running
    pause
    exit /b 1
)
echo SUCCESS: Containers started
echo.

echo [2/4] Waiting for database initialization... (15 seconds)
timeout /t 15 /nobreak > nul
echo.

echo [3/4] Running database migrations...
docker-compose exec -T backend alembic upgrade head
if errorlevel 1 (
    echo WARNING: Migration may have failed. Check logs if needed.
)
echo.

echo [4/4] Creating admin account...
docker-compose exec -T backend python scripts/create_admin.py --username admin --password Admin123!
echo.

echo ========================================
echo Application Started Successfully!
echo ========================================
echo.
echo Access the application:
echo   Frontend:   http://localhost:3000
echo   Backend:    http://localhost:8000/docs
echo   Health:     http://localhost:8000/health
echo.
echo Default admin credentials:
echo   Username: admin
echo   Password: Admin123!
echo.
echo Common commands:
echo   View logs:  docker-compose logs -f
echo   Stop:       docker-compose down
echo   Restart:    docker-compose restart
echo.
pause
