# Implementation Plan: Local LLM Web Application for Local Government

**Branch**: `001-local-llm-webapp` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-local-llm-webapp/spec.md`

## Summary

Build an air-gapped Local LLM web application for small local government employees to use AI assistance for administrative tasks without internet connectivity. The system provides conversational AI, document analysis, conversation history management, and multi-user support with administrative oversight - all running on local infrastructure using Meta-Llama-3-8B with vLLM for inference optimization.

**Key Value**: Replace unavailable cloud-based AI services (ChatGPT, Gemini) with a secure, locally-hosted alternative that maintains data privacy in a closed network environment.

## Technical Context

**Frontend Stack**:
- React 18+ with TypeScript
- Next.js 14+ (App Router for SSR/SSG capabilities)
- TailwindCSS for styling
- React Query for state management and data fetching
- Streaming UI for real-time LLM responses

**Backend Stack**:
- FastAPI (primary API server - async, high performance)
- Django (optional - if admin panel needs Django's built-in admin UI)
- Python 3.11+
- PostgreSQL 15+ for data persistence
- SQLAlchemy ORM with Alembic migrations

**LLM Infrastructure**:
- Model: meta-llama/Meta-Llama-3-8B
- Inference Engine: vLLM (optimized for throughput and latency)
- Streaming: Server-Sent Events (SSE) for real-time response streaming
- Context Management: In-memory conversation context with 4,000 character response limit

**Document Processing**:
- PyPDF2 or pdfplumber for PDF extraction
- python-docx for DOCX processing
- LangChain or custom chunking for document Q&A
- Vector storage: In-memory or lightweight (ChromaDB/FAISS) for document embeddings

**Deployment & Infrastructure**:
- Architecture: Monolithic (single deployable unit for simplicity)
- Containerization: Docker + Docker Compose
- Deployment: On-premises, single server
- Components:
  - Web UI (Next.js frontend served via nginx or Next.js server)
  - API Server (FastAPI backend)
  - LLM Inference Service (vLLM server)
  - PostgreSQL Database
  - (Optional) Nginx reverse proxy

**Authentication & Security**:
- Session-based authentication (HTTP-only cookies)
- Password hashing: bcrypt or argon2
- Integration with government internal authentication system (LDAP/AD integration if available)
- Role-based access: User vs Administrator
- Session timeout: 30 minutes inactivity

**Storage**:
- Database: PostgreSQL (user accounts, conversations, messages, documents metadata)
- File Storage: Local filesystem for uploaded documents
- Conversation context: In-memory with database persistence

**Testing**:
- Frontend: Jest + React Testing Library
- Backend: pytest + pytest-asyncio
- Integration: API contract tests
- E2E: Playwright or Cypress

**Target Platform**:
- Server: Linux (Ubuntu 22.04 LTS recommended) with GPU support (NVIDIA CUDA for vLLM)
- Client: Modern web browsers (Chrome, Firefox, Edge) on Windows workstations

**Project Type**: Web application (frontend + backend + LLM service)

**Performance Goals**:
- Response time: 5 seconds maximum (10 seconds target from spec)
- Streaming latency: <500ms first token
- Concurrent users: 10+ without degradation >20%
- Document processing: 20-page PDF in <60 seconds
- API response time: <200ms for non-LLM endpoints

**Constraints**:
- **CRITICAL**: No internet connectivity (air-gapped/closed network)
- Hardware: Minimal viable specs (1x GPU with 16GB+ VRAM for Llama-3-8B)
- Response limit: 4,000 characters maximum
- File upload: 50MB maximum per file
- Korean language support mandatory
- Maintainability: Priority over performance optimization

**Scale/Scope**:
- Users: 10-50 employees
- Conversations: Thousands per user (indefinite retention)
- Documents: Hundreds per user
- Storage growth: ~1-5GB per month estimated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Status**: Constitution template is not yet populated. Proceeding with standard software engineering principles:

✅ **Simplicity First**: Monolithic architecture chosen over microservices for maintainability
✅ **Library-First**: Use established libraries (vLLM, LangChain, React Query) over custom implementations
✅ **Testability**: Clear separation of concerns (frontend/backend/LLM service) enables independent testing
✅ **Observability**: Structured logging for debugging in air-gapped environment
✅ **No External Dependencies**: All services run locally, no internet required

**Potential Violations to Monitor**:
- ⚠️ Using both FastAPI and Django may add complexity - **Decision**: Start with FastAPI only, evaluate Django admin panel later
- ⚠️ Document Q&A with embeddings adds complexity - **Decision**: Phase 3 feature, can start with simple text extraction

## Project Structure

### Documentation (this feature)

```
specs/001-local-llm-webapp/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api-spec.yaml    # OpenAPI specification
│   └── README.md        # Contract documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
local-llm-webapp/
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/                # Next.js 14 App Router
│   │   │   ├── (auth)/         # Auth routes (login, etc.)
│   │   │   ├── (user)/         # User routes (chat, history)
│   │   │   ├── (admin)/        # Admin routes (dashboard, user mgmt)
│   │   │   ├── api/            # API routes (if needed for SSR)
│   │   │   └── layout.tsx      # Root layout
│   │   ├── components/         # React components
│   │   │   ├── chat/           # Chat interface components
│   │   │   ├── admin/          # Admin panel components
│   │   │   ├── ui/             # Reusable UI components
│   │   │   └── layout/         # Layout components
│   │   ├── lib/                # Utilities
│   │   │   ├── api.ts          # API client
│   │   │   └── utils.ts        # Helper functions
│   │   └── types/              # TypeScript types
│   ├── public/                 # Static assets
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Configuration management
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   └── document.py
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   └── admin.py
│   │   ├── api/                # API routes
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── conversations.py
│   │   │   │   ├── documents.py
│   │   │   │   └── admin.py
│   │   │   └── deps.py         # Dependencies (auth, db)
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── llm_service.py  # vLLM integration
│   │   │   ├── document_service.py
│   │   │   └── admin_service.py
│   │   ├── core/               # Core utilities
│   │   │   ├── security.py     # Password hashing, sessions
│   │   │   └── database.py     # DB connection
│   │   └── utils/              # Helper functions
│   ├── alembic/                # Database migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── llm-service/                # vLLM inference service (optional separate service)
│   ├── server.py               # vLLM server wrapper
│   ├── config.yaml             # vLLM configuration
│   └── requirements.txt
│
├── docker/                     # Docker configuration
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   ├── llm-service.Dockerfile
│   └── nginx.conf              # Nginx reverse proxy config
│
├── docker-compose.yml          # Full stack orchestration
├── docker-compose.dev.yml      # Development override
├── .env.example                # Environment variables template
└── README.md                   # Project documentation
```

**Structure Decision**:

Chose **Web application structure** with separate frontend/backend/llm-service directories because:
1. Clear separation of concerns (UI, API, ML inference)
2. Independent scaling potential (though running on single server initially)
3. Frontend can be developed/tested without running LLM
4. Backend API can be tested independently
5. Standard pattern familiar to most developers

**Rationale for monolithic deployment**: Despite separate directories, all services deploy together via Docker Compose on a single server to:
- Simplify operations for small government IT team
- Reduce network complexity in air-gapped environment
- Easier backup and disaster recovery
- Lower resource overhead vs microservices

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Three separate services (frontend, backend, LLM) | LLM inference requires separate process/GPU; Frontend needs SSR for initial load performance; Backend needs async API handling | Single monolith would mix concerns (UI rendering, API logic, ML inference) and make testing/scaling individual components impossible |
| Vector database for document Q&A | Document context exceeds 4,000 char limit; Need semantic search across documents | Simple text search insufficient for "summarize this policy" or "compare these 3 documents" use cases from spec |

