# Feature Specification: Local LLM Web Application for Local Government

**Feature Branch**: `001-local-llm-webapp`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "소규모 지방자치단체 공무원 대상, 폐쇄망 환경에서 이용 가능한 Local LLM 웹 애플리케이션 서비스를 구축한다. 이는 ChatGPT, Gemini와 같은 외부 에이전트의 사용이 제한되는 환경에서 업무 지원용 LLM 기반 도구를 제공하기 위함이다."

## Clarifications

### Session 2025-10-28

- Q: Document Q&A implementation strategy - should we use simple text extraction or vector embeddings for document analysis? → A: Vector embeddings + similarity search (ChromaDB/FAISS) to properly support multi-document comparison and accurate source references (User Story 3, Acceptance Scenarios 2 & 4)
- Q: Administrator data access scope - can administrators view user conversation contents, or only metadata for storage management? → A: Metadata only (username, conversation titles, message counts, storage usage) - conversation message contents are not accessible to administrators, preserving user privacy while enabling storage management (FR-032, User Story 5)
- Q: Backup and recovery strategy for air-gapped environment - what backup requirements are needed to support 30-day continuous operation? → A: Daily automated backups + weekly full backups with minimum 30-day retention (standard government policy), stored locally on separate storage volume, with documented restore procedures for IT staff (SC-010, Assumption #8)
- Q: Document generation mode activation - how does the user explicitly request document creation to trigger the 10,000 character limit? → A: Keyword detection in user queries (Korean keywords: "문서 작성", "초안 생성", "공문", "보고서 작성", etc.) automatically activates document generation mode, maintaining natural conversation flow (FR-017)
- Q: Tag system implementation - should tags be free-form user input or administrator-defined with manual selection? → A: Administrator-defined tags with automatic matching - administrators create organization-wide tag list (e.g., departments, projects, document types), system automatically analyzes conversation content and assigns matching tags based on semantic similarity to tag names/keywords, administrators can add new tags as needed, users can manually adjust auto-assigned tags if needed (FR-016, User Story 2)
- Q: 사용자별 저장 공간 할당 정책 - 사용자가 10GB 한도를 완전히 초과하면 어떻게 처리해야 하나요? → A: 자동 정리 - 10GB 도달 시 가장 오래된 대화/문서 자동 아카이브 또는 삭제 (30일 이상 미사용), 사용자에게 정리 내역 알림 표시 (FR-020, FR-019)
- Q: 동시 세션 한도 초과 시 처리 - 사용자가 4번째 로그인을 시도하면 어떻게 처리해야 하나요? → A: 가장 오래된 세션 자동 종료 - 가장 오래 활동이 없던 세션을 자동으로 로그아웃, 해당 세션에 "다른 위치에서 로그인하여 종료되었습니다." 알림 표시 (FR-030)
- Q: 문서 업로드 범위와 수명 - 사용자가 업로드한 문서는 어느 범위에서 접근 가능해야 하나요? → A: 대화별 범위 - 각 대화마다 독립적으로 문서 업로드, 해당 대화 내에서만 참조 가능, 대화 삭제 시 문서도 함께 삭제 (FR-009, FR-019, User Story 3)
- Q: 관리자 계정 초기 생성 방법 - FR-034 초기 설정 마법사와 FR-033 DB 직접 수정 요구사항이 충돌하는데, 첫 관리자는 어떻게 생성되어야 하나요? → A: 초기 설정 마법사 예외 - 시스템 첫 실행 시에만 설정 마법사가 첫 관리자 계정 생성 허용, setup.lock 파일 생성으로 재실행 방지, 이후 추가 관리자는 데이터베이스 직접 수정으로만 생성 가능 (FR-033, FR-034)
- Q: 태그 자동 할당 실행 시점 - 시스템이 대화에 태그를 자동으로 할당하는 시점은 언제인가요? → A: 대화 생성 시 - 사용자가 첫 메시지를 보낼 때 대화 제목과 첫 메시지 내용을 분석하여 태그 자동 할당, 이후 자동 업데이트 없음 (사용자가 수동으로 태그 추가/제거 가능) (FR-016, FR-043)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Text Generation and Q&A (Priority: P1)

Government employees need to ask questions and receive AI-generated responses for routine administrative tasks such as drafting documents, answering policy questions, or getting information summaries - all within their secure network without internet access.

**Why this priority**: This is the core functionality that provides immediate value. Employees can use the system for basic work assistance without compromising security by using external services.

**Independent Test**: Can be fully tested by submitting a text query through the web interface and receiving a relevant response, demonstrating that the local LLM is operational and accessible.

**Acceptance Scenarios**:

1. **Given** an employee is logged into the web application, **When** they type a question about administrative procedures and submit it, **Then** the system displays an answer within 10 seconds that meets quality criteria: directly related to question topic, grammatically correct Korean (맞춤법, 조사, 어미), composed of complete sentences (minimum 1), provides requested information type (e.g., procedural question → step-by-step explanation). Quality measurement method defined in SC-004
2. **Given** an employee needs to draft a formal letter, **When** they request document generation with specific parameters (recipient, purpose, tone), **Then** the system generates an appropriate draft document
3. **Given** an employee submits a query, **When** the LLM is processing, **Then** the system shows a loading indicator and does not freeze the interface
4. **Given** an employee receives a response, **When** they want to continue the conversation, **Then** they can submit follow-up questions that maintain context from previous exchanges

---

### User Story 2 - Conversation History Management (Priority: P2)

Employees need to save, retrieve, and organize their previous conversations with the LLM to reference past work, continue interrupted tasks, or share helpful responses with colleagues.

**Why this priority**: Conversation persistence adds significant value by allowing work continuity and knowledge sharing, but the system can function without it for immediate queries.

**Independent Test**: Can be tested by creating multiple conversations, navigating away, and verifying all conversations are saved and retrievable with their full content and metadata.

**Acceptance Scenarios**:

1. **Given** an employee has completed a conversation, **When** they navigate away and return later, **Then** they can view their complete conversation history with timestamps
2. **Given** an employee has multiple saved conversations, **When** they want to find a specific past discussion, **Then** they can search or filter conversations by keywords, date, or topic
3. **Given** an employee is viewing a saved conversation, **When** they want to continue the discussion, **Then** they can resume the conversation with full context preserved
4. **Given** an employee wants to organize their work, **When** they create or view conversations, **Then** they can assign custom titles and select from administrator-defined tags to conversations for easier retrieval and filtering

---

### User Story 3 - Document Upload and Analysis (Priority: P3)

Employees need to upload documents (reports, policies, memos) and ask the LLM to analyze, summarize, or extract information from them to support their research and decision-making tasks.

**Why this priority**: This enhances the LLM's utility significantly but requires additional processing capabilities. The core Q&A functionality (P1) and conversation management (P2) provide value independently.

**Independent Test**: Can be tested by uploading a sample government document, asking specific questions about its content, and verifying the LLM provides accurate answers based on the document.

**Acceptance Scenarios**:

1. **Given** an employee has a PDF or text document, **When** they upload it to the current conversation through the interface, **Then** the system processes the document and confirms it's ready for analysis within 30 seconds
2. **Given** an employee has uploaded a document to the current conversation, **When** they ask questions about its content, **Then** the LLM provides answers based on the document's information with source references
3. **Given** an employee uploads a long policy document to the current conversation, **When** they request a summary, **Then** the system generates a concise summary highlighting key points
4. **Given** an employee has uploaded multiple documents to the current conversation, **When** they ask comparative questions, **Then** the LLM can reference and compare information across all uploaded documents within that conversation (documents are not accessible from other conversations)

---

### User Story 4 - Multi-User Access with Basic Security (Priority: P4)

Multiple employees in the local government office need to access the LLM service simultaneously with individual accounts while ensuring their conversations remain private and the system remains stable.

**Why this priority**: Multi-user support is essential for organizational deployment but can be added after core functionality is proven. Initial testing can be done with a single user account.

**Independent Test**: Can be tested by creating multiple user accounts, having them use the system simultaneously, and verifying each user only sees their own conversations and experiences responsive performance.

**Acceptance Scenarios**:

1. **Given** a new employee needs access, **When** an administrator creates their account, **Then** the employee can log in with their credentials and access the service
2. **Given** multiple employees are using the system, **When** each submits queries simultaneously, **Then** all users receive responses without significant performance degradation
3. **Given** an employee is logged in, **When** they view their conversation history, **Then** they only see their own conversations, not those of other users
4. **Given** an employee session is inactive for 30 minutes, **When** they attempt to interact with the system, **Then** they are required to re-authenticate

---

### User Story 5 - Administrator Dashboard and User Management (Priority: P5)

IT staff need to manage user accounts, monitor system usage, and track system health to ensure the service operates smoothly and remains available for all employees.

**Why this priority**: Administrator functions are critical for long-term operational success but not required for initial functionality testing. The system can operate with manually configured users for early validation.

**Independent Test**: Can be tested by logging in as an administrator, creating/deleting user accounts, viewing usage statistics, and monitoring system health metrics without requiring the full user-facing application to be complete.

**Acceptance Scenarios**:

1. **Given** an administrator logs into the admin panel, **When** they navigate to the user management section, **Then** they see a list of all registered users with their account status and last login time
2. **Given** an administrator needs to create a new user account, **When** they enter a username and generate an initial password, **Then** the system creates the account and provides the credentials for distribution to the employee
3. **Given** an employee forgot their password, **When** an administrator resets it through the admin panel, **Then** a new temporary password is generated and the administrator can provide it to the employee
4. **Given** an employee leaves the organization, **When** an administrator disables or deletes their account, **Then** the user can no longer log in and their data is either archived or removed per policy
5. **Given** an administrator wants to monitor system usage, **When** they view the usage statistics dashboard, **Then** they see metrics including total active users, queries processed today/this week/this month, and average response times
6. **Given** an administrator wants to check system health, **When** they view the system health panel, **Then** they see server uptime, available storage space, memory usage, and LLM service status
7. **Given** system storage is running low, **When** an administrator views the storage metrics, **Then** they receive a warning and can see which users or conversations (by title, message count, storage size) are consuming the most space without viewing message contents
8. **Given** an administrator needs to organize conversation categorization, **When** they access the tag management interface, **Then** they can create new tags with names and colors, edit existing tags, view tag usage counts, and delete unused tags (with confirmation for tags in use)

---

### Edge Cases & Error Handling

**EC-001: Response Length Limit Exceeded**
- **Scenario**: LLM generates response exceeding 4,000 character limit
- **Handling**: Truncate response at 3,900 characters, append "[응답이 길이 제한으로 잘렸습니다. 더 구체적인 질문으로 나누어 주세요.]" (Response truncated due to length limit. Please split into more specific questions.)
- **Covered by**: FR-017, T045

**EC-002: Document Processing Capacity Exceeded**
- **Scenario**: Uploaded document exceeds 50MB OR text extraction exceeds memory limits
- **Handling**: Reject upload with error message "파일이 너무 큽니다. 50MB 이하의 파일을 업로드해주세요." (File too large. Please upload files under 50MB.) OR chunk document into smaller segments for processing
- **Covered by**: FR-015, T081, T094

**EC-003: System Resource Exhaustion**
- **Scenario**: Multiple concurrent queries exceed vLLM max_num_seqs (16 concurrent requests)
- **Handling**: Queue additional requests with user message "다른 사용자의 요청을 처리 중입니다. 잠시만 기다려주세요." (Processing other users' requests. Please wait a moment.). Return 503 Service Unavailable if queue exceeds 50 requests.
- **Covered by**: T105

**EC-004: Special Characters & Multi-Language Input**
- **Scenario**: User submits query with mixed Korean/English, emojis, or special formatting
- **Handling**: Pass input directly to LLM without sanitization (Llama-3 handles Unicode). Preserve formatting in message storage and display.
- **Covered by**: FR-014, T059

**EC-005: Invalid or Corrupted File Upload**
- **Scenario**: User uploads non-PDF/DOCX/TXT file OR corrupted file
- **Handling**: Validate file type via magic number (not extension). Reject with error "지원하지 않는 파일 형식입니다. PDF, DOCX, TXT 파일만 업로드 가능합니다." (Unsupported file format. Only PDF, DOCX, TXT allowed.) If corruption detected during extraction, return error "파일이 손상되었습니다." (File is corrupted.)
- **Covered by**: FR-015, T081, T094

**EC-006: Network Interruption During Request**
- **Scenario**: User's browser loses connection to server mid-request
- **Handling**: Frontend: Display reconnection message, retry request on reconnect. Backend: Continue processing request, store result in message history so user can retrieve on reconnect.
- **Implementation**: Add reconnection logic in frontend/src/lib/api.ts, use React Query retry mechanisms
- **Covered by**: T139a

**EC-007: LLM Service Unavailable**
- **Scenario**: vLLM service crashes, restarts, or is under maintenance
- **Handling**: Return 503 Service Unavailable with message "AI 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요." (AI service temporarily unavailable. Please try again later.). Admin dashboard displays LLM service status (red indicator).
- **Covered by**: T117, T152 (health checks)

**EC-008: Sensitive Information Detection**
- **Scenario**: User uploads document potentially containing PII or classified data
- **Handling**: OUT OF SCOPE for MVP. No automated detection. Rely on user training and assumption that air-gapped environment already provides security boundary. Future enhancement: keyword scanning for Social Security Numbers, classified markings.
- **Status**: Deferred to post-MVP

**EC-009: Empty or Whitespace-Only Query**
- **Scenario**: User submits empty string or whitespace-only input
- **Handling**: Client-side: disable submit button when input is empty or whitespace-only. Server-side: return 400 Bad Request if somehow submitted with error message "질문을 입력해주세요." (Please enter a question.)
- **Covered by**: FR-003

**EC-010: Duplicate Conversation Titles**
- **Scenario**: User creates multiple conversations with identical titles
- **Handling**: Allow duplicate titles (do not auto-append numbers). Users can distinguish conversations by date. Rationale: same topic may be discussed multiple times across different time periods.
- **Covered by**: FR-006, FR-016

**EC-011: Automatic Storage Cleanup**
- **Scenario**: User's storage reaches 10GB limit, triggering automatic cleanup of conversations/documents inactive for 30+ days
- **Handling**: System identifies oldest inactive items (sorted by last_accessed timestamp), deletes them until storage drops below 9GB (10% buffer), displays notification modal: "저장 공간 부족으로 30일 이상 사용하지 않은 항목을 자동으로 정리했습니다. [정리 내역 보기]" showing list of deleted items (title, last access date, size recovered). If cleanup fails mid-process, rollback transaction and display error: "자동 정리 중 오류가 발생했습니다. 관리자에게 문의하세요.", notify administrator.
- **Edge case within edge case**: All items are recent (none >30 days old) but storage still at 10GB → Display error to user: "저장 공간이 부족합니다. 사용하지 않는 대화나 문서를 삭제해주세요." and prevent new uploads/conversations until manual deletion.
- **Covered by**: FR-020, FR-019

**EC-012: Concurrent Session Limit Exceeded**
- **Scenario**: User attempts 4th login while already having 3 active sessions
- **Handling**: Backend identifies oldest session by last_activity timestamp (last API request time), terminates that session (delete session token from database, invalidate Redis cache entry if used), allow new login to proceed. Terminated session: on next API request receives 401 Unauthorized, frontend detects and displays modal "다른 위치에서 로그인하여 종료되었습니다.", redirects to login page after 5 seconds.
- **Implementation detail**: Track last_activity timestamp on every authenticated API request. Display session info in user settings: device/browser (from User-Agent), location (if available), last activity time.
- **Covered by**: FR-030

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST operate entirely within a closed network environment without requiring internet connectivity
- **FR-002**: System MUST provide a web-based interface accessible through standard web browsers on the internal network
- **FR-003**: Users MUST be able to submit text queries and receive LLM-generated responses
- **FR-004**: System MUST display a visual indicator when processing user queries
- **FR-005**: System MUST support conversational context, allowing follow-up questions within the same session
- **FR-006**: System MUST allow users to create, view, and delete their saved conversations
- **FR-007**: System MUST support searching or filtering through saved conversations
- **FR-008**: System MUST accept document uploads in common formats (PDF, TXT, DOCX)
- **FR-009**: System MUST process uploaded documents using vector embeddings (ChromaDB or FAISS) for semantic search, enable question-answering based on document content with accurate source references (page numbers, sections), and support multi-document comparison queries within the same conversation (documents are scoped to individual conversations, accessible only within that conversation, and automatically deleted when the conversation is deleted)
- **FR-010**: System MUST support multiple concurrent users with individual authentication
- **FR-011**: System MUST ensure each user can only access their own conversation history and uploaded documents
- **FR-012**: System MUST provide session management with automatic timeout after 30 minutes (1,800 seconds) of inactivity measured from last user request (click, input, scroll), display warning modal 3 minutes before timeout asking "곧 로그아웃됩니다. 계속하시겠습니까?", redirect to login page on timeout, and save draft messages to local storage for recovery upon re-login
- **FR-013**: System MUST display error messages in user-friendly language when operations fail
- **FR-014**: System MUST support Korean language for both queries and responses
- **FR-015**: System MUST validate uploaded files for type and size before processing
- **FR-016**: System MUST allow users to edit conversation titles and automatically assign tags from administrator-defined tag list when the first message is sent (system analyzes conversation title and first message content using semantic similarity to auto-assign relevant tags; administrators manage organization-wide tag list including creation, editing, and deletion of tags with optional keywords; users can manually add/remove auto-assigned tags at any time; tags are not automatically updated after initial assignment)
- **FR-017**: System MUST limit response length with two modes: default mode (4,000 character maximum), document generation mode (10,000 character maximum activated by keyword detection in user queries: "문서 작성", "초안 생성", "공문", "보고서 작성", or similar document creation terms), truncating at 3,900/9,900 characters respectively with warning messages "응답이 길이 제한으로 잘렸습니다. 더 구체적인 질문으로 나누어 주세요." or "문서가 너무 깁니다. 더 짧게 요청해주세요."
- **FR-018**: System MUST provide an administrator panel with user management (account creation/deletion, password resets), usage statistics, and system health monitoring capabilities
- **FR-019**: System MUST retain conversations and uploaded documents until users manually delete them OR administrators remove them due to storage constraints (with user notification)
- **FR-020**: System MUST display storage usage warnings to users when their personal storage exceeds 80% of per-user quota (10GB), and automatically archive or delete oldest conversations/documents (inactive for 30+ days) when 10GB limit is reached, displaying notification to user with list of cleaned items and total space recovered
- **FR-021**: System MUST display storage usage warnings to administrators when total system storage exceeds 80% capacity
- **FR-022**: Administrators MUST be able to view per-user storage consumption in the admin panel
- **FR-023**: System MUST prevent file uploads when total system storage exceeds 95% capacity
- **FR-024**: Administrators MUST be able to view aggregate usage statistics including number of active users, total queries processed, average response times, and system resource utilization
- **FR-025**: Administrators MUST be able to create new user accounts with unique usernames and initial passwords
- **FR-026**: Administrators MUST be able to disable or delete user accounts
- **FR-027**: Administrators MUST be able to reset user passwords when requested
- **FR-028**: System MUST display system health metrics to administrators including server uptime, available storage, and LLM service status
- **FR-029**: System MUST enforce password complexity requirements: minimum 8 characters, at least 2 types among letters/numbers/special characters, and use bcrypt hashing with cost factor 12
- **FR-030**: System MUST support concurrent logins from the same user account (maximum 3 sessions), with each session independently managed, all sessions invalidated upon forced logout, and automatically terminate the oldest inactive session (by last_activity timestamp) when a 4th login is attempted, displaying notification "다른 위치에서 로그인하여 종료되었습니다." to the terminated session
- **FR-031**: System MUST implement login attempt protection: account lockout for 30 minutes after 5 consecutive failed attempts, IP-based rate limiting (maximum 10 login attempts per minute per IP), with administrator unlock capability
- **FR-032**: System MUST enforce database-level data isolation using user_id filtering, return 403 Forbidden when session user differs from resource owner, and restrict administrator access to user conversation message contents (administrators can view metadata: username, conversation titles, message counts, timestamps, storage usage for management purposes, but cannot read actual message content; deletion allowed for storage management)
- **FR-033**: System MUST prevent privilege escalation by managing administrator accounts in separate table, allowing administrator privilege grants only through direct database modification (except for the initial administrator created via setup wizard on first run), and preventing administrators from removing their own privileges
- **FR-034**: System MUST provide initial setup wizard on first run requiring administrator account creation (username, password), system name configuration, and storage allocation, with setup.lock file created after completion to prevent reconfiguration and disable setup wizard for subsequent runs (additional administrators can only be created via direct database modification per FR-033)
- **FR-035**: System MUST define distinct UI states for chat interface: idle (placeholder "질문을 입력하세요"), typing (character counter), processing (spinner + "AI가 답변을 생성하고 있습니다..."), streaming (real-time text with cursor animation), completed (re-enable input), and error (red icon + retry button)
- **FR-036**: System MUST manage conversational context with 10-message window (5 user + 5 AI), 2,048 token limit, FIFO removal when exceeded, system messages always included, and load recent 10 messages when resuming saved conversations
- **FR-037**: System MUST format error messages following "[problem description] + [user action]" pattern in polite Korean (존댓말), minimize technical terms, avoid blame language, with examples: "일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요." for server errors, "지원하지 않는 파일 형식입니다. PDF, DOCX, TXT 파일만 업로드 가능합니다." for invalid files
- **FR-038**: System MUST provide usage statistics dashboard displaying user metrics (total registered, active in last 7 days, currently online), query metrics (today/week/month counts, P50/P95/P99 response times, failure rate), resource metrics (storage usage overall and top 5 users, memory %, CPU %), and system metrics (uptime, LLM status, recent 10 error logs)
- **FR-039**: System MUST display zero-state UI: for new users show "아직 대화가 없습니다" with highlighted "새 대화 시작하기" button and optional usage examples; for empty document uploads show "업로드된 문서가 없습니다" with drag-drop area and supported formats; for empty search results show "검색 결과가 없습니다" with keyword suggestion
- **FR-040**: System MUST support browsers Chrome 90+, Edge 90+, Firefox 88+ (not Internet Explorer), require minimum 1280x720 resolution and JavaScript enabled
- **FR-041**: System MUST limit conversations to 1,000 messages per conversation, display warning "대화가 너무 깁니다. 새 대화를 시작해주세요." when limit reached while allowing continued use with performance warning, and exempt administrators from limit for debugging
- **FR-042**: System MUST implement automated backup strategy: daily incremental backups of database and uploaded documents at 2 AM, weekly full backups every Sunday, minimum 30-day backup retention, backups stored on separate storage volume (not system disk), and provide documented restore procedures accessible to IT staff through admin panel
- **FR-043**: System MUST provide tag management interface for administrators to create, edit, and delete organization-wide tags (tag attributes: name, optional keywords for matching, color/icon for visual distinction, creation date), automatically assign tags to conversations when the first message is sent by analyzing conversation title and first message content and matching to tag names/keywords using semantic similarity (embedding-based with sentence-transformers), prevent deletion of tags currently in use by displaying usage count and requiring confirmation, allow users to filter conversations by single or multiple tags, and enable users to manually adjust auto-assigned tags at any time (tags not automatically updated after initial assignment)

### Key Entities

- **User**: Government employee who uses the system; has unique credentials, can create conversations, upload documents
- **Administrator**: IT staff member with elevated privileges; can manage user accounts, view system statistics, monitor system health, manage organization-wide tags
- **Conversation**: A series of messages between a user and the LLM; has a title, creation timestamp, last modified timestamp, belongs to a single user, can be associated with multiple tags, can contain uploaded documents
- **Message**: Individual query or response within a conversation; contains text content, timestamp, role (user or assistant), limited to 4,000 characters
- **Document**: File uploaded by a user for analysis; has filename, file type, upload timestamp, processed content (extracted text + vector embeddings), belongs to a specific conversation (not shared across conversations), automatically deleted when parent conversation is deleted
- **Session**: Active authenticated connection for a user or administrator; has expiration time, tracks current conversation, tracks last activity timestamp for concurrent session management
- **Tag**: Organization-wide label created by administrators for auto-categorizing conversations; has name, optional keywords for matching, color/icon, creation date, usage count; system automatically assigns tags to conversations based on semantic analysis of message content; users can manually adjust auto-assigned tags

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a query and receive a relevant response within 10 seconds for queries under 500 characters (target: 5 seconds; maximum acceptable: 10 seconds)
- **SC-002**: System supports at least 10 concurrent users without response time degradation exceeding 20% (baseline: single-user average 5 seconds per SC-001, target: ≤6 seconds with 10 concurrent users)
- **SC-003**: Users can upload and process a 20-page PDF document within 60 seconds
- **SC-004**: 한국어 쿼리의 90%가 문법적으로 정확하고 맥락적으로 적절한 응답을 받음
  - **측정 방법**: 50개 다양한 업무 시나리오 쿼리로 구성된 테스트 세트 사용
  - **평가 기준**: 각 응답을 3가지 차원으로 수동 채점 (각 0-10점)
    1. 문법 정확성: 맞춤법, 조사 사용, 문장 구조
    2. 질문 관련성: 질문에 대한 답변 적절성
    3. 한국어 자연스러움: 어색한 번역체 없이 자연스러운 표현
  - **합격 기준**: 90% 이상의 쿼리가 총 30점 만점에 24점 이상 (80% 점수)
  - **테스트 도구**: `scripts/test-korean-quality.py` (T059)
- **SC-005**: Conversation history retrieval completes within 2 seconds regardless of the number of saved conversations
- **SC-006**: System maintains 99% uptime during business hours (weekdays 9 AM - 6 PM)
- **SC-007**: 사용자가 24시간 후 저장된 대화를 재개할 때 컨텍스트를 95% 정확도로 유지
  - **컨텍스트 보존 의미**:
    - 데이터베이스: 모든 메시지 내용 100% 보존 (영구 저장)
    - LLM 컨텍스트: 재개 시 최근 10개 메시지를 LLM에 로드 (FR-036 준수)
    - 95% 정확도: 재개 후 첫 후속 질문이 이전 대화 맥락을 반영한 적절한 응답 생성
  - **측정 방법**:
    1. 10개 다중 메시지 대화 생성 (각 5-10 메시지)
    2. 24시간 대기 (또는 시스템 시간 조작)
    3. 각 대화를 재개하여 컨텍스트 의존적 질문 제출 (예: "앞서 말한 그 정책은 언제부터 시행되나요?")
  - **합격 기준**: 10개 대화 중 9개 이상이 모든 메시지를 데이터베이스에 보존하고, 재개 후 질문이 이전 맥락 반영한 답변 생성
  - **테스트 도구**: `scripts/test-context-preservation.py` (Phase 8 추가 예정)
- **SC-008**: Zero unauthorized access incidents to other users' conversations or documents during testing period
- **SC-009**: 85% of employees can complete their first query and receive a response without requiring assistance or training
- **SC-010**: System operates continuously for 30 days in air-gapped environment without requiring external updates or connectivity
- **SC-011**: Administrators can create a new user account in under 1 minute
- **SC-012**: Usage statistics dashboard loads within 3 seconds and displays accurate data
- **SC-013**: System health metrics update in real-time with maximum 30-second delay

## Assumptions

This specification is based on the following assumptions:

1. **Network Environment**: The local government has an internal network infrastructure that supports web applications, even though it's isolated from the internet
2. **Hardware Resources**: Server hardware meeting minimum specifications is available: CPU (8-core Intel Xeon or equivalent), RAM (32GB minimum, 64GB recommended), GPU (NVIDIA RTX 3090 or A100 with 16GB+ VRAM and CUDA support required), Storage (500GB+ SSD for OS/app/data, NVMe SSD 1TB recommended), Network (internal Gigabit Ethernet)
3. **User Devices**: Government employees have access to computers with supported browsers (Chrome 90+, Edge 90+, Firefox 88+, minimum 1280x720 resolution, JavaScript enabled). Internet Explorer is not supported.
4. **Data Sensitivity**: While the environment is air-gapped for security, the specific classification level of data that can be processed is not defined
5. **LLM Capabilities**: Meta-Llama-3-8B (meta-llama/Meta-Llama-3-8B) will be used as the local LLM model, providing reasonable quality Korean language support when deployed via vLLM inference engine
6. **User Volume & Storage**: "Small local government" implies approximately 10-50 employees who might use the system. Storage provisioning assumes 10GB per user (500GB total for 50 users), with monthly growth of 1-5GB total. Administrators responsible for storage expansion when capacity warnings occur.
7. **Authentication**: Basic username/password authentication is sufficient; advanced methods like SSO or multi-factor authentication are not required
8. **Maintenance**: Technical staff are available to perform system maintenance, updates, and user management on the local server
9. **Document Scope**: Documents processed are primarily administrative in nature (policies, reports, memos) rather than specialized technical documents
10. **Response Quality**: Users understand that local LLM responses may not match the quality of cloud-based services like ChatGPT but value the security and availability tradeoffs
11. **File Size Limits**: Document uploads will be limited to 50MB per file as a reasonable default for administrative documents

## Dependencies

- Local server infrastructure with sufficient compute resources
- Meta-Llama-3-8B model files (meta-llama/Meta-Llama-3-8B) that support Korean language and can run on local hardware with vLLM
- Server with GPU support (NVIDIA CUDA, minimum 16GB VRAM for Llama-3-8B inference)
- Vector database (ChromaDB or FAISS) with embedding model for document semantic search
- Embedding model files compatible with ChromaDB/FAISS (e.g., sentence-transformers) pre-downloaded for offline installation
- Separate storage volume for backups (minimum 1TB recommended, separate from system disk for redundancy)
- Internal network with stable connectivity between employee workstations and the application server
- Browser compatibility with modern web standards for the user interface
- IT staff access to the server for initial deployment and ongoing maintenance

## Out of Scope

This feature specification explicitly excludes:

- Integration with external cloud services or APIs
- Real-time collaboration features (multiple users editing the same conversation simultaneously)
- Advanced analytics or usage reporting dashboards
- Mobile application support (tablet/smartphone apps)
- Integration with existing government IT systems (HR, document management, etc.)
- Custom LLM model training or fine-tuning on government-specific data
- Voice input/output capabilities
- Automated compliance checking or policy violation detection in responses
- Export of conversations to specific government document formats
- Version control or audit trails for document changes
- Advanced security features like encryption at rest, detailed access logs, or role-based permissions beyond basic user separation
