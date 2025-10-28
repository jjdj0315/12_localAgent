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
- shadcn/ui or Headless UI for component library (especially admin panel)
- React Query for state management and data fetching
- Streaming UI for real-time LLM responses

**Backend Stack**:
- FastAPI (primary API server - async, high performance)
- Python 3.11+
- PostgreSQL 15+ for data persistence
- SQLAlchemy ORM with Alembic migrations

**LLM Infrastructure**:
- Model: meta-llama/Meta-Llama-3-8B
- Inference Engine: vLLM (optimized for throughput and latency)
- Streaming: Server-Sent Events (SSE) for real-time response streaming
- Context Management: 10-message window (5 user + 5 AI), 2,048 token limit, FIFO removal when exceeded (FR-036)
- Response Limits: Default 4,000 characters / Document generation mode 10,000 characters (FR-017)

**Document Processing**:
- **pdfplumber** for PDF extraction (선택 이유: PyPDF2 대비 한글 텍스트 추출 품질 우수, 표/레이아웃 구조 보존, 활발한 유지보수)
- python-docx for DOCX processing
- LangChain or custom chunking for document Q&A
- Vector storage: In-memory or lightweight (ChromaDB/FAISS) for document embeddings
  - Note: All dependencies (ChromaDB/FAISS pip packages) included in requirements.txt for offline installation in air-gapped environment
- **Semantic Tag Matching** (FR-043):
  - Embedding model: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2 or similar) for Korean support
  - Strategy: Embed conversation content + tag keywords, calculate cosine similarity
  - Threshold: Auto-assign tags with similarity > 0.7
  - Fallback: LLM-based classification if embedding quality insufficient

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
- Password hashing: **bcrypt with cost factor 12 (mandatory)** (FR-029)
- Password complexity: minimum 8 characters, at least 2 types among letters/numbers/special characters (FR-029)
- Concurrent login support: maximum 3 sessions per user, independent timeout management (FR-030)
- Session timeout: 30 minutes from last user request, 3-minute warning modal, draft message recovery via local storage (FR-012)
- Login protection (FR-031):
  - Account lockout: 30 minutes after 5 consecutive failed attempts
  - IP-based rate limiting: maximum 10 login attempts per minute per IP
  - Administrator unlock capability
- Data isolation (FR-032):
  - Database-level: user_id filtering enforced in ORM queries
  - API-level: 403 Forbidden when session user ≠ resource owner
  - Administrator restriction: deletion only, no direct data access
- Privilege escalation prevention (FR-033):
  - Separate admin table (no is_admin flag)
  - Admin privilege grants via direct database modification only
  - Administrators cannot remove own privileges
- Integration with government internal authentication system (LDAP/AD integration if available - optional)
- Role-based access: User vs Administrator (separate tables)

**Storage**:
- Database: PostgreSQL (user accounts, conversations, messages, documents metadata)
- File Storage: Local filesystem for uploaded documents
- Conversation context: In-memory with database persistence
- **Backup Strategy** (FR-042):
  - Daily incremental backups: 2 AM (pg_dump with custom format)
  - Weekly full backups: Sunday 2 AM (pg_dump + filesystem snapshot)
  - Retention: Minimum 30 days (rotate old backups automatically)
  - Location: Separate storage volume (/backup or dedicated NAS)
  - Restore procedures: Documented in admin panel, executable by IT staff
  - Automation: cron jobs or systemd timers for scheduling

**Testing**:
- Frontend: Jest + React Testing Library
- Backend: pytest + pytest-asyncio
- Integration: API contract tests
- E2E: Playwright or Cypress

**Target Platform**:
- Server: Linux (Ubuntu 22.04 LTS recommended) with GPU support (NVIDIA CUDA for vLLM)
  - Minimum hardware: CPU 8-core Intel Xeon, RAM 32GB (64GB recommended), GPU NVIDIA RTX 3090/A100 16GB+ VRAM, SSD 500GB+ (NVMe 1TB recommended)
- Client: Supported browsers on Windows workstations (FR-040)
  - Chrome 90+
  - Edge 90+
  - Firefox 88+
  - Minimum 1280x720 resolution
  - JavaScript enabled (required)
  - Internet Explorer: NOT supported

