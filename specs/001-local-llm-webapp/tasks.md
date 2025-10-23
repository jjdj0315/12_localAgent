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
- [X] T002 [P] Initialize backend Python project in backend/ with pyproject.toml and requirements.txt (FastAPI, SQLAlchemy, Alembic, vLLM client dependencies)
- [X] T003 [P] Initialize frontend Next.js 14 project in frontend/ with TypeScript, TailwindCSS, React Query
- [X] T004 [P] Create Docker configuration files in docker/ (frontend.Dockerfile, backend.Dockerfile, llm-service.Dockerfile, nginx.conf)
- [X] T005 Create docker-compose.yml for full stack orchestration (postgres, backend, llm-service, frontend, nginx)
- [X] T006 [P] Create .env.example with all required environment variables (database, secrets, LLM config, API URLs)
- [X] T007 [P] Configure ESLint and Prettier for frontend in frontend/.eslintrc.js and frontend/.prettierrc
- [X] T008 [P] Configure Black, Ruff, and mypy for backend in backend/pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Setup

- [X] T009 Create PostgreSQL schema and Alembic migration framework in backend/alembic/
- [X] T010 [P] Implement database connection and session management in backend/app/core/database.py
- [X] T011 Create initial migration (v0.1.0) defining all tables (users, conversations, messages, documents, conversation_documents, sessions) in backend/alembic/versions/001_initial_schema.py

### Authentication & Security

- [X] T012 Implement password hashing utilities (bcrypt) in backend/app/core/security.py
- [X] T013 Implement session management service in backend/app/services/auth_service.py
- [X] T014 Create authentication dependency for route protection in backend/app/api/deps.py (get_current_user, get_current_admin)
- [X] T015 [P] Implement admin role check middleware in backend/app/api/deps.py (require_admin dependency)

### Data Models (Shared Entities)

- [X] T016 [P] Create User model (SQLAlchemy) in backend/app/models/user.py
- [X] T017 [P] Create Session model (SQLAlchemy) in backend/app/models/session.py
- [X] T018 [P] Create Conversation model (SQLAlchemy) in backend/app/models/conversation.py
- [X] T019 [P] Create Message model (SQLAlchemy) in backend/app/models/message.py
- [X] T020 [P] Create Document model (SQLAlchemy) in backend/app/models/document.py
- [X] T021 Create ConversationDocument association model (SQLAlchemy) in backend/app/models/conversation_document.py

### Pydantic Schemas (API Contracts)

- [X] T022 [P] Create auth schemas (LoginRequest, LoginResponse, UserProfile) in backend/app/schemas/auth.py
- [X] T023 [P] Create conversation schemas (ConversationCreate, ConversationUpdate, ConversationResponse) in backend/app/schemas/conversation.py
- [X] T024 [P] Create message schemas (MessageCreate, MessageResponse) in backend/app/schemas/message.py
- [X] T025 [P] Create document schemas (DocumentCreate, DocumentResponse) in backend/app/schemas/document.py
- [X] T026 [P] Create admin schemas (UserCreate, UserResponse, StatsResponse) in backend/app/schemas/admin.py

### API Infrastructure

- [X] T027 Create FastAPI application instance with CORS, middleware, error handlers in backend/app/main.py
- [X] T028 Setup API router structure in backend/app/api/v1/ (auth.py, chat.py, conversations.py, documents.py, admin.py)
- [X] T029 [P] Implement global error handler and logging configuration in backend/app/main.py
- [X] T030 [P] Configure environment variables and settings management in backend/app/config.py

### LLM Service Setup

- [X] T031 Create vLLM server wrapper script in llm-service/server.py
- [X] T032 Create vLLM configuration file in llm-service/config.yaml (model path, max_model_len: 4096, gpu_memory_utilization: 0.9, max_num_seqs: 16)
- [X] T033 Implement LLM client service in backend/app/services/llm_service.py (handle requests to vLLM server, streaming support)

### Frontend Infrastructure

- [X] T034 Create Next.js app structure with App Router in frontend/src/app/ ((auth), (user), (admin) route groups)
- [X] T035 [P] Implement API client with session management in frontend/src/lib/api.ts
- [X] T036 [P] Create TypeScript types from OpenAPI spec in frontend/src/types/api.ts
- [X] T037 [P] Setup React Query configuration in frontend/src/app/providers.tsx
- [X] T038 [P] Create reusable UI components (Button, Input, Card, Loading) in frontend/src/components/ui/

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Text Generation and Q&A (Priority: P1) 🎯 MVP

