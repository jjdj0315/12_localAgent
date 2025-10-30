# Tasks: Local LLM Web Application for Local Government

**Input**: Design documents from `/specs/001-local-llm-webapp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded. Focus on implementation and manual testing per acceptance scenarios.

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
- [X] T008A [P] Create offline dependency bundling script in scripts/bundle-offline-deps.sh:
  - Download all Python packages from requirements.txt using `pip download -d ./offline_packages/ -r backend/requirements.txt`
  - Download HuggingFace models (GGUF for Phase 10, safetensors for Phase 13 optional) using huggingface-cli
  - Download toxic-bert, sentence-transformers models for air-gapped installation
  - Create tarball archive for transfer to air-gapped server
  - Document usage in scripts/bundle-offline-deps.README.md (per FR-081, FR-082)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Setup

- [X] T009 Create PostgreSQL schema and Alembic migration framework in backend/alembic/
- [X] T010 [P] Implement database connection and session management in backend/app/core/database.py
- [X] T011 Create initial migration (v0.1.0) defining core tables (users, admins, conversations, messages, documents, sessions, tags, conversation_tags, login_attempts, safety_filter_rules, filter_events, tools, tool_executions, agents, agent_workflows, agent_workflow_steps, audit_logs) in backend/alembic/versions/001_initial_schema.py

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

### LLM Service Setup (HuggingFace Transformers)

- [X] T035 Create HuggingFace Transformers LLM service wrapper in backend/app/services/llm_service.py (load Qwen2.5-1.5B-Instruct with 4-bit quantization using BitsAndBytes)
- [X] T036 Create LLM configuration in backend/app/config.py (model_name, max_model_len: 4096, device_map: auto, quantization_config)
- [X] T037 Implement streaming response handler using Server-Sent Events in backend/app/services/llm_service.py

### Frontend Infrastructure

- [X] T038 Create Next.js app structure with App Router in frontend/src/app/ ((auth), (user), (admin) route groups)
- [X] T039 [P] Implement API client with session management in frontend/src/lib/api.ts
- [X] T040 [P] Create TypeScript types from OpenAPI spec in frontend/src/types/api.ts
- [X] T041 [P] Setup React Query configuration in frontend/src/app/providers.tsx
- [X] T042 [P] Create reusable UI components (Button, Input, Card, Loading) in frontend/src/components/ui/

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

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
- [X] T059 [US2] Implement auto-tag assignment logic triggered on first message in backend/app/services/tag_service.py
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
- [X] T106 [US5] Implement backup management endpoints in backend/app/api/v1/admin.py (trigger backup, view backup history per FR-042)
- [X] T106A [P] [US5] Create backup automation scripts in scripts/:
  - backup-daily.sh: Incremental backup using pg_dump + rsync for documents (scheduled daily at 2 AM via cron)
  - backup-weekly.sh: Full backup using pg_dump --format=custom (scheduled weekly on Sunday)
  - cleanup-old-backups.sh: Delete backups older than 30 days, keep minimum 4 weekly full backups
  - restore-from-backup.sh: Restore database and documents from backup (documented procedure for IT staff)
  - Create crontab configuration example in scripts/crontab.example (per FR-042)

### Frontend Implementation

- [X] T107 [P] [US5] Create admin login page in frontend/src/app/(admin)/login/page.tsx
- [X] T108 [P] [US5] Create admin dashboard layout in frontend/src/app/(admin)/dashboard/layout.tsx
- [X] T109 [P] [US5] Implement UserManagement component in frontend/src/components/admin/UserManagement.tsx
- [X] T110 [P] [US5] Implement StatsDashboard component in frontend/src/components/admin/StatsDashboard.tsx
- [X] T111 [P] [US5] Implement SystemHealth component in frontend/src/components/admin/SystemHealth.tsx
- [X] T112 [P] [US5] Implement StorageMetrics component in frontend/src/components/admin/StorageMetrics.tsx
- [X] T113 [P] [US5] Implement TagManagement component in frontend/src/components/admin/TagManagement.tsx
- [X] T114 [P] [US5] Implement BackupManagement component in frontend/src/components/admin/BackupManagement.tsx
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

## Phase 9: User Story 7 - ReAct Agent with Government Tools (Priority: P3)

**Goal**: AI can use reasoning steps and specialized tools (document search, calculator, date/schedule, data analysis, templates, legal reference) to answer complex queries

**Independent Test**: Submit multi-step query → verify Thought/Action/Observation display → verify tool usage → verify final answer.

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

### Backend - ReAct Agent

- [X] T155 [US7] Implement ReAct loop orchestrator in backend/app/services/react_agent_service.py (Thought → Action → Observation pattern, max 5 iterations per FR-062)
- [X] T156 [US7] Implement tool execution safety in backend/app/services/react_agent_service.py (30-second timeout, identical call detection, sandboxing per FR-063)
- [X] T157 [US7] Implement transparent error handling in backend/app/services/react_agent_service.py (display errors in Observation, agent provides alternatives per FR-065)
- [X] T158 [US7] Implement tool execution audit logging in backend/app/services/react_agent_service.py (timestamp, user_id, tool_name, sanitized params, result per FR-066)
- [X] T159 [US7] Integrate ReAct agent into chat endpoint (detect when to use tools) in backend/app/api/v1/chat.py

### Backend - Admin Interface

- [X] T160 [US7] Implement tool management endpoints in backend/app/api/v1/admin/tools.py (enable/disable tools, view tool list per FR-067)
- [X] T161 [US7] Implement tool usage statistics endpoint GET /api/v1/admin/tools/stats in backend/app/api/v1/admin/tools.py (per-tool usage, avg time, error rate per FR-069)

### Frontend Implementation

- [X] T162 [P] [US7] Implement ReActDisplay component in frontend/src/components/react/ReActDisplay.tsx (show Thought/Action/Observation with emoji prefixes 🤔/⚙️/👁️ per FR-064)
- [X] T163 [P] [US7] Create ToolManagement admin component in frontend/src/components/admin/ToolManagement.tsx
- [X] T164 [P] [US7] Create ToolStatistics admin component in frontend/src/components/admin/ToolStatistics.tsx
- [ ] T165 [US7] Integrate ReAct display into chat interface in frontend/src/app/(user)/chat/page.tsx

### Manual Testing

- [ ] T166 [US7] Test ReAct agent completes 2-3 tool task within 30 seconds (per SC-016)
- [ ] T167 [US7] Test each of 6 tools individually (document search, calculator, date/schedule, data analysis, template, legal reference)
- [ ] T168 [US7] Test tool execution success rate <10% error across 100 invocations (per SC-017)
- [ ] T169 [US7] Test ReAct agent stops at 5 iterations with helpful summary
- [ ] T170 [US7] Test transparent error display when tool fails
- [ ] T171 [US7] Verify tool execution audit log (sanitized parameters, no PII)

---

## Phase 10: User Story 8 - Multi-Agent System for Complex Workflows (Priority: P4)

**Goal**: Complex tasks are automatically routed to specialized agents (Citizen Support, Document Writing, Legal Research, Data Analysis, Review) that can work sequentially or in parallel

**Independent Test**: Submit complex multi-step request → verify orchestrator routes to correct agents → verify sequential workflow → verify attribution.

### Backend - Agent Models

- [X] T172 [US8] Create Agent model (SQLAlchemy) in backend/app/models/agent.py
- [X] T173 [US8] Create AgentWorkflow model (SQLAlchemy) in backend/app/models/agent_workflow.py
- [X] T174 [US8] Create AgentWorkflowStep model (SQLAlchemy) in backend/app/models/agent_workflow_step.py
- [X] T175 [US8] Create agent schemas in backend/app/schemas/agent.py

### Backend - LLM Service Infrastructure (FR-071A)

- [X] T175A [US8] Create abstract base class in backend/app/services/base_llm_service.py (define generate(), generate_with_agent(), get_agent_prompt() methods for environment-agnostic interface)
- [X] T175B [P] [US8] Implement llama.cpp service in backend/app/services/llama_cpp_llm_service.py (GGUF model loading, CPU optimization, optional LoRA adapter loading for infrastructure testing)
- [X] T175C [US8] Create LLM service factory in backend/app/services/llm_service_factory.py (environment variable LLM_BACKEND selector: llama_cpp or vLLM)
- [X] T175D [US8] Create vLLM service stub in backend/app/services/vllm_llm_service.py (production implementation placeholder, to be completed later)
- [X] T175E [P] [US8] Create GGUF model download script in scripts/download_gguf_model.py (download Qwen2.5-1.5B-Instruct GGUF Q4_K_M from HuggingFace for local testing)
- [X] T175F [P] [US8] Create dummy LoRA generator script in scripts/create_dummy_lora.py:
  - Create 5 dummy GGUF LoRA files for infrastructure testing (not actual fine-tuning)
  - **Important**: Dummy files are for path detection and loading mechanism testing only
  - If llama.cpp requires valid LoRA file format for loading, generate minimal valid empty LoRA files using llama.cpp tools or compatible library
  - If llama.cpp accepts any file, simple placeholder files (b'DUMMY_LORA') are sufficient
  - Test script should verify: file exists, loading mechanism works (even if adapter has no effect)
  - **Removal**: Per plan.md LoRA Transition Decision Tree, if Phase 10 completes successfully with dummy LoRA, immediately remove dummy LoRA loading code (T175F files) before Phase 11 unless proceeding with actual fine-tuning
- [X] T175G [US8] Update requirements.txt to include llama-cpp-python (for Phase 10), add vllm as optional dependency (for later)
- [X] T175H [US8] Create models directory structure (models/ for GGUF base model, models/lora/ for dummy adapters) and configure paths in backend/app/config.py

### Backend - Agent Implementations

- [X] T176 [P] [US8] Create Citizen Support Agent prompt template in backend/prompts/citizen_support.txt and implement in backend/app/services/agents/citizen_support.py (use BaseLLMService via factory pattern, empathetic responses, 존댓말, completeness check per FR-071.1)
- [X] T177 [P] [US8] Create Document Writing Agent prompt template in backend/prompts/document_writing.txt and implement in backend/app/services/agents/document_writing.py (use BaseLLMService, formal language, standard sections per FR-071.2)
- [X] T178 [P] [US8] Create Legal Research Agent prompt template in backend/prompts/legal_research.txt and implement in backend/app/services/agents/legal_research.py (use BaseLLMService, cite articles, plain-language interpretation per FR-071.3)
- [X] T179 [P] [US8] Create Data Analysis Agent prompt template in backend/prompts/data_analysis.txt and implement in backend/app/services/agents/data_analysis.py (use BaseLLMService, Korean formatting, trend identification per FR-071.4)
- [X] T180 [P] [US8] Create Review Agent prompt template in backend/prompts/review.txt and implement in backend/app/services/agents/review.py (use BaseLLMService, error detection, improvement suggestions per FR-071.5)

### Backend - Orchestrator (LangGraph-based)

- [X] T181 [US8] Create few-shot orchestrator prompt file in backend/prompts/orchestrator_few_shot.txt (2-3 example queries per agent per FR-070)
- [X] T182 [P] [US8] Implement LangGraph-based orchestrator in backend/app/services/orchestrator_service.py (AgentState TypedDict, StateGraph setup, classify_intent node per FR-070)
- [X] T183 [US8] Implement single agent execution node in orchestrator_service.py (_execute_single_agent method)
- [X] T184 [US8] Implement sequential workflow node in orchestrator_service.py (_execute_sequential method, agent chaining with context sharing per FR-072, FR-077)
- [X] T185 [US8] Implement parallel agent execution node in orchestrator_service.py (_execute_parallel method, asyncio.gather for max 3 agents per FR-078)
- [X] T186 [US8] Implement workflow routing logic in orchestrator_service.py (_route_workflow_type conditional edges)
- [X] T187 [US8] Implement error handling node in orchestrator_service.py (_handle_error method, upstream failure detection per FR-073)
- [X] T188 [US8] Implement workflow complexity limits in orchestrator_service.py (max 5 agents, max 3 parallel, 5-minute timeout with asyncio.wait_for per FR-079)
- [X] T189 [US8] Implement workflow execution logging in orchestrator_service.py (execution_log in state, timestamp/agent/status tracking per FR-075)
- [X] T189A [US8] Implement keyword-based orchestrator alternative (optional admin-configurable mode, fallback if LangGraph fails per FR-076)
- [X] T190 [US8] Integrate multi-agent system into chat endpoint in backend/app/api/v1/chat.py (call orchestrator.route_and_execute)

### Backend - Admin Interface

- [X] T191 [US8] Implement agent management endpoints in backend/app/api/v1/admin/agents.py:
  - POST /api/v1/admin/agents/{agent_name}/toggle (enable/disable individual agents per FR-076)
  - PUT /api/v1/admin/agents/routing-mode (body: {mode: 'llm' | 'keyword'}, configure orchestrator routing mode, takes effect immediately without restart per FR-076)
  - GET /api/v1/admin/agents/routing-mode (retrieve current routing mode configuration)
  - PUT /api/v1/admin/agents/{agent_name}/keywords (body: {keywords: string[]}, edit keyword patterns for agent routing rules per FR-076)
- [X] T192 [US8] Implement agent performance metrics endpoint GET /api/v1/admin/agents/stats in backend/app/api/v1/admin/agents.py (task counts, response time, error rate per FR-076)

### Frontend Implementation

- [X] T193 [P] [US8] Implement MultiAgentDisplay component in frontend/src/components/agents/MultiAgentDisplay.tsx (agent attribution with labels and icons per FR-074)
- [X] T194 [P] [US8] Implement WorkflowProgress component in frontend/src/components/agents/WorkflowProgress.tsx (show current agent and stage per FR-072)
- [X] T195 [P] [US8] Create AgentManagement admin component in frontend/src/components/admin/AgentManagement.tsx
- [X] T196 [P] [US8] Create AgentStatistics admin component in frontend/src/components/admin/AgentStatistics.tsx
- [ ] T197 [US8] Integrate multi-agent display into chat interface in frontend/src/app/(user)/chat/page.tsx

### Manual Testing

- [ ] T197A [US8] Test LLM service factory (verify llama.cpp loads correctly with LLM_BACKEND=llama_cpp environment variable)
- [ ] T197B [US8] Test GGUF model loading (Qwen2.5-1.5B Q4_K_M loads successfully on CPU)
- [ ] T197C [US8] Test dummy LoRA adapter detection (optional, verify dummy files detected without errors if present)
- [ ] T198 [US8] Test orchestrator routing accuracy (85%+ correct per SC-021) on test dataset of 50 queries
- [ ] T199 [US8] Test sequential 3-agent workflow completes within 90 seconds (per SC-022)
- [ ] T200 [US8] Test parallel agent execution for independent sub-tasks (max 3 agents)
- [ ] T201 [US8] Test agent failure handling (upstream failure stops downstream)
- [ ] T202 [US8] Test workflow complexity limits (5 agents, 3 parallel, 5-minute timeout)
- [ ] T203 [US8] Verify agent attribution clearly labels each contribution
- [ ] T204 [US8] Test CPU performance (verify responses complete within acceptable time on 8-16 core CPU)

---

## Phase 11: Common Air-Gapped & Advanced Features Integration (Priority: P3-P4)

**Goal**: Ensure all advanced features work in air-gapped environment, implement resource limits, graceful degradation, and documentation

**Prerequisites**: Phase 8 (US6 - Safety Filter), Phase 9 (US7 - ReAct Agent), Phase 10 (US8 - Multi-Agent) MUST be completed before Phase 11 air-gapped testing (T220 requires all advanced features operational)

**Independent Test**: Disable internet → verify all features work. Test resource limits → verify queueing/503 responses.

### Backend - Resource Limits & Graceful Degradation

- [ ] T204 Implement resource limit middleware in backend/app/middleware/resource_limit_middleware.py (max 10 ReAct sessions, max 5 multi-agent workflows, queue or 503 per FR-086)
- [ ] T205 Implement graceful degradation in backend/app/services/graceful_degradation_service.py (safety filter fallback to rule-based, ReAct fallback to standard LLM, orchestrator fallback to general LLM per FR-087)
- [ ] T206 Create centralized AuditLog model (SQLAlchemy) in backend/app/models/audit_log.py
- [ ] T207 Implement centralized audit logging service in backend/app/services/audit_log_service.py (filter/tool/agent actions per FR-083)
- [ ] T208 Implement audit log query endpoint GET /api/v1/admin/audit-logs in backend/app/api/v1/admin/audit_logs.py (filter by date, user, action type)

### Backend - Admin Customization

- [ ] T209 Implement template upload endpoint POST /api/v1/admin/templates in backend/app/api/v1/admin/templates.py (allow .jinja2 file upload per FR-084)
- [ ] T210 Implement agent routing keyword editor endpoint in backend/app/api/v1/admin/agents.py (edit keyword patterns per FR-084)
- [ ] T211 Implement resource limit configuration endpoint in backend/app/api/v1/admin/config.py (adjust concurrency limits per FR-084)

### Frontend - Advanced Features Dashboard

- [ ] T212 [P] Create AdvancedFeaturesDashboard layout in frontend/src/components/admin/AdvancedFeaturesDashboard.tsx (tabs for Safety Filter, ReAct Tools, Multi-Agent per FR-085)
- [ ] T213 [P] Create AuditLogViewer component in frontend/src/components/admin/AuditLogViewer.tsx
- [ ] T214 [P] Create TemplateManager component in frontend/src/components/admin/TemplateManager.tsx
- [ ] T215 Integrate advanced features tabs into admin dashboard in frontend/src/app/(admin)/dashboard/layout.tsx

### Documentation

- [ ] T216 Create backup and restore procedures document in docs/admin/backup-restore-guide.md (pg_dump commands, rsync procedures per FR-042, FR-088)
- [ ] T217 Create advanced features administration manual in docs/admin/advanced-features-manual.md (safety filter config, tool management, agent setup per FR-088)
- [ ] T218 Create customization guide in docs/admin/customization-guide.md:
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
- [ ] T219 Create Korean user manual in docs/user/user-guide-ko.md (basic usage, document upload, safety features)

### Air-Gapped Deployment Testing

- [ ] T220 Test complete air-gapped deployment (disable all network, verify all features work per SC-020)
- [ ] T221 Verify all AI models and tool data files load from local disk:
  - AI models: Qwen2.5-1.5B (or GGUF equivalent), toxic-bert, sentence-transformers (per FR-081)
  - ReAct tool data: korean_holidays.json in backend/data/, Jinja2 templates in backend/templates/ (per FR-068)
  - Multi-agent prompts: agent prompt templates in backend/prompts/*.txt (per FR-080)
  - Verify file paths configured correctly in backend/app/config.py
  - Confirm no "file not found" errors during service startup
- [ ] T222 Verify model loading time <60 seconds and feature execution within normal ranges (per SC-020)

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Final touches, optimization, and production readiness

### Error Handling & UX

- [ ] T223 [P] Implement standardized error message formatter in frontend/src/lib/errorMessages.ts (Korean, [problem] + [action] pattern per FR-037)
- [ ] T224 [P] Implement zero-state UI components in frontend/src/components/ui/ (empty conversations, documents, search results per FR-039)
- [ ] T225 Implement response length limits in backend/app/services/llm_service.py (4000 chars default, 10000 chars document mode with truncation warnings per FR-017)
- [ ] T226 Implement conversation message limit (1000 messages) in backend/app/api/v1/chat.py with warning message per FR-041

### Performance & Monitoring

- [ ] T227 Add health check endpoints in backend/app/api/v1/health.py (database, LLM service, storage)
- [ ] T228 Implement structured logging with correlation IDs in backend/app/core/logging.py
- [ ] T229 Add performance monitoring middleware in backend/app/middleware/performance_middleware.py (track response times, identify slow endpoints)

### Security Hardening

- [ ] T230 Implement CORS configuration in backend/app/main.py (limit to internal network origins)
- [ ] T231 Add input validation for all API endpoints (length limits, type validation)
- [ ] T232 Implement rate limiting for API endpoints in backend/app/middleware/rate_limit_middleware.py

### Deployment

- [ ] T233 Create production docker-compose.yml with proper resource limits
- [ ] T234 Create deployment documentation in docs/deployment/deployment-guide.md (hardware requirements, installation steps, troubleshooting)
- [ ] T235 Create environment-specific .env templates (.env.development, .env.production)

### Final Validation

- [ ] T236 Run full system test with 10 concurrent users (verify <20% performance degradation per SC-002)
- [ ] T237 Validate all success criteria (SC-001 through SC-020)
- [ ] T238 Final Korean language quality test (90% pass rate per SC-004)
- [ ] T239 Security audit (verify FR-029 bcrypt cost 12, FR-032 data isolation, FR-033 admin separation)
- [ ] T240 Air-gapped deployment final verification

---

## Phase 13: vLLM Migration (Post-MVP, Optional)

**Purpose**: Migrate from llama.cpp (CPU-optimized test environment) to vLLM (GPU-optimized production environment) for improved performance and multi-user concurrency

**Prerequisites**: Phase 10 완료 (Multi-Agent with llama.cpp validated), GPU hardware available

**When to Execute**: After Phase 10 SC-021/SC-022 validation, IF:
- GPU server available (NVIDIA RTX 3090/A100 16GB+ VRAM)
- Multi-user concurrency required (>10 concurrent users)
- Response time improvement needed (current CPU latency >5 seconds)

### vLLM Service Implementation

- [ ] T241 Complete vLLM service implementation in backend/app/services/vllm_llm_service.py (currently stub at T175D) - implement generate(), generate_with_agent(), PagedAttention configuration
- [ ] T242 Create vLLM Dockerfile in docker/vllm-service.Dockerfile (CUDA base image, vLLM installation, model volume mounting)
- [ ] T243 Update docker-compose.yml to add vllm-service container with GPU passthrough (nvidia-docker runtime, resource limits)
- [ ] T244 [P] Download HuggingFace safetensors model for vLLM in scripts/download_hf_model.py (Qwen/Qwen2.5-1.5B-Instruct or meta-llama/Meta-Llama-3-8B)
- [ ] T245 [P] Create vLLM configuration file in llm-service/vllm_config.yaml (gpu_memory_utilization: 0.9, max_num_seqs: 16, tensor_parallel_size: 1)

### Agent System Integration

- [ ] T246 Update agent prompt templates to work with both llama.cpp and vLLM (ensure prompt format compatibility in backend/prompts/*.txt)
- [ ] T247 Test BaseLLMService interface with vLLM backend (verify factory pattern works, agents switch transparently)
- [ ] T248 (Optional) Implement vLLM LoRA support in vllm_llm_service.py IF Phase 10 LoRA decision tree determined LoRA is beneficial (enable_lora=True, LoRARequest per agent)

### Migration & Validation

- [ ] T249 Create migration guide in docs/deployment/llama-cpp-to-vllm-migration.md (environment variable changes, model file preparation, rollback procedures)
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
- Phase 10: US8 - Multi-Agent (T172-T203)
- Phase 11: Advanced Integration (T204-T222)

**Total Phase 2 Tasks**: ~90 tasks

**Phase 2 Rationale**: Advanced features add significant value but increase complexity. Defer to Phase 2 after MVP is stable and validated.

---

## Dependencies & Execution Order

### Critical Path (Must Complete in Order)

1. Phase 1: Setup → Phase 2: Foundational (T001-T042) - **BLOCKING**
2. After foundational complete, user stories can proceed independently
3. Within each user story: Backend models/services → API endpoints → Frontend UI → Testing

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
- **Developer 3**: Frontend (all user stories) + US5 admin + US8 multi-agent

---

## Summary

**Total Tasks**: 267 (updated with dual LLM strategy: llama.cpp + vLLM + migration path)
- Setup: 8 tasks
- Foundational: 34 tasks
- US1 (P1): 13 tasks
- US2 (P1): 15 tasks
- US3 (P2): 13 tasks
- US4 (P2): 16 tasks
- US5 (P2): 22 tasks
- US6 (P3): 24 tasks
- US7 (P3): 26 tasks
- US8 (P4): 43 tasks (includes 8 LLM infrastructure tasks + 4 testing tasks)
- Common Integration (P3-P4): 19 tasks
- Polish: 18 tasks
- **vLLM Migration (Optional, Post-MVP): 16 tasks**

**MVP Tasks**: ~150 (Phases 1-7 + Phase 12)
**Advanced Features**: ~101 (Phases 8-11, includes Multi-Agent system)
**Production Optimization**: 16 (Phase 13, optional vLLM migration)

**Phase 10 Focus**: Multi-Agent system with llama.cpp (local testing)
**Phase 13 Focus**: vLLM migration (optional production optimization, GPU-accelerated)

**Parallel Opportunities**: ~120 tasks marked with [P] can execute in parallel

**Independent Testing**: Each user story phase includes manual testing checklist per acceptance scenarios from spec.md

**Next Step**: Begin with Phase 1 Setup (T001-T008), then Phase 2 Foundational (T009-T042). After foundational checkpoint, proceed with MVP user stories (US1-US5) in parallel.
