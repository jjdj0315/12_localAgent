@echo off
REM Local LLM Web Application - Stop Script

echo ========================================
echo Stopping Local LLM Web Application
echo ========================================
echo.

echo Stopping Docker containers...
docker-compose down

echo.
echo SUCCESS: All containers stopped
echo.
echo To remove data volumes (WARNING: deletes all data):
echo   docker-compose down -v
echo.
pause
