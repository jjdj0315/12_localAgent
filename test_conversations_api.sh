#!/bin/bash
# Phase 2 Conversations API Test Script

API_URL="http://localhost:8000/api/v1"
COOKIE_FILE="test_cookies.txt"

echo "==================================="
echo "Phase 2 API Test Script"
echo "==================================="
echo ""

# 1. Login
echo "1. 로그인 중..."
LOGIN_RESPONSE=$(curl -s -c $COOKIE_FILE -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}')
echo "✓ 로그인 완료: $LOGIN_RESPONSE"
echo ""

# 2. Create conversation
echo "2. 새 대화 생성 중..."
CREATE_RESPONSE=$(curl -s -b $COOKIE_FILE -X POST "$API_URL/conversations" \
  -H "Content-Type: application/json" \
  -d '{"title": "테스트 대화", "tags": ["테스트", "확인"]}')
echo "✓ 생성됨: $CREATE_RESPONSE"
CONV_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "  대화 ID: $CONV_ID"
echo ""

# 3. List conversations
echo "3. 대화 목록 조회 중..."
LIST_RESPONSE=$(curl -s -b $COOKIE_FILE "$API_URL/conversations?page=1&page_size=5")
TOTAL=$(echo $LIST_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "✓ 총 대화 수: $TOTAL"
echo ""

# 4. Get conversation detail
echo "4. 대화 상세 조회 중..."
GET_RESPONSE=$(curl -s -b $COOKIE_FILE "$API_URL/conversations/$CONV_ID")
echo "✓ 대화 상세: $GET_RESPONSE"
echo ""

# 5. Update conversation
echo "5. 대화 수정 중..."
UPDATE_RESPONSE=$(curl -s -b $COOKIE_FILE -X PATCH "$API_URL/conversations/$CONV_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "수정된 테스트", "tags": ["수정됨"]}')
echo "✓ 수정됨: $UPDATE_RESPONSE"
echo ""

# 6. Search conversations
echo "6. 대화 검색 중 (키워드: '수정')..."
SEARCH_RESPONSE=$(curl -s -b $COOKIE_FILE "$API_URL/conversations?search=수정")
SEARCH_COUNT=$(echo $SEARCH_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "✓ 검색 결과: $SEARCH_COUNT 개"
echo ""

# 7. Filter by tag
echo "7. 태그 필터링 중 (태그: '수정됨')..."
TAG_RESPONSE=$(curl -s -b $COOKIE_FILE "$API_URL/conversations?tag=수정됨")
TAG_COUNT=$(echo $TAG_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "✓ 태그 필터 결과: $TAG_COUNT 개"
echo ""

# 8. Delete conversation
echo "8. 대화 삭제 중..."
DELETE_RESPONSE=$(curl -s -b $COOKIE_FILE -X DELETE "$API_URL/conversations/$CONV_ID" -w "\nHTTP Status: %{http_code}")
echo "✓ 삭제됨: $DELETE_RESPONSE"
echo ""

# Cleanup
rm -f $COOKIE_FILE

echo "==================================="
echo "모든 테스트 완료!"
echo "==================================="
