@echo off
echo ========================================
echo Local LLM MVP 중지 스크립트
echo ========================================
echo.

echo Docker 컨테이너 중지 중...
docker-compose -f docker-compose.dev.yml down

echo.
echo ✓ 모든 컨테이너가 중지되었습니다.
echo.
echo 데이터를 포함하여 완전히 삭제하려면:
echo   docker-compose -f docker-compose.dev.yml down -v
echo.
pause
