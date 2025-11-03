# Implementation Plan: Admin Dashboard Metrics History & Graphs

**Branch**: `002-admin-metrics-history` | **Date**: 2025-11-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-admin-metrics-history/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature adds historical metrics tracking and visualization to the existing admin dashboard. The system will automatically collect dashboard metrics (active users, storage, sessions, conversations, documents, tags) at hourly and daily intervals, store them in PostgreSQL, and display interactive graphs with time-range selection, period comparison, and CSV/PDF export capabilities. Key technical approach: scheduled background tasks for metric collection, time-series data tables with automatic cleanup, React charting library for visualization, and client-side downsampling for performance.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript (frontend)
**Primary Dependencies**:
  - Backend: FastAPI, SQLAlchemy 2.0 (async), APScheduler 3.10+ (task scheduling), pandas 2.1+ (data processing), ReportLab 4.0+ (PDF generation)
  - Frontend: React 18+, Next.js 14+ (App Router), Chart.js + react-chartjs-2 (charting), downsample (LTTB algorithm)
**Storage**: PostgreSQL 15+ (time-series tables for metric snapshots and daily aggregates)
**Testing**: pytest (backend), Jest + React Testing Library (frontend)
**Target Platform**: Docker containers on Windows Server (via Docker Desktop), air-gapped deployment
**Project Type**: Web application (existing backend + frontend)
**Performance Goals**:
  - Dashboard loads with 7 days of metrics in <2 seconds (SC-001)
  - Graph rendering <3 seconds for any time range via downsampling (SC-007)
  - Metric collection completes in <5 seconds without blocking users (SC-003)
**Constraints**:
  - Air-gapped environment (no external APIs)
  - Korean language UI/errors
  - Windows development environment compatibility (PowerShell, backslash paths)
  - Client-side downsampling to ≤1000 points (FR-022)
  - Export files ≤10MB with auto-downsampling (FR-014, FR-015)
**Scale/Scope**:
  - 6 metric types tracked
  - 30 days hourly data (~720 points) + 90 days daily data (~90 points) per metric
  - Estimated storage: ~100KB/day total
  - 3 new API endpoints, 1 background task scheduler, 3 React components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

**I. Air-Gap Compatibility**: ✅ PASS
- All dependencies bundled (APScheduler, pandas, ReportLab, charting library)
- No external API calls required
- Metric data stored locally in PostgreSQL
- CSV/PDF generation server-side without cloud services

**II. Korean Language Support**: ✅ PASS
- All UI messages in Korean (FR-021: "데이터 수집 중입니다...")
- Tooltips in Korean (FR-009: "이 기간 동안 데이터 수집 실패")
- Export file names and headers in Korean
- Error messages from metric collection in Korean

**III. Security & Privacy First**: ✅ PASS
- Admin-only access (extends existing admin auth)
- No user-level data exposure (system-wide aggregates only)
- Session timeout enforced by existing middleware
- Historical data immutable (FR-011: preserved even when underlying data changes)

**IV. Simplicity Over Optimization**: ✅ PASS
- Uses existing FastAPI backend and Next.js frontend
- Established libraries: APScheduler (proven task scheduler), pandas (data processing)
- Single background task for collection (no distributed scheduling)
- Monolithic deployment within existing containers

**V. Testability & Observability**: ✅ PASS
- Data collection status indicator (FR-019)
- Structured logging for metric collection failures
- Clear error states in UI (empty states, missing data tooltips)
- Manual testing via acceptance scenarios in spec.md

**VI. Windows 개발 환경 호환성**: ✅ PASS
- APScheduler works on Windows
- PowerShell scripts for deployment
- Path handling via `os.path.join()` in Python
- Docker Desktop for Windows supported
- UTF-8 encoding for Korean data

### Pre-Implementation Gates

- ✅ Constitution compliance verified (all principles pass)
- ✅ Edge cases converted to functional requirements (FR-009, FR-020, FR-021, FR-022)
- ✅ Storage limits defined (30 days hourly, 90 days daily, FR-003, FR-017)

**Status**: CLEARED to proceed to Phase 0

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
backend/
├── app/
│   ├── models/
│   │   ├── metric_snapshot.py      # NEW: Hourly/daily metric data model
│   │   └── metric_type.py          # NEW: Metric type definitions (enum or table)
│   ├── services/
│   │   ├── metrics_collector.py    # NEW: Collect current system metrics
│   │   ├── metrics_service.py      # NEW: Query/aggregate historical data
│   │   └── export_service.py       # NEW: CSV/PDF export with downsampling
│   ├── api/v1/
│   │   └── metrics.py              # NEW: /metrics endpoints (GET, export)
│   ├── tasks/
│   │   └── scheduled_tasks.py      # MODIFIED: Add metric collection scheduler
│   └── core/
│       └── scheduler.py            # MODIFIED: Initialize APScheduler
├── alembic/versions/
│   └── {timestamp}_add_metrics_tables.py  # NEW: Migration for metric tables
└── tests/
    ├── test_metrics_collector.py   # NEW
    ├── test_metrics_service.py     # NEW
    └── test_export_service.py      # NEW

frontend/
├── src/
│   ├── app/admin/
│   │   └── metrics/
│   │       └── page.tsx            # NEW: Metrics history page
│   ├── components/admin/
│   │   ├── MetricsGraph.tsx        # NEW: Time-series line chart component
│   │   ├── MetricsComparison.tsx   # NEW: Period comparison component
│   │   ├── MetricsExport.tsx       # NEW: Export button component
│   │   └── MetricsTimeRange.tsx    # NEW: Time range selector
│   ├── lib/
│   │   ├── metricsApi.ts           # NEW: API client for metrics endpoints
│   │   └── chartUtils.ts           # NEW: Downsampling utilities
│   └── types/
│       └── metrics.ts              # NEW: TypeScript interfaces for metrics
└── tests/
    └── components/admin/
        ├── MetricsGraph.test.tsx   # NEW
        └── MetricsTimeRange.test.tsx  # NEW
```

**Structure Decision**: Web application (Option 2). Extends existing FastAPI backend and Next.js frontend. All new files added to established directory structure from feature 001-local-llm-webapp.

## Complexity Tracking

*No Constitution violations. This section intentionally left blank.*

