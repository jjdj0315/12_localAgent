# Implementation Plan: Local LLM Web Application for Local Government

**Branch**: `001-local-llm-webapp` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-local-llm-webapp/spec.md`

## Summary

Build an air-gapped Local LLM web application for small local government employees to use AI assistance for administrative tasks without internet connectivity. The system provides conversational AI, document analysis, conversation history management, multi-user support with administrative oversight, **plus advanced features: Safety Filter (content moderation + PII masking), ReAct Agent (tool-augmented reasoning), and Multi-Agent System (task-specialized agents with prompt engineering in Phase 10, optional LoRA fine-tuning in Phase 14)** - all running on local infrastructure using Qwen2.5-1.5B-Instruct (current) or Qwen3-4B-Instruct (future upgrade) with llama.cpp for CPU-compatible deployment.

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
- **Primary Model (All Phases)**: Qwen3-4B-Instruct
  - GGUF Q4_K_M: ~2.5GB
  - Performance: SC-001 CPU baseline 8-12s response time (acceptable for government use)
  - Qwen2.5-72B-level quality, 20-40% improvement in math/coding
- **Fallback Option**: Qwen2.5-1.5B-Instruct
  - GGUF Q4_K_M: ~1GB
  - Use case: Resource-constrained systems (<16GB RAM)
- **Model Format Strategy**:
  - **Phase 10 (CPU-optimized baseline)**: GGUF format (Qwen2.5-1.5B or Qwen3-4B Q4_K_M) via llama.cpp for CPU-optimized local deployment
  - **Phase 13 (GPU-accelerated, Optional)**: HuggingFace safetensors via vLLM for GPU-accelerated multi-user deployment
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
  - Embedding model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (~420MB, Korean support, CPU-compatible)
  - Strategy: Embed conversation content + tag keywords, calculate cosine similarity
  - Threshold: Auto-assign tags with similarity > 0.7
  - Fallback: LLM-based classification if embedding quality insufficient

**Safety Filter System** (FR-050 series):
- **Two-Phase Filtering** (Sequential execution for performance optimization):
  - Phase 1 (Rule-based): Keyword matching + regex patterns for 5 categories (violence, sexual, dangerous, hate, PII)
    - If clean → Pass directly to LLM (skip Phase 2 for efficiency)
    - If flagged → Proceed to Phase 2 for ML verification
  - Phase 2 (ML-based): unitary/toxic-bert (~400MB, multilingual, CPU-compatible) for toxic content classification
    - Only executed if Phase 1 flagged content (performance optimization)
    - Final decision: Block if either phase fails
  - **Performance**: Typical clean message <100ms (Phase 1 only), flagged message <2s (both phases)
- **PII Detection & Masking** (FR-052):
  - 주민등록번호: 6 digits + dash + 7 digits → 123456-*******
  - Phone: 010-XXXX-XXXX or 01XXXXXXXXX → 010-****-****
  - Email: user@domain → u***@domain
- **Admin Customization** (FR-055): Keyword rules, confidence thresholds, category enable/disable
- **Logging** (FR-056): Filter events logged (timestamp, user_id, category, action) WITHOUT message content
- **False Positive Handling** (FR-058): Retry option with rule-based filter bypass, ML filter still applied

**ReAct Agent System** (FR-060 series):
- **Architecture**: Thought → Action → Observation loop (max 5 iterations, FR-062)
- **Six Government Tools** (FR-061): Document Search, Calculator, Date/Schedule, Data Analysis, Document Template, Legal Reference. See spec.md FR-061 for detailed tool descriptions and parameter specifications
- **Safety Features** (FR-063): 30-second timeout per tool, identical call detection (3x limit), sandboxed execution
- **UX Display** (FR-064): Real-time Thought/Action/Observation with emoji prefixes (🤔/⚙️/👁️)
- **Error Handling** (FR-065): Transparent failure display, agent provides alternative or guidance
- **Audit Trail** (FR-066): All tool executions logged with sanitized parameters

**Multi-Agent System** (FR-070 series):
- **Orchestrator**: LLM-based intent classification (default, few-shot prompt with **2 examples per agent**, ≤1000 token budget to reserve ≥1000 tokens for user query in 2048 context window per FR-070) OR keyword-based routing (admin-configurable alternative)
- **Five Specialized Agents** (FR-071):
  1. Citizen Support Agent: Empathetic citizen inquiry responses (존댓말, completeness check) + **Prompt Engineering (Phase 10)**
  2. Document Writing Agent: Government document generation (formal language, standard sections) + **Prompt Engineering (Phase 10)**
  3. Legal Research Agent: Regulation search + plain-language interpretation + **Prompt Engineering (Phase 10)**
  4. Data Analysis Agent: Statistical analysis with Korean formatting (천 단위 쉼표) + **Prompt Engineering (Phase 10)**
  5. Review Agent: Content review for errors (factual, grammatical, policy compliance) + **Prompt Engineering (Phase 10)**
- **LoRA Adapter Architecture** (FR-071A) - **DEFERRED TO PHASE 14 POST-MVP**:
  - **Phase 10 Implementation**: Prompt engineering only (Zero/Few-shot learning) for all 5 specialized agents
  - **Rationale**: Avoid learning data collection complexity (500-1000 samples/agent, 4-6 weeks effort) per Constitution Principle IV (Simplicity Over Optimization)
  - **Phase 14 Activation Criteria**: IF Phase 10 evaluation shows insufficient performance (<80% quality score), THEN proceed with LoRA fine-tuning
  - **LoRA Implementation (if activated in Phase 14)**:
    - Base model: Qwen2.5-1.5B-Instruct (current) or Qwen3-4B-Instruct (future)
    - Dynamic adapter loading: Each agent loads task-specific LoRA adapter on first invocation
    - Adapter caching: Loaded adapters cached in memory to minimize switching overhead
    - Switching latency: <3 seconds per agent invocation (adapter load + inference)
    - Implementation: HuggingFace PEFT library for CPU-compatible adapter management
    - Storage: LoRA weights in `/models/lora_adapters/{agent_name}/` directories (~100-500MB per adapter)
    - Learning data collection: 500-1000 samples per agent (total 2500-5000 samples) from government employees or public datasets
- **Workflow Support** (FR-072-079):
  - Sequential workflows: Multi-step tasks with agent chaining (Phase 10: prompt context switching; Phase 14: adapter switches if LoRA activated)
  - Parallel execution: Independent sub-tasks dispatched simultaneously (max 3 parallel)
  - Complexity limits: Max 5 agents per chain, 5-minute total timeout
- **Context Sharing** (FR-077): Agents in same workflow share conversation context and previous outputs
- **Admin Management** (FR-076): Enable/disable agents, configure routing mode, edit keyword patterns, view performance metrics

**LoRA Adapter Evaluation Protocol** (FR-071A) - **PHASE 14 ONLY**:

**Goal**: Determine if agent-specific LoRA adapters provide meaningful quality improvement (≥10%) over base Qwen3-4B model.

**Evaluation Setup**:
1. **Evaluators**: 3명의 공무원 (또는 한국어 원어민, 업무 맥락 이해 필수)
2. **Test Queries**: 각 에이전트당 50개 (총 250개)
   - Citizen Support Agent: 민원 문의 50개
   - Document Writing Agent: 공문서 작성 요청 50개
   - Legal Research Agent: 법규 검색 질문 50개
   - Data Analysis Agent: 데이터 분석 요청 50개
   - Review Agent: 검토 대상 문서 50개
3. **Blind Comparison**:
   - Response A: Base model (Qwen3-4B, no adapter)
   - Response B: Agent-specific LoRA adapter
   - Evaluator는 A/B 구분 모름 (랜덤 순서)

**Evaluation Criteria** (0-10 scale, 각 응답에 대해):
1. **Task Completion** (0-10): 요청한 작업을 완료했는가?
2. **Quality** (0-10): 문법, 형식, 전문성
3. **Government Context** (0-10): 공무원 업무 맥락 적합성

**Total Score**: 3개 차원 합계 (최대 30점)

**Statistical Analysis**:
- **Mean Score Difference**: `mean(LoRA) - mean(Base)`
- **Improvement %**: `(mean(LoRA) - mean(Base)) / mean(Base) * 100`
- **Significance Test**: Paired t-test (p < 0.05 required)
- **Inter-rater Reliability**: Krippendorff's alpha > 0.7 required

**Decision Criteria**:
| Condition | Action |
|-----------|--------|
| Improvement < 5% | **Remove LoRA** - Not worth complexity |
| Improvement 5-10% AND p > 0.05 | **Remove LoRA** - Not statistically significant |
| Improvement ≥10% AND p < 0.05 | **Keep LoRA** - Meaningful benefit |

**Implementation**:
- **When**: After Phase 11 (Multi-Agent System) implementation complete
- **Tool**: `scripts/evaluate-lora-agents.py` (evaluation interface)
- **Duration**: 2-3 days (evaluator availability)
- **Fallback**: If LoRA removed, use base model with **agent-specific system prompts only** (simpler architecture, easier maintenance per Constitution Principle IV)

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
- **Development Environment**: Windows 10/11 workstations (per Constitution Principle VI)
  - IDE: VSCode (Windows native) or PyCharm
  - Python: 3.11+ via Windows Installer
  - Docker: Docker Desktop for Windows (WSL2 backend recommended)
  - Terminal: PowerShell 7+ or Windows Terminal
  - Git: Git for Windows with CRLF handling configured
- **Deployment Environment**: Linux (Ubuntu 22.04 LTS recommended)
  - Deployed via Docker containers (abstracts OS differences between dev and production)
  - All path operations use `os.path.join()` or `pathlib.Path` for cross-platform compatibility (Constitution VI)
  - No OS-specific commands in application code (PowerShell scripts only for Windows dev tooling)
  - Minimum hardware (CPU-only): CPU 8-core Intel Xeon (16-core recommended for production), RAM 32GB (64GB recommended), SSD 500GB+ (NVMe 1TB recommended)
  - Optional GPU acceleration: NVIDIA RTX 3090/A100 16GB+ VRAM with CUDA support (improves Qwen3-4B response time to 3-8 seconds and concurrent user capacity to 10-16 users)
- **Client**: Supported browsers on Windows workstations (FR-040)
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

**Model Naming Conventions**:
LLM 모델은 맥락에 따라 다음과 같이 참조됩니다:

| 맥락 | 표기법 | 예시 | 사용처 |
|------|-------|------|--------|
| 일반 참조 | `Qwen3-4B-Instruct` | "We use Qwen3-4B-Instruct" | spec.md, 문서, 대화 |
| HuggingFace 저장소 | `Qwen/Qwen3-4B-Instruct` | `from_pretrained("Qwen/Qwen3-4B-Instruct")` | Python 코드 (vLLM), Dependencies |
| GGUF 파일명 | `qwen3-4b-instruct-q4_k_m.gguf` | `llama_cpp.Llama(model_path="...")` | llama.cpp 로딩, 파일 시스템 |
| 환경변수/설정 | `MODEL_NAME=qwen3-4b-instruct` | `.env` 파일, config.py | 설정 파일 |

**통일 원칙**:
- 코드에서는 **설정 파일에서 읽은 값 사용** (하드코딩 금지)
- 문서에서는 **"Qwen3-4B-Instruct"** 형식 우선 사용
- 기술 문서에서 경로 필요 시: **"Qwen3-4B-Instruct (HuggingFace: `Qwen/Qwen3-4B-Instruct`, GGUF: `qwen3-4b-instruct-q4_k_m.gguf`)"** 형식

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
  - Max 5 concurrent Multi-Agent workflows (return 503 if exceeded)
  - Safety filter timeout: 2 seconds (allow message through with warning if exceeded)

**Scale/Scope**:
- Users: 10-50 employees
- Conversations: Thousands per user (indefinite retention)
- Documents: Hundreds per user
- Storage growth: ~1-5GB per month estimated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Loaded**: `.specify/memory/constitution.md` v1.1.0 (Ratified: 2025-10-22, Last Amended: 2025-11-01)

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

✅ **VI. Windows 개발 환경 호환성** *(Added in Constitution v1.1.0, 2025-11-01)*
- **Path handling**: Uses `os.path.join()` for cross-platform compatibility, no hardcoded Unix paths (/)
- **Command compatibility**: Dual script support:
  - Bash scripts for Linux production deployment (`scripts/bundle-offline-deps.sh`)
  - PowerShell scripts for Windows development environment (`scripts/bundle-offline-deps.ps1`, `scripts/backup-daily.ps1`, `scripts/register-backup-task.ps1`)
- **File encoding**: UTF-8 without BOM for all source files (Korean character support)
- **Line endings**: Git configured to handle CRLF (Windows) ↔ LF (Linux) conversion automatically
- **Docker**: Development uses Docker Desktop for Windows with WSL2 backend
- **Environment variables**: `.env` file supports Windows path format (backslashes)
- **Development tools**: VSCode/PyCharm on Windows, Python 3.11+ Windows installer, Git for Windows
- **Prohibited**: No Unix-only commands (`chmod`, `ln -s`) in application code, no hardcoded Unix paths (`/usr/local/bin`), no Bash-only build processes

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
  - Target 8 seconds (maximum acceptable 12 seconds) response time on 16-core CPU per SC-001 (acceptable for administrative tasks)
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

    # Count tokens using actual tokenizer (DO NOT use character approximation for Korean)
    # Load tokenizer once and cache for performance
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")  # or Qwen3-4B when available

    def count_tokens(messages):
        # Concatenate all message content and count tokens
        combined_text = " ".join(msg["content"] for msg in messages)
        return len(tokenizer.encode(combined_text))

    total_tokens = count_tokens(context)

    # Trim if exceeds 2048 tokens
    while total_tokens > 2048 and len(context) > 2:
        context.pop(0)  # FIFO - remove oldest message
        total_tokens = count_tokens(context)

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
- **Library**: llama.cpp-python
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
            model_path="/models/qwen3-4b-instruct-q4_k_m.gguf",
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
            # Note: llama.cpp-python LoRA support may vary by version
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
        """Build LangGraph state machine for Multi-Agent workflows"""
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
            model="Qwen/Qwen3-4B-Instruct",
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

        # LoRA support available in Phase 14 (Post-MVP) per FR-071A
        # Activate only after prompt engineering validation in Phase 10
        # Reference: .specify/memory/constitution.md Principle IV (Simplicity Over Optimization)

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
├── qwen3-4b-instruct-q4_k_m.gguf              # Base model (GGUF)
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
    └─ PASS → LoRA 전환 평가 시작GIL
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

**Performance Measurement Criteria** (referenced in Decision Tree "Improvement <10%" condition):
- **Response Quality**: 3-person blind evaluation (0-10 scale) - PRIMARY metric
- **Response Time**: P50/P95 latency comparison (adapter switching overhead)
- **Accuracy**: Domain-specific accuracy (e.g., legal citation correctness for Legal Agent)
- **Overall Improvement**: Average across 3 metrics weighted as Quality 50%, Time 30%, Accuracy 20%

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

# Install llama.cpp-python offline
pip download llama.cpp-python -d ./offline_packages/
# Transfer to air-gapped server
pip install --no-index --find-links=./offline_packages/ llama.cpp-python
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

---

## Security Hardening (Feature 002 Patch)

**Priority**: P0 (Blocking) - Must be completed before production deployment
**Requirements**: FR-110, FR-111, FR-112, FR-113, FR-114
**Success Criteria**: SC-028, SC-029, SC-030, SC-031, SC-032

### Overview

This section addresses 5 critical security and operational issues discovered during Feature 002 code review (2025-11-04):

1. **CSRF Protection Missing (FR-110)** - CRITICAL
   Cookie-based authentication without CSRF validation allows cross-site attacks on admin functions

2. **Middleware Not Applied (FR-111)** - CRITICAL
   RateLimitMiddleware, ResourceLimitMiddleware, PerformanceMiddleware exist but not registered in main.py

3. **Session Token Exposure (FR-112)** - HIGH
   secure=False allows HTTP transmission, no environment-based configuration, tokens may appear in logs

4. **DB Metric Inconsistency (FR-113)** - MEDIUM
   Metrics collected sequentially cause timestamp drift, no transaction isolation

5. **Korean Encoding Issues (FR-114)** - MEDIUM
   UTF-8 BOM causes parsing errors on Linux/Mac, no OS detection for encoding

### Architecture Changes

#### 1. CSRF Protection (FR-110)

**New Middleware**: `backend/app/middleware/csrf_middleware.py`

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import secrets

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing requests"""

    CSRF_EXEMPT_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/setup",
        "/health",
        "/api/v1/health"
    ]

    async def dispatch(self, request: Request, call_next):
        # GET, HEAD, OPTIONS bypass CSRF check
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)

            # Generate and set CSRF token for authenticated users
            if request.url.path not in self.CSRF_EXEMPT_PATHS:
                csrf_token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key="csrf_token",
                    value=csrf_token,
                    httponly=False,  # JS needs to read this
                    secure=True,     # HTTPS only
                    samesite="strict",
                    max_age=1800     # 30 minutes
                )
            return response

        # POST, PUT, DELETE, PATCH require CSRF validation
        if request.url.path in self.CSRF_EXEMPT_PATHS:
            return await call_next(request)

        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        if not csrf_cookie or csrf_cookie != csrf_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF 토큰이 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요."
            )

        return await call_next(request)
```

