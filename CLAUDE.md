﻿# 12_localAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-28

## Active Technologies (001-local-llm-webapp)
- **Backend**: Python 3.11+ + FastAPI
- **Frontend**: TypeScript + React 18+ + Next.js 14+ (App Router)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **LLM**: Meta-Llama-3-8B via vLLM inference engine
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) for semantic tag matching (FR-043)
- **Document Processing**: pdfplumber, python-docx, ChromaDB/FAISS
- **Styling**: TailwindCSS + shadcn/ui or Headless UI
- **State Management**: React Query
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

## Recent Changes
- 2025-10-28: **Clarifications Applied** - Document scope (conversation-scoped), storage auto-cleanup (30-day inactive), session limit handling (auto-terminate oldest), admin init setup (wizard exception), tag timing (first message)
- 2025-10-28: Updated data model - Added `last_accessed_at` to Conversation and Document, `storage_size_bytes` to Conversation, `conversation_id` FK to Document (removed Conversation_Document join table)
- 2025-10-28: Updated API contracts - Documents now scoped to conversations (`/conversations/{id}/documents`), added conversation_id to Document schema
- 2025-10-28: Added Tag entity with semantic auto-matching (FR-043)
- 2025-10-28: Added backup strategy with pg_dump + rsync (FR-042)
- 2025-10-28: Added sentence-transformers for tag embeddings

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
