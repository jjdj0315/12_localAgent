@echo off
echo ========================================
echo Rebuilding Local LLM MVP
echo ========================================
echo.

echo Step 1: Stopping containers...
docker-compose -f docker-compose.dev.yml down
echo.

echo Step 2: Rebuilding backend container...
docker-compose -f docker-compose.dev.yml build --no-cache backend
echo.

echo Step 3: Starting all containers...
docker-compose -f docker-compose.dev.yml up -d
echo.

echo Step 4: Waiting for database... (20 seconds)
timeout /t 20 /nobreak > nul
echo.

echo Step 5: Running database migrations...
docker-compose -f docker-compose.dev.yml exec -T backend alembic upgrade head
if errorlevel 1 (
    echo ERROR: Migration failed
    echo Checking logs...
    docker-compose -f docker-compose.dev.yml logs backend
    pause
    exit /b 1
)
echo SUCCESS: Migration complete
echo.

echo Step 6: Creating admin account...
docker-compose -f docker-compose.dev.yml exec -T backend python scripts/create_admin.py --username admin --password Admin123!
echo.

echo Step 7: Checking service status...
docker-compose -f docker-compose.dev.yml ps
echo.

echo ========================================
echo Rebuild Complete!
echo ========================================
echo.
echo Open in browser:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000/docs
echo.
echo Login: admin / Admin123!
echo.
pause