**Frontend Integration**: `frontend/src/lib/api.ts`

```typescript
// Axios interceptor to include CSRF token
import Cookies from 'js-cookie';

api.interceptors.request.use((config) => {
  // Include CSRF token for state-changing requests
  if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase() || '')) {
    const csrfToken = Cookies.get('csrf_token');
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }
  return config;
});
```

#### 2. Middleware Registration (FR-111)

**Update**: `backend/app/main.py`

```python
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.resource_limit_middleware import ResourceLimitMiddleware
from app.middleware.performance_middleware import PerformanceMiddleware
from app.middleware.metrics import MetricsMiddleware

# CRITICAL: Middleware order matters!
# Applied in reverse order (last added = first executed)
app.add_middleware(CORSMiddleware, ...)           # 6th - outermost
app.add_middleware(CSRFMiddleware)                 # 5th
app.add_middleware(RateLimitMiddleware,            # 4th
                   requests_per_minute=60)
app.add_middleware(ResourceLimitMiddleware,        # 3rd
                   max_react_sessions=10,
                   max_agent_workflows=5)
app.add_middleware(PerformanceMiddleware)          # 2nd
app.add_middleware(MetricsMiddleware)              # 1st - innermost
```

**Execution Order** (request flow):
1. CORS → 2. CSRF → 3. Rate Limit → 4. Resource Limit → 5. Performance → 6. Metrics → **Route Handler**