**Project Type**: Web application (frontend + backend + LLM service)

**Performance Goals**:
- Response time: 5 seconds maximum (10 seconds target from spec)
- Streaming latency: <500ms first token
- Concurrent users: 10+ without degradation >20%
- Document processing: 20-page PDF in <60 seconds
- API response time: <200ms for non-LLM endpoints

**Constraints**:
- **CRITICAL**: No internet connectivity (air-gapped/closed network)
- Hardware: Minimal viable specs (CPU 8-core, RAM 32GB+, GPU 16GB+ VRAM for Llama-3-8B)
- Response limits: Default 4,000 characters / Document generation mode 10,000 characters (FR-017)
- File upload: 50MB maximum per file
- Conversation limit: 1,000 messages per conversation (FR-041)
- Context window: 10 messages (5 user + 5 AI), 2,048 tokens (FR-036)
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
- ⚠️ Document Q&A with embeddings adds complexity - **Decision**: Phase 3 feature, can start with simple text extraction
- ⚠️ Custom admin UI vs Django Admin - **Decision**: FastAPI-only backend with React admin UI. Django would add second framework; small admin UI (10-15 components) is manageable with shadcn/ui or Headless UI component libraries

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
│   │   │   │   ├── ChatInput.tsx      # Input with 6 UI states (FR-035)
│   │   │   │   ├── MessageList.tsx    # Message display with streaming
│   │   │   │   ├── LoadingIndicator.tsx  # Processing state spinner
│   │   │   │   └── StreamingMessage.tsx  # Real-time response display
│   │   │   ├── admin/          # Admin panel components
│   │   │   │   ├── UserManagement.tsx    # User CRUD operations
│   │   │   │   ├── StatsDashboard.tsx    # Usage metrics (FR-038)
│   │   │   │   ├── SystemHealth.tsx      # System health monitoring
│   │   │   │   ├── StorageMetrics.tsx    # Storage usage display
│   │   │   │   ├── TagManagement.tsx     # Tag CRUD, usage stats (FR-043)
│   │   │   │   └── BackupManagement.tsx  # Backup status, restore (FR-042)
│   │   │   ├── ui/             # Reusable UI components
│   │   │   │   ├── ErrorMessage.tsx      # Standardized errors (FR-037)
│   │   │   │   ├── EmptyState.tsx        # Zero-state UI (FR-039)
│   │   │   │   └── SessionWarningModal.tsx  # Timeout warning (FR-012)
│   │   │   └── layout/         # Layout components
│   │   ├── lib/                # Utilities
│   │   │   ├── api.ts          # API client with retry logic
│   │   │   ├── utils.ts        # Helper functions
│   │   │   ├── errorMessages.ts   # Error message formatter (FR-037)
│   │   │   └── localStorage.ts    # Draft message recovery (FR-012)
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useSessionTimeout.ts  # Session management
│   │   │   └── useChatState.ts       # Chat UI state machine (FR-035)
│   │   └── types/              # TypeScript types
│   │   │   ├── chat.ts         # Chat-related types
│   │   │   ├── admin.ts        # Admin-related types
│   │   │   ├── api.ts          # API response types
│   │   │   └── tag.ts          # Tag-related types (FR-043)
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
│   │   │   ├── user.py         # User model
│   │   │   ├── admin.py        # Admin model (separate table, FR-033)
│   │   │   ├── session.py      # Session model (concurrent login support, FR-030)
│   │   │   ├── login_attempt.py  # Login attempt tracking (FR-031)
│   │   │   ├── conversation.py # Conversation model (1000 msg limit, FR-041)
│   │   │   ├── message.py      # Message model
│   │   │   ├── document.py     # Document model
│   │   │   ├── tag.py          # Tag model (admin-defined, FR-043)
│   │   │   └── conversation_tag.py  # Conversation-Tag join table
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── auth.py         # Login, session schemas
│   │   │   ├── conversation.py # Conversation schemas
│   │   │   ├── message.py      # Message schemas with context window
│   │   │   ├── admin.py        # Admin schemas
│   │   │   ├── stats.py        # Statistics schemas (FR-038)
│   │   │   ├── setup.py        # Initial setup schemas (FR-034)
│   │   │   └── tag.py          # Tag schemas (FR-043)
│   │   ├── api/                # API routes
│   │   │   ├── v1/
│   │   │   │   ├── auth.py     # Login, logout, password reset
│   │   │   │   ├── chat.py     # Chat with context management
│   │   │   │   ├── conversations.py  # Conversation CRUD
│   │   │   │   ├── documents.py      # Document upload/analysis
│   │   │   │   ├── admin.py    # User management, stats (FR-038)
│   │   │   │   ├── setup.py    # Initial setup wizard (FR-034)
│   │   │   │   └── tags.py     # Tag management, auto-matching (FR-043)
│   │   │   └── deps.py         # Dependencies (auth, db, rate limiting)
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py       # Authentication, session management
│   │   │   ├── password_service.py   # Password validation, hashing (FR-029)
│   │   │   ├── rate_limit_service.py # IP rate limiting (FR-031)
│   │   │   ├── llm_service.py  # vLLM integration with context (FR-036)
│   │   │   ├── document_service.py   # Document processing
│   │   │   ├── admin_service.py      # User management, account locking
│   │   │   ├── stats_service.py      # Usage statistics (FR-038)
│   │   │   ├── setup_service.py      # Initial setup wizard (FR-034)
│   │   │   ├── tag_service.py        # Tag CRUD, semantic matching (FR-043)
│   │   │   └── backup_service.py     # Backup automation, restore (FR-042)
│   │   ├── middleware/         # Custom middleware
│   │   │   ├── session_timeout.py    # Session timeout (FR-012)
│   │   │   ├── rate_limiter.py       # IP-based rate limiting (FR-031)
│   │   │   └── data_isolation.py     # Database-level filtering (FR-032)
│   │   ├── core/               # Core utilities
│   │   │   ├── security.py     # Password hashing (bcrypt cost 12), sessions
│   │   │   ├── database.py     # DB connection with filtering
│   │   │   └── config.py       # Configuration with setup lock check
│   │   └── utils/              # Helper functions
│   │   │   ├── error_formatter.py    # Korean error messages (FR-037)
│   │   │   └── validators.py         # Input validation
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
| Custom React admin UI (not Django Admin) | Maintain single-framework simplicity; Full control over Korean language UI; Consistent development stack | Django Admin would require second web framework, dual ORM systems, and Korean localization. Admin UI is small (10-15 components) and manageable with component libraries (shadcn/ui) |