**Goal**: Enable employees to submit text queries and receive LLM-generated responses with conversational context, all within the web interface.

**Independent Test**:
1. Employee logs in
2. Submits Korean query "행정 업무에서 공문서를 작성할 때 주의사항이 무엇인가요?"
3. Receives relevant response within 10 seconds
4. Submits follow-up question
5. Response maintains context from previous exchange

### Backend Implementation

- [X] T039 [US1] Implement POST /auth/login endpoint in backend/app/api/v1/auth.py (create session, set HTTP-only cookie)
- [X] T040 [US1] Implement POST /auth/logout endpoint in backend/app/api/v1/auth.py (invalidate session)
- [X] T041 [US1] Implement GET /auth/me endpoint in backend/app/api/v1/auth.py (return current user profile)
- [X] T042 [US1] Implement POST /chat/send endpoint in backend/app/api/v1/chat.py (non-streaming LLM response)
- [X] T043 [US1] Implement POST /chat/stream endpoint in backend/app/api/v1/chat.py (Server-Sent Events streaming)
- [X] T044 [US1] Implement conversation context management in backend/app/services/llm_service.py (load previous messages, maintain 4,000 char limit)
- [X] T045 [US1] Add response character limit enforcement (4,000 chars) in backend/app/services/llm_service.py
- [X] T046 [US1] Implement loading indicator state handling in LLM service (track processing status)

### Frontend Implementation

- [X] T047 [P] [US1] Create login page in frontend/src/app/(auth)/login/page.tsx
- [X] T048 [P] [US1] Create authentication context/hook in frontend/src/lib/auth.tsx (useAuth)
- [X] T049 [US1] Create chat interface layout in frontend/src/app/(user)/chat/page.tsx
- [X] T050 [P] [US1] Create message display component in frontend/src/components/chat/MessageList.tsx
- [X] T051 [P] [US1] Create message input component with submit button in frontend/src/components/chat/MessageInput.tsx
- [X] T052 [P] [US1] Create loading indicator component in frontend/src/components/chat/LoadingIndicator.tsx
- [X] T053 [US1] Implement streaming response handling with EventSource in frontend/src/lib/api.ts (streamChat function)
- [X] T054 [US1] Integrate chat components with API client in frontend/src/app/(user)/chat/page.tsx
- [X] T055 [US1] Add error handling and user-friendly error messages in chat interface

### Deployment & Validation

- [X] T056 [US1] Create initial admin user creation script in backend/scripts/create_admin.py
- [X] T057 [US1] Update docker-compose.yml with health checks for all services
- [ ] T058 [US1] Write deployment validation script (test login, chat query) per quickstart.md
- [ ] T059 [US1] Test Korean language query and response quality with Llama-3-8B

**Checkpoint**: ✅ User Story 1 implementation complete - employees can log in, ask questions, and receive streaming LLM responses with context. Testing pending.

---

## Phase 4: User Story 2 - Conversation History Management (Priority: P2)

**Goal**: Enable employees to save, retrieve, search, and organize their conversation history for work continuity and knowledge sharing.

**Independent Test**:
1. Employee completes a conversation with 5+ messages
2. Navigates away and returns later
3. Can view full conversation list with timestamps
4. Can search conversations by keyword
5. Can resume conversation with full context preserved

### Backend Implementation

- [X] T060 [US2] Implement GET /conversations endpoint in backend/app/api/v1/conversations.py (list with pagination, search, tag filtering)
- [X] T061 [US2] Implement POST /conversations endpoint in backend/app/api/v1/conversations.py (create new conversation)
- [X] T062 [US2] Implement GET /conversations/{id} endpoint in backend/app/api/v1/conversations.py (retrieve conversation with messages)
- [X] T063 [US2] Implement PATCH /conversations/{id} endpoint in backend/app/api/v1/conversations.py (update title/tags)
- [X] T064 [US2] Implement DELETE /conversations/{id} endpoint in backend/app/api/v1/conversations.py (delete conversation and messages)
- [X] T065 [US2] Implement conversation search service in backend/app/services/conversation_service.py (keyword search across messages, PostgreSQL full-text search)
- [X] T066 [US2] Add conversation auto-title generation from first user message in backend/app/services/conversation_service.py
- [X] T067 [US2] Implement tag management service in backend/app/services/conversation_service.py (add, remove, filter by tags)

