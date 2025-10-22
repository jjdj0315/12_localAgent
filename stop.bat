@echo off
echo ========================================
echo Stopping Local LLM MVP
echo ========================================
echo.

echo Stopping Docker containers...
docker-compose -f docker-compose.dev.yml down

echo.
echo SUCCESS: All containers stopped
echo.
echo To remove data volumes:
echo   docker-compose -f docker-compose.dev.yml down -v
echo.
pause
