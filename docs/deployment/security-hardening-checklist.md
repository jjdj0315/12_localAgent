# Security Hardening Deployment Checklist

**Purpose**: Production deployment validation checklist for security hardening features (FR-110~FR-114, Phase 11.6)

**Target Audience**: DevOps engineers, system administrators

**Last Updated**: 2025-11-05

---

## Pre-Deployment Configuration

### 1. Environment Configuration (FR-112)

**File**: `.env` or environment variables

```bash
# Set production environment (CRITICAL)
ENVIRONMENT=production

# Verify environment-based settings will apply:
# - Cookie secure flag: true (requires HTTPS)
# - Cookie SameSite: strict (prevents CSRF)
# - Session timeout: 30 minutes (1800 seconds)
```

**Validation**:
```bash
# Check environment variable
echo $ENVIRONMENT

# Expected: production
```

**Status**: ☐ Complete

---

### 2. HTTPS Certificate (FR-112)

**Requirement**: SSL/TLS certificate must be installed and valid

**Validation Steps**:
1. Visit `https://your-domain.com`
2. Click padlock icon in browser address bar
3. Verify certificate is valid and not expired
4. Verify certificate is issued by trusted CA

**Alternative CLI Validation**:
```bash
# Check certificate details
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Expected output:
# notBefore=...
# notAfter=... (future date)
```

**Status**: ☐ Complete

---

## Security Feature Validation

### 3. CSRF Protection (FR-110, T283-T286)

**Test All Admin Endpoints**:

```bash
# Test 1: POST without CSRF token → 403
curl -X POST https://your-domain.com/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test"}' \
  -w "\n%{http_code}\n"

# Expected: 403 Forbidden
# Response should contain Korean error: "CSRF 토큰이 유효하지 않습니다"

# Test 2: GET sets CSRF token cookie
curl -i https://your-domain.com/api/v1/conversations

# Expected: Set-Cookie header with csrf_token
# Cookie should have: secure; samesite=strict; max-age=1800

# Test 3: Login endpoint is exempt (no CSRF required)
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}' \
  -w "\n%{http_code}\n"

# Expected: 401 (authentication error, NOT 403 CSRF error)
```

**Status**: ☐ Complete

---

### 4. Rate Limiting (FR-111, T287-T288)

**Run Load Test**:

```bash
# Execute rate limit test script
bash scripts/test_rate_limit.sh https://your-domain.com

# Expected results:
# - First 60 requests: HTTP 200
# - 61st request: HTTP 429 (Too Many Requests)
# - Error message in Korean: "요청 횟수 제한을 초과했습니다"

# Manual test
for i in {1..65}; do
  curl -s -o /dev/null -w "%{http_code}\n" https://your-domain.com/api/v1/health
  sleep 0.5
done

# Expected: First 60 return 200, remaining return 429
```

**Acceptance Criteria**:
- ✓ First 60 requests succeed
- ✓ 61st request returns 429
- ✓ Error message in Korean

**Status**: ☐ Complete

---

### 5. Resource Limiting (FR-111, T287-T288)

**Test Concurrent Session Limits**:

```bash
# Test: 11th concurrent ReAct session → 503
# This requires simulating 11 simultaneous long-running requests

# Use GNU parallel or similar tool:
seq 1 12 | parallel -j 12 \
  'curl -X POST https://your-domain.com/api/v1/react/execute \
   -H "Content-Type: application/json" \
   -d '"'"'{"query": "test"}'"'"' \
   -w "\n%{http_code}\n"'

# Expected: 10 return 200, 1-2 return 503
# 503 response should contain: "ReAct 세션 용량이 초과되었습니다"
```

**Acceptance Criteria**:
- ✓ Max 10 concurrent ReAct sessions
- ✓ Max 5 concurrent Agent workflows
- ✓ 503 errors with Korean messages

**Status**: ☐ Complete

---

### 6. Log Masking (FR-112, T291-T292)

**Verify Tokens Masked in Logs**:

```bash
# Check application logs
docker-compose logs backend | grep -i "session_token\|password\|csrf_token\|bearer"

# Expected: All sensitive values should show [REDACTED]
# Example:
# {"session_token": "[REDACTED]", "user_id": 1, ...}
# {"password": "[REDACTED]", "username": "admin"}

# FAIL if you see actual token values:
# ✗ {"session_token": "abc123xyz", ...}  # BAD - not masked
```

**Test Patterns**:
```bash
# Trigger login to generate logs
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "test123"}'

# Check logs immediately
docker-compose logs --tail=50 backend | grep password

# Expected: password=[REDACTED] or "password": "[REDACTED]"
```

**Acceptance Criteria**:
- ✓ session_token values masked
- ✓ password values masked
- ✓ csrf_token values masked
- ✓ Bearer tokens masked

**Status**: ☐ Complete

---

### 7. Metric Collection Consistency (FR-113, T293-T295)

**Test Metric Timestamp Consistency**:

```bash
# Query recent metrics via API
curl https://your-domain.com/api/v1/metrics/current \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Or query database directly:
docker-compose exec db psql -U llm_app -d llm_webapp -c \
  "SELECT metric_type, collected_at FROM metric_snapshots
   WHERE collected_at = (SELECT MAX(collected_at) FROM metric_snapshots)
   ORDER BY metric_type;"

# Expected: All 6 metrics have IDENTICAL collected_at timestamp
# Example:
# active_users     | 2025-11-05 10:00:00+00
# storage_bytes    | 2025-11-05 10:00:00+00  # Same timestamp
# active_sessions  | 2025-11-05 10:00:00+00  # Same timestamp
# ...
```

**Database Isolation Level Check**:
```bash
docker-compose exec db psql -U llm_app -d llm_webapp -c \
  "SHOW transaction_isolation;"

# Expected: read committed
```

**Acceptance Criteria**:
- ✓ All metrics in same collection have identical timestamp
- ✓ Isolation level is READ COMMITTED
- ✓ No failed collections in last hour

**Status**: ☐ Complete

---

### 8. CSV Export Encoding (FR-114, T296-T299)

**Test on Windows**:

1. **Browser Test** (Windows machine):
   - Navigate to Admin Dashboard → Metrics Export
   - Select metrics: Active Users, Storage Bytes
   - Export format: CSV
   - Click "내보내기"
   - **Open downloaded CSV in Excel**

2. **Validation**:
   - ✓ File opens directly (no encoding dialog)
   - ✓ Korean characters display correctly: 활성 사용자, 저장소, 메트릭
   - ✓ Column headers are clean (no ï»¿ or weird symbols)
   - ✓ No garbled text or ??? symbols

**Test on Linux/Mac**:

1. **CLI Test**:
```bash
# Export CSV
curl -X POST https://your-domain.com/api/v1/metrics/export \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64)" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_types": ["active_users"],
    "granularity": "hourly",
    "start_time": "2025-11-01T00:00:00Z",
    "end_time": "2025-11-05T00:00:00Z",
    "format": "csv"
  }' | jq '.download_url'

# Download and check
wget http://your-domain.com/api/v1/metrics/exports/{filename}

# Verify encoding
file {filename}
# Expected: UTF-8 Unicode text (no BOM mentioned for Linux)

# Test with pandas
python3 -c "import pandas as pd; df = pd.read_csv('{filename}'); print(df.columns[0])"
# Expected: Clean column name, no BOM characters
```

2. **Validation**:
   - ✓ File is UTF-8 encoded
   - ✓ No BOM for Linux/Mac clients
   - ✓ pandas reads CSV without errors
   - ✓ First column name has no BOM artifacts

**Acceptance Criteria**:
- ✓ Windows: Opens in Excel without encoding dialog
- ✓ Linux/Mac: Plain UTF-8 without BOM
- ✓ Korean text displays correctly on all platforms

**Status**: ☐ Complete

---

## Automated Test Suite

Run comprehensive test suite before deployment:

```bash
# Run all security tests
cd backend
pytest tests/test_csrf.py -v
pytest tests/test_cookie_security.py -v
pytest tests/test_metric_consistency.py -v
pytest tests/test_encoding.py -v

# Expected: All tests pass (0 failures)
```

**Status**: ☐ Complete

---

## Production Smoke Test

After deployment, run quick smoke test:

```bash
# Health check
curl https://your-domain.com/health

# Expected: {"status": "healthy"}

# Admin auth check
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "$ADMIN_PASSWORD"}'

# Expected: Session token returned, no 403 errors

# Metrics API check
curl https://your-domain.com/api/v1/metrics/current \
  -H "Authorization: Bearer $TOKEN"

# Expected: Current metric values returned
```

**Status**: ☐ Complete

---

## Rollback Plan

If any validation fails:

1. **Revert to previous version**:
```bash
docker-compose down
git checkout <previous-stable-tag>
docker-compose up -d
```

2. **Check logs**:
```bash
docker-compose logs --tail=100 backend
docker-compose logs --tail=100 frontend
```

3. **Document issue** in incident log with:
   - Which check failed
   - Error messages observed
   - Logs captured

---

## Sign-Off

**Deployment Date**: _________________

**Deployed By**: _________________

**Validated By**: _________________

**Notes**:


---

## Appendix: Common Issues

### Issue 1: CSRF 403 on all requests

**Symptom**: All POST/PUT/DELETE requests return 403

**Cause**: ENVIRONMENT not set to production, or HTTPS not configured

**Solution**:
1. Verify `ENVIRONMENT=production` in .env
2. Verify HTTPS certificate is valid
3. Restart services: `docker-compose restart`

---

### Issue 2: Rate limiting not working

**Symptom**: Can send >60 requests without 429

**Cause**: Rate limit middleware not registered or in wrong order

**Solution**:
1. Check `backend/app/main.py` middleware stack
2. Verify RateLimitMiddleware is registered
3. Restart backend service

---

### Issue 3: Korean text garbled in Excel

**Symptom**: Korean text shows as ??? or boxes in Excel

**Cause**: BOM not added for Windows clients

**Solution**:
1. Check User-Agent detection in `backend/app/api/v1/metrics.py`
2. Verify `add_bom=is_windows` parameter is passed
3. Test with Windows User-Agent header

---

## References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Rate Limiting Best Practices](https://www.nginx.com/blog/rate-limiting-nginx/)
- [UTF-8 BOM for Windows Compatibility](https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8)
- Project Specification: `specs/001-local-llm-webapp/spec.md` (FR-110~FR-114)