## Design Considerations for New Requirements

*Updated 2025-10-28 based on spec.md improvements*

### Security Implementation (FR-029 ~ FR-033)

**Password Management (FR-029)**:
- Library: `bcrypt` (NOT argon2) for compatibility and simplicity
- Cost factor: 12 (hardcoded, not configurable)
- Validation: Client-side + server-side with clear Korean error messages
- Implementation: `backend/app/services/password_service.py`

**Session Management (FR-030)**:
- Storage: PostgreSQL `sessions` table with user_id, token, created_at, last_activity
- Concurrent sessions: Track per user, limit enforcement in login endpoint
- Session cleanup: Background task (Celery or APScheduler) to prune expired sessions
- Forced logout: DELETE all sessions for user_id

**Login Protection (FR-031)**:
- Login attempts: PostgreSQL `login_attempts` table with ip_address, username, timestamp, success
- Account locking: `users.locked_until` timestamp field
- Rate limiting: In-memory cache (Redis if available, otherwise Python dict with TTL)
- Implementation: Middleware `backend/app/middleware/rate_limiter.py`

**Data Isolation (FR-032)**:
- ORM level: SQLAlchemy event listeners to auto-inject user_id filter
- API level: Dependency injection in `deps.py` to get current_user
- Admin restriction: Separate `admin_service.py` with explicit delete-only methods
- Testing: Contract tests to verify 403 responses

