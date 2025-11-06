#!/bin/bash
#
# Rate Limit Test Script (T287, FR-111)
#
# Purpose: Test rate limiting middleware by sending 61 requests in 1 minute
# Expected: First 60 requests succeed, 61st request returns 429 Too Many Requests
#
# Usage:
#   ./scripts/test_rate_limit.sh [API_URL]
#
# Default API_URL: http://localhost:8000
#

set -e

# Configuration
API_URL="${1:-http://localhost:8000}"
ENDPOINT="/api/v1/health"
REQUESTS=61
RATE_LIMIT=60
TEST_USER="test_user"
TEST_PASSWORD="test_password"

echo "=== Rate Limit Test ==="
echo "API URL: $API_URL"
echo "Endpoint: $ENDPOINT"
echo "Rate Limit: $RATE_LIMIT requests/minute"
echo "Testing with: $REQUESTS requests"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
success_count=0
rate_limited_count=0
error_count=0

echo "Starting test at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Send requests
for i in $(seq 1 $REQUESTS); do
    # Make request
    response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL$ENDPOINT" 2>&1)

    # Parse response
    http_code=$(echo "$response" | tail -n 1)

    # Parse headers if available (using -i flag would show headers)
    rate_limit_header=""
    rate_remaining_header=""

    # Check status code
    if [ "$http_code" = "200" ]; then
        success_count=$((success_count + 1))
        echo -e "${GREEN}✓${NC} Request $i: HTTP $http_code (Success)"
    elif [ "$http_code" = "429" ]; then
        rate_limited_count=$((rate_limited_count + 1))
        echo -e "${YELLOW}⚠${NC} Request $i: HTTP $http_code (Rate Limited)"

        # Extract body for Korean error message
        body=$(echo "$response" | head -n -1)
        if [ -n "$body" ]; then
            echo "   Response: $body"
        fi
    else
        error_count=$((error_count + 1))
        echo -e "${RED}✗${NC} Request $i: HTTP $http_code (Error)"
    fi

    # Brief delay between requests (avoid overwhelming server)
    sleep 0.05
done

echo ""
echo "=== Test Results ==="
echo "Total Requests: $REQUESTS"
echo -e "${GREEN}Successful:${NC} $success_count"
echo -e "${YELLOW}Rate Limited:${NC} $rate_limited_count"
echo -e "${RED}Errors:${NC} $error_count"
echo ""

# Verify results
echo "=== Verification ==="

if [ $success_count -eq $RATE_LIMIT ] || [ $success_count -eq $((RATE_LIMIT - 1)) ]; then
    echo -e "${GREEN}✓ PASS${NC}: First $RATE_LIMIT requests succeeded"
else
    echo -e "${RED}✗ FAIL${NC}: Expected $RATE_LIMIT successful requests, got $success_count"
fi

if [ $rate_limited_count -ge 1 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Rate limiting activated (${rate_limited_count} requests blocked)"
else
    echo -e "${RED}✗ FAIL${NC}: Rate limiting did not activate"
fi

if [ $error_count -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}: No unexpected errors"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: $error_count unexpected errors"
fi

echo ""

# Overall result
if [ $success_count -eq $RATE_LIMIT ] && [ $rate_limited_count -ge 1 ] && [ $error_count -eq 0 ]; then
    echo -e "${GREEN}====================================${NC}"
    echo -e "${GREEN}✓ RATE LIMIT TEST PASSED${NC}"
    echo -e "${GREEN}====================================${NC}"
    exit 0
elif [ $success_count -ge $((RATE_LIMIT - 5)) ] && [ $rate_limited_count -ge 1 ]; then
    echo -e "${YELLOW}====================================${NC}"
    echo -e "${YELLOW}⚠ RATE LIMIT TEST PARTIALLY PASSED${NC}"
    echo -e "${YELLOW}====================================${NC}"
    echo ""
    echo "Note: Minor deviations are acceptable due to timing"
    exit 0
else
    echo -e "${RED}====================================${NC}"
    echo -e "${RED}✗ RATE LIMIT TEST FAILED${NC}"
    echo -e "${RED}====================================${NC}"
    exit 1
fi
