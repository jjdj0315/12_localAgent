# Research: Admin Dashboard Metrics History & Graphs

**Feature**: 002-admin-metrics-history
**Date**: 2025-11-02
**Phase**: 0 (Research & Technology Selection)

## Overview

This document consolidates research findings for technology choices, best practices, and implementation patterns for the metrics history feature.

## 1. Frontend Charting Library Selection

### Decision: Chart.js + react-chartjs-2 v5.x

**Rationale**:
1. **Superior Performance**: Smallest bundle size (71.3 kB vs 135-139 kB for alternatives), canvas rendering reduces DOM overhead for 1000-point graphs
2. **Air-Gap Compatible**: Fully npm-installable with zero runtime CDN dependencies, built-in TypeScript definitions
3. **Strong Time-Series Support**: Native time scales, Korean locale support (`ko-KR`), period comparison via multi-dataset

**Alternatives Considered**:
- **Recharts (SVG)**: Rejected due to performance concerns (SVG rendering struggles >1000 points, 4s render times reported), larger bundle (139 kB)
- **Victory (SVG)**: Rejected due to largest bundle (135 kB), steeper learning curve, TypeScript gaps

**Installation**:
```bash
npm install react-chartjs-2 chart.js chartjs-adapter-date-fns date-fns downsample
```

**Key Implementation Notes**:
- Use `locale: 'ko-KR'` for Korean tooltips/dates
- Dotted lines for gaps require multiple datasets with `borderDash: [5, 5]`
- Period comparison: two datasets with different `borderColor` and `borderDash`
- Downsampling: Use LTTB (Largest-Triangle-Three-Buckets) algorithm from `downsample` package before passing to Chart.js
- Performance: Set `parsing: false`, `normalized: true` for pre-formatted data

## 2. Backend Task Scheduling

### Decision: APScheduler 3.10+

**Rationale**:
1. **Proven Python Library**: Industry-standard for scheduled tasks in FastAPI/Flask apps
2. **Windows Compatible**: Works natively on Windows Server, no Unix-specific dependencies
3. **Flexible Scheduling**: Supports cron-like expressions and interval-based triggers

**Alternatives Considered**:
- **Celery**: Rejected due to additional complexity (Redis/RabbitMQ broker required), overkill for single background task
- **Built-in asyncio timers**: Rejected due to lack of persistence, restart recovery

**Installation**:
```bash
pip install apscheduler==3.10.4
```

**Key Implementation Notes**:
- Use `BackgroundScheduler` for non-blocking execution
- Hourly trigger: `IntervalTrigger(hours=1)`
- Daily trigger: `CronTrigger(hour=0, minute=0)` for midnight UTC
- Retry logic: Manual implementation in collector (max 3 retries per FR-020)
- Logging: Integrate with existing structured logging

## 3. Time-Series Data Storage Pattern

### Decision: Two-Table Approach (Hourly + Daily Aggregates)

**Rationale**:
1. **Storage Efficiency**: Separate retention policies (30 days hourly, 90 days daily per FR-003)
2. **Query Performance**: Pre-aggregated daily data avoids expensive GROUP BY on large hourly datasets
3. **Simplicity**: No need for TimescaleDB or specialized time-series DB extensions

**Schema Design**:
```sql
-- Hourly snapshots table
CREATE TABLE metric_snapshots (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,  -- 'active_users', 'storage_bytes', etc.
    value BIGINT NOT NULL,
    granularity VARCHAR(10) NOT NULL,  -- 'hourly' or 'daily'
    collected_at TIMESTAMP NOT NULL,   -- UTC
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_metric_type_time (metric_type, granularity, collected_at DESC)
);
```

**Alternatives Considered**:
- **Single table with partition**: Rejected due to PostgreSQL 15 partition complexity, overkill for small data volume
- **Separate table per metric type**: Rejected due to schema explosion (6 tables), violates simplicity principle

**Key Implementation Notes**:
- Use single `metric_snapshots` table with `granularity` discriminator
- Composite index on `(metric_type, granularity, collected_at DESC)` for efficient time-range queries
- Daily aggregates computed during overnight collection (00:00 UTC)
- Cleanup via scheduled task: `DELETE WHERE granularity='hourly' AND collected_at < NOW() - INTERVAL '30 days'`

