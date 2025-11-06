# Security Monitoring Guide

**Purpose**: Monitor security hardening features and detect issues in production (FR-110~FR-114, Phase 11.6)

**Target Audience**: DevOps engineers, SRE teams, system administrators

**Last Updated**: 2025-11-05

---

## Overview

This guide covers monitoring for security features deployed in Phase 11.6:
- CSRF protection (FR-110)
- Rate limiting (FR-111)
- Resource limiting (FR-111)
- Session token security (FR-112)
- Metric consistency (FR-113)
- Korean encoding compatibility (FR-114)

---

## Key Metrics to Monitor

### 1. CSRF Protection (FR-110)

**Monitor 403 Errors (CSRF Issues)**

**Metric**: `http_requests_total{status_code="403", path=~"/api/v1/.*"}`

**Normal Baseline**: <5 per day (legitimate malicious attempts or misconfigured clients)

**Alert Threshold**: >50 per hour

**Severity**: MEDIUM (potential attack or misconfiguration)

**Query Examples**:

```promql
# Prometheus: Count of 403 errors per hour
sum(increase(http_requests_total{status_code="403"}[1h]))

# Rate of 403 errors per endpoint
rate(http_requests_total{status_code="403"}[5m]) by (path)
```

**Log Query**:
```bash
# Check recent CSRF errors
docker-compose logs backend | grep "403" | grep "CSRF" | tail -20

# Count CSRF errors in last hour
docker-compose logs --since 1h backend | grep -c "CSRF 토큰이 유효하지 않습니다"
```

**Response Procedures**:

1. **High volume (>50/hour)**:
   - Check if legitimate: Review User-Agent patterns
   - Identify source IPs: `docker-compose logs backend | grep 403 | awk '{print $NF}' | sort | uniq -c | sort -rn`
   - Block malicious IPs at firewall/load balancer level
   - Document incident

2. **Sudden spike from single client**:
   - Likely misconfigured client (missing CSRF token handling)
   - Contact user/admin of that client
   - Verify frontend is including X-CSRF-Token header

3. **403 on exempt endpoints (login, health)**:
   - CRITICAL: CSRF middleware misconfigured
   - Check `backend/app/middleware/csrf_middleware.py` CSRF_EXEMPT_PATHS
   - Emergency hotfix if needed

**Alerting Rule** (Prometheus Alertmanager):
```yaml
- alert: HighCSRFErrorRate
  expr: sum(rate(http_requests_total{status_code="403"}[5m])) > 0.5
  for: 10m
  labels:
    severity: medium
  annotations:
    summary: "High rate of CSRF 403 errors"
    description: "CSRF protection is blocking {{ $value }} requests/second for 10 minutes"
```

---

### 2. Rate Limiting (FR-111)

**Monitor 429 Errors (Rate Limiting)**

**Metric**: `http_requests_total{status_code="429"}`

**Normal Baseline**: 10-50 per day (aggressive clients, automated scripts)

**Alert Threshold**: >500 per hour (potential DDoS attempt)

**Severity**: HIGH (resource protection, possible attack)

**Query Examples**:

```promql
# Rate limit hits per hour
sum(increase(http_requests_total{status_code="429"}[1h]))

# Top rate-limited IPs (requires custom metric)
topk(10, sum by (client_ip) (increase(http_requests_total{status_code="429"}[1h])))
```

**Log Query**:
```bash
# Count rate limit hits
docker-compose logs --since 1h backend | grep -c "429"

# Identify rate-limited users/IPs
docker-compose logs backend | grep "429" | awk '{print $8}' | sort | uniq -c | sort -rn | head -10
```

**Response Procedures**:

1. **Normal volume (<100/day)**:
   - No action needed
   - Periodic review of top limited clients

2. **High volume (>500/hour)**:
   - Identify source(s): Single IP or distributed?
   - **Single IP**: Likely bot or misconfigured script
     - Check if legitimate user: Contact if identifiable
     - Consider IP ban if malicious
   - **Distributed**: Potential DDoS
     - Enable DDoS protection at CDN/load balancer level
     - Review rate limit settings (may need adjustment)

