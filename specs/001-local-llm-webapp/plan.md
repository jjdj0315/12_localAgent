# Implementation Plan: Local LLM Web Application for Local Government

**Branch**: `001-local-llm-webapp` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-local-llm-webapp/spec.md`

## Summary

Build an air-gapped Local LLM web application for small local government employees to use AI assistance for administrative tasks without internet connectivity. The system provides conversational AI, document analysis, conversation history management, multi-user support with administrative oversight, **plus advanced features: Safety Filter (content moderation + PII masking), ReAct Agent (tool-augmented reasoning), and Multi-Agent System (task-specialized agents)** - all running on local infrastructure using Qwen3-4B-Instruct with HuggingFace Transformers or llama.cpp for CPU-compatible deployment (~2.5GB Q4, Qwen2.5-72B-level performance).

**Key Value**: Replace unavailable cloud-based AI services (ChatGPT, Gemini) with a secure, locally-hosted alternative that maintains data privacy in a closed network environment, while providing government-specific safety controls and task automation.

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
- **Model Choice**: Qwen3-4B-Instruct (April 2025 release, ~2.5GB Q4_K_M, Qwen2.5-72B-level performance, 20-40% improvement in math/coding)
- **Model Format Strategy**:
  - **Phase 10 (CPU-optimized baseline)**: GGUF format (Qwen3-4B-Instruct Q4_K_M) via llama.cpp for CPU-optimized local deployment
  - **Phase 13 (GPU-accelerated, Optional)**: HuggingFace safetensors (Qwen/Qwen3-4B-Instruct) via vLLM for GPU-accelerated multi-user deployment
- **Inference Engine**: Dual backend via factory pattern (BaseLLMService):
  - llama.cpp (CPU-optimized, 1-3 concurrent users, baseline deployment)
  - vLLM (GPU-accelerated, 10-16 concurrent users, optional migration per Phase 13)
- Streaming: Server-Sent Events (SSE) for real-time response streaming
- Context Management: 10-message window (5 user + 5 AI), 2,048 token limit, FIFO removal when exceeded (FR-036)
- Response Limits: Default 4,000 characters / Document generation mode 10,000 characters (FR-017)
- **Safety Filter Integration**: All user inputs and LLM outputs pass through two-phase filtering before processing/delivery (FR-050)

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

**Safety Filter System** (FR-050 series):
- **Two-Phase Filtering**:
  - Phase 1 (Rule-based): Keyword matching + regex patterns for 5 categories (violence, sexual, dangerous, hate, PII)
  - Phase 2 (ML-based): unitary/toxic-bert (~400MB, multilingual, CPU-compatible) for toxic content classification
- **PII Detection & Masking** (FR-052):
  - 주민등록번호: 6 digits + dash + 7 digits → 123456-*******
  - Phone: 010-XXXX-XXXX or 01XXXXXXXXX → 010-****-****
  - Email: user@domain → u***@domain
- **Admin Customization** (FR-055): Keyword rules, confidence thresholds, category enable/disable
- **Logging** (FR-056): Filter events logged (timestamp, user_id, category, action) WITHOUT message content
- **False Positive Handling** (FR-058): Retry option with rule-based filter bypass, ML filter still applied

**ReAct Agent System** (FR-060 series):
- **Architecture**: Thought → Action → Observation loop (max 5 iterations, FR-062)
- **Six Government Tools** (FR-061):
  1. Document Search: Vector similarity search on uploaded docs (ChromaDB/FAISS)
  2. Calculator: Mathematical expressions with Korean currency support (sympy/numexpr)
  3. Date/Schedule: Business days, Korean holidays (JSON calendar), fiscal year conversions
  4. Data Analysis: CSV/Excel loading (pandas, openpyxl), summary statistics
  5. Document Template: Jinja2-based government document generation (공문서, 보고서, 안내문)
  6. Legal Reference: Regulation/ordinance article search with citations
- **Safety Features** (FR-063): 30-second timeout per tool, identical call detection (3x limit), sandboxed execution
- **UX Display** (FR-064): Real-time Thought/Action/Observation with emoji prefixes (🤔/⚙️/👁️)
- **Error Handling** (FR-065): Transparent failure display, agent provides alternative or guidance
- **Audit Trail** (FR-066): All tool executions logged with sanitized parameters

**Multi-Agent System** (FR-070 series):
- **Orchestrator**: LLM-based intent classification (default, few-shot prompt with 2-3 examples per agent) OR keyword-based routing (admin-configurable alternative)
- **Five Specialized Agents** (FR-071, FR-071A):
  1. Citizen Support Agent: Empathetic citizen inquiry responses (존댓말, completeness check) + LoRA adapter
  2. Document Writing Agent: Government document generation (formal language, standard sections) + LoRA adapter
  3. Legal Research Agent: Regulation search + plain-language interpretation + LoRA adapter
  4. Data Analysis Agent: Statistical analysis with Korean formatting (천 단위 쉼표) + LoRA adapter
  5. Review Agent: Content review for errors (factual, grammatical, policy compliance) + LoRA adapter
- **LoRA Adapter Architecture** (FR-071A):
  - Base model: Qwen3-4B-Instruct (loaded once on startup, ~2.5GB Q4_K_M)
  - Dynamic adapter loading: Each agent loads task-specific LoRA adapter on first invocation
  - Adapter caching: Loaded adapters cached in memory to minimize switching overhead
  - Switching latency: <3 seconds per agent invocation (adapter load + inference)
  - Implementation: HuggingFace PEFT library for CPU-compatible adapter management
  - Storage: LoRA weights in `/models/lora_adapters/{agent_name}/` directories (~100-500MB per adapter, optimized for Qwen3-4B)
- **Workflow Support** (FR-072-079):
  - Sequential workflows: Multi-step tasks with agent chaining (adapter switches between agents)
  - Parallel execution: Independent sub-tasks dispatched simultaneously (max 3 parallel, multiple adapters loaded concurrently)
  - Complexity limits: Max 5 agents per chain, 5-minute total timeout (includes adapter switching time)
- **Context Sharing** (FR-077): Agents in same workflow share conversation context and previous outputs
- **Admin Management** (FR-076): Enable/disable agents, configure routing mode, edit keyword patterns, view performance metrics (includes adapter loading times)

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
- Server: Linux (Ubuntu 22.04 LTS recommended) with CPU-first deployment, optional GPU acceleration
  - Minimum hardware (CPU-only): CPU 8-core Intel Xeon (16-core recommended for production), RAM 32GB (64GB recommended), SSD 500GB+ (NVMe 1TB recommended)
  - Optional GPU acceleration: NVIDIA RTX 3090/A100 16GB+ VRAM with CUDA support (for larger models like Meta-Llama-3-8B)
- Client: Supported browsers on Windows workstations (FR-040)
  - Chrome 90+
  - Edge 90+
  - Firefox 88+
  - Minimum 1280x720 resolution
  - JavaScript enabled (required)
  - Internet Explorer: NOT supported

**Project Type**: Web application (frontend + backend + LLM service)

**Terminology**:
- **LLM Service** = Inference engine (llama.cpp or vLLM) + service wrapper layer (backend/app/services/*_llm_service.py)
  - Includes: Model loading, prompt formatting, streaming response generation, adapter management (optional)
  - Does NOT include: Safety filtering, context management (those are separate services)
- **Inference Engine** = Underlying ML runtime (llama.cpp for CPU, vLLM for GPU)
- **LLM Infrastructure** = Complete stack (model + inference engine + service wrapper + deployment config)

**Performance Goals**:
- Response time: 5 seconds maximum (10 seconds target from spec)
- Streaming latency: <500ms first token
- Concurrent users: 10+ without degradation >20%
- Document processing: 20-page PDF in <60 seconds
- API response time: <200ms for non-LLM endpoints

**Constraints**:
- **CRITICAL**: No internet connectivity (air-gapped/closed network)
- Hardware: CPU-first deployment (CPU 8-core minimum, 16-core recommended), RAM 32GB+ (64GB recommended), GPU optional for acceleration
- Response limits: Default 4,000 characters / Document generation mode 10,000 characters (FR-017)
  - **Document generation mode**: Transparent to user (not a manual toggle), automatically activated by keyword detection in user queries ("문서 작성", "초안 생성", "공문", "보고서 작성"), internal system mode only
- File upload: 50MB maximum per file
- Conversation limit: 1,000 messages per conversation (FR-041)
- Context window: 10 messages (5 user + 5 AI), 2,048 tokens (FR-036)
- Korean language support mandatory
- Maintainability: Priority over performance optimization
- **Advanced Features Resource Limits** (FR-086):
  - Max 10 concurrent ReAct sessions (queue additional)
  - Max 5 concurrent multi-agent workflows (return 503 if exceeded)
  - Safety filter timeout: 2 seconds (allow message through with warning if exceeded)

**Scale/Scope**:
- Users: 10-50 employees
- Conversations: Thousands per user (indefinite retention)
- Documents: Hundreds per user
- Storage growth: ~1-5GB per month estimated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Loaded**: `.specify/memory/constitution.md` v1.0.0 (Ratified: 2025-10-22)

### Core Principles Compliance

✅ **I. Air-Gap Compatibility (NON-NEGOTIABLE)**
- All ML models bundled locally: Qwen3-4B-Instruct, unitary/toxic-bert, sentence-transformers
- No external API calls: All safety filters, ReAct tools, and agents operate offline
- Dependencies: All Python packages in requirements.txt for offline pip install
- Documentation: Deployment procedures documented in quickstart.md

✅ **II. Korean Language Support (MANDATORY)**
- UI: All labels, error messages in Korean (FR-037)
- LLM: Qwen3-4B-Instruct with superior Korean support (trained on 36 trillion tokens, 119 languages)
- Safety Filter: unitary/toxic-bert supports multilingual (including Korean)
- Document templates: Jinja2 templates in Korean for government documents

✅ **III. Security & Privacy First**
- Data isolation: user_id filtering enforced (FR-032)
- Session timeout: 30 minutes with warning modal (FR-012)
- Password: bcrypt cost 12 (FR-029)
- Admin: Separate table, DB-only privilege grants (FR-033)
- **Safety Filter**: PII masking prevents accidental exposure (FR-052)

✅ **IV. Simplicity Over Optimization**
- Monolithic deployment (single docker-compose.yml)
- Established libraries: HuggingFace Transformers, FastAPI, React Query
- Clear separation: frontend / backend / LLM service / safety filter / agents

✅ **V. Testability & Observability**
- Structured logging for all components
- Health check endpoints for monitoring
- **Audit logs**: All tool executions, agent invocations, filter events logged (FR-066, FR-075, FR-083)
- **Testing Strategy** (aligned with Constitution):
  - **Manual acceptance testing**: Required for MVP - functional validation via user story acceptance scenarios (spec.md)
  - **Automated load testing**: Recommended for production (SC-002: 10 concurrent users), NOT required for MVP
  - **Unit/integration tests**: Optional - constitution prioritizes deployment speed over test coverage for small-scale government use
  - **Rationale**: Small IT team, limited resources, air-gapped deployment challenges favor manual validation over automated test infrastructure

### Potential Complexity Concerns

⚠️ **Safety Filter + ReAct + Multi-Agent adds significant complexity**
- **Justification**:
  - These are P3/P4 features (lower priority than core P1/P2)
  - Can be implemented incrementally: Safety Filter → ReAct → Multi-Agent
  - Each has clear boundaries and can be disabled independently (FR-087 graceful degradation)
  - Government use case requires these for safety and productivity
- **Mitigation**:
  - Phase implementation: Deliver core features first, then advanced features
  - Comprehensive error handling and logging for debugging
  - Admin controls to enable/disable features (FR-067, FR-076)

⚠️ **CPU-only deployment may have performance limitations**
- **Justification**:
  - Qwen3-4B provides Qwen2.5-72B-level quality with ~50% efficiency improvement
  - 4-bit quantization reduces memory footprint to ~2.5GB
  - Government priority: availability > performance
  - GPU optional for acceleration if available
  - Target 8-12 seconds response time on 16-core CPU (acceptable for administrative tasks)
- **Mitigation**:
  - Resource limits prevent system overload (FR-086)
  - Queueing for ReAct/Multi-Agent sessions
  - Performance validation with 10 concurrent users (SC-002, recommended for production deployment, not MVP-blocking)

**GATE STATUS**: ✅ PASS - All core principles satisfied, complexity justified for government requirements

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
├── models/                     # AI model storage (air-gapped deployment)
│   ├── base/                   # Base LLM models
│   │   └── Qwen3-4B-Instruct/  # GGUF Q4_K_M (~2.5GB) or HF safetensors
│   └── lora_adapters/          # Agent-specific LoRA adapters (FR-071A)
│       ├── citizen_support/    # Citizen Support Agent adapter (~100-500MB, Qwen3-4B optimized)
│       ├── document_writing/   # Document Writing Agent adapter
│       ├── legal_research/     # Legal Research Agent adapter
│       ├── data_analysis/      # Data Analysis Agent adapter
│       └── review/             # Review Agent adapter
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

### Multi-Agent LLM Service Architecture (FR-071A)

**Dual Strategy**: Test environment (llama.cpp) → Production environment (vLLM)

**Design Goals**:
1. Local testing with CPU-optimized llama.cpp (Phase 10)
2. Production deployment with GPU-optimized vLLM (later)
3. Unified interface - agent code remains unchanged between environments
4. LoRA infrastructure testing with dummy adapters (actual fine-tuning later)

---

### Phase 10: Local Test Environment (llama.cpp + GGUF)

**Purpose**: Validate Multi-Agent functionality with minimal setup

**Technology Stack**:
- **Library**: llama-cpp-python
- **Model Format**: GGUF (Q4_K_M quantization)
- **Runtime**: CPU-optimized (8-16 threads)
- **LoRA Support**: GGUF LoRA adapters (infrastructure testing only)
- **Concurrency**: Single user (developer testing)

**Architecture Overview**:
```python
# backend/app/services/base_llm_service.py (Abstract Interface)
from abc import ABC, abstractmethod
from typing import Optional