## 4. Data Downsampling Algorithm

### Decision: LTTB (Largest-Triangle-Three-Buckets)

**Rationale**:
1. **Visual Fidelity**: Preserves peak/valley trends better than naive sampling (every Nth point)
2. **Industry Standard**: Used by Grafana, Kibana for time-series visualization
3. **npm Package**: `downsample` library provides ready implementation

**Algorithm Overview**:
- Divides data into buckets (e.g., 10,000 points → 1000 buckets)
- For each bucket, selects point that forms largest triangle with neighbors
- Guarantees output size exactly matches target (1000 points)

**Alternatives Considered**:
- **Every Nth Point Sampling**: Rejected due to potential loss of important spikes/dips
- **Min-Max Decimation**: Rejected due to inconsistent point counts

**Key Implementation Notes**:
```typescript
import { LTTB } from 'downsample';

function downsampleMetrics(data: MetricPoint[], targetPoints: number = 1000): MetricPoint[] {
  if (data.length <= targetPoints) return data;

  const xyData = data.map(d => [d.timestamp.getTime(), d.value]);
  const downsampled = LTTB(xyData, targetPoints);

  return downsampled.map(([ts, val]) => ({
    timestamp: new Date(ts),
    value: val
  }));
}
```

## 5. CSV/PDF Export Implementation

### Decision: pandas (CSV) + ReportLab (PDF)

**Rationale**:
1. **pandas CSV**: Native support for large datasets, efficient UTF-8 encoding for Korean headers
2. **ReportLab PDF**: Pure Python, air-gap compatible, supports Korean fonts (NanumGothic)
3. **Server-Side Generation**: Avoids client-side memory issues with large exports

**Alternatives Considered**:
- **Client-side export (browser download)**: Rejected due to 10MB file size limit, potential browser crashes
- **WeasyPrint (PDF)**: Rejected due to heavier dependencies (Cairo, Pango)

**Installation**:
```bash
pip install pandas==2.1.3 reportlab==4.0.7
```

**Key Implementation Notes**:
- CSV: Use `pandas.DataFrame.to_csv(encoding='utf-8-sig')` for Excel compatibility
- PDF: Embed NanumGothic font for Korean text rendering
- Downsampling: Apply LTTB before export if raw data exceeds 10MB estimate
- File size check: `len(csv_string.encode('utf-8')) > 10 * 1024 * 1024`

## 6. Retry Logic for Failed Collections

### Decision: Exponential Backoff with Max 3 Retries (Per FR-020)

**Rationale**:
1. **Resilience**: Handles transient DB connection issues, temporary load spikes
2. **Prevents Cascade**: Exponential backoff avoids overwhelming already-stressed system
3. **Audit Trail**: Failed collections logged for admin visibility

**Implementation Pattern**:
```python
async def collect_metrics_with_retry(metric_type: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            value = await calculate_metric(metric_type)
            await save_metric_snapshot(metric_type, value)
            logger.info(f"Metric collected: {metric_type}={value}")
            return
        except Exception as e:
            wait_seconds = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"Collection failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_seconds)
            else:
                logger.error(f"Max retries exceeded for {metric_type}")
                # Record failure in separate table for FR-019 (collection status)
                await record_collection_failure(metric_type)
```

**Key Implementation Notes**:
- Retry only on transient errors (DB timeout, connection reset), not validation errors
- Track retry attempts in logs for observability
- Failed collections (after 3 retries) create gap → shown as dotted line per FR-009

## 7. Timezone Handling Strategy

### Decision: Store UTC, Display Local (Per FR-018)

**Rationale**:
1. **Data Integrity**: UTC storage prevents DST ambiguities, server relocation issues
2. **Admin Flexibility**: Future support for distributed admins in different timezones
3. **Standard Practice**: Industry best practice for time-series data

**Implementation Pattern**:
```python
# Backend: Always store UTC
from datetime import datetime, timezone

collected_at = datetime.now(timezone.utc)
```