3. **Legitimate users hitting limit**:
   - Review if 60 req/min limit is appropriate for use case
   - Consider whitelisting specific admin IPs
   - Adjust rate limit if justified by business needs

**Alerting Rule**:
```yaml
- alert: HighRateLimitHits
  expr: sum(rate(http_requests_total{status_code="429"}[5m])) > 5
  for: 15m
  labels:
    severity: high
  annotations:
    summary: "High rate limiting activity"
    description: "{{ $value }} requests/second are being rate limited"
```

---

### 3. Resource Limiting (FR-111)

**Monitor 503 Errors (Resource Limiting)**

**Metric**: `http_requests_total{status_code="503", path=~"/api/v1/(react|agent|workflow).*"}`

**Normal Baseline**: <10 per day (concurrent load spikes)

**Alert Threshold**: >100 per hour (resource exhaustion, high load)

**Severity**: HIGH (service degradation)

**Query Examples**:

```promql
# Resource limit 503s per hour
sum(increase(http_requests_total{status_code="503",path=~"/api/v1/(react|agent).*"}[1h]))

# 503 rate by endpoint
rate(http_requests_total{status_code="503"}[5m]) by (path)
```

**Log Query**:
```bash
# Check resource limit errors
docker-compose logs backend | grep "503" | grep -E "ReAct|Agent|워크플로우" | tail -20

# Count by type
docker-compose logs --since 1h backend | grep "503" | grep -c "ReAct 세션 용량"
docker-compose logs --since 1h backend | grep "503" | grep -c "멀티 에이전트 워크플로우"
```

**Response Procedures**:

1. **Occasional 503s (<10/day)**:
   - Normal behavior during peak load
   - No action needed
   - Monitor for trends

2. **Frequent 503s (>100/hour)**:
   - **Check active sessions**:
     ```bash
     docker-compose exec db psql -U llm_app -d llm_webapp -c \
       "SELECT COUNT(*) FROM sessions WHERE expires_at > NOW();"
     ```
   - **Check long-running queries**:
     ```bash
     docker-compose exec db psql -U llm_app -d llm_webapp -c \
       "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity
        WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"
     ```
   - **Scaling action**:
     - Short-term: Increase limits in `backend/app/main.py` (max_react_sessions, max_agent_workflows)
     - Long-term: Scale horizontally (add more backend replicas)

3. **Sustained high 503 rate**:
   - CRITICAL: System under heavy load or attack
   - Enable queue system for ReAct/Agent requests
   - Consider autoscaling backend replicas
   - Contact development team for optimization review

**Alerting Rule**:
```yaml
- alert: ResourceExhaustion
  expr: sum(rate(http_requests_total{status_code="503"}[5m])) > 1
  for: 10m
  labels:
    severity: high
  annotations:
    summary: "Resource limits being hit frequently"
    description: "{{ $value }} requests/second are being rejected due to resource limits"
```

---

### 4. Metric Collection Health (FR-113)

**Monitor Metric Collection Failure Rate**

**Metric**: `metric_collection_failures_total`

**Success Criteria**: <1% failure rate per cycle (SC-022)

**Alert Threshold**: >5% failure rate

**Severity**: MEDIUM (data quality issue)

**Query Examples**:

```promql
# Failure rate
sum(rate(metric_collection_failures_total[1h])) /
sum(rate(metric_collections_total[1h])) * 100

# Failures by metric type
sum by (metric_type) (increase(metric_collection_failures_total[24h]))
```

**Database Query**:
```bash
# Check recent failures
docker-compose exec db psql -U llm_app -d llm_webapp -c \
  "SELECT metric_type, attempted_at, error_message
   FROM metric_collection_failures
   ORDER BY attempted_at DESC
   LIMIT 10;"

# Failure rate in last 24 hours
docker-compose exec db psql -U llm_app -d llm_webapp -c \
  "SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM metric_snapshots WHERE collected_at > NOW() - INTERVAL '24 hours')
   FROM metric_collection_failures
   WHERE attempted_at > NOW() - INTERVAL '24 hours';"
```