### Frontend Implementation

- [X] T068 [P] [US2] Create conversation list page in frontend/src/app/history/page.tsx
- [X] T069 [P] [US2] Create conversation card component in frontend/src/components/chat/ConversationCard.tsx (title, timestamp, tags)
- [X] T070 [P] [US2] Create search bar component in frontend/src/components/chat/SearchBar.tsx (keyword and tag filters)
- [ ] T071 [P] [US2] Create conversation detail view in frontend/src/app/(user)/conversation/[id]/page.tsx
- [X] T072 [P] [US2] Create tag editor component in frontend/src/components/chat/TagEditor.tsx
- [X] T073 [US2] Implement conversation list with React Query (pagination, infinite scroll) in frontend/src/app/history/page.tsx
- [X] T074 [US2] Implement search functionality with debouncing in frontend/src/app/history/page.tsx
- [X] T075 [US2] Add "Resume Conversation" button that loads context in chat interface (implemented in ConversationCard click handler)
- [X] T076 [US2] Add "Delete Conversation" confirmation modal in frontend/src/components/chat/DeleteConfirmModal.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - employees can chat AND manage their conversation history.

---

## Phase 5: User Story 3 - Document Upload and Analysis (Priority: P3)

**Goal**: Enable employees to upload documents (PDF, TXT, DOCX) and ask the LLM to analyze, summarize, or extract information from them.

**Independent Test**:
1. Employee uploads a 20-page PDF policy document
2. System confirms processing within 30 seconds
3. Employee asks "이 문서를 요약해주세요"
4. LLM provides summary with source references
5. Employee uploads second document and asks comparative question

### Backend Implementation

