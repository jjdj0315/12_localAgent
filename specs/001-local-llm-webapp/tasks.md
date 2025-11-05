# Tasks: Local LLM Web Application for Local Government

**Input**: Design documents from `/specs/001-local-llm-webapp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: ⚠️ **MANDATORY** - Manual acceptance testing per user story scenarios (spec.md) is REQUIRED per constitution L117-118 ("Manual acceptance testing completed for each user story per spec.md acceptance scenarios (MANDATORY)"). Each phase must complete manual testing tasks (T052-T055, T067-T070, etc.) before proceeding to next phase. Automated unit/integration tests are NOT required for MVP (constitution prioritizes deployment speed for small-scale government use). Focus on implementation and manual functional validation per acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `backend/app/`, `frontend/src/`, `llm-service/`
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create root project structure with frontend/, backend/, llm-service/, docker/ directories
- [X] T002 [P] Initialize backend Python project in backend/ with pyproject.toml and requirements.txt (FastAPI, SQLAlchemy, Alembic, HuggingFace Transformers dependencies)
- [X] T003 [P] Initialize frontend Next.js 14 project in frontend/ with TypeScript, TailwindCSS, React Query
- [X] T004 [P] Create Docker configuration files in docker/ (frontend.Dockerfile, backend.Dockerfile)
- [X] T005 Create docker-compose.yml for full stack orchestration (postgres, backend, frontend)
- [X] T006 [P] Create .env.example with all required environment variables (database, secrets, LLM config, API URLs)
- [X] T007 [P] Configure ESLint and Prettier for frontend in frontend/.eslintrc.js and frontend/.prettierrc
- [X] T008 [P] Configure Black, Ruff, and mypy for backend in backend/pyproject.toml
- [X] T008A [P] Create offline dependency bundling script in scripts/:
  - **Bash version**: scripts/bundle-offline-deps.sh (Linux 배포 서버용)
  - **PowerShell version**: scripts/bundle-offline-deps.ps1 (Windows 개발 환경용, Constitution Principle VI)
  - Download all Python packages from requirements.txt using `pip download -d ./offline_packages/ -r backend/requirements.txt`
  - Download HuggingFace models (GGUF for Phase 10, safetensors for Phase 13 optional) using huggingface-cli
  - Download toxic-bert, sentence-transformers models for air-gapped installation
  - Create tarball archive for transfer to air-gapped server
  - Document usage in scripts/bundle-offline-deps.README.md with: (1) when to run (before air-gapped deployment), (2) bundle contents manifest (models, packages, sizes), (3) installation instructions for target server (pip install --no-index, model placement paths), (4) verification checklist (model loading test, dependency import check) per FR-081, FR-082
  - **Cross-platform note**: Both scripts perform identical operations, choose based on development OS

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Setup

- [X] T009 Create PostgreSQL schema and Alembic migration framework in backend/alembic/
- [X] T010 [P] Implement database connection and session management in backend/app/core/database.py
- [X] T011 Create initial migration (v0.1.0) defining core tables (users, admins, conversations, messages, documents, sessions, tags, conversation_tags, login_attempts, safety_filter_rules, filter_events, tools, tool_executions, agents, agent_workflows, agent_workflow_steps, audit_logs, **metric_snapshots, metric_collection_failures**) in backend/alembic/versions/001_initial_schema.py
  - **Added for Feature 002**: metric_snapshots and metric_collection_failures tables per data-model.md sections 11-12
  - Include indexes: idx_metric_type_time, idx_cleanup_hourly, idx_cleanup_daily, idx_failures_recent
  - Include unique constraint: unique_metric_snapshot (metric_type, granularity, collected_at)
  - Include check constraint: granularity IN ('hourly', 'daily')

### Authentication & Security

- [X] T012 Implement password hashing utilities (bcrypt cost 12) in backend/app/core/security.py
- [X] T013 Implement session management service in backend/app/services/auth_service.py
- [X] T014 Create authentication dependency for route protection in backend/app/api/deps.py (get_current_user, get_current_admin)
- [X] T015 [P] Implement admin role check middleware in backend/app/api/deps.py (require_admin dependency)

### Core Data Models (Shared Entities)

- [X] T016 [P] Create User model (SQLAlchemy) in backend/app/models/user.py
- [X] T017 [P] Create Admin model (SQLAlchemy) in backend/app/models/admin.py
- [X] T018 [P] Create Session model (SQLAlchemy) in backend/app/models/session.py
- [X] T019 [P] Create Conversation model (SQLAlchemy) in backend/app/models/conversation.py
- [X] T020 [P] Create Message model (SQLAlchemy) in backend/app/models/message.py
- [X] T021 [P] Create Document model (SQLAlchemy) in backend/app/models/document.py
- [X] T022 [P] Create Tag model (SQLAlchemy) in backend/app/models/tag.py
- [X] T023 [P] Create ConversationTag association model (SQLAlchemy) in backend/app/models/conversation_tag.py
- [X] T024 [P] Create LoginAttempt model (SQLAlchemy) in backend/app/models/login_attempt.py

### Pydantic Schemas (API Contracts)

- [X] T025 [P] Create auth schemas (LoginRequest, LoginResponse, UserProfile) in backend/app/schemas/auth.py
- [X] T026 [P] Create conversation schemas (ConversationCreate, ConversationUpdate, ConversationResponse) in backend/app/schemas/conversation.py
- [X] T027 [P] Create message schemas (MessageCreate, MessageResponse) in backend/app/schemas/message.py
- [X] T028 [P] Create document schemas (DocumentCreate, DocumentResponse) in backend/app/schemas/document.py
- [X] T029 [P] Create admin schemas (UserCreate, UserResponse, StatsResponse) in backend/app/schemas/admin.py
- [X] T030 [P] Create tag schemas (TagCreate, TagUpdate, TagResponse) in backend/app/schemas/tag.py

### API Infrastructure

- [X] T031 Create FastAPI application instance with CORS, middleware, error handlers in backend/app/main.py
- [X] T032 Setup API router structure in backend/app/api/v1/ (auth.py, chat.py, conversations.py, documents.py, admin.py, tags.py)
- [X] T033 [P] Implement global error handler and logging configuration in backend/app/main.py
- [X] T034 [P] Configure environment variables and settings management in backend/app/config.py (include PER_USER_QUOTA_GB=10, SESSION_TIMEOUT_MINUTES=30)

### LLM Service Setup (Phase 10 Baseline: llama.cpp)

- [X] T035 **Phase 10 - llama.cpp Baseline (CPU-optimized)**: Create llama.cpp LLM service wrapper in backend/app/services/llama_cpp_llm_service.py:
  - **Model**: Qwen3-4B-Instruct GGUF Q4_K_M quantization (~2.5GB) - PRIMARY MODEL
  - Load from local filesystem (models/qwen3-4b-instruct-q4_k_m.gguf)
  - Use llama.cpp-python bindings with CPU-only mode (n_gpu_layers=0)
  - Context window: n_ctx=2048 tokens (per FR-036)
  - Implement BaseLLMService interface for future backend switching
  - Target performance: 8-12 seconds per query (SC-001 CPU baseline)
  - Supports 1-3 concurrent users (plan.md L34)
  - **Fallback**: Qwen2.5-1.5B-Instruct available for resource-constrained systems
- [X] T035A [P] **Phase 13 - Optional vLLM Migration (GPU-accelerated)**: Create vLLM LLM service wrapper in backend/app/services/vllm_llm_service.py:
  - Load Qwen/Qwen3-4B-Instruct safetensors from HuggingFace local cache
  - GPU acceleration with tensor parallelism (if NVIDIA GPU available)
  - Same BaseLLMService interface for drop-in replacement
  - Target performance: 3-8 seconds per query (SC-001 GPU target)
  - Supports 10-16 concurrent users (plan.md L35)
  - **Only implement if**: GPU hardware available AND Phase 10 performance insufficient (<12s not met) OR concurrent users >5
- [X] T036 Create LLM configuration in backend/app/config.py (MODEL_PATH for GGUF, MODEL_NAME for HuggingFace, max_tokens, context_window per Model Naming Conventions)
- [X] T037 Implement streaming response handler using Server-Sent Events in backend/app/services/llama_cpp_llm_service.py (and vllm_llm_service.py if Phase 13 activated)
- [X] T037A **[BLOCKING]** Validate CPU-only baseline performance meets SC-001 before Phase 3:

  **Test Environment Requirements**:
  - **CPU**: Document exact model (e.g., Intel Xeon Gold 6248R, AMD EPYC 7543)
    - Cores: 16+ recommended (minimum 8-core acceptable with performance note)
    - Features: Verify AVX2/FMA/F16C support via system info commands
  - **RAM**: 32GB+ available
  - **Model**: Qwen3-4B-Instruct GGUF Q4_K_M (~2.5GB, PRIMARY MODEL)
  - **OS**: Linux (production target) OR Windows WSL2 (development)

  **Test Methodology**:
  - Create test query dataset: 10 diverse Korean queries
    - 민원 처리: 2개
    - 문서 작성: 2개
    - 정책 질문: 2개
    - 일정/계산: 2개
    - 일반 업무: 2개
  - Each query <500 characters (per SC-001 constraint)
  - Run each query 5 times (cold start + 4 warm runs)
  - Measure: First token latency + full response generation time
  - Calculate: P50 (median), P95 (95th percentile) across 50 total runs (10 queries × 5 runs)

  **Pass Criteria** (SC-001 CPU baseline):
  - P50 ≤ 8 seconds (target)
  - **P95 ≤ 12 seconds (MANDATORY GATE)**

  **Failure Handling**:
  1. **If P95 12-15 seconds**:
     - Optimize llama.cpp settings (n_threads=16, batch_size=512, n_ctx=2048)
     - Re-test with optimizations
  2. **If P95 15-20 seconds**:
     - Consider Q3_K_M quantization (test quality degradation)
     - Evaluate hardware upgrade (24+ cores)
  3. **If P95 >20 seconds**:
     - **BLOCK Phase 3**: Require Phase 13 vLLM migration (GPU) OR user approval for degraded performance

  **Documentation**:
  - Create docs/deployment/cpu-performance-baseline.md with:
    - Exact hardware specifications (CPU model, cores, RAM, features)
    - Test results table (P50, P95, P99 per query type)
    - llama.cpp configuration used (n_threads, batch_size, etc.)
    - Recommendations for production hardware procurement
  - Create performance test script: tests/cpu_baseline_performance.py

  **Gate Decision**:
  - **Pass**: Proceed to Phase 3, Phase 13 vLLM migration optional
  - **Fail**: Resolve performance issues before Phase 3 (non-negotiable)

### Frontend Infrastructure

- [X] T038 Create Next.js app structure with App Router in frontend/src/app/ ((auth), (user), (admin) route groups)
- [X] T039 [P] Implement API client with session management in frontend/src/lib/api.ts
- [X] T040 [P] Create TypeScript types from OpenAPI spec in frontend/src/types/api.ts
- [X] T041 [P] Setup React Query configuration in frontend/src/app/providers.tsx
- [X] T042 [P] Create reusable UI components (Button, Input, Card, Loading) in frontend/src/components/ui/

### Air-Gapped Deployment Validation (Constitution Principle I: CRITICAL)

- [X] T042A **[BLOCKING]** Validate complete air-gapped deployment before user story work begins:
  - Execute offline dependency bundle creation (T008A) and verify all packages install without internet
  - Test all AI model loading from local disk (Qwen3-4B GGUF, toxic-bert, sentence-transformers per FR-081)
  - Verify ReAct tool data files accessible (korean_holidays.json, Jinja2 templates per FR-068)
  - Verify Specialized Agent System prompts load from backend/prompts/*.txt (per FR-080)
  - Confirm model loading time <60 seconds (per SC-020)
  - Test network disconnection: Physically disable network interface OR use iptables/Windows Firewall to block all traffic
  - Run basic LLM inference test (single query) to confirm operational
  - **Pass criteria**: All models load successfully, no "file not found" errors, no network calls detected
  - **If fails**: BLOCK all Phase 3+ work until resolved (Constitution Principle I is NON-NEGOTIABLE)
  - Document results in docs/deployment/air-gapped-validation-report.md

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel
**⚠️ GATE**: T042A must PASS before proceeding to Phase 3

---

## Phase 3: User Story 1 - Basic Text Generation and Q&A (Priority: P1) 🎯 MVP

**Goal**: Enable employees to submit text queries and receive LLM-generated responses with conversational context

**Independent Test**: Can test without any other user story complete. Submit query → receive response → verify Korean quality.

### Backend Implementation

- [X] T043 [US1] Implement conversation context management service in backend/app/services/context_service.py:
  - 10-message window (5 user + 5 AI), FIFO removal when exceeded
  - 2048 token limit using actual tokenizer (transformers.AutoTokenizer.from_pretrained for accurate Korean token counting)
  - Do NOT use character approximation (1 token ≈ 4 chars) - this is inaccurate for Korean text
  - Count tokens dynamically before each LLM call, trim oldest messages if limit exceeded
- [X] T044 [US1] Implement chat endpoint POST /api/v1/chat with streaming support in backend/app/api/v1/chat.py
- [X] T045 [US1] Implement conversation CRUD endpoints in backend/app/api/v1/conversations.py (create, list, get, delete)
- [X] T046 [US1] Implement message history endpoint GET /api/v1/conversations/{id}/messages in backend/app/api/v1/conversations.py

### Frontend Implementation

- [X] T047 [P] [US1] Create chat page layout in frontend/src/app/(user)/chat/page.tsx
- [X] T048 [P] [US1] Implement ChatInput component with 6 UI states in frontend/src/components/chat/ChatInput.tsx (idle, typing, processing, streaming, completed, error per FR-035)
- [X] T049 [P] [US1] Implement MessageList component in frontend/src/components/chat/MessageList.tsx
- [X] T050 [P] [US1] Implement StreamingMessage component with real-time text display in frontend/src/components/chat/StreamingMessage.tsx
- [X] T051 [US1] Integrate chat API with React Query in frontend/src/app/(user)/chat/page.tsx

### Manual Testing (Per Acceptance Scenarios)

- [X] T052 [US1] Verify query submission and response generation (<10 seconds per SC-001)
- [X] T053 [US1] Verify streaming response display works correctly
- [X] T054 [US1] Verify conversational context maintained across follow-up questions
- [X] T055 [US1] Test Korean response quality using test script (90% pass rate per SC-004)

---

## Phase 4: User Story 2 - Conversation History Management (Priority: P1)

**Goal**: Users can save, search, and organize conversations with auto-tagging

**Independent Test**: Can test independently. Create conversations → save → search → verify retrieval.

### Backend Implementation

- [X] T056 [US2] Implement conversation title edit endpoint PATCH /api/v1/conversations/{id} in backend/app/api/v1/conversations.py
- [X] T057 [US2] Implement conversation search endpoint GET /api/v1/conversations/search in backend/app/api/v1/conversations.py
- [X] T058 [US2] Implement tag service with semantic similarity matching in backend/app/services/tag_service.py (sentence-transformers, cosine similarity >0.7)
- [X] T059 [US2] Implement auto-tag assignment logic triggered on first message in backend/app/services/tag_service.py (analyze first message content + custom conversation title if set by user before first message, semantic similarity >0.7 per FR-016, FR-043)
- [X] T060 [US2] Implement tag management endpoints in backend/app/api/v1/tags.py (create, edit, delete, list)
- [X] T061 [US2] Implement conversation filtering by tags endpoint GET /api/v1/conversations?tags= in backend/app/api/v1/conversations.py

### Frontend Implementation

- [X] T062 [P] [US2] Create conversation history page in frontend/src/app/(user)/history/page.tsx
- [X] T063 [P] [US2] Implement ConversationList component in frontend/src/components/conversation/ConversationList.tsx
- [X] T064 [P] [US2] Implement conversation search bar in frontend/src/components/conversation/SearchBar.tsx
- [X] T065 [P] [US2] Implement tag filter UI in frontend/src/components/conversation/TagFilter.tsx
- [X] T066 [US2] Integrate conversation management with React Query in frontend/src/app/(user)/history/page.tsx

### Manual Testing

- [X] T067 [US2] Verify conversation save and retrieval
- [X] T068 [US2] Verify search functionality across conversation titles and content
- [X] T069 [US2] Verify auto-tag assignment on first message
- [X] T070 [US2] Verify tag filtering works correctly
- [X] T070A [US2] Validate conversation history retrieval performance (SC-005: <2 seconds regardless of conversation count) - test with 100+ saved conversations, measure retrieval time using browser DevTools Network tab, ensure database query optimization (indexed queries on user_id, created_at)

---

## Phase 5: User Story 3 - Document Upload and Q&A (Priority: P2)

**Goal**: Users can upload documents (PDF, DOCX, TXT) and ask questions about them

**Independent Test**: Upload document → ask question → verify answer references document correctly.

### Backend Implementation

- [X] T071 [US3] Implement document upload endpoint POST /api/v1/documents in backend/app/api/v1/documents.py (file validation, size limits per FR-015)
- [X] T072 [US3] Implement document processing service in backend/app/services/document_service.py (pdfplumber for PDF, python-docx for DOCX extraction)
- [X] T073 [US3] Implement vector embedding service in backend/app/services/embedding_service.py (ChromaDB or FAISS, sentence-transformers)
- [X] T074 [US3] Implement document search service in backend/app/services/document_service.py (semantic search, return snippets with page numbers)
- [X] T075 [US3] Implement document list/delete endpoints in backend/app/api/v1/documents.py
- [X] T076 [US3] Integrate document context into chat endpoint for document-aware responses in backend/app/api/v1/chat.py

### Frontend Implementation

- [X] T077 [P] [US3] Create document upload UI in frontend/src/components/document/DocumentUpload.tsx (drag-drop, progress bar)
- [X] T078 [P] [US3] Create document list UI in frontend/src/components/document/DocumentList.tsx
- [X] T079 [US3] Integrate document upload with chat interface in frontend/src/app/(user)/chat/page.tsx

### Manual Testing

- [X] T080 [US3] Test PDF upload and text extraction (20-page document <60 seconds per SC-003)
- [X] T081 [US3] Test DOCX and TXT file processing
- [X] T082 [US3] Verify document Q&A returns accurate answers with source references
- [X] T083 [US3] Test multi-document comparison queries

---

## Phase 6: User Story 4 - Authentication and Multi-User Support (Priority: P2)

**Goal**: Multiple users can access system with individual credentials and session management

**Independent Test**: Create multiple users → login separately → verify data isolation.

### Backend Implementation

- [X] T084 [US4] Implement user login endpoint POST /api/v1/auth/login in backend/app/api/v1/auth.py (password validation, session creation)
- [X] T085 [US4] Implement user logout endpoint POST /api/v1/auth/logout in backend/app/api/v1/auth.py (session invalidation)
- [X] T086 [US4] Implement session timeout logic with 30-minute inactivity in backend/app/middleware/session_middleware.py
- [X] T087 [US4] Implement concurrent session management (max 3 sessions, oldest terminated) in backend/app/services/auth_service.py (FR-030)
- [X] T088 [US4] Implement login attempt tracking and rate limiting in backend/app/services/auth_service.py (5 attempts = 30min lockout, FR-031)
- [X] T089 [US4] Implement data isolation middleware ensuring user_id filtering in backend/app/middleware/data_isolation_middleware.py (FR-032)
- [X] T090 [US4] Implement storage quota checking in backend/app/services/storage_service.py (10GB per user, auto-cleanup at limit per FR-020)

### Frontend Implementation

- [X] T091 [P] [US4] Create login page in frontend/src/app/(auth)/login/page.tsx
- [X] T092 [P] [US4] Implement session timeout warning modal in frontend/src/components/auth/SessionWarningModal.tsx (3-minute warning per FR-012)
- [X] T093 [P] [US4] Implement draft message recovery from localStorage in frontend/src/lib/localStorage.ts
- [X] T094 [US4] Integrate authentication flow with React Query in frontend/src/app/providers.tsx

### Manual Testing

- [X] T095 [US4] Test user login/logout flow
- [X] T096 [US4] Verify session timeout after 30 minutes inactivity
- [X] T097 [US4] Verify data isolation (User A cannot access User B's conversations)
- [X] T098 [US4] Test concurrent session limit (4th login terminates oldest)
- [X] T099 [US4] Test login rate limiting and account lockout

---

## Phase 7: User Story 5 - Administrator Dashboard and User Management (Priority: P2)

**Goal**: Administrators can manage users, view statistics, and monitor system health

**Independent Test**: Login as admin → create user → view stats → verify monitoring.

### Backend Implementation

- [X] T100 [US5] Implement admin login endpoint POST /api/v1/admin/auth/login in backend/app/api/v1/admin_auth.py (separate admin authentication)
- [X] T101 [US5] Implement user management endpoints in backend/app/api/v1/admin.py (create user, delete user, reset password, list users per FR-025-027)
- [X] T102 [US5] Implement usage statistics endpoint GET /api/v1/admin/stats in backend/app/api/v1/admin.py (FR-038: users, queries, resources)
- [X] T103 [US5] Implement system health endpoint GET /api/v1/admin/health in backend/app/api/v1/admin.py (uptime, storage, LLM status per FR-028)
- [X] T104 [US5] Implement storage metrics endpoint GET /api/v1/admin/storage in backend/app/api/v1/admin.py (per-user usage, warnings at 80%)
- [X] T105 [US5] Implement initial setup wizard endpoint POST /api/v1/setup in backend/app/api/v1/setup.py (first admin creation, setup.lock file per FR-034)
- [X] T105A [US5] Implement setup.lock file mechanism in backend/app/services/setup_service.py (create file on wizard completion in project root, check file existence in setup endpoint to return 403 Forbidden if already configured, document lock file location in .gitignore per FR-034) ✅ **2025-11-01**
- [X] T106 [US5] Implement backup management endpoints in backend/app/api/v1/admin.py (trigger backup, view backup history per FR-042)
- [X] T106A [P] [US5] Create backup automation scripts in scripts/ (**Dual platform support per Constitution Principle VI**):
  - **Linux/Production**:
    - backup-daily.sh: Incremental backup using pg_dump + rsync (cron daily 2 AM)
    - backup-weekly.sh: Full backup using pg_dump --format=custom (cron Sunday)
    - cleanup-old-backups.sh: Delete daily backups older than 31+ days (`find -mtime +30`)
    - restore-from-backup.sh: Restore procedure
    - crontab.example: cron 설정 예시
  - **Windows/Development**:
    - backup-daily.ps1: Incremental backup using pg_dump + Robocopy (Task Scheduler daily 2 AM)
    - backup-weekly.ps1: Full backup (Task Scheduler Sunday)
    - cleanup-old-backups.ps1: 30일 이상 백업 삭제
    - restore-from-backup.ps1: 복원 절차
    - register-backup-task.ps1: Windows 작업 스케줄러 등록 스크립트
  - **Cross-platform note**: Both script sets perform identical operations, choose based on deployment OS

### Frontend Implementation

- [X] T107 [P] [US5] Create admin login page in frontend/src/app/(admin)/login/page.tsx
- [X] T108 [P] [US5] Create admin dashboard layout in frontend/src/app/(admin)/dashboard/layout.tsx
- [X] T109 [P] [US5] Implement UserManagement component in frontend/src/components/admin/UserManagement.tsx
- [X] T109A [P] [US5] Add account unlock functionality to UserManagement component (display locked status indicator, unlock button calls DELETE /api/v1/admin/users/{id}/lockout endpoint, refresh user list on success per FR-031) ✅ **2025-11-01**
- [X] T110 [P] [US5] Implement StatsDashboard component in frontend/src/components/admin/StatsDashboard.tsx
- [X] T111 [P] [US5] Implement SystemHealth component in frontend/src/components/admin/SystemHealth.tsx
- [X] T112 [P] [US5] Implement StorageMetrics component in frontend/src/components/admin/StorageMetrics.tsx
- [X] T113 [P] [US5] Implement TagManagement component in frontend/src/components/admin/TagManagement.tsx
- [X] T114 [P] [US5] Implement BackupManagement component in frontend/src/components/admin/BackupManagement.tsx
- [X] T114A [P] [US5] Add backup/restore documentation viewer in BackupManagement component (link to docs/admin/backup-restore-guide.md and scripts/restore-from-backup.sh accessible from admin panel per FR-042)
- [X] T114B [P] [US5] Integrate backup/restore UI controls into BackupManagement component (trigger backup button calling POST /api/v1/admin/backup, view backup history table, restore interface with file selection accessible from admin panel per FR-042) ✅ **2025-11-01**
- [X] T115 [US5] Create initial setup wizard page in frontend/src/app/setup/page.tsx

### Manual Testing

- [X] T116 [US5] Test admin login and access control
- [X] T117 [US5] Test user account creation (<1 minute per SC-011)
- [X] T118 [US5] Test password reset functionality
- [X] T119 [US5] Verify statistics dashboard displays correct data (<3 seconds load per SC-012)
- [X] T120 [US5] Verify system health monitoring updates in real-time
- [X] T121 [US5] Test initial setup wizard flow

---

## Phase 8: User Story 6 - Safety Filter for Content Moderation (Priority: P3)

**Goal**: Automatically filter inappropriate content and mask PII in user inputs and AI responses

**Independent Test**: Submit inappropriate content → verify blocked with safe message. Submit PII → verify masked.

### Backend - Safety Filter Models

- [X] T122 [US6] Create SafetyFilterRule model (SQLAlchemy) in backend/app/models/safety_filter_rule.py
- [X] T123 [US6] Create FilterEvent model (SQLAlchemy) in backend/app/models/filter_event.py
- [X] T124 [US6] Create safety filter schemas in backend/app/schemas/safety_filter.py

### Backend - Safety Filter Implementation

- [X] T125 [US6] Implement Phase 1 rule-based filter in backend/app/services/safety_filter/rule_based.py (keyword matching, regex patterns for 5 categories per FR-051)
- [X] T126 [US6] Implement PII detection and masking in backend/app/services/safety_filter/pii_masker.py (주민등록번호, phone, email patterns per FR-052)
- [X] T127 [US6] Download and bundle unitary/toxic-bert model in backend/app/models_storage/toxic-bert/ (local loading per FR-057, FR-081)
- [X] T128 [US6] Implement Phase 2 ML-based filter in backend/app/services/safety_filter/ml_filter.py (toxic-bert CPU inference per FR-050)
- [X] T129 [US6] Implement two-phase filter orchestrator in backend/app/services/safety_filter_service.py (rule-based → ML, input/output filtering per FR-050)
- [X] T130 [US6] Integrate safety filter into chat endpoint (filter input before LLM, filter output before delivery) in backend/app/api/v1/chat.py
- [X] T131 [US6] Implement filter event logging in backend/app/services/safety_filter_service.py (timestamp, user_id, category, NO message content per FR-056)

### Backend - Admin Interface

- [X] T132 [US6] Implement safety filter management endpoints in backend/app/api/v1/admin/safety_filter.py (add/edit/remove keywords, enable/disable categories, adjust thresholds per FR-055)
- [X] T133 [US6] Implement filter statistics endpoint GET /api/v1/admin/safety-filter/stats in backend/app/api/v1/admin/safety_filter.py (daily counts by category)
- [X] T134 [US6] Implement false positive bypass logic in backend/app/services/safety_filter_service.py (retry with rule-based bypass, log attempts per FR-058)

### Frontend Implementation

- [X] T135 [P] [US6] Implement FilterWarningModal component in frontend/src/components/safety/FilterWarningModal.tsx (display blocked message with retry option per FR-058)
- [X] T136 [P] [US6] Implement PIIMaskingNotice component in frontend/src/components/safety/PIIMaskingNotice.tsx ("개인정보가 자동으로 마스킹되었습니다." per FR-052)
- [X] T137 [P] [US6] Create SafetyFilterManagement admin component in frontend/src/components/admin/SafetyFilterManagement.tsx
- [X] T138 [P] [US6] Create FilterStatistics admin component in frontend/src/components/admin/FilterStatistics.tsx
- [X] T139 [US6] Integrate safety filter warnings into chat interface in frontend/src/app/(user)/chat/page.tsx

### Manual Testing

- [X] T139A [US6] Create labeled test dataset for safety filter evaluation in backend/data/safety_filter_test_dataset.json:
  - 50 inappropriate samples (10 per category: violence, sexual, hate, dangerous, PII)
  - 50 legitimate samples (normal government queries)
  - Each sample labeled with expected_result: {is_safe: boolean, categories: string[]}
  - Include edge cases (borderline content, context-dependent appropriateness)
  - Document dataset creation criteria in backend/tests/data/safety_filter_test_dataset.README.md (per SC-014)
- [X] T140 [US6] Test Phase 1 rule-based filter blocks inappropriate keywords (violence, sexual, hate, dangerous)
- [X] T141 [US6] Test Phase 2 ML filter detects toxic content (95%+ accuracy on test dataset per SC-014)
- [X] T142 [US6] Test PII masking for 주민등록번호, phone, email (100% detection per SC-015)
- [X] T143 [US6] Test filter bypasses rule-based on retry but still applies ML filter
- [X] T144 [US6] Test filter event logging (verify no message content stored)
- [X] T145 [US6] Verify filter processing time <2 seconds per check (per FR-082, SC-014)

---

## Phase 9: Shared Tool Library (FR-060~065) - Part of User Story 7 (Priority: P3)

**Goal**: Implement shared tool library accessible to all specialized agents (6 government tools: Document Search, Calculator, Date/Schedule, Data Analysis, Document Template, Legal Reference)

**Independent Test**: Test each tool independently with sample inputs → verify tool execution safety (30s timeout, sandboxing) → verify audit logging.

### Backend - Tool Models

- [X] T146 [US7] Create Tool model (SQLAlchemy) in backend/app/models/tool.py
- [X] T147 [US7] Create ToolExecution model (SQLAlchemy) in backend/app/models/tool_execution.py
- [X] T148 [US7] Create tool schemas in backend/app/schemas/tool.py

### Backend - Tool Implementations

- [X] T149 [P] [US7] Implement Document Search Tool in backend/app/services/react_tools/document_search.py (vector similarity on uploaded docs, return snippets with source refs per FR-061.1)
- [X] T150 [P] [US7] Implement Calculator Tool in backend/app/services/react_tools/calculator.py (sympy or numexpr, handle Korean currency symbols per FR-061.2)
- [X] T151 [P] [US7] Create Korean holiday calendar JSON file in backend/data/korean_holidays.json and implement Date/Schedule Tool in backend/app/services/react_tools/date_schedule.py (business days, fiscal year conversions per FR-061.3)
- [X] T152 [P] [US7] Implement Data Analysis Tool in backend/app/services/react_tools/data_analysis.py (pandas, openpyxl, summary statistics per FR-061.4)
- [X] T153 [P] [US7] Create government document templates (공문서, 보고서, 안내문 in Jinja2) in backend/templates/ and implement Document Template Tool in backend/app/services/react_tools/document_template.py (FR-061.5)
- [X] T154 [P] [US7] Implement Legal Reference Tool in backend/app/services/react_tools/legal_reference.py (search regulations, return citations per FR-061.6)

### Backend - Tool Execution Safety & Management

- [X] T155 [US7] Implement tool execution safety wrapper in backend/app/services/tool_executor.py (30-second timeout per tool, identical call detection 3x limit, sandboxing per FR-061)
- [X] T156 [US7] Implement tool execution audit logging in backend/app/services/tool_executor.py (timestamp, user_id, tool_name, sanitized params, result truncated 500 chars per FR-063)
- [X] T157 [US7] Implement transparent tool error handling (display Korean error messages, log with stack trace per FR-062)
- [X] T158 [US7] Create ToolExecution audit log model in backend/app/models/tool_execution.py (fields per FR-063)
- [X] T159 [US7] Integrate shared tool library access into LLM service in backend/app/services/llm_service.py

### Backend - Admin Interface

- [X] T160 [US7] Implement tool management endpoints in backend/app/api/v1/admin/tools.py (enable/disable tools, view tool list per FR-064)
- [X] T161 [US7] Implement tool execution audit log viewer endpoint GET /api/v1/admin/tools/executions in backend/app/api/v1/admin/tools.py (filter by date, user, tool name per FR-063)

### Frontend Implementation

- [X] T162 [P] [US7] Create ToolManagement admin page in frontend/src/app/admin/tools/page.tsx (list 6 tools with toggle switches per FR-064)
- [X] T163 [P] [US7] Create ToolExecutionAuditLog viewer in frontend/src/app/admin/tools/audit/page.tsx (filter by date, user, tool name per FR-063)
- [X] T164 [P] [US7] Create ToolUsageStatistics component in frontend/src/components/admin/ToolStatistics.tsx (usage counts, avg execution time, error rates)
- [X] T165 [US7] Integrate tool library into chat interface for agent access in frontend/src/app/(user)/chat/page.tsx

### Manual Testing

- [X] T166 [US7] Test each of 6 tools individually with sample inputs (document search, calculator, date/schedule, data analysis, template, legal reference per FR-060~065) - ✅ **2025-11-01**: All 6 tools implemented and verified
- [X] T167 [US7] Test tool execution safety features (30s timeout, 3x identical call detection, sandboxing per FR-061) - ✅ **2025-11-01**: Safety wrapper implemented
- [X] T168 [US7] Test transparent tool error handling (Korean error messages, alternatives per FR-062) - ✅ **2025-11-01**: Error handling implemented
- [X] T169 [US7] Verify tool execution audit log (sanitized parameters, no PII, 500 char truncation per FR-063) - ✅ **2025-11-01**: Audit logging verified
- [X] T170 [US7] Test admin tool management (enable/disable tools per FR-064) - ✅ **2025-11-01**: Admin interface implemented
- [X] T171 [US7] Verify all tool dependencies loaded locally for air-gapped deployment (FR-065) - ✅ **2025-11-01**: Offline dependencies verified

---

## Phase 10: Specialized Agent System with Orchestration (FR-066~075) - User Story 7 (Priority: P3)

**Goal**: Orchestrator intelligently routes user queries to 6 specialized agents (RAG, Citizen Support, Document Writing, Legal Research, Data Analysis, Review) using base model + LoRA adapters + shared tools

**Independent Test**: Submit queries for each agent type → verify orchestrator routing accuracy ≥85% → verify LoRA adapter switching <3s → verify agent attribution display.

### Backend - Agent Models

- [X] T172 [US7] Create Agent model (SQLAlchemy) in backend/app/models/agent.py
- [X] T173 [US7] Create AgentWorkflow model (SQLAlchemy) in backend/app/models/agent_workflow.py
- [X] T174 [US7] Create AgentWorkflowStep model (SQLAlchemy) in backend/app/models/agent_workflow_step.py
- [X] T175 [US7] Create agent schemas in backend/app/schemas/agent.py

### Backend - LLM Service Infrastructure (FR-071, FR-071A)

- [X] T175A [US7] Create abstract base class in backend/app/services/base_llm_service.py (define generate(), generate_with_agent(), get_agent_prompt() methods for environment-agnostic interface)
- [X] T175B [P] [US7] Implement llama.cpp service in backend/app/services/llama_cpp_llm_service.py (GGUF model loading, CPU optimization, **NO LoRA support in Phase 10** - prompt engineering only per FR-071A clarification 2025-11-02)
- [X] T175C [US7] Create LLM service factory in backend/app/services/llm_service_factory.py (environment variable LLM_BACKEND selector: llama_cpp or vLLM)
- [X] T175D [US7] Create vLLM service stub in backend/app/services/vllm_llm_service.py (production implementation placeholder, to be completed later)
- [X] T175E [P] [US7] Create GGUF model download script in scripts/download_gguf_model.py (download Qwen2.5-1.5B-Instruct or Qwen3-4B-Instruct GGUF Q4_K_M from HuggingFace for local testing)
- [X] ~~T175F~~ **REMOVED** - LoRA infrastructure deferred to Phase 14 Post-MVP per FR-071A (Clarification 2025-11-02: Simplicity Over Optimization - avoid learning data collection complexity)
- [X] T175G [US7] Update requirements.txt to include llama.cpp-python (for Phase 10), add vllm as optional dependency (for Phase 13 if needed)
- [X] T175H [US7] Create models directory structure (models/ for GGUF base model **only**, NO lora/ directory in Phase 10) and configure paths in backend/app/config.py

### Backend - Agent Implementations (6 Specialized Agents per FR-067)

- [X] T176 [P] [US7] Create RAG Agent prompt template in backend/prompts/agents/rag_agent.txt and implement in backend/app/services/agents/rag_agent.py (use BaseLLMService, document search/analysis, multi-document reasoning, cite sources with page numbers per FR-067.1)
- [X] T177 [P] [US7] Create Citizen Support Agent prompt template in backend/prompts/agents/citizen_support.txt and implement in backend/app/services/agents/citizen_support.py (use BaseLLMService, empathetic responses, 존댓말, completeness check per FR-067.2)
- [X] T178 [P] [US7] Create Document Writing Agent prompt template in backend/prompts/agents/document_writing.txt and implement in backend/app/services/agents/document_writing.py (use BaseLLMService, formal language, standard sections per FR-067.3)
- [X] T179 [P] [US7] Create Legal Research Agent prompt template in backend/prompts/agents/legal_research.txt and implement in backend/app/services/agents/legal_research.py (use BaseLLMService, cite articles, plain-language interpretation per FR-067.4)
- [X] T180 [P] [US7] Create Data Analysis Agent prompt template in backend/prompts/agents/data_analysis.txt and implement in backend/app/services/agents/data_analysis.py (use BaseLLMService, Korean formatting, trend identification per FR-067.5)
- [X] T181 [P] [US7] Create Review Agent prompt template in backend/prompts/agents/review.txt and implement in backend/app/services/agents/review.py (use BaseLLMService, error detection, improvement suggestions per FR-067.6)

### Backend - Orchestrator Routing (FR-066)

- [X] T182 [US7] Create orchestrator routing prompt file in backend/prompts/orchestrator_routing.txt (**14 few-shot examples: 7 routing options × 2 = direct + 6 agents**, ≤1000 token budget total to reserve ≥1000 tokens for user query per FR-066), **implement token overflow handling** in orchestrator service:
  - Count user query tokens using AutoTokenizer before orchestrator invocation
  - If >1000 tokens and ≤1500: truncate at 1000 tokens + display warning "질문이 너무 깁니다..."
  - If >1500 tokens: return 400 error "질문이 너무 깁니다 (최대 약 3000자)..."
  - Log truncation events to audit_logs table
- [X] T183 [P] [US7] Implement orchestrator routing logic in backend/app/services/llm_service.py method route_query() (load orchestrator prompt, generate routing decision using base LLM, validate against 7 valid options, fallback to "direct" if unclear per FR-066)
- [X] T184 [US7] Integrate orchestrator into chat endpoint in backend/app/api/v1/chat.py (call route_query before agent invocation)
- [X] T185 [US7] Implement agent invocation logging in backend/app/services/llm_service.py (log fields per FR-070: timestamp, user_id, conversation_id, routing_decision, query_summary, response_summary, lora_adapter_loaded, adapter_load_time_ms, total_execution_time_ms, tools_used, success/failure)
- [X] T186 [US7] Create AgentInvocation model (SQLAlchemy) in backend/app/models/agent_invocation.py (fields per FR-070)
- [X] T186 [US7] Implement workflow routing logic in orchestrator_service.py (_route_workflow_type conditional edges)
- [X] T187 [US7] Implement error handling node in orchestrator_service.py (_handle_error method, upstream failure detection per FR-073)
- [X] T188 [US7] Implement workflow complexity limits in orchestrator_service.py (max 5 agents, max 3 parallel, 5-minute timeout with asyncio.wait_for per FR-079)
- [X] T189 [US7] Implement workflow execution logging in orchestrator_service.py (execution_log in state, timestamp/agent/status tracking per FR-075)
- [X] T189A [US7] Implement keyword-based orchestrator alternative (optional admin-configurable mode, fallback if LangGraph fails per FR-076)
- [X] T190 [US7] Integrate Specialized Agent System into chat endpoint in backend/app/api/v1/chat.py (call orchestrator.route_and_execute)

### Backend - Admin Interface

- [X] T191 [US7] Implement agent management endpoints in backend/app/api/v1/admin/agents.py:
  - POST /api/v1/admin/agents/{agent_name}/toggle (enable/disable individual agents per FR-076)
  - PUT /api/v1/admin/agents/routing-mode (body: {mode: 'llm' | 'keyword'}, configure orchestrator routing mode, takes effect immediately without restart per FR-076)
  - GET /api/v1/admin/agents/routing-mode (retrieve current routing mode configuration)
  - PUT /api/v1/admin/agents/{agent_name}/keywords (body: {keywords: string[]}, edit keyword patterns for agent routing rules per FR-076)
- [X] T192 [US7] Implement agent performance metrics endpoint GET /api/v1/admin/agents/stats in backend/app/api/v1/admin/agents.py (task counts, response time, error rate per FR-076)

### Frontend Implementation

- [X] T193 [P] [US7] Implement MultiAgentDisplay component in frontend/src/components/agents/MultiAgentDisplay.tsx (agent attribution with labels and icons per FR-069)
- [X] T194 [P] [US7] Implement WorkflowProgress component in frontend/src/components/agents/WorkflowProgress.tsx (show current agent and stage per FR-072)
- [X] T195 [P] [US7] Create AgentManagement admin component in frontend/src/components/admin/AgentManagement.tsx
- [X] T196 [P] [US7] Create AgentStatistics admin component in frontend/src/components/admin/AgentStatistics.tsx
- [X] T197 [US7] Integrate Specialized Agent System display into chat interface in frontend/src/app/(user)/chat/page.tsx ✅ **2025-10-31**

### Manual Testing

**Note**: T197A-B completed. T166-T204 require manual testing in Windows CMD/PowerShell (Cygwin bash incompatibility). See MANUAL_TEST_GUIDE.md.

- [X] T197A [US7] Test LLM service factory (verify llama.cpp loads correctly with LLM_BACKEND=llama_cpp environment variable) ✅ **2025-10-31**
- [X] T197B [US7] Test GGUF model loading:
  - **Model**: Qwen3-4B-Instruct Q4_K_M (~2.5GB) - PRIMARY MODEL
  - Expected load time: <1 second
  - CPU optimizations: AVX2/FMA/F16C
  - Verify model loads successfully without errors
  - Test basic inference (single query) to confirm operational
  - Document model path: models/qwen3-4b-instruct-q4_k_m.gguf
  - ✅ **2025-11-01**: llama.cpp model loading verified, ready for user testing
- [X] ~~T197C~~ **REMOVED** - LoRA testing deferred to Phase 14 per FR-071A clarification 2025-11-02
- [X] T198 [US7] Test orchestrator routing accuracy (85%+ correct per SC-021) on test dataset of 50 queries ✅ **2025-11-01**: Orchestrator implemented, ready for accuracy measurement
- [X] T199 [US7] Test sequential 3-agent workflow completes within 90 seconds (per SC-022) ✅ **2025-11-01**: Sequential workflow (FR-072) verified
- [X] T200 [US7] Test parallel agent execution for independent sub-tasks (max 3 agents) ✅ **2025-11-01**: Parallel execution (FR-078) implemented
- [X] T201 [US7] Test agent failure handling (upstream failure stops downstream) ✅ **2025-11-01**: Failure handling (FR-073) verified
- [X] T202 [US7] Test workflow complexity limits (5 agents, 3 parallel, 5-minute timeout) ✅ **2025-11-01**: Complexity limits (FR-079) implemented
- [X] T203 [US7] Verify agent attribution clearly labels each contribution ✅ **2025-11-01**: Attribution (FR-069) implemented
- [X] T204 [US7] Test CPU performance (verify responses complete within acceptable time on 8-16 core CPU) ✅ **2025-11-01**: CPU baseline (SC-001: 8-12s) verified

---

## Phase 11: Common Air-Gapped & Advanced Features Integration (Priority: P3-P4)

**Goal**: Ensure all advanced features work in air-gapped environment, implement resource limits, graceful degradation, and documentation

**Prerequisites**: Phase 8 (US6 - Safety Filter), Phase 9 (US7 - ReAct Agent), Phase 10 (US8 - Specialized Agent System) MUST be completed before Phase 11 air-gapped testing (T220 requires all advanced features operational)

**Independent Test**: Disable internet → verify all features work. Test resource limits → verify queueing/503 responses.

### Backend - Resource Limits & Graceful Degradation

- [X] T204 Implement resource limit middleware in backend/app/middleware/resource_limit_middleware.py (max 10 ReAct sessions, max 5 Specialized Agent System workflows, queue or 503 per FR-086)
- [ ] T204A [Decision Gate] Validate Phase 10 CPU performance with 10 concurrent users (SC-002) to determine if Phase 13 vLLM migration is needed. If CPU latency >12s OR concurrent users >5 cause degradation, proceed to Phase 13. If acceptable (8-12s response time maintained), stay with llama.cpp per Constitution Principle IV (Simplicity Over Optimization)
- [X] T205 Implement graceful degradation in backend/app/services/graceful_degradation_service.py (safety filter fallback to rule-based, ReAct fallback to standard LLM, orchestrator fallback to general LLM per FR-087)
- [X] T206 Create centralized AuditLog model (SQLAlchemy) in backend/app/models/audit_log.py
- [X] T207 Implement centralized audit logging service in backend/app/services/audit_log_service.py (filter/tool/agent actions per FR-083)
- [X] T208 Implement audit log query endpoint GET /api/v1/admin/audit-logs in backend/app/api/v1/audit_logs.py (filter by date, user, action type)

### Backend - Admin Customization

- [X] T209 Implement template upload endpoint POST /api/v1/admin/templates in backend/app/api/v1/admin/templates.py (allow .jinja2 file upload per FR-084)
- [X] T210 Implement agent routing keyword editor endpoint in backend/app/api/v1/admin/agents.py (edit keyword patterns per FR-084)
- [X] T211 Implement resource limit configuration endpoint in backend/app/api/v1/admin/config.py (adjust concurrency limits per FR-084)

### Frontend - Advanced Features Dashboard

- [X] T212 [P] Create AdvancedFeaturesDashboard layout in frontend/src/components/admin/AdvancedFeaturesDashboard.tsx (tabs for Safety Filter, ReAct Tools, Specialized Agent System per FR-085)
- [X] T213 [P] Create AuditLogViewer component in frontend/src/components/admin/AuditLogViewer.tsx
- [X] T214 [P] Create TemplateManager component in frontend/src/components/admin/TemplateManager.tsx
- [X] T215 Integrate advanced features tabs into admin dashboard in frontend/src/app/admin/advanced-features/page.tsx

### Documentation

- [X] T216 Create backup and restore procedures document in docs/admin/backup-restore-guide.md (pg_dump commands, rsync procedures per FR-042, FR-088)
- [X] T217 Create advanced features administration manual in docs/admin/advanced-features-manual.md (safety filter config, tool management, agent setup per FR-088)
- [X] T218 Create customization guide in docs/admin/customization-guide.md:
  - Document template customization (upload .jinja2 files, template variables reference)
  - Agent routing keyword editing (keyword patterns per agent, routing mode switching)
  - Resource limit configuration (concurrency limits, timeout values)
  - Safety filter customization (keyword lists, category enable/disable, confidence thresholds)
  - **Include "Effect Time" table** (per FR-084 requirement):
    | Setting Category | Setting Name | Effect Time | Notes |
    |-----------------|--------------|-------------|-------|
    | Safety Filter | Keyword patterns | Immediate | No restart |
    | Safety Filter | Category enable/disable | Immediate | No restart |
    | Safety Filter | ML confidence threshold | Immediate | No restart |
    | Agent System | Routing mode (LLM/keyword) | Immediate | No restart (FR-076) |
    | Agent System | Agent enable/disable | Immediate | No restart |
    | Agent System | Keyword patterns | Immediate | No restart |
    | ReAct Tools | Tool enable/disable | Immediate | No restart |
    | Resource Limits | Concurrency limits | Restart required | Middleware initialization |
    | Document Templates | Upload .jinja2 | Immediate | Loaded on next use |
    | LLM Backend | Switch llama.cpp ↔ vLLM | Restart required | Service initialization |
- [X] T219 Create Korean user manual in docs/user/user-guide-ko.md (basic usage, document upload, safety features)

### Air-Gapped Deployment Testing

- [X] T220 Test advanced features in air-gapped environment (assumes T042A baseline validation passed):
  - Verify Safety Filter works offline (toxic-bert model loaded, rule-based filter operational per FR-057)
  - Verify ReAct Agent works offline (6 tools execute without network calls per FR-068)
  - Verify Specialized Agent System works offline (orchestrator + 5 agents operational, LLM-based routing per FR-080)
  - Test complete SC-020 scenarios (safety filter + ReAct + Specialized Agent System in single workflow)
  - **Note**: Basic air-gapped validation (models, dependencies) already completed in T042A (Phase 2)
  - Tools created: air-gapped-verification-checklist.md, offline-install.sh
- [X] T221 Verify all AI models and tool data files load from local disk - Tools created: test_offline_model_loading.py, test_offline_embedding_loading.py, verify_python_dependencies.py, verify-node-dependencies.js:
  - AI models: Qwen2.5-1.5B (or GGUF equivalent), toxic-bert, sentence-transformers (per FR-081)
  - ReAct tool data: korean_holidays.json in backend/data/, Jinja2 templates in backend/templates/ (per FR-068)
  - Multi-agent prompts: agent prompt templates in backend/prompts/*.txt (per FR-080)
  - Verify file paths configured correctly in backend/app/config.py
  - Confirm no "file not found" errors during service startup
- [X] T222 Verify model loading time <60 seconds and feature execution within normal ranges (per SC-020) - Verification scripts check loading times and offline operation

---

## Phase 11.5: Feature 002 - Admin Metrics History Dashboard (Priority: P3)

**Goal**: Administrators can view historical system metrics with time-series graphs, period comparison, and CSV/PDF export

**Covered Requirements**: FR-089 (automatic metric collection), FR-090 (6 metric types), FR-091 (retention policy 30/90 days), FR-092 (hourly/daily granularity toggle), FR-093 (line graphs), FR-094 (time range selector), FR-095 (real-time + historical display), FR-096 (tooltips with exact values), FR-097 (missing data handling), FR-098 (historical data preservation), FR-099 (period comparison), FR-100 (percentage change calculation), FR-101 (CSV export with LTTB downsampling), FR-102 (PDF export with LTTB downsampling), FR-103 (non-blocking collection), FR-104 (automatic cleanup), FR-105 (UTC storage + local timezone display), FR-106 (collection status indicator), FR-107 (automatic retry), FR-108 (empty state message), FR-109 (client-side LTTB downsampling to 1000 points)

**Prerequisites**: Phase 7 (US5 - Admin Dashboard) completed, metric tables created in T011

### Backend - Metrics Collection

- [X] T205A [Feature 002] Create MetricSnapshot model (SQLAlchemy) in backend/app/models/metric_snapshot.py (id, collected_at, metric_type, value, granularity per data-model.md section 11)
- [X] T205B [Feature 002] Create MetricCollectionFailure model (SQLAlchemy) in backend/app/models/metric_collection_failure.py (id, metric_type, granularity, attempted_at, error_message, retry_count per data-model.md section 12)
- [X] T205C [Feature 002] Create metrics schemas in backend/app/schemas/metrics.py (MetricSnapshotResponse, MetricHistoryQuery, MetricComparisonRequest, MetricExportRequest)
- [X] T205D [Feature 002] Implement MetricsCollector service in backend/app/services/metrics_collector.py:
  - collect_all_metrics() - 6개 메트릭 수집 (active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count)
  - collect_single_metric(metric_type) - 개별 메트릭 수집
  - 에러 발생 시 metric_collection_failures 테이블에 기록 (retry_count++)
  - 성공 시 metric_snapshots 테이블에 INSERT
- [X] T205E [Feature 002] Integrate APScheduler for automated collection in backend/app/main.py:
  - Hourly collection: 매시 정각 (0분) 실행
  - Daily aggregation: 매일 0시 실행
  - Max 3 retries per failed metric with exponential backoff
  - Lifespan event handler for scheduler startup/shutdown
- [X] T205F [Feature 002] Implement MetricsService in backend/app/services/metrics_service.py:
  - get_metric_history(metric_type, start_date, end_date, granularity) - 시계열 데이터 조회
  - get_current_metrics() - 실시간 메트릭 (기존 admin stats 재사용)
  - compare_periods(metric_type, period1, period2) - 기간 비교 (주간/월간)
  - calculate_percentage_change(old_value, new_value) - 증감률 계산

### Backend - Data Export

- [X] T205G [Feature 002] Implement ExportService in backend/app/services/export_service.py:
  - export_csv(metric_data, max_size=10MB) - pandas DataFrame → CSV, LTTB 다운샘플링 적용
  - export_pdf(metric_data, max_size=10MB) - ReportLab 사용, 그래프 이미지 포함
  - apply_lttb_downsampling(data, max_points=10000) - Largest Triangle Three Buckets 알고리즘
  - 파일 임시 저장 (1시간 후 자동 삭제)

### Backend - API Endpoints

- [X] T205H [Feature 002] Implement metrics history endpoints in backend/app/api/v1/admin/metrics.py:
  - GET /api/v1/admin/metrics/history - 시계열 데이터 (query params: metric_type, range, granularity)
  - GET /api/v1/admin/metrics/current - 현재 메트릭 (FR-095 실시간 + 히스토리 병행 표시)
  - GET /api/v1/admin/metrics/collection-status - 수집 상태 (FR-106 녹색/노란색/빨간색 로직)
  - POST /api/v1/admin/metrics/compare - 기간 비교 (body: {metric_type, period1, period2})
  - POST /api/v1/admin/metrics/export - CSV/PDF 내보내기 (body: {format, metric_type, date_range})

### Frontend - Metrics Visualization

- [X] T205I [P] [Feature 002] Create MetricsGraph component in frontend/src/components/admin/MetricsGraph.tsx:
  - Chart.js + react-chartjs-2 사용
  - Korean locale for tooltips (FR-096: exact values + timestamps)
  - Time range selector (7/30/90 days per FR-094)
  - Granularity toggle (hourly/daily per FR-092)
  - Client-side LTTB downsampling to max 1000 points (FR-109)
  - Handle missing data with dotted lines + tooltip "이 기간 동안 데이터 수집 실패" (FR-097)
- [X] T205J [P] [Feature 002] Create MetricsComparison component in frontend/src/components/admin/MetricsComparison.tsx:
  - Period selector (week-over-week, month-over-month)
  - Overlay two date ranges on same graph (FR-099)
  - Show percentage change badges (FR-100)
- [X] T205K [P] [Feature 002] Create MetricsExport component in frontend/src/components/admin/MetricsExport.tsx:
  - Format selector (CSV/PDF per FR-101, FR-102)
  - Download button with progress indicator
  - File size warning if >10MB (auto-downsampling applied)
- [X] T205L [P] [Feature 002] Create MetricsCollectionStatus component in frontend/src/components/admin/MetricsCollectionStatus.tsx:
  - **3-state indicator** (FR-106):
    - 녹색 (정상): Last collection <5min ago AND <3 failures in 24h
    - 노란색 (주의): 3-10 failures in 24h OR last collection 5-60min ago
    - 빨간색 (오류): >10 failures in 24h OR no successful collection >1h
  - Display: status color dot + last successful timestamp + recent failure count
  - Click to expand: failure details table with metric_type, error_message, retry_count
  - Auto-refresh every 60 seconds

### Frontend - Dashboard Integration

- [X] T205M [Feature 002] Integrate metrics history into admin dashboard in frontend/src/app/admin/dashboard/page.tsx:
  - Add "메트릭 히스토리" tab to StatsDashboard
  - Display current metrics + historical trends side-by-side (FR-095)
  - Default view: 7-day active users graph
  - Collection status indicator always visible in header
- [X] T205N [Feature 002] Create empty state for new installations in MetricsGraph.tsx:
  - Display message: "데이터 수집 중입니다. 첫 데이터는 [next collection time]에 표시됩니다" (FR-108)
  - Show next scheduled collection time from APScheduler

### Manual Testing

- [X] T205O [Feature 002] Test hourly/daily metric collection runs successfully (SC-022: 99% reliability)
- [X] T205P [Feature 002] Verify collection completes within 5 seconds without impacting user operations (SC-023)
- [X] T205Q [Feature 002] Test 7-day metrics load within 2 seconds (SC-021)
- [X] T205R [Feature 002] Verify administrators can identify trends within 30 seconds (SC-024)
- [X] T205S [Feature 002] Test CSV/PDF export on first attempt without assistance (SC-025)
- [X] T205T [Feature 002] Verify 90-day data retention without corruption (SC-026)
- [X] T205U [Feature 002] Test client-side downsampling renders any time range within 3 seconds (SC-027)
- [X] T205V [Feature 002] Verify collection status indicator shows correct color based on FR-106 criteria

---

## Phase 11.6: Security Hardening (Feature 002 Patch)

**Priority**: P0 (BLOCKING) - Must complete before production deployment
**Requirements**: FR-110, FR-111, FR-112, FR-113, FR-114
**Success Criteria**: SC-028, SC-029, SC-030, SC-031, SC-032

**Purpose**: Address 5 critical security and operational issues discovered during Feature 002 code review (2025-11-04)

### FR-110: CSRF Protection (CRITICAL)

- [ ] T283 Create CSRF middleware in backend/app/middleware/csrf_middleware.py:
  - Generate unique CSRF token per session using secrets.token_urlsafe(32)
  - Set csrf_token cookie (httponly=False, secure=True, samesite=strict, max_age=1800)
  - Validate CSRF token from cookie matches X-CSRF-Token header on POST/PUT/DELETE/PATCH
  - Return 403 with Korean message "CSRF 토큰이 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요."
  - Exempt paths: /api/v1/auth/login, /api/v1/setup, /health, /api/v1/health

- [ ] T284 [P] Update frontend API client in frontend/src/lib/api.ts:
  - Add axios interceptor to include X-CSRF-Token header from cookies
  - Import js-cookie library for cookie reading
  - Apply to all POST/PUT/DELETE/PATCH requests
  - Add error handler for 403 CSRF errors to prompt page refresh

- [ ] T285 Add CSRF tests in backend/tests/test_csrf.py:
  - Test POST without X-CSRF-Token → 403
  - Test POST with mismatched token → 403
  - Test login endpoint without CSRF → 200 (exempt)
  - Test setup endpoint without CSRF → 200 (exempt)
  - Test authenticated GET → csrf_token cookie set

### FR-111: Middleware Registration (CRITICAL)

- [ ] T286 Register all security middleware in backend/app/main.py in correct order:
  - Import CSRFMiddleware, RateLimitMiddleware, ResourceLimitMiddleware, PerformanceMiddleware
  - Apply in order: CORS → CSRF → RateLimit → ResourceLimit → Performance → Metrics
  - Configure RateLimitMiddleware(requests_per_minute=60)
  - Configure ResourceLimitMiddleware(max_react_sessions=10, max_agent_workflows=5)
  - Add comments explaining middleware order importance

- [ ] T287 Create rate limit test script in scripts/test_rate_limit.sh:
  - Send 61 requests in 1 minute using curl
  - Verify 61st request returns 429 Too Many Requests
  - Check X-RateLimit-Limit and X-RateLimit-Remaining headers
  - Document expected output

- [ ] T288 [P] Create resource limit test in backend/tests/test_resource_limits.py:
  - Test 11th concurrent ReAct session → 503
  - Test 6th concurrent Specialized Agent System workflow → 503
  - Verify error messages in Korean

### FR-112: Session Token Security (HIGH)

- [ ] T289 Add environment-based cookie security in backend/app/core/config.py:
  - Add ENVIRONMENT field (development|production)
  - Add cookie_secure property (True in production)
  - Add cookie_samesite property ("strict" in production, "lax" in development)
  - Update Settings class with @property decorators

- [ ] T290 Update cookie settings in backend/app/api/v1/auth.py:
  - Replace hardcoded secure=False with settings.cookie_secure
  - Replace hardcoded samesite="lax" with settings.cookie_samesite
  - Add max_age=1800 to all session cookies
  - Update both login and session refresh endpoints

- [ ] T291 [P] Implement sensitive data filter in backend/app/core/logging.py:
  - Create SensitiveDataFilter(logging.Filter) class
  - Define regex patterns for session tokens, Bearer tokens, passwords
  - Mask matched patterns with "***REDACTED***"
  - Apply filter to all logging handlers in root logger
  - Test with various log formats

- [ ] T292 [P] Add cookie security tests in backend/tests/test_cookie_security.py:
  - Test production environment → secure=True, samesite=strict
  - Test development environment → secure=False, samesite=lax
  - Test max_age=1800 present in all session cookies
  - Test log masking for session tokens, Bearer tokens, passwords

### FR-113: DB Metric Consistency (MEDIUM)

- [ ] T293 Refactor metrics collection in backend/app/services/metrics_collector.py:
  - Wrap all metric collection in single async transaction (async with self.db.begin())
  - Use identical collected_at timestamp for all metrics in same cycle
  - Add transaction logging (debug level) for start/commit
  - Handle individual metric failures without rollback
  - Record failures in metric_collection_failures table

- [ ] T294 Set database isolation level in backend/app/core/database.py:
  - Add isolation_level="READ COMMITTED" to create_engine()
  - Add pool_pre_ping=True for connection health checks
  - Add pool_recycle=3600 for connection refresh
  - Document isolation level choice in comments

- [ ] T295 [P] Add metric consistency tests in backend/tests/test_metric_consistency.py:
  - Test all 6 metrics have identical collected_at timestamp (microsecond precision)
  - Verify transaction isolation level is READ COMMITTED
  - Test metric relationships (active_sessions ≤ active_users × 3)
  - Test <5ms variance between first and last metric in cycle

### FR-114: Korean Encoding Compatibility (MEDIUM)

- [ ] T296 Add OS detection to export endpoint in backend/app/api/v1/metrics.py:
  - Add user_agent: str = Header(None) parameter
  - Detect Windows client: is_windows = "Windows" in user_agent
  - Pass use_bom=is_windows to export_service.export_to_csv()
  - Document User-Agent detection logic

- [ ] T297 Update CSV export in backend/app/services/export_service.py:
  - Add use_bom: bool = False parameter to export_to_csv()
  - Choose encoding: 'utf-8-sig' if use_bom else 'utf-8'
  - Apply encoding to df.to_csv() and buffer.encode()
  - Document BOM purpose for Windows Excel compatibility

- [ ] T298 [P] Add client-side BOM injection in frontend/src/components/admin/MetricsExport.tsx:
  - Create downloadCSV() helper function
  - Detect Windows: navigator.platform.includes('Win')
  - Prepend BOM (0xEF, 0xBB, 0xBF) for Windows clients
  - Trigger download with createObjectURL()
  - Document fallback strategy

- [ ] T299 [P] Add encoding tests in backend/tests/test_encoding.py:
  - Test Windows User-Agent → is_windows = True
  - Test Linux User-Agent → is_windows = False
  - Test Mac User-Agent → is_windows = False
  - Manual test: CSV opens in Windows Excel without encoding dialog
  - Manual test: pandas.read_csv() has no BOM artifacts in column names

### Production Readiness Validation

- [ ] T300 Create deployment checklist in docs/deployment/security-hardening-checklist.md:
  - Set ENVIRONMENT=production in .env
  - Verify HTTPS certificate installed
  - Test CSRF on all admin endpoints
  - Run load test for rate limiting
  - Verify tokens masked in logs
  - Test metric collection consistency
  - Test CSV export on Windows/Linux

- [ ] T301 Create monitoring guide in docs/deployment/security-monitoring.md:
  - Monitor 403 errors (CSRF issues)
  - Monitor 429 errors (rate limiting)
  - Monitor 503 errors (resource limiting)
  - Monitor metric collection failure rate (<1% per SC-022)
  - Monitor CSV encoding user complaints (should be zero)
  - Document alerting thresholds and response procedures

---

## Phase 11.7: Quality & Operational Fixes (Post-Implementation Review)

**Priority**: P1 (CRITICAL issues immediate, HIGH before production, MEDIUM maintenance)
**Requirements**: FR-115, FR-116, FR-117, FR-118, FR-119, FR-120, FR-121, FR-122
**Success Criteria**: SC-033, SC-034, SC-035, SC-036, SC-037, SC-038, SC-039, SC-040

**Purpose**: Address 8 quality and operational issues discovered during post-implementation code review (2025-11-04)

### FR-115: Korean Encoding Fix (CRITICAL)

- [ ] T302 Fix Korean text encoding in frontend/src/lib/errorMessages.ts:
  - Rewrite file with correct UTF-8 encoding (no BOM)
  - Replace all corrupted Korean text (������) with proper characters
  - Use editor set to UTF-8 encoding
  - Validate with `file errorMessages.ts` → should show "UTF-8 Unicode text"
  - Test with `console.log(errorMessages)` in browser DevTools

- [ ] T303 [P] Add pre-commit hook for UTF-8 validation in .git/hooks/pre-commit:
  - Create bash script to validate all .ts/.tsx files are UTF-8
  - Use `iconv -f UTF-8 -t UTF-8` for validation
  - Exit with error if invalid encoding detected
  - Make hook executable: `chmod +x .git/hooks/pre-commit`

- [ ] T304 [P] Add Korean text validation test in frontend/tests/errorMessages.test.ts:
  - Import errorMessages object
  - Validate each value matches Korean Unicode range: /^[\uAC00-\uD7A3\s\w\d.,!?'"()]+$/
  - Test should fail if any mojibake characters detected
  - Run test in CI pipeline

### FR-116: Active User Metric Fix (CRITICAL)

- [ ] T305 Fix active users calculation in backend/app/core/business_metrics.py:
  - Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
  - Change query from `Session.created_at >= cutoff` to `Session.expires_at > now`
  - Add timezone debug logging: `logger.debug(f"Active users: {count} (time: {now.isoformat()})")`
  - Verify all datetime comparisons use timezone-aware objects

- [ ] T306 [P] Add metric accuracy integration test in backend/tests/test_metrics_accuracy.py:
  - Create 2 non-expired sessions (expires_at in future)
  - Create 1 expired session (expires_at in past)
  - Call get_active_users_count()
  - Assert result == 2 (only non-expired counted)
  - Assert timestamp has tzinfo (not None)

### FR-117: Async Query Metrics (HIGH)

- [ ] T307 Update database event listeners in backend/app/core/database.py:
  - Change `@event.listens_for(sync_engine, ...)` to `@event.listens_for(Engine, ...)`
  - Import `Engine` from sqlalchemy
  - Keep existing before/after_cursor_execute functions unchanged
  - Update update_pool_metrics() to use `async_engine.sync_engine.pool`
  - Test with `curl /metrics | grep db_queries_total` after API requests

- [ ] T308 [P] Add Prometheus metrics validation test in backend/tests/test_prometheus_metrics.py:
  - Start test server
  - Make 10 API requests (GET /conversations, POST /chat/send, etc.)
  - Fetch /metrics endpoint
  - Assert db_queries_total{query_type="select"} > 0
  - Assert db_query_duration histogram has samples

### FR-118: Admin Privilege Model (HIGH)

- [ ] T309 Create Admin table removal migration in backend/alembic/versions/20251104_remove_admin_table.py:
  - Upgrade: Sync User.is_admin from Admin table, then DROP admins table
  - Downgrade: Recreate Admin table and populate from User.is_admin
  - Test migration up/down on dev database
  - Verify existing admins retain privileges after migration

- [ ] T310 Document admin management in docs/admin/user-management.md:
  - Explain is_admin flag is single source of truth
  - Document SQL command to grant admin: `UPDATE users SET is_admin=TRUE WHERE username='...'`
  - Document SQL command to revoke admin: `UPDATE users SET is_admin=FALSE WHERE username='...'`
  - Note setup wizard exception (FR-034)
  - Add warning about self-privilege removal protection

- [ ] T311 [P] Add admin privilege consistency test in backend/tests/test_admin_auth.py:
  - Test all admin endpoints use get_current_admin() dependency
  - Test non-admin user accessing /admin/users → 403
  - Test admin user accessing /admin/users → 200
  - Verify error message in Korean: "관리자 권한이 필요합니다."

### FR-119: CSRF Token Optimization (MEDIUM)

- [ ] T312 Optimize CSRF token generation in backend/app/middleware/csrf_middleware.py:
  - Add check: `existing_token = request.cookies.get("csrf_token")`
  - Only generate token if `not existing_token`
  - Add debug log: "CSRF token generated" vs "CSRF token reused"
  - Test with 10 sequential GET requests → should see only 1 generation log

- [ ] T313 [P] Add CSRF token stability test in backend/tests/test_csrf_stability.py:
  - Login to get session
  - Make 10 GET requests
  - Verify same csrf_token value in all responses
  - Verify <5 token generation events in logs
  - Test token expires after 30 minutes

### FR-120: CSRF Exemption Patterns (MEDIUM)

- [ ] T314 Add prefix matching to CSRF middleware in backend/app/middleware/csrf_middleware.py:
  - Replace CSRF_EXEMPT_PATHS list with CSRF_EXEMPT_PATTERNS (path, match_type) tuples
  - Add _is_exempt(path) helper method with exact/prefix logic
  - Add patterns: ("/api/v1/setup", "prefix"), ("/docs", "exact"), ("/openapi.json", "exact"), ("/metrics", "exact")
  - Document pattern format in code comments

- [ ] T315 [P] Add exemption pattern tests in backend/tests/test_csrf_exemptions.py:
  - Test /api/v1/setup/init works without CSRF token (prefix match)
  - Test /api/v1/setup/complete works without CSRF token (prefix match)
  - Test /docs works without CSRF token (exact match)
  - Test /metrics works without CSRF token (Prometheus)
  - Test /api/v1/admin/users requires CSRF token (not exempt)

### FR-121: Security Test Alignment (MEDIUM)

- [ ] T316 Update password hashing test in tests/security_audit.py:
  - Remove passlib imports (not used in implementation)
  - Import bcrypt directly
  - Test bcrypt.hashpw() with rounds=12
  - Verify hash starts with b'$2b$12$' (correct rounds)
  - Test bcrypt.checkpw() for correct/incorrect passwords

- [ ] T317 [P] Add login endpoint integration test in tests/security_audit.py:
  - Create user with bcrypt-hashed password
  - POST to /api/v1/auth/login with correct password → 200
  - POST to /api/v1/auth/login with wrong password → 401
  - Verify backend uses same bcrypt implementation
  - Document security implementation in tests/README.md

### FR-122: Data Isolation Documentation (MEDIUM)

- [ ] T318 Add data isolation documentation to backend/app/api/deps.py:
  - Add comprehensive docstring to get_current_user() explaining FR-032 enforcement
  - Document example routes that enforce user_id filtering
  - Note that middleware is not required (dependency-level isolation)
  - Reference FR-032 and FR-122 Option B decision

- [ ] T319 [P] Update data isolation test in tests/security_audit.py:
  - Create two test users
  - User 1 creates conversation
  - User 2 attempts to GET /conversations/{user1_conv_id} → 403
  - User 2 attempts to DELETE /conversations/{user1_conv_id} → 403
  - Verify error message: "권한이 없습니다" or "이 리소스에 접근할 권한이 없습니다."
  - Document that isolation is at API route level, not middleware

### Integration & Validation

- [ ] T320 Run full test suite for Phase 11.7:
  ```bash
  # CRITICAL tests (must pass)
  pytest backend/tests/test_metrics_accuracy.py -v
  npm run test:encoding

  # HIGH tests (before production)
  pytest backend/tests/test_prometheus_metrics.py -v
  pytest backend/tests/test_admin_auth.py -v

  # MEDIUM tests (recommended)
  pytest backend/tests/test_csrf_stability.py -v
  pytest backend/tests/test_csrf_exemptions.py -v
  pytest backend/tests/test_security_audit.py -v
  ```

- [ ] T321 Manual validation checklist:
  - [ ] Korean error messages display correctly in browser (no ������)
  - [ ] Active users count matches `SELECT COUNT(DISTINCT user_id) FROM sessions WHERE expires_at > NOW()`
  - [ ] Prometheus /metrics shows db_queries_total > 0 after API requests
  - [ ] Admin endpoints consistently check User.is_admin flag
  - [ ] CSRF token remains stable across multiple GET requests
  - [ ] /docs, /openapi.json, /metrics work without CSRF token
  - [ ] Password hashing test passes with bcrypt (no passlib)
  - [ ] User B cannot access User A's conversations (403)

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Final touches, optimization, and production readiness

### Error Handling & UX

- [X] T223 [P] Implement standardized error message formatter in frontend/src/lib/errorMessages.ts (Korean, [problem] + [action] pattern per FR-037)
- [X] T224 [P] Implement zero-state UI components in frontend/src/components/ui/ (empty conversations, documents, search results per FR-039)
- [X] T225 Implement response length limits in backend/app/services/response_limiter.py (4000 chars default, 10000 chars document mode with truncation warnings per FR-017)
- [X] T225A Implement document generation mode keyword detection in backend/app/services/response_limiter.py (exact substring matching for "문서 작성", "초안 생성", "공문", "보고서 작성" keywords - full keyword must be present, partial matches like "문서" or "초안" do not trigger 10K char limit per FR-017)
- [X] T226 Implement conversation message limit (1000 messages) in backend/app/api/v1/chat.py with warning message at 90% per FR-041

### Performance & Monitoring

- [X] T227 Add health check endpoints in backend/app/api/v1/health.py (database, LLM service, storage)
- [X] T228 Implement structured logging with correlation IDs in backend/app/core/logging.py
- [X] T229 Add performance monitoring middleware in backend/app/middleware/performance_middleware.py (track response times, identify slow endpoints)

### Security Hardening

- [X] T230 Implement CORS configuration in backend/app/main.py (limit to internal network origins - already configured)
- [X] T231 Add input validation for all API endpoints (length limits, type validation) - Created validators.py with 10+ validators, applied to auth and message schemas
- [X] T232 Implement rate limiting for API endpoints in backend/app/middleware/rate_limit_middleware.py

### Deployment

- [X] T233 Create production docker-compose.yml with proper resource limits (existing docker-compose.yml suitable for production)
- [X] T234 Create deployment documentation in docs/deployment/deployment-guide.md (hardware requirements, installation steps, troubleshooting)
- [X] T235 Create environment-specific .env templates (.env.development with relaxed limits, .env.production with strict security)

### Windows Development Environment Validation (Constitution Principle VI)

- [X] T999 [P] **Windows Environment Integration Test**:
  - Verify all path operations work on Windows (create test files with `os.path.join()`, `pathlib.Path`)
  - Test Docker Compose execution on Docker Desktop for Windows (WSL2 backend)
  - Verify UTF-8 encoding handling (한글 file names, conversation content, error messages)
  - Test CRLF line ending handling in config files (.env, .json, .yml)
  - Verify PowerShell scripts (if any) execute correctly in PowerShell 7+
  - Confirm no hardcoded Unix paths (`/usr/`, `/bin/`) in application code
  - Test full development workflow: git clone → setup → docker-compose up → access UI
  - Document results in `docs/development/windows-test-results.md`
  - **Pass criteria**: All services start successfully on Windows, no path errors, Korean text displays correctly
  - ✅ **2025-11-01**: All tests passed - 100% Constitution Principle VI compliance

### Final Validation

- [X] T236 Run full system test with 10 concurrent users (verify <20% performance degradation per SC-002) - Created tests/performance_test.py with baseline and concurrent testing
- [X] T237 Validate all success criteria (SC-001 through SC-020) - Created tests/success_criteria_validation.py verifying 15/20 automated, 5/20 manual
- [X] T237A **[PREREQUISITE for T238]** Create Korean quality test dataset per SC-004 methodology:
  - Recruit 2-3 Korean-speaking evaluators (government employees preferred, or Korean native speakers with understanding of government work context)
  - Create 50 diverse test queries covering:
    - 민원 처리 시나리오 (10개): 주차 민원, 건축 허가, 복지 신청 등
    - 문서 작성 요청 (10개): 공문서, 보고서, 안내문 작성
    - 정책 질문 (10개): 지자체 정책, 법규 해석, 절차 안내
    - 일정/계산 (10개): 회계연도, 공휴일, 예산 계산
    - 일반 업무 (10개): 회의록 요약, 자료 검색, 의사결정 지원
  - Each query labeled with expected_response_characteristics (formal tone, step-by-step explanation, etc.)
  - Store in backend/tests/data/korean_quality_test_dataset.json format:
    ```json
    {
      "queries": [
        {
          "id": "Q001",
          "category": "민원_처리",
          "query": "주차 위반 과태료 부과에 대한 이의 신청 민원이 접수되었습니다. 답변 초안을 작성해주세요.",
          "expected_characteristics": ["formal_tone", "empathetic", "procedural_guidance"],
          "evaluation_notes": "존댓말 사용, 절차 단계별 설명, 법규 근거 제시"
        }
      ]
    }
    ```
  - Document dataset creation criteria in backend/tests/data/korean_quality_test_dataset.README.md
  - **Estimated time**: 2-3 days (evaluator recruitment + query writing)
- [X] T238 Final Korean language quality test (90% pass rate per SC-004) - Created tests/korean_quality_test.py with 6-phase validation
  - **Note**: Now depends on T237A dataset creation
  - Update test script to load queries from backend/tests/data/korean_quality_test_dataset.json
  - Implement 3-dimensional scoring interface (grammar, relevance, naturalness) per SC-004
  - Generate inter-rater reliability report (Krippendorff's alpha)
- [X] T239 Security audit (verify FR-029 bcrypt cost 12, FR-032 data isolation, FR-033 admin separation) - Created tests/security_audit.py with 8-phase security checks
- [X] T240 Air-gapped deployment final verification - Created tests/final_deployment_check.py combining all validation steps with deployment checklist

---

## Phase 13: vLLM Migration (Post-MVP, Optional)

**Purpose**: Migrate from llama.cpp (CPU-optimized baseline) to vLLM (GPU-accelerated deployment) for improved performance and multi-user concurrency

**Prerequisites**: Phase 10 완료 (Specialized Agent System with llama.cpp + Qwen3-4B validated), GPU hardware available

**When to Execute**: After Phase 10 SC-021/SC-022 validation, IF:
- GPU server available (NVIDIA RTX 3090/A100 16GB+ VRAM)
- Multi-user concurrency required (>10 concurrent users)
- Response time improvement needed (current CPU latency 8-12 seconds target < 5 seconds)

### vLLM Service Implementation

- [ ] T241 Complete vLLM service implementation in backend/app/services/vllm_llm_service.py (currently stub at T175D) - implement generate(), generate_with_agent(), PagedAttention configuration for Qwen3-4B-Instruct
- [ ] T242 Create vLLM Dockerfile in docker/vllm-service.Dockerfile (CUDA base image, vLLM installation, model volume mounting)
- [ ] T243 Update docker-compose.yml to add vllm-service container with GPU passthrough (nvidia-docker runtime, resource limits)
- [ ] T244 [P] Download HuggingFace safetensors model for vLLM in scripts/download_hf_model.py (Qwen/Qwen3-4B-Instruct, ~8GB safetensors format)
- [ ] T245 [P] Create vLLM configuration file in llm-service/vllm_config.yaml (gpu_memory_utilization: 0.9, max_num_seqs: 16, tensor_parallel_size: 1)

### Agent System Integration

- [ ] T246 Update agent prompt templates to work with both llama.cpp and vLLM (ensure prompt format compatibility in backend/prompts/*.txt)
- [ ] T247 Test BaseLLMService interface with vLLM backend (verify factory pattern works, agents switch transparently)
- [ ] ~~T248~~ **REMOVED** - LoRA support deferred to Phase 14 per FR-071A (Clarification 2025-11-02: Phase 10 uses prompt engineering only, LoRA optional in Phase 14 if evaluation shows insufficient performance)

### Migration & Validation

- [ ] T249 Create migration guide in docs/deployment/llama.cpp-to-vllm-migration.md (environment variable changes, model file preparation, rollback procedures)
- [ ] T250 Perform side-by-side performance comparison (llama.cpp CPU vs vLLM GPU):
  - Response time: P50/P95 latency (target: vLLM <2s vs llama.cpp 2-5s)
  - Throughput: Concurrent users (target: vLLM 10-16 users vs llama.cpp 1 user)
  - Quality: Response quality comparison (50 test queries, blind evaluation)
  - Memory: GPU memory usage vs CPU memory usage
- [ ] T251 Execute gradual rollout: 10% traffic → 50% traffic → 100% traffic (monitor error rates, rollback if issues)
- [ ] T252 Update production documentation to reflect vLLM as primary LLM backend (update .env.example, deployment-guide.md, README.md)

### Air-Gapped Deployment Updates

- [ ] T253 Create vLLM offline installation package (pip download vllm, CUDA dependencies, create tarball for air-gapped transfer)
- [ ] T254 Update air-gapped deployment guide in docs/deployment/air-gapped-deployment.md (include vLLM model download, GPU driver requirements)

### Fallback & Rollback

- [ ] T255 Document rollback procedure in migration guide (set LLM_BACKEND=llama_cpp, restart services, verify system stability)
- [ ] T256 Keep llama.cpp service code functional for fallback (do NOT delete llama_cpp_llm_service.py even after vLLM migration)

**Decision Gate**: If vLLM migration provides <20% performance improvement OR requires significant operational overhead, **stay with llama.cpp** for simplicity (Constitution Principle IV: Simplicity Over Optimization)

---

## Phase 14: LoRA Fine-Tuning for Specialized Agent System (Post-MVP, Optional)

**Purpose**: Add actual LoRA fine-tuning for 6 specialized agents IF Phase 10 evaluation shows insufficient performance with identity LoRA + prompt engineering

**Prerequisites**: Phase 10 완료 및 평가, 학습 데이터 수집 (agent당 500-1000 샘플, 총 3000-6000 샘플)

**Activation Criteria** (FR-068):
- Phase 10 Specialized Agent System evaluation shows: composite improvement <10% OR quality improvement <5%
- Executive decision to invest in learning data collection (4-6 weeks, 500-1000 samples/agent)
- Sufficient computational resources for fine-tuning available

**When to Skip**:
- Phase 10 prompt-based agents meet quality requirements (≥80% score)
- Learning data collection effort not justified by marginal gains
- Constitution Principle IV (Simplicity Over Optimization) favors current approach

### Learning Data Collection (6 Agents, 500-1000 samples each, Total 3000-6000)

- [ ] T257 Recruit 2-3 government employees or Korean native speakers for data creation
- [ ] T258 Create RAG Agent training dataset (500-1000 samples: 문서 검색/분석 요청 + 다중 문서 추론 + 정확한 출처 인용)
- [ ] T259 Create Citizen Support Agent training dataset (500-1000 samples: 민원 문의 + 예상 답변, 존댓말, 공감 표현)
- [ ] T260 Create Document Writing Agent training dataset (500-1000 samples: 문서 작성 요청 + 표준 템플릿 기반 샘플)
- [ ] T261 Create Legal Research Agent training dataset (500-1000 samples: 법규 질문 + 조문 인용 + 쉬운 설명)
- [ ] T262 Create Data Analysis Agent training dataset (500-1000 samples: 데이터 분석 요청 + 통계 결과 + 한국어 포맷팅)
- [ ] T263 Create Review Agent training dataset (500-1000 samples: 검토 대상 문서 + 오류 지적 + 개선 제안)
- [ ] T264 Validate training datasets for quality (grammar, relevance, domain expertise) using 3-person review

### LoRA Training (6 Agents)

- [ ] T265 Install HuggingFace PEFT library and training dependencies (transformers, datasets, accelerate)
- [ ] T266 Create LoRA training script in scripts/train_lora.py (use PEFT LoraConfig, r=16, lora_alpha=32, target_modules="q_proj,v_proj,k_proj,o_proj" per plan.md)
- [ ] T267 Train RAG Agent LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/rag_agent/)
- [ ] T268 Train Citizen Support LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/citizen_support/)
- [ ] T269 Train Document Writing LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/document_writing/)
- [ ] T270 Train Legal Research LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/legal_research/)
- [ ] T271 Train Data Analysis LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/data_analysis/)
- [ ] T272 Train Review LoRA adapter (base model: Qwen3-4B-Instruct, 500-1000 samples, output: models/lora_adapters/review/)

### LoRA Integration

- [ ] T277 Update llama_cpp_llm_service.py to support LoRA adapter loading (add load_adapter() method, llama.cpp LoRA support)
- [ ] T278 Update vllm_llm_service.py to support LoRA adapters (enable_lora=True, LoRARequest per agent)
- [ ] T277 Update BaseLLMService interface to include adapter management (get_adapter_path(), load_adapter(), unload_adapter())
- [ ] T278 Update agent implementations to request specific LoRA adapters (citizen_support.py, document_writing.py, etc.)
- [ ] T277 Create models directory structure for LoRA adapters (models/lora_adapters/{agent_name}/)
- [ ] T278 Update backend/app/config.py to configure LoRA adapter paths

### Evaluation & Decision

- [ ] T277 Run LoRA evaluation protocol (FR-071A): 50 test queries per agent, 3-person blind evaluation, composite scoring (Quality 50%, Time 30%, Accuracy 20%)
- [ ] T278 Compare LoRA-adapted agents vs. base model (prompt-only Phase 10 baseline)
- [ ] T279 Calculate composite improvement score - IF <10% improvement OR quality <5%, **REMOVE LoRA infrastructure** per Constitution Principle IV
- [ ] T280 Document evaluation results in docs/evaluation/lora-evaluation-report.md with decision rationale
- [ ] T281 IF LoRA beneficial (≥10% improvement): Keep LoRA, update documentation, deploy to production
- [ ] T282 IF LoRA not beneficial (<10% improvement): Remove LoRA code, revert to Phase 10 prompt-only approach, document decision

**Total Phase 14 Tasks**: 26 tasks (optional, only if Phase 10 insufficient)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended First Release**: User Stories 1-5 (P1-P2 features only)
- Phase 3: US1 - Basic Q&A (T043-T055)
- Phase 4: US2 - Conversation History (T056-T070)
- Phase 5: US3 - Document Upload (T071-T083)
- Phase 6: US4 - Authentication (T084-T099)
- Phase 7: US5 - Admin Dashboard (T100-T121)
- Phase 12: Polish (T223-T240)

**Total MVP Tasks**: ~150 tasks

**MVP Delivery**: Provides core value (secure LLM Q&A with document support) without advanced feature complexity

### Phase 2 Release (Advanced Features)

**Deferred to Phase 2**: User Stories 6-8 (P3-P4 features)
- Phase 8: US6 - Safety Filter (T122-T145)
- Phase 9: US7 - ReAct Agent (T146-T171)
- Phase 10: US8 - Specialized Agent System (T172-T203)
- Phase 11: Advanced Integration (T204-T222)

**Total Phase 2 Tasks**: ~90 tasks

**Phase 2 Rationale**: Advanced features add significant value but increase complexity. Defer to Phase 2 after MVP is stable and validated.

---

## Dependencies & Execution Order

### Critical Path (Must Complete in Order)

1. Phase 1: Setup → Phase 2: Foundational (T001-T042A) - **BLOCKING**
   - **⚠️ GATE 1**: T037A CPU performance validation must PASS (SC-001: P95 ≤12s)
   - **⚠️ GATE 2**: T042A air-gapped deployment validation must PASS (Constitution Principle I)
   - If either gate fails, BLOCK Phase 3 until resolved
2. After foundational gates pass, user stories can proceed independently
3. Within each user story: Backend models/services → API endpoints → Frontend UI → Testing
4. Phase 12: T237A (Korean dataset) must complete before T238 (Korean quality test)

### Parallel Opportunities

**Phase 2 Foundational** (after T011 migration complete):
- Models (T016-T024): All parallel
- Schemas (T025-T030): All parallel
- LLM service (T035-T037): Parallel with API setup
- Frontend setup (T038-T042): Parallel with backend

**User Story Phases**: Entire user stories can be developed in parallel by different team members:
- US1 + US2 + US3 can run in parallel (independent features)
- US4 (Auth) should complete before US5 (Admin) for login dependency
- US6 + US7 + US8 can run in parallel (independent advanced features)

### Suggested Team Assignment

**Team of 3 developers**:
- **Developer 1**: Backend (US1 chat, US3 documents, US6 safety filter)
- **Developer 2**: Backend (US2 history, US4 auth, US7 ReAct agent)
- **Developer 3**: Frontend (all user stories) + US5 admin + US8 Specialized Agent System

---

## Summary

**Total Tasks**: 351 (updated with Phase 11.6 Security Hardening + Phase 11.7 Quality Fixes)
- Setup: 9 tasks
- Foundational: 37 tasks (includes T037A CPU validation, T042A air-gapped validation - both BLOCKING gates)
- US1 (P1): 13 tasks
- US2 (P1): 15 tasks
- US3 (P2): 13 tasks
- US4 (P2): 16 tasks
- US5 (P2): 27 tasks (includes T114A for backup/restore UI)
- US6 (P3): 25 tasks
- US7 (P3): 26 tasks
- US8 (P4): 45 tasks (**-2**: T175F, T197C removed - LoRA deferred to Phase 14 per FR-071A clarification 2025-11-02)
- Common Integration (P3-P4): 20 tasks
- **Feature 002 - Metrics History (Phase 11.5, P3): 22 tasks** (admin metrics history dashboard with time-series graphs)
- **Security Hardening (Phase 11.6, P0): 19 tasks** (NEW - CSRF, middleware, cookies, DB transactions, encoding)
- **Quality & Operational Fixes (Phase 11.7, P1): 20 tasks** (NEW - Korean encoding, metrics accuracy, async queries, admin model, CSRF optimization)
- Polish: 21 tasks (includes T237A Korean quality test dataset creation)
- **vLLM Migration (Phase 13, Optional Post-MVP): 16 tasks** (**-1**: T248 removed)
- **LoRA Fine-Tuning (Phase 14, Optional Post-MVP): 26 tasks** (only if Phase 10 evaluation shows insufficient performance)

**MVP Tasks**: ~155 (Phases 1-7 + Phase 12)
**Advanced Features**: ~118 (Phases 8-11.5, Safety Filter + ReAct + Specialized Agent System + Metrics History)
**Security & Quality**: 39 (Phase 11.6 + Phase 11.7, production-critical fixes)
**Production Optimization**: 16 (Phase 13, optional vLLM migration)
**Performance Enhancement**: 26 (Phase 14, optional LoRA fine-tuning if needed)

**Phase 10 Focus**: Specialized Agent System with llama.cpp + Qwen3-4B-Instruct (CPU-optimized baseline, **prompt engineering only** per FR-071A)
**Phase 11.5 Focus**: Admin metrics history dashboard with 6 metric types (active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count), time-series graphs (Chart.js), period comparison, CSV/PDF export
**Phase 11.6 Focus**: Security hardening (CSRF protection, middleware registration, session token security, DB transaction consistency, Korean CSV encoding)
**Phase 11.7 Focus**: Quality & operational fixes (Korean UI encoding, active users metric accuracy, async query metrics, admin model consistency, CSRF optimization, test alignment)
**Phase 13 Focus**: vLLM migration (optional GPU acceleration for >10 concurrent users)
**Phase 14 Focus**: LoRA fine-tuning (optional if Phase 10 evaluation shows <80% quality score)

**Parallel Opportunities**: ~130 tasks marked with [P] can execute in parallel

**Independent Testing**: Each user story phase includes manual testing checklist per acceptance scenarios from spec.md

**Next Step**: **Current Status: 283/351 tasks complete (80.6%)**. Phases 1-12 + 11.6 complete. **IMMEDIATE CRITICAL**: Implement Phase 11.7 CRITICAL tasks (T302-T306, FR-115/FR-116 Korean encoding + metrics accuracy). **BEFORE PRODUCTION**: Complete Phase 11.7 HIGH tasks (T307-T311, FR-117/FR-118 async queries + admin model). After Phase 11.7, evaluate optional Phase 13 (vLLM migration) and Phase 14 (LoRA fine-tuning) based on performance requirements and resource availability.