**Response Procedures**:

1. **Failure rate <1%**:
   - Normal (occasional DB connection issues, transient errors)
   - No action needed
   - Weekly review of failure types

2. **Failure rate 1-5%**:
   - Review error messages: `SELECT DISTINCT error_message FROM metric_collection_failures WHERE attempted_at > NOW() - INTERVAL '24 hours'`
   - Common causes:
     - Database connection pool exhaustion
     - Long-running queries blocking metric collection
     - Disk space issues
   - Fix root cause

3. **Failure rate >5%**:
   - CRITICAL: Systematic issue
   - Check database health: `docker-compose exec db pg_isready`
   - Check disk space: `df -h`
   - Check connection pool: Review `backend/app/core/database.py` pool settings
   - Restart services if needed: `docker-compose restart backend db`

**Alerting Rule**:
```yaml
- alert: MetricCollectionFailureRateHigh
  expr: |
    (sum(increase(metric_collection_failures_total[1h])) /
     sum(increase(metric_collections_total[1h]))) > 0.05
  for: 30m
  labels:
    severity: medium
  annotations:
    summary: "Metric collection failure rate above 5%"
    description: "{{ $value | humanizePercentage }} of metric collections are failing"
```

---

### 5. CSV Encoding Issues (FR-114)

**Monitor CSV Encoding User Complaints**

**Expected**: Zero complaints about Korean text encoding in Excel

**Monitoring Method**: User feedback tracking

**Success Criteria**: No encoding-related support tickets

**Response Procedures**:

1. **User reports Korean text as ??? or garbled**:
   - Ask for screenshot
   - Verify OS (Windows/Mac/Linux)
   - Check User-Agent detection:
     ```bash
     docker-compose logs backend | grep "내보내기 요청 OS 감지" | tail -10
     ```
   - Verify BOM parameter: Should show `Windows=True` for Windows clients

2. **Excel shows encoding dialog on open**:
   - BOM not added for Windows client
   - Check `backend/app/api/v1/metrics.py` line 397 detection logic
   - Verify `backend/app/services/export_service.py` uses correct encoding

3. **pandas shows BOM in column names**:
   - BOM incorrectly added for Linux/Mac
   - Should be `add_bom=False` for non-Windows
   - Fix User-Agent detection logic

**Testing**:
```bash
# Weekly test on Windows VM
# 1. Navigate to Admin Dashboard
# 2. Export metrics as CSV
# 3. Open in Excel
# 4. Verify Korean text displays correctly

# Log review
docker-compose logs --since 7d backend | grep "내보내기" | grep "Windows="
```

**Alerting**:
- No automated alert (relies on user feedback)
- Include in weekly operational review
- Document any encoding-related tickets

---

## Monitoring Dashboard

### Recommended Grafana Dashboard Panels

**Panel 1: HTTP Error Rates**
```promql
# Stacked area chart
sum by (status_code) (rate(http_requests_total{status_code=~"4..|5.."}[5m]))
```

**Panel 2: Security Feature Activity**
```promql
# Table
| Metric | Query |
|--------|-------|
| CSRF Blocks | `sum(increase(http_requests_total{status_code="403"}[24h]))` |
| Rate Limits | `sum(increase(http_requests_total{status_code="429"}[24h]))` |
| Resource Limits | `sum(increase(http_requests_total{status_code="503"}[24h]))` |
```

**Panel 3: Metric Collection Health**
```promql
# Gauge
(1 - (sum(rate(metric_collection_failures_total[1h])) / sum(rate(metric_collections_total[1h])))) * 100
```

**Panel 4: Top Rate-Limited Paths**
```promql
# Bar gauge
topk(10, sum by (path) (increase(http_requests_total{status_code="429"}[24h])))
```

---

## Log Aggregation

### Important Log Patterns

**CSRF Violations**:
```
Pattern: "CSRF 토큰이 유효하지 않습니다"
Level: WARNING
Action: Review client configuration
```

