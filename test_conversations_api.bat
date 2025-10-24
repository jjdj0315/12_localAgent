@echo off
chcp 65001 >nul
echo ===================================
echo Phase 2 API 테스트 스크립트
echo ===================================
echo.

set API_URL=http://localhost:8000/api/v1
set COOKIE_FILE=test_cookies.txt

echo 1. 로그인 중...
curl -s -c %COOKIE_FILE% -X POST "%API_URL%/auth/login" -H "Content-Type: application/json" -d "{\"username\": \"admin\", \"password\": \"Admin123!\"}"
echo.
echo ✓ 로그인 완료
echo.

echo 2. 새 대화 생성 중...
curl -s -b %COOKIE_FILE% -X POST "%API_URL%/conversations" -H "Content-Type: application/json" -d "{\"title\": \"테스트 대화\", \"tags\": [\"테스트\", \"확인\"]}" > create_result.json
type create_result.json
echo.
echo ✓ 대화 생성 완료
echo.

echo 3. 대화 목록 조회 중 (최근 5개)...
curl -s -b %COOKIE_FILE% "%API_URL%/conversations?page=1&page_size=5"
echo.
echo ✓ 목록 조회 완료
echo.

echo 4. 대화 검색 테스트 (키워드: 테스트)...
curl -s -b %COOKIE_FILE% "%API_URL%/conversations?search=테스트"
echo.
echo ✓ 검색 완료
echo.

echo ===================================
echo 테스트 완료!
echo ===================================
echo.
echo 다음 확인 방법:
echo 1. 브라우저에서 http://localhost:8000/docs 접속
echo 2. /api/v1/conversations 섹션 확인
echo 3. Try it out 버튼으로 직접 테스트
echo.

del %COOKIE_FILE% 2>nul
del create_result.json 2>nul
pause