- [X] T077 [US3] Implement POST /documents endpoint in backend/app/api/v1/documents.py (multipart file upload, validation)
- [X] T078 [US3] Implement GET /documents endpoint in backend/app/api/v1/documents.py (list user's documents with pagination)
- [X] T079 [US3] Implement GET /documents/{id} endpoint in backend/app/api/v1/documents.py (document metadata)
- [X] T080 [US3] Implement DELETE /documents/{id} endpoint in backend/app/api/v1/documents.py (delete document and file)
- [X] T081 [US3] Implement file validation service in backend/app/services/document_service.py (magic number check, size limit 50MB)
- [X] T082 [P] [US3] Implement PDF text extraction in backend/app/services/document_service.py (using pdfplumber)
- [X] T083 [P] [US3] Implement DOCX text extraction in backend/app/services/document_service.py (using python-docx)
- [X] T084 [P] [US3] Implement TXT file processing in backend/app/services/document_service.py
- [X] T085 [US3] Implement document storage service in backend/app/services/document_service.py (save to /uploads/{user_id}/{doc_id}.{ext})
- [X] T086 [US3] Implement document context injection for LLM queries in backend/app/services/llm_service.py (prepend document content to prompt)
- [X] T087 [US3] Add document reference tracking to conversation_document join table in backend/app/services/document_service.py
- [X] T088 [US3] Implement multi-document context handling (combine multiple docs for comparative queries) in backend/app/services/llm_service.py

### Frontend Implementation

- [X] T089 [P] [US3] Create document upload page in frontend/src/app/documents/page.tsx
- [X] T090 [P] [US3] Create file upload component with drag-and-drop in frontend/src/components/documents/FileUploader.tsx
- [X] T091 [P] [US3] Create document list component in frontend/src/components/documents/DocumentList.tsx
- [X] T092 [P] [US3] Create document card component in frontend/src/components/documents/DocumentCard.tsx (filename, type, size, upload date)
- [X] T093 [US3] Implement file upload with progress indicator in frontend/src/components/documents/FileUploader.tsx (integrated)
- [X] T094 [US3] Add file type and size validation on client side in frontend/src/components/documents/FileUploader.tsx (integrated)
- [X] T095 [US3] Create document selection UI in chat interface (select docs for context) in frontend/src/components/chat/DocumentSelector.tsx
- [X] T096 [US3] Integrate document selection with chat API in frontend/src/app/chat/page.tsx (pass document_ids to /chat/send)
- [X] T097 [US3] Add visual indicator for document-attached conversations in conversation list

**Checkpoint**: All three priority features work independently - employees can chat, manage history, AND analyze documents.

---

## Phase 6: User Story 4 - Multi-User Access with Basic Security (Priority: P4)

**Goal**: Enable multiple employees to use the system simultaneously with individual accounts, ensuring conversation privacy and system stability.

**Independent Test**:
1. Administrator creates 3 user accounts
2. All 3 users log in simultaneously
3. Each submits queries at the same time
4. Each user only sees their own conversations
5. Session timeout after 30 minutes of inactivity works correctly

### Backend Implementation

- [ ] T098 [US4] Implement user isolation enforcement in conversation queries (WHERE user_id = current_user.id) in backend/app/api/v1/conversations.py
- [ ] T099 [US4] Implement user isolation enforcement in document queries in backend/app/api/v1/documents.py
- [ ] T100 [US4] Add permission check for conversation access (403 if user doesn't own conversation) in backend/app/api/deps.py
- [ ] T101 [US4] Add permission check for document access (403 if user doesn't own document) in backend/app/api/deps.py
- [ ] T102 [US4] Implement session timeout mechanism (30 minutes) in backend/app/services/auth_service.py (update expires_at on each request)
- [ ] T103 [US4] Implement session cleanup background task in backend/app/services/auth_service.py (delete expired sessions)
- [ ] T104 [US4] Add concurrent user request handling optimization (async/await throughout) in backend/app/api/v1/chat.py
- [ ] T105 [US4] Implement request queuing for LLM service (if concurrent requests exceed max_num_seqs) in backend/app/services/llm_service.py

### Frontend Implementation

- [ ] T106 [P] [US4] Implement session expiration detection in frontend/src/lib/api.ts (handle 401 responses)
- [ ] T107 [P] [US4] Create session timeout warning modal in frontend/src/components/auth/SessionTimeoutModal.tsx (warn at 28 minutes)
- [ ] T108 [US4] Implement automatic session refresh on user activity in frontend/src/lib/auth.tsx
- [ ] T109 [US4] Add session expiration redirect to login page in frontend/src/app/(user)/layout.tsx
- [ ] T110 [US4] Test concurrent user scenarios (10+ simultaneous users) and verify isolation

**Checkpoint**: Multi-user system is functional - multiple employees can use the system simultaneously with proper isolation and security.

---

## Phase 7: User Story 5 - Administrator Dashboard and User Management (Priority: P5)

**Goal**: Enable IT staff to manage user accounts, monitor system usage, and track system health for operational success.

**Independent Test**:
1. Administrator logs into admin panel
2. Creates new user account, receives initial password
3. Views usage statistics (active users, queries processed, avg response time)
4. Monitors system health (CPU, GPU, memory, storage, uptime)
5. Resets user password
6. Deletes inactive user account

### Backend Implementation

- [ ] T111 [US5] Implement GET /admin/users endpoint in backend/app/api/v1/admin.py (list all users with pagination)
- [ ] T112 [US5] Implement POST /admin/users endpoint in backend/app/api/v1/admin.py (create user, generate initial password)
- [ ] T113 [US5] Implement DELETE /admin/users/{id} endpoint in backend/app/api/v1/admin.py (delete user and their data)
- [ ] T114 [US5] Implement POST /admin/users/{id}/reset-password endpoint in backend/app/api/v1/admin.py (generate temporary password)
- [ ] T115 [US5] Implement GET /admin/stats endpoint in backend/app/api/v1/admin.py (usage statistics with period filter)
- [ ] T116 [US5] Implement statistics collection service in backend/app/services/admin_service.py (calculate active users, query counts, avg response time)
- [ ] T117 [US5] Implement system health monitoring service in backend/app/services/admin_service.py (CPU, memory, GPU via nvidia-smi, storage, uptime)
- [ ] T118 [US5] Implement storage usage calculation per user in backend/app/services/admin_service.py (sum document file sizes)
- [ ] T119 [US5] Add response time tracking to message creation in backend/app/models/message.py (store processing_time_ms field)

### Frontend Implementation

- [ ] T120 [P] [US5] Create admin dashboard layout in frontend/src/app/(admin)/layout.tsx
- [ ] T121 [P] [US5] Create admin home page with overview cards in frontend/src/app/(admin)/page.tsx
- [ ] T122 [P] [US5] Create user management page in frontend/src/app/(admin)/users/page.tsx
- [ ] T123 [P] [US5] Create user creation form in frontend/src/components/admin/UserCreateForm.tsx
- [ ] T124 [P] [US5] Create user list table in frontend/src/components/admin/UserTable.tsx
- [ ] T125 [P] [US5] Create password reset modal in frontend/src/components/admin/PasswordResetModal.tsx
- [ ] T126 [P] [US5] Create usage statistics dashboard in frontend/src/app/(admin)/stats/page.tsx
- [ ] T127 [P] [US5] Create system health monitoring panel in frontend/src/app/(admin)/health/page.tsx
- [ ] T128 [P] [US5] Create chart components for statistics visualization in frontend/src/components/admin/StatsCharts.tsx (active users over time, query volume, response times)
- [ ] T129 [US5] Implement real-time health metrics updates (polling every 30 seconds) in frontend/src/app/(admin)/health/page.tsx
- [ ] T130 [US5] Add storage warning indicator (when >80% full) in admin dashboard
- [ ] T131 [US5] Add admin-only route protection in frontend/src/app/(admin)/layout.tsx (check is_admin from user profile)
- [ ] T131a [P] [US5] Implement per-user storage quota calculation in backend/app/services/admin_service.py (sum file sizes by user_id)
- [ ] T131b [P] [US5] Add storage quota warning to file upload endpoint in backend/app/api/v1/documents.py (check before allowing upload)
- [ ] T131c [P] [US5] Create storage usage visualization in frontend/src/app/(admin)/storage/page.tsx (per-user breakdown, total capacity)

**Checkpoint**: Full admin capabilities are functional - IT staff can manage users and monitor system health.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

### Documentation

- [ ] T132 [P] Create README.md in project root with overview, features, tech stack
- [ ] T133 [P] Create air-gapped deployment guide in docs/deployment.md (following quickstart.md procedures)
- [ ] T134 [P] Create user manual in Korean in docs/user-guide-ko.md (login, chat, document upload, conversation management)
- [ ] T135 [P] Create admin manual in docs/admin-guide.md (user management, system monitoring, troubleshooting)

### Error Handling & Logging

- [ ] T136 [P] Enhance error messages to be user-friendly in Korean in backend/app/api/v1/ (all endpoints)
- [ ] T137 [P] Implement structured logging with JSON output in backend/app/core/logging.py (use structlog)
- [ ] T138 [P] Add request ID tracking across logs in backend/app/main.py (middleware)
- [ ] T139 [P] Configure log rotation in docker-compose.yml (logrotate configuration)
- [ ] T139a [P] Implement network interruption handling with automatic retry in frontend/src/lib/api.ts (React Query retry policy)

### Performance Optimization

- [ ] T140 Add database indexes per data-model.md recommendations (conversation user_updated, message conversation_created, document user_uploaded)
- [ ] T141 [P] Implement connection pooling for PostgreSQL in backend/app/core/database.py (pool_size: 20, max_overflow: 40)
- [ ] T142 [P] Add Redis caching for session validation (optional, evaluate if DB bottleneck) in backend/app/services/auth_service.py
- [ ] T143 Optimize LLM response streaming (reduce first-token latency) by tuning vLLM config in llm-service/config.yaml
- [ ] T144 [P] Implement frontend code splitting and lazy loading for admin panel in frontend/next.config.js

### Security Hardening

- [ ] T145 Add HTTPS support with self-signed certificate (for internal network) in docker/nginx.conf
- [ ] T146 [P] Implement CSRF protection for state-changing operations in backend/app/main.py (CSRF middleware)
- [ ] T147 [P] Add rate limiting for login endpoint (5 attempts per 15 minutes) in backend/app/api/v1/auth.py
- [ ] T148 [P] Implement audit logging for admin actions in backend/app/models/audit_log.py (track user creation, deletion, password resets)
- [ ] T149 Add SQL injection prevention verification (review all SQLAlchemy queries) across backend/app/

### Production Readiness

- [ ] T150 Create database backup script in scripts/backup-database.sh (pg_dump with compression)
- [ ] T151 Create database restore script in scripts/restore-database.sh
- [ ] T152 [P] Create health check endpoint /health in backend/app/api/v1/health.py (DB connection, LLM service status)
- [ ] T153 [P] Setup monitoring dashboard export script in scripts/export-metrics.py (generate CSV of usage stats)
- [ ] T154 Test full air-gapped deployment procedure per quickstart.md (image export, transfer, import, deploy)
- [ ] T155 Perform load testing with 10 concurrent users in scripts/load-test.py (verify SC-002: <20% degradation)
- [ ] T156 Verify Korean language response quality across 50+ test queries in scripts/test-korean-quality.py
- [ ] T157 Test document processing with various Korean PDF/DOCX files (government documents)
- [ ] T158 Create emergency recovery procedures document in docs/disaster-recovery.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run parallel to US1 if staffed)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion (can run parallel to US1/US2 if staffed)
- **User Story 4 (Phase 6)**: Depends on Foundational + User Story 1 completion (needs chat functionality to test isolation)
- **User Story 5 (Phase 7)**: Depends on Foundational completion (can run parallel to US1-4, but ideally after US1 for easier testing)
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← CRITICAL BLOCKER
    ↓
    ├→ Phase 3 (US1 - Basic Chat) ← MVP START HERE
    ├→ Phase 4 (US2 - History) [independent]
    ├→ Phase 5 (US3 - Documents) [independent]
    ├→ Phase 7 (US5 - Administrator) [independent]
    └→ Phase 6 (US4 - Multi-User) [requires US1 complete]
         ↓
Phase 8 (Polish)
```

### Within Each User Story

- Backend endpoints before frontend pages
- Models and schemas in Foundational phase (already created)
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T002, T003, T004, T006, T007, T008 can all run in parallel (different files)

**Foundational Phase (Phase 2)**:
- T010 and T011 can run in parallel (database setup)
- T016-T021 can all run in parallel (all models, different files)
- T022-T026 can all run in parallel (all schemas, different files)
- T029, T030, T035-T038 can run in parallel (independent utilities)

**User Story 1 (Phase 3)**:
- T047, T048, T050, T051, T052 can run in parallel (frontend components, different files)

**User Story 2 (Phase 4)**:
- T068-T072 can run in parallel (frontend components, different files)

**User Story 3 (Phase 5)**:
- T082, T083, T084 can run in parallel (document extraction, different files)
- T089-T092 can run in parallel (frontend components, different files)

**User Story 5 (Phase 7)**:
- T120-T128 can all run in parallel (admin frontend components, different files)

**Polish Phase (Phase 8)**:
- T132-T135 can run in parallel (documentation, different files)
- T136-T139 can run in parallel (error handling and logging, different concerns)
- T141, T142, T144-T149 can run in parallel (independent improvements)

**After Foundational Phase Completes**:
- User Stories 1, 2, 3, 5 can ALL be developed in parallel by different team members
- User Story 4 should start after User Story 1 completes

---

## Parallel Example: User Story 1 (Basic Chat)

```bash
# Frontend components can all be built in parallel:
Task: "Create login page in frontend/src/app/(auth)/login/page.tsx"
Task: "Create authentication context in frontend/src/lib/auth.tsx"
Task: "Create message display component in frontend/src/components/chat/MessageList.tsx"
Task: "Create message input component in frontend/src/components/chat/MessageInput.tsx"
Task: "Create loading indicator in frontend/src/components/chat/LoadingIndicator.tsx"

# These are all independent React components in different files
```

---

## Parallel Example: Foundational Phase

```bash
# All SQLAlchemy models can be created in parallel:
Task: "Create User model in backend/app/models/user.py"
Task: "Create Session model in backend/app/models/session.py"
Task: "Create Conversation model in backend/app/models/conversation.py"
Task: "Create Message model in backend/app/models/message.py"
Task: "Create Document model in backend/app/models/document.py"

# All Pydantic schemas can be created in parallel:
Task: "Create auth schemas in backend/app/schemas/auth.py"
Task: "Create conversation schemas in backend/app/schemas/conversation.py"
Task: "Create message schemas in backend/app/schemas/message.py"
Task: "Create document schemas in backend/app/schemas/document.py"
Task: "Create admin schemas in backend/app/schemas/admin.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only - Fastest Path to Value)

1. **Week 1**: Complete Phase 1 (Setup) + Start Phase 2 (Foundational)
2. **Week 2-3**: Complete Phase 2 (Foundational) - CRITICAL
3. **Week 4**: Complete Phase 3 (User Story 1 - Basic Chat)
4. **STOP and VALIDATE**: Test User Story 1 independently per acceptance scenarios
5. **Deploy internally**: Get employee feedback on basic chat functionality

**Result**: Working air-gapped LLM chat application for government employees

### Incremental Delivery (Add Features Progressively)

1. **Foundation** (Weeks 1-3): Setup + Foundational → Database, auth, models, API infrastructure ready
2. **MVP** (Week 4): User Story 1 → Test independently → **Deploy (Employees can now chat with LLM!)**
3. **History** (Week 5): User Story 2 → Test independently → Deploy (Employees can now manage conversations)
4. **Documents** (Week 6-7): User Story 3 → Test independently → Deploy (Employees can now analyze documents)
5. **Multi-User** (Week 8): User Story 4 → Test with 10+ users → Deploy (Production-ready for all employees)
6. **Administrator** (Week 9): User Story 5 → Test admin functions → Deploy (IT staff can manage system)
7. **Polish** (Week 10): Phase 8 → Security, performance, docs → **Final production release**

Each deployment adds value without breaking previous features!

### Parallel Team Strategy (3 Developers)

**Phase 1-2** (Weeks 1-3): All developers work together on Setup + Foundational
- Critical that foundation is solid before splitting work

**Phase 3+** (Weeks 4-9): Once Foundational is complete, split by user story:
- **Developer A**: User Story 1 (Chat) → User Story 4 (Multi-User)
- **Developer B**: User Story 2 (History) → Help with User Story 4
- **Developer C**: User Story 3 (Documents) → User Story 5 (Administrator)

**Phase 8** (Week 10): All developers work together on Polish

**Advantages**:
- Stories complete and integrate independently
- Faster overall delivery (3 stories in parallel)
- Each developer owns end-to-end implementation of their story

---

## Task Summary

**Total Tasks**: 162

**Tasks per Phase**:
- Phase 1 (Setup): 8 tasks
- Phase 2 (Foundational): 30 tasks
- Phase 3 (User Story 1 - Basic Chat): 21 tasks
- Phase 4 (User Story 2 - History): 17 tasks
- Phase 5 (User Story 3 - Documents): 21 tasks
- Phase 6 (User Story 4 - Multi-User): 13 tasks
- Phase 7 (User Story 5 - Administrator): 24 tasks (added T131a, T131b, T131c for storage management)
- Phase 8 (Polish): 28 tasks (added T139a for network interruption handling)

**Parallel Opportunities**:
- 79 tasks marked [P] can run in parallel (50% of total)
- After Foundational phase: 4 user stories (US1, US2, US3, US5) can be developed in parallel

**Independent Test Criteria**:
- Each user story has clear acceptance scenarios from spec.md
- Each phase checkpoint validates story independence
- No user story depends on another (except US4 on US1)

**MVP Scope**:
- Phases 1-3 only (Setup + Foundational + User Story 1)
- 59 tasks total for MVP (unchanged - new tasks are in Phase 7 and 8)
- Delivers core value: air-gapped LLM chat for government employees

---

## Notes

- **[P] tasks**: Different files, no dependencies, safe to parallelize
- **[Story] labels**: Maps tasks to user stories for traceability and independence
- **File paths**: All tasks include exact file paths for clarity
- **No test tasks**: Specification does not request TDD approach; manual testing via acceptance scenarios
- **Air-gap focus**: All dependencies bundled, no external API calls
- **Korean support**: Validated throughout (queries, responses, UI, documentation)
- **Security**: Session-based auth, user isolation, admin controls
- **Performance**: Streaming responses, async backend, optimized inference
- **Maintainability**: Clean separation, type safety, structured logging

**Commit Strategy**: Commit after each task or logical task group (e.g., all models, all schemas)

**Validation**: Stop at each phase checkpoint to validate independently per acceptance scenarios

**Avoid**: Vague tasks, same-file conflicts, cross-story dependencies that break independence