**Rate Limit Hits**:
```
Pattern: "요청 횟수 제한을 초과했습니다"
Level: WARNING
Action: Identify client, check if legitimate
```

**Resource Exhaustion**:
```
Pattern: "ReAct 세션 용량이 초과되었습니다" OR "멀티 에이전트 워크플로우 용량이 초과되었습니다"
Level: ERROR
Action: Check load, consider scaling
```

**Metric Collection Failures**:
```
Pattern: "메트릭 수집 실패" OR "최대 재시도 횟수 초과"
Level: ERROR
Action: Check database health
```

### ELK/Splunk Queries

```
# Elasticsearch
GET /logs-*/_search
{
  "query": {
    "bool": {
      "should": [
        {"match": {"message": "CSRF"}},
        {"match": {"message": "429"}},
        {"match": {"message": "503"}}
      ]
    }
  },
  "size": 100,
  "sort": [{"@timestamp": "desc"}]
}
```

---

## Incident Response Playbook

### Scenario 1: CSRF Attack

**Symptoms**:
- Sudden spike in 403 errors (>100/minute)
- Multiple different source IPs
- Targeting admin endpoints

**Actions**:
1. Confirm attack: Review User-Agent patterns
2. Enable IP blocking at firewall level
3. Check if any requests succeeded (potential breach)
4. Document incident, review security logs

**Recovery**: 2-4 hours

---

### Scenario 2: DDoS / Rate Limit Overwhelmed

**Symptoms**:
- Massive 429 spike (>1000/minute)
- Distributed sources
- Service degradation

**Actions**:
1. Enable DDoS protection at CDN/load balancer
2. Temporarily lower rate limit to preserve resources
3. Analyze traffic patterns
4. Block malicious IP ranges

**Recovery**: 1-2 hours (with CDN protection)

---

### Scenario 3: Resource Exhaustion

**Symptoms**:
- Sustained 503 errors (>50/minute)
- Slow response times
- High CPU/memory usage

**Actions**:
1. Scale backend replicas: `docker-compose up -d --scale backend=3`
2. Check database connection pool
3. Identify long-running queries
4. Review application logs for errors
5. Consider temporary increase of resource limits

**Recovery**: 30 minutes - 1 hour

---

### Scenario 4: Metric Collection Failure

**Symptoms**:
- No new metric data for >1 hour
- High failure rate in metric_collection_failures table
- Missing data in admin dashboard graphs

**Actions**:
1. Check database connectivity: `docker-compose exec db pg_isready`
2. Review backend logs: `docker-compose logs backend | grep "메트릭 수집"`
3. Check disk space: `df -h`
4. Restart metric collector: `docker-compose restart backend`
5. Manually trigger collection via API if needed

**Recovery**: 15-30 minutes

---

## Operational Review Schedule

### Daily
- Review error rate dashboard (403, 429, 503)
- Check metric collection success rate
- Review any overnight incidents

### Weekly
- Export metrics and encoding verification test
- Review top rate-limited clients
- Analyze CSRF block patterns
- Update incident log

### Monthly
- Review alerting thresholds (adjust if needed)
- Capacity planning based on resource limit hits
- Security posture review
- Update this document with lessons learned

---

## Contact Information

**On-Call Escalation**:
- Level 1: DevOps team (rate limits, resource exhaustion)
- Level 2: Backend team (CSRF issues, metric collection)
- Level 3: Security team (suspected attacks, breaches)

**Escalation Criteria**:
- 403 rate >500/minute → Level 2 immediately
- 429 rate >1000/minute → Level 1 immediately, Level 3 if sustained
- 503 rate >100/minute → Level 1 immediately
- Metric failure rate >10% → Level 2 within 2 hours
- Zero-day vulnerability reports → Level 3 immediately

---

## References

- Security Hardening Deployment Checklist: `docs/deployment/security-hardening-checklist.md`
- Project Specification: `specs/001-local-llm-webapp/spec.md` (FR-110~FR-114)
- Middleware Implementation: `backend/app/middleware/`
- Monitoring Setup: `docker-compose.yml` (Prometheus, Grafana services)
