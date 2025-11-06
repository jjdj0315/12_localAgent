# 12_localAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-04

## Active Technologies (001-local-llm-webapp)
- **Backend**: Python 3.11+ + FastAPI
- **Frontend**: TypeScript + React 18+ + Next.js 14+ (App Router)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Vector Database**: Qdrant 1.7+ (HNSW index, Cosine similarity)
- **LLM**: Qwen3-4B-Instruct (~2.5GB Q4_K_M) via llama.cpp (CPU baseline, Phase 10) or vLLM (GPU optional, Phase 13)
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) for semantic tag matching (FR-043)
- **Document Processing**: pdfplumber, python-docx, Qdrant
- **Distributed State**: Redis 7+ (rate limiting, LLM cache)
- **Multiprocess**: Gunicorn 21.2+ with Uvicorn workers
- **Styling**: TailwindCSS + shadcn/ui or Headless UI
- **State Management**: React Query
- **Task Scheduling**: APScheduler 3.10+ (background metrics collection)
- **Data Processing**: pandas 2.1+ (CSV export), ReportLab 4.0+ (PDF generation)
- **Charting**: Chart.js + react-chartjs-2 (time-series visualization)
- **Deployment**: Docker + Docker Compose

## Project Structure
```
local-llm-webapp/
├── frontend/           # Next.js 14 application
│   ├── src/app/        # App Router (auth, user, admin routes)     
│   ├── components/     # React components (chat, admin, ui)
│   ├── lib/            # Utilities (api, errorMessages, localStorage)
│   ├── hooks/          # Custom hooks (useSessionTimeout, useChatState)
│   └── types/          # TypeScript types
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── models/     # SQLAlchemy models (User, Admin, Tag, etc.)
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── api/v1/     # API routes (auth, chat, tags, admin)
│   │   ├── services/   # Business logic (tag_service, backup_service)
│   │   ├── middleware/ # Custom middleware (session, rate limiting)
│   │   └── core/       # Security, database, config
│   ├── alembic/        # Database migrations
│   └── tests/
├── llm-service/        # vLLM inference service
├── docker/             # Dockerfiles
└── docker-compose.yml
```

## Commands
```bash
# Backend
cd backend
pytest tests/
ruff check app/
black app/

# Frontend
cd frontend
npm run test
npm run lint
npm run build

# Full stack
docker-compose up -d
docker-compose logs -f backend
```

## Code Style
- **Python**: Follow PEP 8, use type hints, Black formatting
- **TypeScript**: ESLint + Prettier, strict mode enabled
- **Async**: Use async/await for all I/O operations (FastAPI, PostgreSQL)
- **Error Handling**: Centralized Korean error messages (FR-037)
- **Security**: bcrypt cost 12, data isolation middleware (FR-029, FR-032)

## Key Features
- **Air-gapped deployment**: All dependencies bundled, no internet required (FR-001)
- **Korean language support**: All UI and LLM responses in Korean (FR-014)
- **Tag auto-matching**: Semantic similarity using embeddings (FR-043)
- **Backup strategy**: Daily incremental + weekly full backups (FR-042)
- **Session management**: 30-minute timeout, 3 concurrent sessions max (FR-012, FR-030)
- **Admin privilege isolation**: Separate admins table (FR-033)
- **Metrics history tracking**: Hourly/daily metric snapshots with 30/90 day retention (FR-089~109)
- **Historical data visualization**: Interactive time-series graphs with Korean tooltips (FR-089~109)
- **Period comparison**: Week-over-week and month-over-month metrics analysis (FR-089~109)
- **Data export**: CSV/PDF export with automatic LTTB downsampling for files >10MB (FR-089~109)

## Recent Changes
- 2025-11-04: **Specification Merge** - Merged specs/002-admin-metrics-history into specs/001-local-llm-webapp for unified project management
  - Renumbered FR-001~021 (from 002) to FR-089~109 in unified spec
  - Merged spec.md and data-model.md into single 001 specification
  - Added metric_snapshots and metric_collection_failures tables (12 entities total)
  - Archived original 002 folder to specs/archive/002-admin-metrics-history/
- 2025-11-02: **Feature 002 Implementation Complete** - Admin metrics history dashboard with time-series graphs, period comparison, and CSV/PDF export
  - Backend: MetricsCollector service with APScheduler (hourly/daily collection), MetricsService (time-series queries), ExportService (CSV/PDF with LTTB downsampling)
  - Frontend: MetricsGraph (Chart.js with Korean locale), MetricsComparison (period overlay), MetricsExport (format selector with download)
  - Database: metric_snapshots and metric_collection_failures tables with automatic cleanup
  - 6 metric types tracked: active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count
  - Retention: 30 days hourly + 90 days daily data, export files auto-expire in 1 hour
- 2025-10-28: **Clarifications Applied** - Document scope (conversation-scoped), storage auto-cleanup (30-day inactive), session limit handling (auto-terminate oldest), admin init setup (wizard exception), tag timing (first message)
- 2025-10-28: Updated data model - Added `last_accessed_at` to Conversation and Document, `storage_size_bytes` to Conversation, `conversation_id` FK to Document (removed Conversation_Document join table)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
