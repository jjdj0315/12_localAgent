@echo off
echo ========================================
echo Local LLM MVP 시작 스크립트
echo ========================================
echo.

echo [1/5] Docker 컨테이너 빌드 및 시작...
docker-compose -f docker-compose.dev.yml up --build -d
if errorlevel 1 (
    echo 오류: Docker 컨테이너 시작 실패
    echo Docker Desktop이 실행 중인지 확인하세요.
    pause
    exit /b 1
)
echo ✓ 컨테이너 시작 완료
echo.

echo [2/5] 데이터베이스 준비 대기 중... (15초)
timeout /t 15 /nobreak > nul
echo ✓ 대기 완료
echo.

echo [3/5] 데이터베이스 마이그레이션 실행...
docker-compose -f docker-compose.dev.yml exec -T backend alembic upgrade head
if errorlevel 1 (
    echo 오류: 마이그레이션 실패
    echo 로그를 확인하세요: docker-compose -f docker-compose.dev.yml logs backend
    pause
    exit /b 1
)
echo ✓ 마이그레이션 완료
echo.

echo [4/5] 관리자 계정 생성...
docker-compose -f docker-compose.dev.yml exec -T backend python scripts/create_admin.py --username admin --password Admin123!
echo ✓ 관리자 계정 생성 완료
echo.

echo [5/5] 서비스 상태 확인...
docker-compose -f docker-compose.dev.yml ps
echo.

echo ========================================
echo MVP 시작 완료!
echo ========================================
echo.
echo 다음 주소로 접속하세요:
echo   - 프론트엔드: http://localhost:3000
echo   - 백엔드 API: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo.
echo 로그인 정보:
echo   - 사용자명: admin
echo   - 비밀번호: Admin123!
echo.
echo 로그 확인: docker-compose -f docker-compose.dev.yml logs -f
echo 중지: docker-compose -f docker-compose.dev.yml down
echo.
pause