**Privilege Escalation Prevention (FR-033)**:
- Database: Separate `admins` table (no is_admin boolean)
- Join: users.id = admins.user_id (nullable)
- Admin creation: Alembic migration script or direct SQL only
- Validation: Check admins table in auth dependency

### UI State Management (FR-035)

**Chat UI States**:
- State machine: 6 states (idle, typing, processing, streaming, completed, error)
- Implementation: Custom React hook `useChatState.ts` with useReducer
- Transitions: Explicit actions (SUBMIT, STREAM_START, STREAM_CHUNK, STREAM_END, ERROR, RESET)
- Component: `ChatInput.tsx` consumes state, renders conditionally

**State Persistence**:
- Local storage: Save draft on every keystroke (debounced 500ms)
- Recovery: Load from localStorage on component mount
- Clear: On successful send or explicit user action

### Context Management (FR-036)

**Implementation Strategy**:
```python
# backend/app/services/llm_service.py
def build_context(conversation_id: int, db: Session) -> list[dict]:
    # Get last 10 messages from DB
    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.desc())\
        .limit(10)\
        .all()

    # Reverse to chronological order
    messages.reverse()

    # Convert to LLM format
    context = [{"role": msg.role, "content": msg.content} for msg in messages]

    # Count tokens (approximate: 1 token ≈ 4 chars for Korean)
    total_tokens = sum(len(msg["content"]) // 4 for msg in context)

    # Trim if exceeds 2048 tokens
    while total_tokens > 2048 and len(context) > 2:
        removed = context.pop(0)  # FIFO
        total_tokens -= len(removed["content"]) // 4

    return context
```

### Error Message Formatting (FR-037)

**Implementation**:
```typescript
// frontend/src/lib/errorMessages.ts
export function formatError(error: APIError): string {
  const errorMap: Record<string, string> = {
    'FILE_TOO_LARGE': '파일이 너무 큽니다. 50MB 이하의 파일을 업로드해주세요.',
    'INVALID_FORMAT': '지원하지 않는 파일 형식입니다. PDF, DOCX, TXT 파일만 업로드 가능합니다.',
    'SERVER_ERROR': '일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
    'UNAUTHORIZED': '아이디 또는 비밀번호가 일치하지 않습니다. 다시 확인해주세요.',
    // ... more mappings
  }

  return errorMap[error.code] || '알 수 없는 오류가 발생했습니다.';
}
```

**Backend**:
```python
# backend/app/utils/error_formatter.py
ERROR_MESSAGES = {
    "authentication_failed": "아이디 또는 비밀번호가 일치하지 않습니다. 다시 확인해주세요.",
    "account_locked": "로그인 시도 횟수를 초과했습니다. 30분 후 다시 시도해주세요.",
    # ... more mappings
}

def format_error(error_code: str) -> dict:
    return {"error": error_code, "message": ERROR_MESSAGES.get(error_code, "알 수 없는 오류가 발생했습니다.")}
```

### Usage Statistics (FR-038)

**Metrics Collection**:
- Real-time: In-memory counters (queries today, active users)
- Historical: PostgreSQL aggregate queries with indexes
- Storage: `usage_logs` table with timestamp, user_id, query_id, response_time

**Dashboard API**:
```python
# backend/app/api/v1/admin.py
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    return {
        "users": {
            "total": db.query(User).count(),
            "active_7d": db.query(User).filter(User.last_login > datetime.now() - timedelta(days=7)).count(),
            "online": len(active_sessions)  # from cache
        },
        "queries": {
            "today": db.query(Message).filter(Message.created_at > today_start).count(),
            "this_week": ...,
            "response_times": {
                "p50": calculate_percentile(50),
                "p95": calculate_percentile(95),
                "p99": calculate_percentile(99)
            }
        },
        # ... more metrics per FR-038
    }
```

### Initial Setup Wizard (FR-034)

**Flow**:
1. Application starts → Check `/config/initial-setup.lock`
2. If not exists → Redirect all routes to `/setup`
3. Setup page: Form with admin username, password, system name, storage path
4. On submit → Create admin account, write config, create lock file
5. Redirect to login