#### 3. Session Token Security (FR-112)

**Environment Configuration**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    @property
    def cookie_secure(self) -> bool:
        """HTTPS-only cookies in production"""
        return self.ENVIRONMENT == "production"

    @property
    def cookie_samesite(self) -> str:
        """Strict in production, lax in development"""
        return "strict" if self.ENVIRONMENT == "production" else "lax"

settings = Settings()
```

**Updated Cookie Settings**: `backend/app/api/v1/auth.py`

```python
response.set_cookie(
    key="session_token",
    value=session.session_token,
    httponly=True,
    secure=settings.cookie_secure,      # ✅ Environment-based
    samesite=settings.cookie_samesite,  # ✅ Environment-based
    max_age=1800,                        # ✅ 30 minutes explicit
)
```

**Logging Filter**: `backend/app/core/logging.py`

```python
import logging
import re

class SensitiveDataFilter(logging.Filter):
    """Mask sensitive data in logs"""

    PATTERNS = [
        # Session tokens
        (re.compile(r'(session_token["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9_-]+)'),
         r'\1***REDACTED***'),

        # Bearer tokens (JWT)
        (re.compile(r'(Bearer\s+)([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)'),
         r'\1***REDACTED***'),

        # Passwords
        (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)'),
         r'\1***REDACTED***'),
    ]

    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True

