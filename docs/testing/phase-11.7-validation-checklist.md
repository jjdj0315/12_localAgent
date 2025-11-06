# Phase 11.7: Quality & Operational Fixes - Validation Checklist

**Phase**: 11.7 Quality & Operational Fixes (Post-Implementation Review)  
**Requirements**: FR-115, FR-116, FR-117, FR-118, FR-119, FR-120, FR-121, FR-122  
**Success Criteria**: SC-033, SC-034, SC-035, SC-036, SC-037, SC-038, SC-039, SC-040  
**Date**: 2025-11-06  

## Overview

This checklist validates all 20 tasks in Phase 11.7, covering:
- **CRITICAL**: Korean encoding, metrics accuracy (T302-T307)
- **HIGH**: Async queries, admin model consistency (T308-T311)
- **MEDIUM**: CSRF optimization, security tests, data isolation docs (T312-T321)

## Prerequisites

```bash
# Ensure Docker containers are running
docker-compose up -d

# Verify backend is healthy
curl http://localhost:8000/api/v1/health

# Verify database connection
docker-compose logs backend | grep "Database connected"
```

## Automated Tests (T320)

### 1. CRITICAL Tests (Must Pass)

```bash
# T306: Metric accuracy (timezone-aware, non-expired sessions)
pytest backend/tests/test_metrics_accuracy.py -v

# T304: Korean encoding validation
cd frontend
npm run test -- errorMessages.test.ts
cd ..
```

**Expected Results**:
- `test_active_users_counts_non_expired_sessions` - PASS
- `test_active_users_uses_timezone_aware_datetime` - PASS
- `Error Messages Korean Encoding` - All tests PASS
- No mojibake characters (�)

### 2. HIGH Priority Tests (Before Production)

```bash
# T308: Prometheus metrics validation
pytest backend/tests/test_prometheus_metrics.py -v

# T311: Admin privilege consistency
pytest backend/tests/test_admin_auth.py -v
```

**Expected Results**:
- `/metrics` endpoint returns Prometheus text format
- `db_queries_total` metric increments after API requests
- Non-admin user accessing `/admin/users` → 403
- Admin user accessing `/admin/users` → 200
- Korean error message: "관리자 권한이 필요합니다."

### 3. MEDIUM Priority Tests (Recommended)

```bash
# T313: CSRF token stability
pytest backend/tests/test_csrf_stability.py -v

# T315: CSRF exemption patterns
pytest backend/tests/test_csrf_exemptions.py -v

# T316-T317, T319: Security audit (bcrypt, login, data isolation)
cd tests
python security_audit.py
cd ..
```

**Expected Results**:
- CSRF token remains stable across 10 GET requests
- `/api/v1/setup/init` works without CSRF token
- `/docs`, `/metrics`, `/openapi.json` exempt from CSRF
- Bcrypt hash starts with `$2b$12$`
- Login with correct password → 200
- Login with wrong password → 401
- User B cannot GET/DELETE User A's conversations (403/404)

## Manual Validation Checklist (T321)

### FR-115: Korean Encoding

- [ ] **Browser test**: Open frontend, check error messages display correctly (no ������)
  ```bash
  # Trigger auth error
  POST /api/v1/auth/login with wrong credentials
  # Expected: "사용자 이름 또는 비밀번호가 잘못되었습니다."
  ```

- [ ] **CSV export test** (Windows Excel):
  ```bash
  # Export metrics to CSV
  GET /api/v1/admin/metrics/export?format=csv
  # Open in Excel, verify Korean characters display correctly
  # BOM (UTF-8-sig) should be present for Windows
  ```

### FR-116: Metrics Accuracy

- [ ] **Active users count validation**:
  ```sql
  -- SQL query (PostgreSQL)
  SELECT COUNT(DISTINCT user_id) FROM sessions WHERE expires_at > NOW();
  ```
  ```bash
  # API query
  curl http://localhost:8000/api/v1/admin/metrics/current
  # Compare active_users count with SQL result (should match)
  ```

- [ ] **Timezone-aware datetime**:
  ```bash
  # Check logs for timestamp
  docker-compose logs backend | grep "Active users count"
  # Verify timestamps have timezone info (e.g., "2025-11-06T10:30:00+00:00")
  ```

### FR-117: Prometheus Metrics

- [ ] **Metrics endpoint accessibility**:
  ```bash
  curl http://localhost:8000/metrics
  # Should return Prometheus text format (200 OK)
  ```

- [ ] **Query metrics increment**:
  ```bash
  # Before
  curl http://localhost:8000/metrics | grep db_queries_total

  # Make 10 API requests
  for i in {1..10}; do curl http://localhost:8000/api/v1/health; done

  # After
  curl http://localhost:8000/metrics | grep db_queries_total
  # db_queries_total should have increased by at least 10
  ```

### FR-118: Admin Privilege Model

- [ ] **SQL verification**:
  ```sql
  -- Check User.is_admin is single source of truth
  SELECT username, is_admin FROM users WHERE is_admin = TRUE;
  ```

- [ ] **Admin endpoint test**:
  ```bash
  # Login as non-admin user
  TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "regular_user", "password": "password"}' \
    | jq -r '.session_token')

  # Try to access admin endpoint
  curl -H "Cookie: session_token=$TOKEN" http://localhost:8000/api/v1/admin/users
  # Expected: 403 Forbidden, "관리자 권한이 필요합니다."
  ```