**Lock File**:
```python
# backend/app/core/config.py
SETUP_LOCK_PATH = "/config/initial-setup.lock"

def is_setup_complete() -> bool:
    return os.path.exists(SETUP_LOCK_PATH)

def complete_setup(admin_data: dict):
    # Create admin account
    # Write config
    Path(SETUP_LOCK_PATH).touch()
```

**Middleware**:
```python
# backend/app/main.py
@app.middleware("http")
async def setup_check(request: Request, call_next):
    if not is_setup_complete() and not request.url.path.startswith("/api/v1/setup"):
        return RedirectResponse(url="/setup")
    return await call_next(request)
```

### Browser Compatibility (FR-040)

**Detection**:
```typescript
// frontend/src/lib/browserCheck.ts
export function checkBrowserSupport(): { supported: boolean; message?: string } {
  const ua = navigator.userAgent;

  // Detect IE
  if (ua.indexOf('MSIE') !== -1 || ua.indexOf('Trident/') !== -1) {
    return {
      supported: false,
      message: 'Internet Explorer는 지원하지 않습니다. Chrome, Edge, Firefox를 사용해주세요.'
    };
  }

  // Check version (simplified)
  const isChrome = /Chrome\/(\d+)/.test(ua);
  const isEdge = /Edg\/(\d+)/.test(ua);
  const isFirefox = /Firefox\/(\d+)/.test(ua);

  const chromeVersion = isChrome ? parseInt(ua.match(/Chrome\/(\d+)/)[1]) : 0;
  const edgeVersion = isEdge ? parseInt(ua.match(/Edg\/(\d+)/)[1]) : 0;
  const firefoxVersion = isFirefox ? parseInt(ua.match(/Firefox\/(\d+)/)[1]) : 0;

  if ((isChrome && chromeVersion >= 90) ||
      (isEdge && edgeVersion >= 90) ||
      (isFirefox && firefoxVersion >= 88)) {
    return { supported: true };
  }

  return {
    supported: false,
    message: '브라우저 버전이 너무 낮습니다. 최신 버전으로 업데이트해주세요.'
  };
}
```

**Usage**:
- Run on app mount
- Display warning modal if unsupported
- Allow "Continue anyway" option for testing

### Backup Strategy Implementation (FR-042)

**Backup Types**:
1. **Daily Incremental Backup** (2 AM):
   - PostgreSQL: `pg_dump -F c -d llm_webapp -f /backup/daily/db_$(date +%Y%m%d).dump`
   - Uploaded documents: `rsync -a --link-dest=../previous /uploads /backup/daily/uploads_$(date +%Y%m%d)`

2. **Weekly Full Backup** (Sunday 2 AM):
   - PostgreSQL: Full dump with compression
   - Documents: Complete filesystem snapshot
   - Configuration files: `/backend/.env`, `/llm-service/config.yaml`

**Retention Policy**:
```bash
# Cron job: /etc/cron.d/llm-backup
0 2 * * * root /opt/llm-webapp/scripts/backup-daily.sh
0 2 * * 0 root /opt/llm-webapp/scripts/backup-weekly.sh
0 3 * * * root /opt/llm-webapp/scripts/cleanup-old-backups.sh
```

**Cleanup Script** (`cleanup-old-backups.sh`):
```bash
#!/bin/bash
# Delete backups older than 30 days
find /backup/daily -name "*.dump" -mtime +30 -delete
find /backup/weekly -name "*.tar.gz" -mtime +30 -delete
```

**Restore Procedures**:
- Documented in admin panel (`/admin/backups`)
- Includes step-by-step instructions:
  1. Stop application: `docker-compose down`
  2. Restore database: `pg_restore -d llm_webapp /backup/daily/db_20251028.dump`
  3. Restore files: `rsync -a /backup/daily/uploads_20251028/ /uploads/`
  4. Restart: `docker-compose up -d`

**Monitoring**:
- Backup success/failure logged to `/var/log/llm-backup.log`
- Admin dashboard displays last backup timestamp and status
- Email alerts on backup failure (if SMTP configured)

### Tag Auto-Matching Implementation (FR-043)