# Apply to all handlers
for handler in logging.root.handlers:
    handler.addFilter(SensitiveDataFilter())
```

#### 4. Metric Collection Consistency (FR-113)

**Refactored**: `backend/app/services/metrics_collector.py`

```python
async def collect_all_metrics(self, granularity: str = "hourly") -> dict:
    """Collect all metrics in single transaction for consistency"""
    collected_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    results = {}

    # ✅ Single transaction for all metrics
    async with self.db.begin():
        logger.debug(f"🔄 Starting metric collection transaction (granularity={granularity})")

        for metric_type in MetricType:
            try:
                value = await self._collect_metric(metric_type)

                snapshot = MetricSnapshot(
                    metric_type=metric_type.value,
                    value=value,
                    granularity=granularity,
                    collected_at=collected_at,  # ✅ Identical timestamp
                    retry_count=0
                )
                self.db.add(snapshot)
                results[metric_type.value] = value

            except Exception as e:
                logger.error(f"❌ Metric collection failed: {metric_type.value} - {e}")
                # Record failure but don't rollback transaction
                await self._record_collection_failure(
                    metric_type, collected_at, granularity, str(e)
                )
                results[metric_type.value] = None

        # ✅ Commit all successful metrics at once
        await self.db.commit()
        logger.debug(f"✅ Metric collection transaction committed")

    return results
