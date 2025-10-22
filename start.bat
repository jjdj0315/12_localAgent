@echo off
echo ========================================
echo Starting Local LLM MVP
echo ========================================
echo.

echo Step 1/5: Building and starting Docker containers...
docker-compose -f docker-compose.dev.yml up --build -d
if errorlevel 1 (
    echo ERROR: Failed to start containers
    echo Please check if Docker Desktop is running
    pause
    exit /b 1
)
echo SUCCESS: Containers started
echo.

echo Step 2/5: Waiting for database... (15 seconds)
timeout /t 15 /nobreak > nul
echo SUCCESS: Wait complete
echo.

echo Step 3/5: Running database migrations...
docker-compose -f docker-compose.dev.yml exec -T backend alembic upgrade head
if errorlevel 1 (
    echo ERROR: Migration failed
    echo Check logs: docker-compose -f docker-compose.dev.yml logs backend
    pause
    exit /b 1
)
echo SUCCESS: Migration complete
echo.

echo Step 4/5: Creating admin account...
docker-compose -f docker-compose.dev.yml exec -T backend python scripts/create_admin.py --username admin --password Admin123!
echo SUCCESS: Admin account created
echo.

echo Step 5/5: Checking service status...
docker-compose -f docker-compose.dev.yml ps
echo.

echo ========================================
echo MVP Started Successfully!
echo ========================================
echo.
echo Open in browser:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo.
echo Login credentials:
echo   - Username: admin
echo   - Password: Admin123!
echo.
echo View logs: docker-compose -f docker-compose.dev.yml logs -f
echo Stop: docker-compose -f docker-compose.dev.yml down
echo.
pause