**Architecture**:
```python
# backend/app/services/tag_service.py
from sentence_transformers import SentenceTransformer
import numpy as np

class TagService:
    def __init__(self):
        # Load multilingual embedding model (offline installation)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.similarity_threshold = 0.7

    def auto_assign_tags(self, conversation_id: int, db: Session) -> list[Tag]:
        """Analyze conversation content and assign matching tags"""
        # Get conversation messages
        messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .all()

        # Concatenate message content
        content = " ".join([msg.content for msg in messages])

        # Get all active tags with keywords
        tags = db.query(Tag).filter(Tag.is_active == True).all()

        # Embed conversation content
        content_embedding = self.model.encode(content)

        matched_tags = []
        for tag in tags:
            # Combine tag name + keywords for matching
            tag_text = f"{tag.name} {' '.join(tag.keywords)}"
            tag_embedding = self.model.encode(tag_text)

            # Calculate cosine similarity
            similarity = np.dot(content_embedding, tag_embedding) / \
                (np.linalg.norm(content_embedding) * np.linalg.norm(tag_embedding))

            if similarity >= self.similarity_threshold:
                matched_tags.append(tag)

        # Assign tags to conversation
        for tag in matched_tags:
            conversation_tag = ConversationTag(
                conversation_id=conversation_id,
                tag_id=tag.id,
                assigned_by='system',
                confidence_score=similarity
            )
            db.add(conversation_tag)

        db.commit()
        return matched_tags
```

**Tag Entity Design**:
```python
# backend/app/models/tag.py
class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(50), unique=True, nullable=False)
    keywords = Column(ARRAY(String), nullable=True)  # Optional keywords
    color = Column(String(7), nullable=False)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon name
    usage_count = Column(Integer, default=0)  # Track usage
    created_at = Column(DateTime, default=func.now())
    created_by_admin_id = Column(UUID, ForeignKey('admins.id'))
    is_active = Column(Boolean, default=True)

# backend/app/models/conversation_tag.py
class ConversationTag(Base):
    __tablename__ = "conversation_tags"

    conversation_id = Column(UUID, ForeignKey('conversations.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(UUID, ForeignKey('tags.id', ondelete='RESTRICT'), primary_key=True)
    assigned_by = Column(Enum('system', 'user'), default='system')
    confidence_score = Column(Float, nullable=True)  # For system-assigned tags
    assigned_at = Column(DateTime, default=func.now())
```

**API Endpoints** (`/api/v1/tags`):
- `POST /tags` - Create tag (admin only)
- `GET /tags` - List all tags
- `PUT /tags/{tag_id}` - Update tag (admin only)
- `DELETE /tags/{tag_id}` - Delete tag if usage_count == 0 (admin only)
- `POST /conversations/{conv_id}/auto-tag` - Trigger auto-tagging
- `PUT /conversations/{conv_id}/tags/{tag_id}` - Manually add/remove tag (user)

**Frontend Component** (`TagManagement.tsx`):
```typescript
// Admin tag management interface
interface Tag {
  id: string;
  name: string;
  keywords: string[];
  color: string;
  icon?: string;
  usageCount: number;
  createdAt: string;
}

function TagManagement() {
  const [tags, setTags] = useState<Tag[]>([]);

  const handleCreateTag = (data: TagFormData) => {
    api.post('/api/v1/tags', data);
  };

  const handleDeleteTag = (tagId: string, usageCount: number) => {
    if (usageCount > 0) {
      confirm(`이 태그는 ${usageCount}개의 대화에서 사용 중입니다. 삭제하시겠습니까?`);
    }
    api.delete(`/api/v1/tags/${tagId}`);
  };

  return (
    <div>
      <TagList tags={tags} onDelete={handleDeleteTag} />
      <CreateTagForm onSubmit={handleCreateTag} />
    </div>
  );
}
```

**Fallback Strategy**:
- If embedding quality insufficient for Korean: Use LLM-based classification
- Prompt: "다음 대화 내용을 분석하여 가장 관련성 높은 태그를 선택하세요: [태그 목록]. 대화 내용: [내용]"
- Return top 3 tags with confidence scores