```

**Database Configuration**: `backend/app/core/database.py`

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    isolation_level="READ COMMITTED",  # ✅ Explicit isolation
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### 5. Korean Encoding Compatibility (FR-114)

**OS Detection**: `backend/app/api/v1/metrics.py`

```python
@router.post("/export", ...)
async def export_metrics(
    request: ExportRequest,
    user_agent: str = Header(None),  # ✅ Detect client OS
    db: AsyncSession = Depends(get_db),
    ...
):
    # Windows clients need BOM for Excel
    is_windows = user_agent and "Windows" in user_agent

    if request.format == 'csv':
        file_data, downsampled = export_service.export_to_csv(
            snapshots=all_snapshots,
            use_bom=is_windows  # ✅ Conditional BOM
        )
```

**Updated Export Service**: `backend/app/services/export_service.py`

```python
def export_to_csv(
    self,
    snapshots: list[MetricSnapshot],
    metric_type: str,
    granularity: str,
    use_bom: bool = False,  # ✅ Conditional BOM parameter
    include_metadata: bool = True
) -> tuple[bytes, bool]:
    """Export with OS-specific encoding"""

    # ... data preparation ...

    # ✅ Choose encoding based on client OS
    encoding = 'utf-8-sig' if use_bom else 'utf-8'

    csv_buffer = io.StringIO()
    csv_buffer.write(metadata)
    df.to_csv(csv_buffer, index=False, encoding=encoding)

    csv_data = csv_buffer.getvalue().encode(encoding)

    return csv_data, downsampled
```

**Frontend Fallback**: `frontend/src/components/admin/MetricsExport.tsx`

```typescript
async function downloadCSV(url: string, filename: string) {
  const response = await fetch(url);
  let blob = await response.blob();

  // ✅ Client-side BOM injection as fallback
  if (navigator.platform.includes('Win')) {
    const bom = new Uint8Array([0xEF, 0xBB, 0xBF]);
    blob = new Blob([bom, blob], { type: 'text/csv;charset=utf-8;' });
  }

  // Trigger download
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}
```

### Testing Strategy

#### SC-028: CSRF Protection Validation

**Manual Tests**:
1. POST request without X-CSRF-Token header → expect 403
2. POST request with mismatched token (cookie ≠ header) → expect 403
3. Login endpoint without CSRF token → expect 200 (exempt)
4. Setup endpoint without CSRF token → expect 200 (exempt)
5. Authenticated GET request → verify csrf_token cookie set

**Automated Test** (`backend/tests/test_csrf.py`):
```python
def test_csrf_blocks_invalid_requests(client):
    # Missing header
    response = client.post("/api/v1/admin/users", json={...})
    assert response.status_code == 403

    # Mismatched tokens
    client.cookies.set("csrf_token", "valid-token")
    response = client.post(
        "/api/v1/admin/users",
        json={...},
        headers={"X-CSRF-Token": "wrong-token"}
    )
    assert response.status_code == 403
```

#### SC-029: Middleware Enforcement

**Manual Tests**:
1. Send 61 requests in 1 minute → 61st returns 429
2. Start 11 concurrent ReAct sessions → 11th returns 503
3. Check response headers for X-RateLimit-* values
4. Verify slow endpoints (>1s) logged in performance metrics

**Load Test Script** (`scripts/test_rate_limit.sh`):
```bash
#!/bin/bash
for i in {1..61}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/health &
done
wait
# Expected: 60x "200", 1x "429"
```

#### SC-030: Session Token Security

**Configuration Tests**:
```python
def test_production_cookie_security():
    os.environ['ENVIRONMENT'] = 'production'
    settings = Settings()
    assert settings.cookie_secure == True
    assert settings.cookie_samesite == "strict"

def test_development_cookie_permissive():
    os.environ['ENVIRONMENT'] = 'development'
    settings = Settings()
    assert settings.cookie_secure == False
    assert settings.cookie_samesite == "lax"
```

**Log Masking Test**:
```python
def test_sensitive_data_masked_in_logs(caplog):
    logger.info("session_token=abc123xyz")
    logger.info("Bearer eyJhbGciOiJIUzI1NiIs.payload.signature")
    logger.info("password='secret123'")

    assert "abc123xyz" not in caplog.text
    assert "***REDACTED***" in caplog.text
    assert "secret123" not in caplog.text
```

#### SC-031: Metric Transaction Consistency

**Database Test**:
```python
async def test_metrics_same_timestamp():
    collector = MetricsCollector(db)
    await collector.collect_all_metrics("hourly")

    # Query all metrics from last collection
    snapshots = await db.execute(
        select(MetricSnapshot)
        .order_by(MetricSnapshot.collected_at.desc())
        .limit(6)
    )
    snapshots = snapshots.scalars().all()

    # All timestamps must be identical
    timestamps = [s.collected_at for s in snapshots]
    assert len(set(timestamps)) == 1, "Timestamps must be identical"

    # Verify isolation level
    result = await db.execute(text("SHOW transaction_isolation"))
    assert result.scalar() == "read committed"
```

#### SC-032: Korean Encoding Compatibility

**Platform Tests**:
```python
def test_windows_bom_detection():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    is_windows = "Windows" in user_agent
    assert is_windows == True

def test_linux_no_bom():
    user_agent = "Mozilla/5.0 (X11; Linux x86_64)"
    is_windows = "Windows" in user_agent
    assert is_windows == False