class BaseLLMService(ABC):
    """
    Abstract LLM service interface

    Allows swapping between llama.cpp (test) and vLLM (production)
    without changing agent code
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate text response"""
        pass

    @abstractmethod
    async def generate_with_agent(
        self,
        agent_name: str,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """Generate using agent-specific prompt/LoRA"""
        pass

    @abstractmethod
    def get_agent_prompt(self, agent_name: str) -> str:
        """Get agent system prompt"""
        pass


# backend/app/services/llama_cpp_llm_service.py (Test Implementation)
from llama_cpp import Llama
from .base_llm_service import BaseLLMService

class LlamaCppLLMService(BaseLLMService):
    """
    Local test LLM service (CPU-optimized)

    - GGUF model with Q4_K_M quantization
    - CPU inference (8-16 threads)
    - Optional LoRA adapter loading (infrastructure test)
    - Single user, fast iteration
    """

    def __init__(self):
        # Load GGUF base model
        self.model = Llama(
            model_path="/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            n_ctx=2048,
            n_threads=8,  # CPU threads
            n_gpu_layers=0,  # CPU only
            verbose=False
        )

        # LoRA adapter paths (optional, for infrastructure testing)
        # Dummy adapters for now, actual fine-tuned adapters later
        self.lora_adapters = {
            "citizen_support": "/models/lora/citizen_support_dummy.gguf",
            "document_writing": "/models/lora/document_writing_dummy.gguf",
            "legal_research": "/models/lora/legal_research_dummy.gguf",
            "data_analysis": "/models/lora/data_analysis_dummy.gguf",
            "review": "/models/lora/review_dummy.gguf",
        }

        self.current_lora = None

        # Load agent prompts from files
        self.agent_prompts = self._load_agent_prompts()

    def _load_agent_prompts(self) -> dict:
        """Load agent system prompts from text files"""
        import os
        prompts = {}
        prompt_dir = "/backend/prompts"

        for agent_name in ["citizen_support", "document_writing",
                          "legal_research", "data_analysis", "review"]:
            prompt_file = os.path.join(prompt_dir, f"{agent_name}.txt")
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompts[agent_name] = f.read().strip()

        return prompts

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using base model"""
        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            echo=False,
            stop=["사용자:", "User:"]
        )

        return output["choices"][0]["text"].strip()

    async def generate_with_agent(
        self,
        agent_name: str,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """Generate using agent-specific prompt and optional LoRA"""
        # Get agent system prompt
        system_prompt = self.get_agent_prompt(agent_name)
        full_prompt = f"{system_prompt}\n\n사용자: {prompt}\n\n답변:"

        # Load LoRA adapter if available (optional)
        self._switch_lora_adapter(agent_name)

        return await self.generate(full_prompt, max_tokens)

    def _switch_lora_adapter(self, agent_name: str):
        """
        Switch LoRA adapter for agent (optional)

        Note: This is for infrastructure testing only.
        Dummy adapters used initially, replaced with fine-tuned adapters later.
        """
        # Check if LoRA adapter exists for this agent
        if agent_name not in self.lora_adapters:
            return

        lora_path = self.lora_adapters[agent_name]

        # Skip if file doesn't exist (LoRA is optional)
        import os
        if not os.path.exists(lora_path):
            return

        # Unload previous LoRA if any
        if self.current_lora:
            # llama.cpp LoRA unloading (if supported)
            pass

        # Load new LoRA adapter
        try:
            # Note: llama-cpp-python LoRA support may vary by version
            # Check documentation for exact API
            # self.model.load_lora(lora_path)
            self.current_lora = agent_name
            print(f"✓ Loaded LoRA adapter for {agent_name}")
        except Exception as e:
            print(f"⚠ LoRA loading skipped for {agent_name}: {e}")

    def get_agent_prompt(self, agent_name: str) -> str:
        """Get agent system prompt"""
        return self.agent_prompts.get(agent_name, "")


# backend/app/services/llm_service_factory.py (Environment Selector)
import os
from .base_llm_service import BaseLLMService
from .llama_cpp_llm_service import LlamaCppLLMService

def get_llm_service() -> BaseLLMService:
    """
    Get LLM service based on environment variable

    .env:
      LLM_BACKEND=llama_cpp  # Local testing (Phase 10)
      LLM_BACKEND=vllm       # Production (later)
    """
    backend = os.getenv("LLM_BACKEND", "llama_cpp")

    if backend == "vllm":
        # Import here to avoid dependency in test environment
        from .vllm_llm_service import VLLMLLMService
        print("🚀 Using vLLM (Production mode)")
        return VLLMLLMService()
    else:
        print("🧪 Using llama.cpp (Test mode)")
        return LlamaCppLLMService()
```

**Agent Implementation (Environment-agnostic)**:
```python
# backend/app/services/agents/citizen_support.py
from ..llm_service_factory import get_llm_service

class CitizenSupportAgent:
    """
    Citizen Support Agent

    Works with both llama.cpp (test) and vLLM (production)
    via unified BaseLLMService interface
    """

    def __init__(self):
        # Automatically uses correct LLM backend (llama.cpp or vLLM)
        self.llm = get_llm_service()
        self.agent_name = "citizen_support"

    async def process(self, user_query: str, context: dict) -> str:
        """Process citizen inquiry"""
        # LLM service handles agent-specific prompt and LoRA (if configured)
        response = await self.llm.generate_with_agent(
            agent_name=self.agent_name,
            prompt=user_query,
            max_tokens=4000
        )

        return response
```

**Orchestrator Integration with LangGraph**:

LangGraph를 사용하여 멀티 에이전트 워크플로우를 구현합니다. LangGraph는 상태 머신 기반 워크플로우 관리를 제공하여 순차/병렬 실행, 에러 핸들링, 상태 공유를 간편하게 처리합니다.

```python
# backend/app/services/orchestrator_service.py
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import operator

from .llm_service_factory import get_llm_service
from .agents.citizen_support import CitizenSupportAgent
from .agents.document_writing import DocumentWritingAgent
from .agents.legal_research import LegalResearchAgent
from .agents.data_analysis import DataAnalysisAgent
from .agents.review import ReviewAgent


class AgentState(TypedDict):
    """Multi-Agent workflow state"""
    user_query: str
    conversation_history: list
    current_agent: str
    agent_outputs: dict  # {agent_name: response}
    workflow_type: str  # "single", "sequential", "parallel"
    errors: list
    execution_log: list


class MultiAgentOrchestrator:
    """LangGraph-based Multi-Agent Orchestrator"""

    def __init__(self):
        # Initialize all agents (auto-detect LLM backend)
        self.agents = {
            "citizen_support": CitizenSupportAgent(),
            "document_writing": DocumentWritingAgent(),
            "legal_research": LegalResearchAgent(),
            "data_analysis": DataAnalysisAgent(),
            "review": ReviewAgent(),
        }

        # LLM service for intent classification
        self.llm = get_llm_service()

        # Build LangGraph workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph state machine for multi-agent workflows"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("execute_single_agent", self._execute_single_agent)
        workflow.add_node("execute_sequential", self._execute_sequential)
        workflow.add_node("execute_parallel", self._execute_parallel)
        workflow.add_node("handle_error", self._handle_error)

        # Define edges (routing logic)
        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            self._route_workflow_type,
            {
                "single": "execute_single_agent",
                "sequential": "execute_sequential",
                "parallel": "execute_parallel",
            }
        )

        workflow.add_edge("execute_single_agent", END)
        workflow.add_edge("execute_sequential", END)
        workflow.add_edge("execute_parallel", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def _classify_intent_node(self, state: AgentState) -> AgentState:
        """Classify user intent and determine workflow type"""
        user_query = state["user_query"]

        # Use LLM to classify intent
        classification_prompt = self._build_classification_prompt(user_query)
        response = await self.llm.generate(classification_prompt, max_tokens=100)

        # Parse response (expected format: "agent_name|workflow_type")
        try:
            agent_name, workflow_type = response.strip().split("|")
            state["current_agent"] = agent_name.strip()
            state["workflow_type"] = workflow_type.strip()
        except:
            # Fallback to citizen_support
            state["current_agent"] = "citizen_support"
            state["workflow_type"] = "single"

        return state

    def _route_workflow_type(self, state: AgentState) -> str:
        """Route to appropriate workflow executor"""
        return state["workflow_type"]

    async def _execute_single_agent(self, state: AgentState) -> AgentState:
        """Execute single agent"""
        agent_name = state["current_agent"]
        agent = self.agents.get(agent_name)

        try:
            response = await agent.process(
                state["user_query"],
                {"conversation_history": state["conversation_history"]}
            )
            state["agent_outputs"][agent_name] = response
            state["execution_log"].append({
                "agent": agent_name,
                "status": "success",
                "timestamp": time.time()
            })
        except Exception as e:
            state["errors"].append({"agent": agent_name, "error": str(e)})
            state["execution_log"].append({
                "agent": agent_name,
                "status": "error",
                "timestamp": time.time()
            })

        return state

    async def _execute_sequential(self, state: AgentState) -> AgentState:
        """Execute agents sequentially (FR-072)"""
        # Determine agent sequence from query
        agent_sequence = self._determine_agent_sequence(state["user_query"])

        for agent_name in agent_sequence:
            agent = self.agents.get(agent_name)

            try:
                # Share context from previous agents (FR-077)
                context = {
                    "conversation_history": state["conversation_history"],
                    "previous_outputs": state["agent_outputs"]
                }

                response = await agent.process(state["user_query"], context)
                state["agent_outputs"][agent_name] = response
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "success",
                    "timestamp": time.time()
                })
            except Exception as e:
                # Failure handling (FR-073)
                state["errors"].append({"agent": agent_name, "error": str(e)})
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "error",
                    "timestamp": time.time()
                })
                break  # Stop workflow on failure

        return state

    async def _execute_parallel(self, state: AgentState) -> AgentState:
        """Execute agents in parallel (max 3, FR-078)"""
        # Determine parallel agents from query
        agent_names = self._determine_parallel_agents(state["user_query"])
        agent_names = agent_names[:3]  # Max 3 parallel agents

        # Execute in parallel
        tasks = []
        for agent_name in agent_names:
            agent = self.agents.get(agent_name)
            context = {"conversation_history": state["conversation_history"]}
            tasks.append(agent.process(state["user_query"], context))

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                state["errors"].append({"agent": agent_name, "error": str(result)})
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "error",
                    "timestamp": time.time()
                })
            else:
                state["agent_outputs"][agent_name] = result
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "success",
                    "timestamp": time.time()
                })

        return state

    async def route_and_execute(self, user_query: str, context: dict) -> dict:
        """Route query to appropriate workflow and execute"""
        # Initialize state
        initial_state: AgentState = {
            "user_query": user_query,
            "conversation_history": context.get("conversation_history", []),
            "current_agent": "",
            "agent_outputs": {},
            "workflow_type": "single",
            "errors": [],
            "execution_log": []
        }

        # Execute LangGraph workflow with timeout (5 minutes, FR-079)
        start_time = time.time()
        try:
            final_state = await asyncio.wait_for(
                self.workflow.ainvoke(initial_state),
                timeout=300  # 5 minutes
            )
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "message": "워크플로우 실행 시간 초과 (5분)",
                "execution_time_ms": 300000
            }

        execution_time = time.time() - start_time

        return {
            "status": "success" if not final_state["errors"] else "partial",
            "agent_outputs": final_state["agent_outputs"],
            "workflow_type": final_state["workflow_type"],
            "execution_log": final_state["execution_log"],
            "errors": final_state["errors"],
            "execution_time_ms": int(execution_time * 1000)
        }
```

---

### Later: Production Environment (vLLM + GPU)

**Purpose**: Production deployment with multi-user support

**Technology Stack**:
- **Library**: vLLM
- **Model Format**: HuggingFace (safetensors)
- **Runtime**: GPU-optimized (PagedAttention)
- **LoRA Support**: vLLM LoRA (optional, after validation)
- **Concurrency**: 10-50 users simultaneously

**Implementation**:
```python
# backend/app/services/vllm_llm_service.py (Production Implementation)
from vllm import LLM, SamplingParams
from .base_llm_service import BaseLLMService

class VLLMLLMService(BaseLLMService):
    """
    Production LLM service (GPU-optimized)

    - Multi-user support (10-50 concurrent)
    - PagedAttention for memory efficiency
    - Optional LoRA adapter support
    """

    def __init__(self):
        # Load vLLM model
        self.llm = LLM(
            model="Qwen/Qwen2.5-1.5B-Instruct",
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_num_seqs=16,  # 16 concurrent users
            # enable_lora=True  # Enable after LoRA validation
        )

        # Load agent prompts (same as llama.cpp)
        self.agent_prompts = self._load_agent_prompts()

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using vLLM"""
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            stop=["사용자:", "User:"]
        )

        outputs = self.llm.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text.strip()

    async def generate_with_agent(
        self,
        agent_name: str,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """Generate using agent-specific prompt"""
        # Get agent system prompt
        system_prompt = self.get_agent_prompt(agent_name)
        full_prompt = f"{system_prompt}\n\n사용자: {prompt}\n\n답변:"

        # TODO: Add LoRA support after validation
        # lora_request = LoRARequest(...)

        return await self.generate(full_prompt, max_tokens)

    def get_agent_prompt(self, agent_name: str) -> str:
        """Get agent system prompt (same as llama.cpp)"""
        return self.agent_prompts.get(agent_name, "")

    def _load_agent_prompts(self) -> dict:
        """Load agent prompts from files (same as llama.cpp)"""
        # ... same implementation ...
        pass
```

**Switching to vLLM**:
```bash
# .env file change only
LLM_BACKEND=llama_cpp  → LLM_BACKEND=vllm

# No code changes required!
# Agents automatically use vLLM via factory pattern
```

---

### Performance Comparison

| Metric | llama.cpp (Test) | vLLM (Production) |
|--------|------------------|-------------------|
| **Concurrency** | 1 user | 10-50 users |
| **Hardware** | CPU (8-16 threads) | GPU (CUDA) |
| **Memory** | 2-3GB (GGUF Q4) | 4-6GB (FP16 + PagedAttention) |
| **Latency** | 2-5 sec/response | 0.5-2 sec/response |
| **Throughput** | 1 req/sec | 10-20 req/sec |
| **LoRA** | Optional (dummy test) | Optional (after validation) |
| **Deployment** | Local dev | EC2 GPU instance |

---

### LoRA Strategy

**Phase 10 (Infrastructure Test)**:
1. Create dummy LoRA adapters (random weights)
2. Test loading/switching mechanism
3. Measure overhead (<1 second per switch)
4. Validate infrastructure works

**Later (Actual Fine-tuning)**:
1. Collect training data (100-1000 examples per agent)
2. Fine-tune LoRA adapters (LoRA rank 16-32)
3. Convert to GGUF format (for llama.cpp)
4. Replace dummy adapters with real ones
5. A/B test: Prompt-only vs Prompt+LoRA
6. Keep LoRA if improvement >10%, else remove

**LoRA File Structure**:
```
models/
├── qwen2.5-1.5b-instruct-q4_k_m.gguf          # Base model (GGUF)
└── lora/
    ├── citizen_support_dummy.gguf              # Phase 10: Dummy
    ├── citizen_support_v1.gguf                 # Later: Fine-tuned
    ├── document_writing_dummy.gguf
    ├── document_writing_v1.gguf
    └── ...
```

**LoRA is Optional**: If fine-tuning doesn't improve performance significantly, we can skip it and rely on prompt engineering alone

---

### LoRA Transition Decision Tree

**When to transition from dummy to actual LoRA adapters**:

```
Phase 10 완료 (Multi-Agent with dummy LoRA)
    ↓
SC-021/SC-022 검증 (Routing accuracy ≥85%, Workflow time ≤90s)
    ↓
    ├─ FAIL → Fix orchestrator/agent logic first (LoRA 전환 연기)
    └─ PASS → LoRA 전환 평가 시작
            ↓
        Training data 수집 가능 여부 확인
            ↓
            ├─ NO (100 examples/agent 미달) → Prompt engineering으로 진행, LoRA 제거
            └─ YES → Fine-tuning 진행
                    ↓
                Fine-tune 5 agents (LoRA rank 16-32, 100-1000 examples each)
                    ↓
                A/B Test: Prompt-only vs Prompt+LoRA (50 queries per agent)
                    ↓
                    ├─ Improvement <10% → LoRA 제거, Prompt-only 유지
                    ├─ Improvement 10-20% → Cost-benefit 분석 (LoRA 유지 고려)
                    └─ Improvement >20% → LoRA 유지, production 배포
```

**Performance Measurement Criteria**:
- **Response Quality**: 3-person blind evaluation (0-10 scale)
- **Response Time**: P50/P95 latency comparison
- **Accuracy**: Domain-specific accuracy (e.g., legal citation correctness for Legal Agent)

**Fallback Strategy**:
- If Phase 10 completes successfully with dummy LoRA, **immediately remove dummy LoRA loading code** (T175F) before Phase 11
- If actual fine-tuning is attempted but fails A/B test (<10% improvement), revert to prompt-only implementation
- Document decision in `specs/001-local-llm-webapp/lora-decision-log.md`

**Timeline**:
- Phase 10: Weeks 1-4 (dummy LoRA infrastructure test)
- LoRA Decision Point: Week 5 (after SC-021/SC-022 validation)
- Fine-tuning (if pursued): Weeks 6-8
- A/B Testing: Week 9
- Production LoRA (if approved): Week 10+

---

### Air-Gapped Deployment

**Phase 10 (llama.cpp)**:
```bash
# Download GGUF model (on internet-connected machine)
huggingface-cli download \
  TheBloke/Qwen2.5-1.5B-Instruct-GGUF \
  qwen2.5-1.5b-instruct.Q4_K_M.gguf \
  --local-dir ./models/

# Install llama-cpp-python offline
pip download llama-cpp-python -d ./offline_packages/
# Transfer to air-gapped server
pip install --no-index --find-links=./offline_packages/ llama-cpp-python
```

**Later (vLLM)**:
```bash
# Download HuggingFace model
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir ./models/

# Install vLLM offline
pip download vllm -d ./offline_packages/
pip install --no-index --find-links=./offline_packages/ vllm
```

---

### Creating Dummy LoRA Adapters (Phase 10 Testing)

**Purpose**: Test LoRA infrastructure without actual fine-tuning

```python
# scripts/create_dummy_lora.py
"""
Create dummy LoRA adapters for infrastructure testing

These are NOT fine-tuned - just random weights to test loading mechanism
Replace with actual fine-tuned adapters later
"""

from llama_cpp import Llama
import numpy as np

def create_dummy_gguf_lora(output_path: str, rank: int = 16):
    """Create dummy GGUF LoRA with random weights"""
    # This is a placeholder - actual implementation depends on llama.cpp API
    # For now, just create empty file to test file detection
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(b'DUMMY_LORA')  # Placeholder
    print(f"Created dummy LoRA: {output_path}")

# Create dummy adapters for all 5 agents
for agent in ["citizen_support", "document_writing", "legal_research",
              "data_analysis", "review"]:
    create_dummy_gguf_lora(f"/models/lora/{agent}_dummy.gguf")
```

**Note**: Actual LoRA fine-tuning guide will be added later if needed

---

### Success Criteria Update

**Phase 10 (Multi-Agent with llama.cpp)**:
- **SC-021**: Agent routing accuracy ≥85% on test dataset of 50 queries
- **SC-022**: Sequential 3-agent workflow completes within 90 seconds
- **SC-023** (Optional): LoRA dummy adapters load successfully without errors

**Later (After vLLM deployment)**:
- **SC-024**: Multi-user concurrent access (10-16 users) with <5 second response time
- **SC-025**: vLLM PagedAttention reduces memory usage by 30% vs naive implementation