```typescript
// Frontend: Convert to admin's local timezone
const localTime = new Date(utcTimestamp); // Browser auto-converts
const formatter = new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
});
```

**Key Implementation Notes**:
- PostgreSQL: Use `TIMESTAMP WITH TIME ZONE` column type
- API responses: Include timezone offset in ISO 8601 format (`2025-11-02T14:30:00+00:00`)
- Chart.js: Time scale automatically uses browser's local timezone

## 8. Performance Optimization Checklist

### Database Indexes
```sql
CREATE INDEX idx_metric_type_time ON metric_snapshots (metric_type, granularity, collected_at DESC);
CREATE INDEX idx_collected_at ON metric_snapshots (collected_at) WHERE granularity = 'hourly';
```

### API Query Optimization
- Use `SELECT` with specific columns (avoid `SELECT *`)
- Add `LIMIT` clause based on time range (hourly: max 720 rows for 30 days)
- Use async SQLAlchemy queries to avoid blocking event loop

### Frontend Rendering
- Lazy load charts (render only visible graph initially)
- Debounce time range selector changes (500ms delay)
- Use `React.memo()` for MetricsGraph component
- Virtual scrolling if adding list view of data points

### Bundle Size
- Import Chart.js components individually: `import { Line } from 'react-chartjs-2'`
- Tree-shaking enabled in Next.js production build
- Code-split metrics page (dynamic import)

## 9. Korean Language Error Messages

### Standard Error Templates
```python
# backend/app/core/errors.py
METRIC_ERRORS_KR = {
    "collection_failed": "메트릭 수집 실패: {metric_type}",
    "export_too_large": "내보내기 파일이 너무 큽니다. 더 짧은 기간을 선택하세요.",
    "no_data": "선택한 기간에 데이터가 없습니다.",
    "invalid_range": "잘못된 날짜 범위입니다.",
}
```

```typescript
// frontend/src/lib/errorMessages.ts
export const METRICS_ERRORS = {
  collectionFailed: '데이터 수집 중 오류가 발생했습니다.',
  loadFailed: '메트릭을 불러올 수 없습니다.',
  exportFailed: '내보내기 실패',
  noData: '데이터가 없습니다.',
} as const;
```

## 10. Testing Strategy

### Backend Tests (pytest)
- **Unit**: `test_metrics_collector.py` - Mock DB, verify SQL queries
- **Unit**: `test_downsampling.py` - Verify LTTB algorithm output
- **Integration**: `test_metrics_api.py` - Full request/response cycle
- **Manual**: Verify scheduled task runs (APScheduler logs)

### Frontend Tests (Jest + RTL)
- **Unit**: `MetricsGraph.test.tsx` - Render with mock data
- **Unit**: `chartUtils.test.ts` - Downsampling function
- **Integration**: `metrics-page.test.tsx` - Full page with API mocks
- **Manual**: Visual verification of Korean tooltips, dotted lines

### Acceptance Testing (Per spec.md)
- User Story 1 scenarios: Admin views 7-day graph, hovers for tooltip, changes to 30-day range
- User Story 2 scenarios: Compare this week vs last week
- User Story 3 scenarios: Export CSV/PDF

## 11. Air-Gap Deployment Checklist

- ✅ All npm packages bundled in `frontend/node_modules` (no CDN)
- ✅ All pip packages in `backend/requirements.txt` (no PyPI at runtime)
- ✅ NanumGothic font included in Docker image for PDF generation
- ✅ Date-fns locale data for Korean included in bundle
- ✅ No external API calls (all metrics computed locally)
- ✅ ReportLab PDF generation purely server-side

## Summary

All "NEEDS CLARIFICATION" items from Technical Context resolved:
- ✅ Charting library: Chart.js + react-chartjs-2
- ✅ Task scheduling: APScheduler
- ✅ Downsampling: LTTB algorithm
- ✅ Export: pandas (CSV) + ReportLab (PDF)
- ✅ Timezone: Store UTC, display local
- ✅ Performance: Indexes, lazy loading, code-splitting

Ready to proceed to Phase 1 (Data Model & Contracts).