```

**CSV Validation** (manual):
1. Export CSV on Windows → Open in Excel → No encoding dialog
2. Export CSV on Linux → `pandas.read_csv()` → Check `df.columns[0]` has no '\ufeff'
3. Export CSV → Open in LibreOffice Calc → Korean displays correctly

### Deployment Checklist

**Before Production**:
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Verify HTTPS certificate installed
- [ ] Test CSRF protection on all admin endpoints
- [ ] Run load test to confirm rate limiting works
- [ ] Check logs contain no plaintext tokens/passwords
- [ ] Verify metric collection transaction consistency
- [ ] Test CSV export on Windows/Linux clients

**Post-Deployment Monitoring**:
- [ ] Monitor 403 errors (potential CSRF issues)
- [ ] Monitor 429 errors (rate limit effectiveness)
- [ ] Monitor 503 errors (resource limit effectiveness)
- [ ] Check metric collection failure rate (<1% per SC-022)
- [ ] Verify CSV encoding complaints from users (should be zero)

### Dependencies

**New Python Packages** (already in requirements.txt):
- No new dependencies required (uses existing FastAPI, secrets, re, logging)

**Configuration Files**:
- `.env`: Add `ENVIRONMENT=production` for production deployment
- `backend/app/middleware/csrf_middleware.py`: New file
- `backend/app/core/logging.py`: Enhanced with SensitiveDataFilter

### Success Criteria Summary

- **SC-028**: CSRF blocks 100% of unauthorized requests ✅
- **SC-029**: Rate/resource limits prevent DoS ✅
- **SC-030**: Tokens masked in logs, secure cookies in prod ✅
- **SC-031**: Metrics have identical timestamps (<5ms variance) ✅
- **SC-032**: Korean CSV works on Windows/Linux (>95% UA accuracy) ✅

---

**Implementation Priority**: Complete FR-110 and FR-111 (CRITICAL) before production. FR-112, FR-113, FR-114 can follow in maintenance release.

## Phase 11.7: Quality & Operational Fixes (FR-115 ~ FR-122)

### Overview

This phase addresses critical quality issues and operational inconsistencies discovered during post-implementation review. Issues are prioritized by severity: CRITICAL (immediate user/data impact), HIGH (monitoring/security gaps), MEDIUM (technical debt/test alignment).

**Dependency**: Requires Phase 11.6 (Security Hardening) completion

### Implementation Approach

#### FR-115: Korean Encoding Fix (CRITICAL)

**Problem**: `frontend/src/lib/errorMessages.ts` contains corrupted Korean text (mojibake ������), causing unreadable error messages to users.

**Root Cause**: File saved with incorrect encoding (likely Windows-1252 or ISO-8859-1) instead of UTF-8.

**Solution**:
1. **Immediate fix**: Rewrite `errorMessages.ts` with correct UTF-8 encoding
2. **Prevention**: Add pre-commit hook to validate UTF-8 encoding
3. **Testing**: Regex validation for Korean Unicode range

**Implementation**:
```typescript
// frontend/src/lib/errorMessages.ts (CORRECTED VERSION)
export const errorMessages = {
  // Authentication errors
  INVALID_CREDENTIALS: "사용자 이름 또는 비밀번호가 올바르지 않습니다.",
  SESSION_EXPIRED: "세션이 만료되었습니다. 다시 로그인해주세요.",
  UNAUTHORIZED: "권한이 없습니다.",

  // Network errors
  NETWORK_ERROR: "네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.",
  SERVER_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",

  // ... (complete all error messages with proper Korean)
}