### FR-119: CSRF Token Optimization

- [ ] **Token stability test**:
  ```bash
  # Make 10 GET requests, check Set-Cookie header
  for i in {1..10}; do
    curl -c cookies.txt -b cookies.txt http://localhost:8000/api/v1/health -v 2>&1 | grep "Set-Cookie"
  done
  # Should see "Set-Cookie: csrf_token=" only on first request
  ```

- [ ] **Log verification**:
  ```bash
  docker-compose logs backend | grep "CSRF token"
  # Should see "CSRF token generated" (once) and "CSRF token reused" (9 times)
  ```

### FR-120: CSRF Exemption Patterns

- [ ] **Exempt paths work without token**:
  ```bash
  # Setup endpoint (prefix match)
  curl -X POST http://localhost:8000/api/v1/setup/init \
    -H "Content-Type: application/json" \
    -d '{"admin_username": "admin", "admin_password": "password"}'
  # Should NOT return 403 CSRF error

  # Docs (exact match)
  curl http://localhost:8000/docs
  # Should return 200 OK (Swagger UI)

  # Metrics (exact match)
  curl http://localhost:8000/metrics
  # Should return 200 OK (Prometheus format)
  ```

### FR-121: Security Test Alignment

- [ ] **Bcrypt verification**:
  ```python
  # Python shell
  import bcrypt
  hash = bcrypt.hashpw(b"test", bcrypt.gensalt(rounds=12))
  print(hash[:10])  # Should be b'$2b$12$...'
  ```

- [ ] **Login integration test**: See automated tests above

### FR-122: Data Isolation

- [ ] **Cross-user access test**:
  ```bash
  # User 1 creates conversation
  TOKEN1=$(curl -X POST http://localhost:8000/api/v1/auth/login \
    -d '{"username": "user1", "password": "pass1"}' | jq -r '.session_token')
  
  CONV_ID=$(curl -X POST http://localhost:8000/api/v1/conversations \
    -H "Cookie: session_token=$TOKEN1" \
    -d '{"title": "Private"}' | jq -r '.id')

  # User 2 attempts to access User 1's conversation
  TOKEN2=$(curl -X POST http://localhost:8000/api/v1/auth/login \
    -d '{"username": "user2", "password": "pass2"}' | jq -r '.session_token')

  curl -H "Cookie: session_token=$TOKEN2" \
    http://localhost:8000/api/v1/conversations/$CONV_ID
  # Expected: 403 Forbidden or 404 Not Found
  ```

- [ ] **Documentation check**:
  ```bash
  # Verify comprehensive docstring in deps.py
  cat backend/app/api/deps.py | grep -A 50 "Data Isolation Enforcement"
  # Should see detailed explanation of FR-032 and FR-122 Option B
  ```

## Test Results Summary

| Category | Test | Status | Notes |
|----------|------|--------|-------|
| CRITICAL | Korean Encoding | ⬜ | T302-T304 |
| CRITICAL | Metrics Accuracy | ⬜ | T305-T306 |
| HIGH | Prometheus Metrics | ⬜ | T307-T308 |
| HIGH | Admin Model | ⬜ | T309-T311 |
| MEDIUM | CSRF Optimization | ⬜ | T312-T313 |
| MEDIUM | CSRF Exemptions | ⬜ | T314-T315 |
| MEDIUM | Security Tests | ⬜ | T316-T317 |
| MEDIUM | Data Isolation | ⬜ | T318-T319 |

**Legend**: ✅ Pass | ⬜ Not Tested | ❌ Fail

## Sign-off

- [ ] All CRITICAL tests passed
- [ ] All HIGH tests passed
- [ ] At least 80% of MEDIUM tests passed
- [ ] Manual validation checklist completed
- [ ] No blocking issues identified

**Tested By**: _________________  
**Date**: _________________  
**Phase 11.7 Status**: ⬜ READY FOR PRODUCTION  

## Troubleshooting

### Test Failures

**Symptom**: `test_metrics_accuracy` fails with "No module named 'app'"  
**Solution**: 
```bash
export PYTHONPATH=/mnt/c/02_practice/12_localAgent/backend:$PYTHONPATH
pytest backend/tests/test_metrics_accuracy.py -v
```

**Symptom**: Korean characters display as ������ in browser  
**Solution**: Check frontend encoding:
```bash
file frontend/src/lib/errorMessages.ts
# Should show: UTF-8 Unicode text
```

**Symptom**: CSRF token regenerates on every request  
**Solution**: Check middleware logs:
```bash
docker-compose logs backend | grep "CSRF token"
# Should see "reused" messages, not all "generated"
```

**Symptom**: User B can access User A's conversation  
**Solution**: Check route implementation:
```bash
grep -A 10 "def get_conversation" backend/app/api/v1/conversations.py
# Should have: if conversation.user_id != current_user.id: raise HTTPException(403)
```

## References

- Phase 11.7 Tasks: `specs/001-local-llm-webapp/tasks.md` (Lines 890-1061)
- Test Files: `backend/tests/test_*.py`, `frontend/tests/*.test.ts`
- Documentation: `backend/app/api/deps.py` (T318), `docs/admin/user-management.md` (T310)
- Security Audit: `tests/security_audit.py` (T316-T317, T319)