// Validation test
function validateKoreanText(text: string): boolean {
  const koreanPattern = /^[\uAC00-\uD7A3\s\w\d.,!?'"()]+$/
  return koreanPattern.test(text)
}
```

**Pre-commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Validate UTF-8 encoding in TypeScript files
for file in $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$'); do
  if ! iconv -f UTF-8 -t UTF-8 "$file" > /dev/null 2>&1; then
    echo "ERROR: $file is not valid UTF-8"
    exit 1
  fi
done
```

**Testing**:
```bash
# Manual validation
cd frontend/src/lib
file errorMessages.ts  # Should show: "UTF-8 Unicode text"
iconv -f UTF-8 -t UTF-8 errorMessages.ts > /dev/null && echo "Valid UTF-8"

# Automated test (add to tests/korean_quality_test.py)
def test_error_messages_encoding():
    import re
    from frontend.src.lib import errorMessages  # Assuming TS compiled to JS
    korean_pattern = re.compile(r'^[\uAC00-\uD7A3\s\w\d.,!?\'"()]+$')

    for key, msg in errorMessages.items():
        assert korean_pattern.match(msg), f"{key} contains non-Korean characters: {msg}"
```

#### FR-116: Active User Metric Fix (CRITICAL)

**Problem**: `active_users` metric calculated incorrectly using `created_at >= now - 30m` instead of `expires_at > now`, mixing timezone-naive/aware datetimes.

**Location**: `backend/app/core/business_metrics.py:31`

**Solution**:
```python
# BEFORE (INCORRECT)
async def get_active_users_count(db: AsyncSession) -> int:
    now = datetime.utcnow()  # ❌ Deprecated, timezone-naive
    cutoff = now - timedelta(minutes=30)
    stmt = select(func.count(func.distinct(Session.user_id))).where(
        Session.created_at >= cutoff  # ❌ Wrong logic
    )
    ...

# AFTER (CORRECT)
async def get_active_users_count(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)  # ✅ Timezone-aware
    stmt = select(func.count(func.distinct(Session.user_id))).where(
        Session.expires_at > now  # ✅ Correct: non-expired sessions
    )
    result = await db.execute(stmt)
    count = result.scalar() or 0

    logger.debug(f"Active users count: {count} (current time: {now.isoformat()})")
    return count
```

**Verification**:
```python
# Integration test
async def test_active_users_metric_accuracy():
    # Create 2 active sessions (expire in future)
    session1 = create_session(user_id=1, expires_at=now + timedelta(minutes=10))
    session2 = create_session(user_id=2, expires_at=now + timedelta(minutes=20))

    # Create 1 expired session
    session3 = create_session(user_id=3, expires_at=now - timedelta(minutes=5))

    # Metric should count only non-expired
    metric = await get_active_users_count(db)
    assert metric == 2, f"Expected 2 active users, got {metric}"

    # Verify timezone-aware
    assert metric.collected_at.tzinfo is not None
```

#### FR-117: Async Query Metrics (HIGH)

**Problem**: Event listeners bound only to `sync_engine`, missing async queries from application.

**Solution**:
```python
# backend/app/core/database.py

# BEFORE: Only sync_engine events captured
@event.listens_for(sync_engine, "before_cursor_execute")
def before_cursor_execute(...):
    ...

# AFTER: Capture both sync and async
@event.listens_for(Engine, "before_cursor_execute")  # Universal listener
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._query_start_time
    query_type = _get_query_type(statement)

    db_query_duration.labels(query_type=query_type).observe(duration)
    db_queries_total.labels(query_type=query_type, status='success').inc()

# Update pool metrics to use async engine
def update_pool_metrics():
    try:
        # Get pool from async engine's sync_engine
        pool = async_engine.sync_engine.pool
        db_connections_active.set(pool.checkedout())
    except Exception as e:
        logger.warning(f"Failed to update pool metrics: {e}")
```

**Validation**:
```bash
# Make API requests then check Prometheus
curl http://localhost:8000/api/v1/auth/me  # Trigger async query
curl http://localhost:8000/metrics | grep db_queries_total

# Expected output:
# db_queries_total{query_type="select",status="success"} 42.0
# (should be non-zero if async queries captured)
```

#### FR-118: Admin Privilege Model (HIGH)

**Problem**: Dual privilege models (`User.is_admin` + `Admin` table) with inconsistent usage.

**Decision**: Use `User.is_admin` as single source of truth (simpler, already implemented).

**Migration Path**:
```python
# Option A: Remove Admin table (RECOMMENDED)
# backend/alembic/versions/20251104_remove_admin_table.py

def upgrade():
    # 1. Ensure all users with Admin records have is_admin=True
    op.execute("""
        UPDATE users
        SET is_admin = TRUE
        WHERE id IN (SELECT user_id FROM admins)
    """)

    # 2. Drop Admin table
    op.drop_table('admins')

def downgrade():
    # Recreate Admin table
    op.create_table('admins', ...)
    op.execute("""
        INSERT INTO admins (user_id, created_at)
        SELECT id, created_at FROM users WHERE is_admin = TRUE
    """)
```

**Update Dependency**:
```python
# backend/app/api/deps.py (NO CHANGE NEEDED - already uses is_admin)

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:  # ✅ Already correct
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다."
        )
    return current_user
```

**Documentation**:
```markdown
# docs/admin/user-management.md

## Administrator Management

Administrators are identified by the `is_admin` flag on the User model.

### Creating Administrators
1. Via setup wizard (first admin only, FR-034)
2. Via direct database modification (additional admins, FR-033):
   ```sql
   UPDATE users SET is_admin = TRUE WHERE username = 'john.doe';
   ```

### Removing Admin Privileges
```sql
UPDATE users SET is_admin = FALSE WHERE username = 'john.doe';
```

**Note**: Users cannot remove their own admin privileges (enforced at application level).
```

#### FR-119: CSRF Token Optimization (MEDIUM)

**Problem**: CSRF token regenerated on every GET request, causing unnecessary rotation.

**Solution**:
```python
# backend/app/middleware/csrf_middleware.py

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # GET requests: Only generate token if missing/expired
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)

            if request.url.path not in self.CSRF_EXEMPT_PATHS:
                # Check if token already exists
                existing_token = request.cookies.get("csrf_token")

                if not existing_token:  # Only generate if missing
                    csrf_token = secrets.token_urlsafe(32)
                    response.set_cookie(
                        key="csrf_token",
                        value=csrf_token,
                        httponly=False,
                        secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite,
                        max_age=settings.SESSION_TIMEOUT_MINUTES * 60
                    )
                    logger.debug(f"CSRF token generated for new session")

            return response

        # POST/PUT/DELETE/PATCH: Validate (unchanged)
        ...
```

**Alternative Approach** (generate on login only):
```python
# backend/app/api/v1/auth.py

@router.post("/login")
async def login(...):
    # ... authenticate user ...

    # Generate CSRF token on login
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", csrf_token, ...)

    # Also set session cookie
    response.set_cookie("session_token", session.session_token, ...)

    return LoginResponse(...)
```

#### FR-120: CSRF Exemption Patterns (MEDIUM)

**Solution**:
```python
# backend/app/middleware/csrf_middleware.py

class CSRFMiddleware(BaseHTTPMiddleware):
    # Support both exact and prefix matching
    CSRF_EXEMPT_PATTERNS = [
        ("/api/v1/auth/login", "exact"),
        ("/api/v1/setup", "prefix"),  # Matches /api/v1/setup/*
        ("/health", "exact"),
        ("/api/v1/health", "exact"),
        ("/docs", "exact"),
        ("/openapi.json", "exact"),
        ("/metrics", "exact"),  # Prometheus
    ]

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF validation"""
        for pattern, match_type in self.CSRF_EXEMPT_PATTERNS:
            if match_type == "exact":
                if path == pattern:
                    return True
            elif match_type == "prefix":
                if path.startswith(pattern):
                    return True
        return False

    async def dispatch(self, request: Request, call_next):
        # Use helper for exemption check
        if self._is_exempt(request.url.path):
            logger.debug(f"CSRF exempt path: {request.url.path}")
            return await call_next(request)
        ...
```

#### FR-121: Security Test Alignment (MEDIUM)

**Solution**:
```python
# tests/security_audit.py

# BEFORE (INCORRECT - expects passlib)
def test_password_hashing():
    from passlib.context import CryptContext  # ❌ Not used
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    ...

# AFTER (CORRECT - matches actual implementation)
def test_password_hashing():
    import bcrypt  # ✅ Matches backend/app/core/security.py

    password = "testpassword123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

    # Verify correct password
    assert bcrypt.checkpw(password.encode(), hashed)

    # Verify wrong password
    assert not bcrypt.checkpw("wrongpass".encode(), hashed)

    # Verify rounds = 12 (FR-029)
    assert hashed.startswith(b'$2b$12$')

def test_login_endpoint_uses_bcrypt():
    """Integration test: actual endpoint uses correct hashing"""
    # Create user with known password
    create_user(username="testuser", password="password123")

    # Login should work
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
```

#### FR-122: Data Isolation (MEDIUM)

**Decision**: Use Option B (document existing isolation at dependency level).

**Rationale**: Data isolation already enforced via `get_current_user()` dependency in all routes. No middleware needed.

**Documentation**:
```python
# backend/app/api/deps.py (existing code, add comments)

async def get_current_user(
    session_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract current user from session token.

    Data Isolation (FR-032):
    All API routes using this dependency automatically enforce user_id filtering
    via query filters or ownership validation. Middleware not required.

    Examples:
    - GET /conversations/{id}: Route validates conversation.user_id == current_user.id
    - DELETE /documents/{id}: Route validates document.user_id == current_user.id
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    session = await get_session(db, session_token)
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")

    user = await get_user_by_id(db, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    return user
```

**Update Test Expectations**:
```python
# tests/security_audit.py

def test_data_isolation_via_dependencies():
    """
    Verify data isolation at API dependency level (not middleware).
    FR-032, FR-122 Option B.
    """
    # Create two users
    user1 = create_user("user1")
    user2 = create_user("user2")

    # User1 creates conversation
    conv = create_conversation(user1)

    # User2 attempts to access User1's conversation
    response = client.get(
        f"/api/v1/conversations/{conv.id}",
        cookies={"session_token": user2.session_token}
    )

    # Should return 403 Forbidden
    assert response.status_code == 403
    assert "권한이 없습니다" in response.json()["detail"]
```

### Testing Strategy

#### CRITICAL Tests (must pass before merge)

1. **FR-115**: Korean encoding validation
   ```bash
   npm run test:encoding  # Validates errorMessages.ts
   git diff frontend/src/lib/errorMessages.ts  # Manual review
   ```

2. **FR-116**: Active users metric accuracy
   ```bash
   pytest backend/tests/test_metrics_accuracy.py -v
   ```

#### HIGH Tests (required for production)

3. **FR-117**: Async query metrics
   ```bash
   # Start server, make requests, check metrics
   curl http://localhost:8000/api/v1/conversations
   curl http://localhost:8000/metrics | grep db_queries_total
   ```

4. **FR-118**: Admin privilege consistency
   ```bash
   pytest backend/tests/test_admin_auth.py -v
   ```

#### MEDIUM Tests (recommended)

5-8. **FR-119 ~ FR-122**:
   ```bash
   pytest backend/tests/test_security_enhancements.py -v
   ```

### Deployment Checklist

**Pre-merge**:
- [ ] All CRITICAL tests passing
- [ ] Korean error messages display correctly in browser
- [ ] Active users metric matches database query
- [ ] Prometheus shows non-zero async query counts
- [ ] Admin model documented in user-management.md

**Post-merge monitoring**:
- [ ] No mojibake reports from users
- [ ] Metrics dashboard shows accurate counts
- [ ] Prometheus query metrics increasing
- [ ] No 403 errors on exempt paths

### Success Criteria

- **SC-033**: Korean text displays correctly ✅
- **SC-034**: Active users = non-expired sessions ✅
- **SC-035**: Async queries in Prometheus ✅
- **SC-036**: Admin privilege checks consistent ✅
- **SC-037**: CSRF tokens stable within session ✅
- **SC-038**: Common paths exempt from CSRF ✅
- **SC-039**: Security tests match implementation ✅
- **SC-040**: Data isolation verified ✅

---

**Implementation Priority**:
1. FR-115, FR-116 (CRITICAL) - immediate fix
2. FR-117, FR-118 (HIGH) - before production
3. FR-119 ~ FR-122 (MEDIUM) - maintenance release acceptable
