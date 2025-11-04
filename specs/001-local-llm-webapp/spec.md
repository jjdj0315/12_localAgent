# Feature Specification: Local LLM Web Application for Local Government

**Feature Branch**: `001-local-llm-webapp`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "소규모 지방자치단체 공무원 대상, 폐쇄망 환경에서 이용 가능한 Local LLM 웹 애플리케이션 서비스를 구축한다. 이는 ChatGPT, Gemini와 같은 외부 에이전트의 사용이 제한되는 환경에서 업무 지원용 LLM 기반 도구를 제공하기 위함이다."

**Overview**: Air-gapped Local LLM web application for small local government employees using **Qwen3-4B-Instruct** (~2.5GB Q4_K_M quantization, Qwen2.5-72B-level performance) to provide AI assistance for administrative tasks without internet connectivity. Optional fallback to Qwen2.5-1.5B-Instruct (~1GB) for resource-constrained environments.

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

### Session 2025-10-29

- Q: GPU 하드웨어 요구사항 모순 - Assumption #2는 GPU 필수라고 했지만 Dependencies는 CPU 우선/GPU 선택적이라고 명시. 실제 배포 요구사항은? → A: CPU 우선, GPU 선택 - CPU로 기본 동작 보장, GPU 있으면 가속 활용. 지자체 환경에서 GPU 서버 조달 어려움과 경량 모델(Qwen3-4B)의 CPU 작동 가능성 고려 (Assumption #2, Dependencies)
- Q: Safety Filter 모델 구체화 - "toxic-bert or similar"는 모호함. 폐쇄망 사전 다운로드를 위해 정확한 모델 이름 필요. 어떤 모델 사용? → A: unitary/toxic-bert - 다국어 지원(한국어 포함), ~400MB, CPU 호환, HuggingFace에서 다운로드 가능, 검증된 toxic content 분류 모델 (FR-050, FR-057, Dependencies)
- Q: ReAct 도구 실패 시 사용자 경험 - FR-065는 "우아하게 처리"라고만 명시. 도구 실패 시 사용자에게 어떻게 보여줄지? → A: Transparent failure - Observation에 실패 내용 표시(예: "문서를 찾을 수 없습니다"), AI가 대안 시도 또는 명확한 안내 제공. ReAct의 추론 가시성 유지하면서 실패를 숨기지 않음 (FR-065, User Story 7 Acceptance Scenario 6)
- Q: Multi-Agent Orchestrator 기본 라우팅 모드 - FR-076은 "keyword-based OR LLM-based (admin-configurable)"이라고만 명시. 시스템 기본 모드는? → A: LLM-based 기본 - 더 정확한 의도 파악, 새로운 질문 패턴에 유연 대응, 추가 LLM 호출 비용 허용. Keyword-based는 fallback 또는 관리자가 성능 최적화 시 전환 가능 (FR-070, FR-076)
- Q: LLM-based Orchestrator 프롬프트 전략 - LLM이 5개 에이전트 중 선택하도록 하는 구체적 방법은? → A: Few-shot 예시 기반 - 각 에이전트별 2-3개 대표 질문 예시를 프롬프트에 포함, 간결한 에이전트 설명과 함께 제공. 토큰 효율적이면서 높은 정확도 유지 (FR-070, FR-076, Dependencies)

### Session 2025-11-02

- Q: LoRA 파인튜닝 학습 데이터 수집 전략 - Multi-Agent 시스템(Phase 10)에서 5개 에이전트별 LoRA 어댑터 학습에 필요한 데이터를 어떻게 수집해야 하나요? → A: Phase 14 (Post-MVP)로 연기 - Phase 10에서는 프롬프트 엔지니어링만 사용 (Zero/Few-shot 학습), LoRA 파인튜닝 학습 데이터 수집 불필요. Constitution Principle IV (Simplicity Over Optimization) 준수, FR-071A 측정 방법론에 따라 프롬프트 기반 성능 먼저 검증 후 필요시 Phase 14에서 파인튜닝 진행 (FR-071A)

### Session 2025-11-04

- Q: 한국어 품질 테스트 합격 기준 반올림 - SC-004에서 "90% 이상의 쿼리"가 50개 중 45개(90.0%) vs 44개(88%)인지 불명확. 정확한 합격 개수는? → A: 정확한 개수: 50개 중 45개 이상 합격 (90.0%) - 테스트 재현성과 명확성을 위해 정확한 숫자 기준 사용 (SC-004)
- Q: 문서 생성 모드 키워드 매칭 전략 - FR-017에서 "문서 작성", "초안 생성" 등 키워드 감지 방식이 정확 매칭인지, 부분 매칭 허용인지, LLM 의도 파악인지 불명확. 어떤 전략을 사용하는가? → A: 정확 매칭 (exact substring matching) - 사용자 쿼리에 정의된 키워드 전체가 포함될 경우에만 문서 생성 모드 활성화. 예: "문서 작성해줘" (O), "문서 검색" (X), "초안 생성 부탁" (O), "초안" (X). 오탐지(false positive) 방지 및 예측 가능한 동작 보장 (FR-017, T225A)

## User Scenarios & Testing *(mandatory)*

**Testing Approach**: Manual acceptance testing per user story acceptance scenarios is MANDATORY per constitution. Automated unit/integration tests are NOT required for MVP but may be added later for regression testing.

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

### User Story 2 - Conversation History Management (Priority: P1)

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

## User Story 6 - Safety Filter for Content Moderation (Priority: P3)

Government employees need the system to automatically filter inappropriate content in both user inputs and AI responses to maintain a professional work environment and protect against data exposure.

**Why this priority**: Content filtering is important for workplace safety and data protection but the core Q&A functionality can operate without it. Should be implemented before wide deployment to prevent inappropriate usage.

**Independent Test**: Can be tested by submitting test queries containing inappropriate content (violence, sexual content, hate speech, PII) and verifying they are correctly filtered or masked, without requiring the full application to be deployed.

**Acceptance Scenarios**:

1. **Given** an employee submits a query containing violent, sexual, dangerous, or hateful content, **When** the safety filter analyzes the input, **Then** the system blocks the query and displays a warning message "부적절한 내용이 감지되어 요청을 처리할 수 없습니다." (Inappropriate content detected, cannot process request.)
2. **Given** the LLM generates a response containing inappropriate content, **When** the safety filter scans the output, **Then** the system replaces the entire response with a predefined safe message "안전한 응답을 생성할 수 없습니다. 질문을 다시 작성해주세요." (Cannot generate safe response. Please rephrase your question.)
3. **Given** an employee's query or document contains personal information (주민등록번호, phone numbers, email addresses), **When** the safety filter detects PII patterns, **Then** the system automatically masks the information (e.g., 123456-******* for SSN) before processing and displays a notice "개인정보가 자동으로 마스킹되었습니다." (Personal information has been automatically masked.)
4. **Given** the safety filter blocks content or masks PII, **When** the action is logged, **Then** administrators can view filter events in the admin panel showing timestamp, user, category (violence/sexual/hate/dangerous/PII), and whether it was input or output filtering (message content not logged for privacy)
5. **Given** an administrator needs to customize filtering rules, **When** they access the safety filter management interface, **Then** they can add/remove/edit keyword patterns for each category (violence, sexual, hate, dangerous content) and adjust PII detection patterns, with changes taking effect immediately

---

## User Story 7 - ReAct Agent with Government Tools (Priority: P3)

Government employees need the AI to systematically break down complex tasks using reasoning steps and specialized tools (document search, calculations, date logic, templates) to provide accurate and traceable answers.

**Why this priority**: ReAct agent capabilities significantly enhance AI usefulness for complex government tasks, but basic Q&A (P1) provides immediate value without it. Should be implemented after core functionality is stable.

**Independent Test**: Can be tested by submitting complex queries requiring multiple steps (e.g., "Find regulation X in uploaded documents and calculate budget impact for next fiscal year") and verifying the agent shows clear reasoning steps and tool usage.

**Acceptance Scenarios**:

1. **Given** an employee asks a question requiring document lookup, **When** the ReAct agent processes the request, **Then** the agent displays its reasoning ("Thought: 업로드된 문서에서 관련 규정을 검색해야 합니다"), executes the document search tool, and shows the result before generating final answer
2. **Given** an employee requests a calculation (budget, deadline, statistics), **When** the ReAct agent processes the request, **Then** the agent uses the calculator tool with clear input/output display (e.g., "Action: 계산기(1500000 * 1.05) = 1575000") and explains the result in context
3. **Given** an employee needs to check dates or deadlines, **When** they ask about fiscal years, business days, or holiday schedules, **Then** the agent uses the date/schedule tool to calculate accurate results considering Korean holidays and government calendar rules
4. **Given** an employee requests a standard document (공문서, 보고서), **When** the ReAct agent detects the request, **Then** the agent uses the document template tool to generate structured output with appropriate headers, sections, and formatting based on government document standards
5. **Given** the ReAct agent is processing a task, **When** it completes more than 5 reasoning-action cycles, **Then** the system stops iteration and displays "작업이 너무 복잡합니다. 질문을 단순화해주세요." (Task too complex. Please simplify your question.) with a summary of steps taken so far
6. **Given** a tool execution fails (e.g., document not found, calculation error), **When** the ReAct agent receives an error, **Then** the agent displays the error in its observation and either tries an alternative approach or explains the limitation to the user
7. **Given** an administrator reviews system usage, **When** they view tool execution logs in the admin panel, **Then** they see all tool invocations with timestamps, user, tool name, input parameters, output, and execution time for audit purposes

---

## User Story 8 - Multi-Agent System for Complex Workflows (Priority: P4)

Government employees need complex tasks (like responding to citizen inquiries requiring legal research, document drafting, and review) to be automatically distributed across specialized AI agents working collaboratively.

**Why this priority**: Multi-agent orchestration provides significant productivity gains for complex workflows but requires stable foundation of P1-P3 features. Can be added after single-agent capabilities are proven.

**Independent Test**: Can be tested by submitting a complex request (e.g., "Draft a response to citizen complaint about parking policy, cite relevant ordinances, and review for accuracy") and verifying multiple agents collaborate with clear handoffs.

**Acceptance Scenarios**:

1. **Given** an employee submits a citizen inquiry question, **When** the orchestrator analyzes the request, **Then** the system automatically routes it to the Citizen Support Agent, which generates a draft response considering tone, clarity, and completeness
2. **Given** an employee requests document creation (보고서, 안내문, 정책 문서), **When** the orchestrator assigns the task, **Then** the Document Writing Agent generates structured content following government document standards with appropriate sections, formatting, and professional language
3. **Given** an employee needs legal or regulatory information, **When** the orchestrator detects legal keywords, **Then** the Legal Research Agent searches uploaded regulations/ordinances, cites relevant articles with source references, and provides interpretation in plain language
4. **Given** an employee uploads statistical data or asks for data analysis, **When** the orchestrator routes to the Data Analysis Agent, **Then** the agent provides summary statistics, identifies trends, and suggests visualization approaches suitable for government reports
5. **Given** an agent generates a document or response, **When** the workflow includes a review step, **Then** the Review Agent automatically checks for errors (factual, grammatical, policy compliance), highlights potential issues, and suggests improvements
6. **Given** an employee submits a complex multi-step request (e.g., "Research policy X, draft amendment proposal, and review"), **When** the orchestrator analyzes the task, **Then** multiple agents work sequentially (Legal Research → Document Writing → Review) with each agent's output passed as input to the next, and the user sees progress indicators for each stage
7. **Given** an administrator manages the system, **When** they access the agent management interface, **Then** they can enable/disable specific agents, adjust orchestrator routing rules (keyword-based or LLM-based classification), and view agent performance metrics (task counts, average response times, error rates)
8. **Given** an employee views a Multi-Agent workflow result, **When** they review the response, **Then** the system clearly labels which agent contributed each section (e.g., "법규 검색 에이전트: [content]", "문서 작성 에이전트: [content]") for transparency

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
- **Scenario**: User uploads document or submits query potentially containing PII or classified data
- **Handling**:
  - **Basic PII masking (IN SCOPE for MVP)**: Automatically detect and mask 주민등록번호, phone numbers, email addresses in user inputs and AI outputs (covered by FR-052, Phase 8: US6 - Safety Filter, P3 priority)
  - **Advanced document classification (OUT OF SCOPE for MVP)**: No automated detection of classified markings ("대외비", "비밀", "Confidential"), document-level sensitivity scoring, or complex PII patterns beyond basic masking. Rely on user training and assumption that air-gapped environment already provides security boundary.
- **Rationale**: Basic PII masking (FR-052) is part of US6 (Safety Filter) which is P3 priority, included in Phase 2 Release (Advanced Features). Document classification is deferred to post-MVP.
- **Status**: Basic PII masking in Phase 8, advanced classification deferred to post-MVP

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
- **Handling**: System identifies oldest inactive items (sorted by last_accessed timestamp), deletes them until storage drops below 9GB (10% buffer), displays notification modal: "저장 공간 부족으로 30일 이상 사용하지 않은 항목을 자동으로 정리했습니다. [정리 내역 보기]" showing list of deleted items (title, last access date, size recovered).
- **Rollback Strategy** (handles database transaction vs filesystem inconsistency): Use two-phase commit approach:
  1. **Phase 1 - Mark for deletion**: Start database transaction, mark items for deletion in metadata table (status='pending_deletion'), commit transaction
  2. **Phase 2 - Delete files**: Delete actual document files from filesystem (synchronous or background job)
  3. **Phase 3 - Confirm deletion**: Start new transaction, update status='deleted' in metadata, commit transaction
  4. **On failure**: If file deletion fails in Phase 2, mark as 'deletion_failed', retry in background job (scheduled hourly). Do NOT rollback Phase 1 metadata changes - keep metadata consistent with intent.
  5. **Incomplete state recovery**: On system restart, check for items with status='pending_deletion', retry file deletion, log admin alert if failures persist after 3 retries.
- **Error display**: If cleanup fails (file deletion error, insufficient items to clean), display error: "자동 정리 중 오류가 발생했습니다. 관리자에게 문의하세요.", notify administrator with failed item IDs.
- **Edge case within edge case**: All items are recent (none >30 days old) but storage still at 10GB → Display error to user: "저장 공간이 부족합니다. 사용하지 않는 대화나 문서를 삭제해주세요." and prevent new uploads/conversations until manual deletion.
- **Covered by**: FR-020, FR-019

**EC-012: Concurrent Session Limit Exceeded**
- **Scenario**: User attempts 4th login while already having 3 active sessions
- **Handling**: Backend identifies oldest session by last_activity timestamp (last API request time), terminates that session (delete session token from database, invalidate Redis cache entry if used), allow new login to proceed. Terminated session: on next API request receives 401 Unauthorized, frontend detects and displays modal "다른 위치에서 로그인하여 종료되었습니다.", redirects to login page after 5 seconds.
- **Implementation detail**: Track last_activity timestamp on every authenticated API request. Display session info in user settings: device/browser (from User-Agent), location (if available), last activity time.
- **Covered by**: FR-030

**EC-013: Safety Filter False Positive**
- **Scenario**: Legitimate government query (e.g., about crime statistics, health policies) is incorrectly flagged as inappropriate
- **Handling**: Display filtered message with option "이 내용이 업무와 관련된 경우 [재시도]를 클릭하세요." (If this is work-related, click [Retry]). Retry bypasses rule-based filter but still applies ML model filter. Log all overrides with user ID and query for admin review. Administrators can adjust keyword rules based on false positive reports.
- **Covered by**: FR-050, FR-051, FR-055

**EC-014: PII Masking Incomplete**
- **Scenario**: Personal information in unusual format (e.g., phone number without dashes "01012345678") is not detected
- **Handling**: Support multiple PII pattern variations (주민등록번호: 6 digits + dash + 7 digits, phone: with/without dashes, email: standard regex). If undetected PII is reported by user or admin, add pattern to detection rules. Document known limitations (e.g., names cannot be auto-detected).
- **Covered by**: FR-052

**EC-015: ReAct Agent Infinite Loop**
- **Scenario**: Agent repeatedly attempts the same failed tool or gets stuck in reasoning cycle
- **Handling**: Track tool usage per request. If same tool called 3+ times with identical parameters, force stop with message "도구 실행이 반복되고 있습니다. 다른 방법을 시도해주세요." (Tool execution is repeating. Please try a different approach.). Maximum 5 reasoning cycles enforced (FR-062).
- **Covered by**: FR-062

**EC-016: Tool Execution Timeout**
- **Scenario**: Document search tool takes >30 seconds due to large corpus or complex query
- **Handling**: Set tool execution timeout at 30 seconds. If exceeded, return timeout error to agent. Agent's observation shows "도구 실행 시간 초과" (Tool execution timeout), and agent should explain limitation to user or try alternative approach.
- **Covered by**: FR-060, FR-061

**EC-017: Calculator Tool Malformed Expression**
- **Scenario**: ReAct agent generates invalid calculation expression (e.g., "계산기(1000 원 + 500 원)")
- **Handling**: Parse expressions to extract numbers only, ignore currency symbols and Korean text. If parsing fails completely, return error "잘못된 계산식입니다." (Invalid calculation expression.) to agent. Agent should reformulate or ask user for clarification.
- **Covered by**: FR-061

**EC-018: Multi-Agent Orchestrator Routing Failure**
- **Scenario**: User query is ambiguous and orchestrator cannot determine which agent to route to
- **Handling**: Default to general conversation mode (no specialized agent) and process with standard LLM. If user query explicitly mentions multiple agent domains (e.g., "Search regulations AND draft document AND review"), orchestrator creates sequential workflow automatically.
- **Covered by**: FR-070, FR-072

**EC-019: Agent Collaboration Failure**
- **Scenario**: Legal Research Agent fails (no documents found), but workflow requires its output for Document Writing Agent
- **Handling**: Each agent in workflow receives previous agent's status. If upstream agent failed, downstream agent displays error: "이전 단계가 실패하여 작업을 완료할 수 없습니다." (Cannot complete task due to previous step failure.) and explains what was attempted. User can retry with modified query.
- **Covered by**: FR-073, FR-075

**EC-020: Safety Filter Blocking Tool Output**
- **Scenario**: Document search tool returns content containing PII, which is then flagged by safety filter before returning to user
- **Handling**: Apply safety filter to tool outputs before passing to agent or user. Mask PII in tool results. If tool output is entirely inappropriate, replace with "[도구 결과에 부적절한 내용이 포함되어 필터링되었습니다.]" (Tool output contained inappropriate content and was filtered.). Agent should handle gracefully in its reasoning.
- **Covered by**: FR-050, FR-051, FR-052

## Requirements *(mandatory)*

### Functional Requirements

**Numbering Convention**: FR numbers are organized by feature area with intentional gaps for future expansion:
- FR-001~FR-043: Core functionality (basic chat, document upload, auth, admin)
- FR-044~FR-049: *Reserved for future core features*
- FR-050~FR-058: Safety Filter requirements
- FR-059: *Reserved for future safety features*
- FR-060~FR-069: ReAct Agent requirements
- FR-070~FR-080: Multi-Agent System requirements
- FR-081~FR-088: Common Air-Gapped requirements
- FR-089~FR-109: Admin Metrics History (Feature 002)
- FR-110~FR-114: Security Hardening (Feature 002 Patch)

#### Core Functional Requirements

- **FR-001**: System MUST operate entirely within a closed network environment without requiring internet connectivity
- **FR-002**: System MUST provide a web-based interface accessible through standard web browsers on the internal network
- **FR-003**: Users MUST be able to submit text queries and receive LLM-generated responses
- **FR-004**: System MUST display a visual indicator when processing user queries
- **FR-005**: System MUST support conversational context, allowing follow-up questions within the same session *(See FR-036 for technical implementation details: 10-message window, 2048 token limit)*
- **FR-006**: System MUST allow users to create, view, and delete their saved conversations
- **FR-007**: System MUST support searching or filtering through saved conversations
- **FR-008**: System MUST accept document uploads in common formats (PDF, TXT, DOCX)
- **FR-009**: System MUST process uploaded documents using vector embeddings (ChromaDB or FAISS) for semantic search, enable question-answering based on document content with accurate source references (page numbers, sections), and support multi-document comparison queries within the same conversation (documents are scoped to individual conversations, accessible only within that conversation, and automatically deleted when the conversation is deleted)
- **FR-010**: System MUST support multiple concurrent users with individual authentication
- **FR-011**: System MUST ensure each user can only access their own conversation history and uploaded documents
- **FR-012**: System MUST provide session management with automatic timeout after 30 minutes (1,800 seconds) of inactivity measured from last user request (click, input, scroll), display warning modal 3 minutes before timeout asking "곧 로그아웃됩니다. 계속하시겠습니까?", redirect to login page on timeout, and save draft messages to local storage for recovery upon re-login
- **FR-013**: System MUST display error messages in clear Korean (명확한 한국어) when operations fail, following patterns defined in FR-037: "[problem description] + [user action]" format, polite tone (존댓말), minimal technical terms, no blame language
- **FR-014**: System MUST support Korean language for both queries and responses
- **FR-015**: System MUST validate uploaded files for type and size before processing
- **FR-016**: System MUST allow users to edit conversation titles and automatically assign tags from administrator-defined tag list when the first message is sent (system analyzes first message content using semantic similarity to auto-assign relevant tags; if user has manually set a custom conversation title before sending first message, title is also included in analysis; administrators manage organization-wide tag list including creation, editing, and deletion of tags with optional keywords; users can manually add/remove auto-assigned tags at any time; tags are not automatically updated after initial assignment)
- **FR-017**: System MUST limit response length with two modes: default mode (4,000 character maximum), document generation mode (10,000 character maximum activated by exact substring matching of keywords in user queries: "문서 작성", "초안 생성", "공문", "보고서 작성" - full keyword must be present to activate mode, partial matches like "문서" or "초안" alone do not trigger document mode), truncating at 3,900/9,900 characters respectively with warning messages "응답이 길이 제한으로 잘렸습니다. 더 구체적인 질문으로 나누어 주세요." or "문서가 너무 깁니다. 더 짧게 요청해주세요."
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
- **FR-042**: System MUST implement automated backup strategy with the following specifications:

  **Backup Schedule**:
  - Daily incremental: 2 AM (pg_dump + document rsync/robocopy)
  - Weekly full: Sunday 2 AM (pg_dump --format=custom + full document snapshot)

  **Retention Policy**:
  - **Daily backups**: Keep all from last 30 calendar days, delete on day 31+
  - **Weekly backups**: Keep minimum 4 most recent, regardless of age (永久 보관 아님, 5번째부터 삭제)
  - **Combined guarantee**: Always have at least 30 days of daily recovery points OR 4 weekly recovery points (whichever provides longer coverage)

  **Edge Case Handling**:
  1. **Day 30 backup fails**:
     - Retention: Keep day 29 backup as newest
     - Cleanup: Skip deletion of day 1 backup (retain 30 days from last successful)
     - Alert: Log warning to admin dashboard + email notification (if configured)
     - Resolution: Next successful backup resets 30-day window

  2. **Multiple consecutive failures** (>3 days):
     - Retention: Freeze deletion (no cleanup until successful backup)
     - Alert: Critical alert to admin dashboard (red indicator)
     - Manual intervention: Administrator must investigate disk space/permissions

  3. **Disk space insufficient after cleanup**:
     - Action: Halt new backups, display error "백업 공간 부족. 수동 정리 필요."
     - Alert: Critical notification to admin panel
     - Recovery: Administrator must free space or expand backup volume

  **Storage**:
  - Location: Separate storage volume (not system disk)
  - Path: /backup (Linux) or D:\backups (Windows)
  - Access: Admin panel link to docs/admin/backup-restore-guide.md
- **FR-043**: System MUST provide tag management interface for administrators to create, edit, and delete organization-wide tags (tag attributes: name, optional keywords for matching, color/icon for visual distinction, creation date), automatically assign tags to conversations when the first message is sent by analyzing first message content and matching to tag names/keywords using semantic similarity (embedding-based with sentence-transformers; if user has manually set a custom conversation title before sending first message, title is also included in analysis), prevent deletion of tags currently in use by displaying usage count and requiring confirmation, allow users to filter conversations by single or multiple tags, and enable users to manually adjust auto-assigned tags at any time (tags not automatically updated after initial assignment)

#### Safety Filter Requirements (FR-050 series)

*Note: FR-051 and FR-052 are sub-requirements of FR-050's two-phase system, separated for clarity in implementation and testing*

- **FR-050** *(Parent requirement - defines filtering architecture)*: System MUST implement two-phase content filtering for both user inputs and AI responses: Phase 1 (rule-based filter using keyword matching and regex patterns for CPU execution), Phase 2 (lightweight classification model unitary/toxic-bert running on CPU with local weights), with filtering applied synchronously before LLM processing (for input) and before response delivery (for output)
- **FR-051** *(Sub-requirement of FR-050 - defines filtering categories)*: System MUST filter content across five categories: violence (폭력성), sexual content (성적 내용), dangerous content (위험한 질문), hate speech (혐오 발언), and personal information exposure (개인정보 유출), with configurable keyword lists per category managed by administrators
- **FR-052** *(Sub-requirement of FR-050 - defines PII masking patterns)*: System MUST automatically detect and mask personal information patterns: 주민등록번호 (6 digits + dash + 7 digits → 123456-*******), phone numbers (010-XXXX-XXXX or 01XXXXXXXXX → 010-****-****), email addresses (user@domain → u***@domain), with notification "개인정보가 자동으로 마스킹되었습니다." displayed to user
- **FR-053**: System MUST return filtering results with fields: is_safe (boolean), categories (list of violated categories), confidence (0-1 score from ML model if used), matched_patterns (list of triggered keywords from rule-based filter, not logged to preserve privacy)
- **FR-054**: System MUST display predefined safe messages when content is blocked: for input filtering "부적절한 내용이 감지되어 요청을 처리할 수 없습니다." (Inappropriate content detected), for output filtering "안전한 응답을 생성할 수 없습니다. 질문을 다시 작성해주세요." (Cannot generate safe response), replacing entire original content to prevent exposure
- **FR-055**: System MUST provide administrator interface for safety filter management: add/edit/remove keyword patterns per category, enable/disable categories, view filter statistics (daily counts by category for input/output), adjust confidence thresholds for ML model, with all changes taking effect immediately without restart
- **FR-056**: System MUST log all filter events to database with fields: timestamp, user_id, category, filter_type (input/output), action_taken (blocked/masked), confidence_score, but MUST NOT log actual message content for privacy protection
- **FR-057**: System MUST load all safety filter models and keyword lists locally from disk on application startup, with no external network calls required, supporting fully air-gapped deployment
- **FR-058**: System MUST allow filter bypass for false positives: display "이 내용이 업무와 관련된 경우 [재시도]를 클릭하세요." option when input is blocked, retry bypasses rule-based filter but still applies ML filter, log all bypass attempts with user_id for administrator review

#### ReAct Agent Requirements (FR-060 series)

- **FR-060**: System MUST implement ReAct (Reasoning and Acting) pattern with loop structure: Thought (사고: LLM generates reasoning step) → Action (행동: execute tool with parameters) → Observation (관찰: display tool result) → repeat until final answer, with each step visible to user in chat interface
- **FR-061**: System MUST provide six government-specialized tools for ReAct agent:
  1. Document Search Tool: searches uploaded documents in current conversation using vector similarity, returns text snippets with source references (filename, page)
  2. Calculator Tool: evaluates mathematical expressions (addition, subtraction, multiplication, division, percentages), handles Korean currency symbols (원), returns numeric result
  3. Date/Schedule Tool: calculates business days excluding weekends/Korean public holidays, fiscal year conversions (회계연도), deadline calculations from start date + duration
  4. Data Analysis Tool: loads CSV/Excel files from uploads, provides summary statistics (mean, median, sum, count), basic filtering and grouping
  5. Document Template Tool: generates structured Korean government documents (공문서, 보고서, 안내문) with standard headers, sections, signature blocks
  6. Legal Reference Tool: searches uploaded regulations/ordinances for specific articles, returns citations with article numbers and full text
- **FR-062**: System MUST limit ReAct agent iterations: maximum 5 reasoning-action cycles per user query (default, configurable by admin), stop with message "작업이 너무 복잡합니다. 질문을 단순화해주세요." if limit reached, display summary of steps taken so far to help user reformulate
- **FR-063**: System MUST implement tool execution safety: 30-second timeout per tool call, track identical tool calls (if same tool + same parameters called 3+ times, force stop with error "도구 실행이 반복되고 있습니다."), sandbox tool execution to prevent system access beyond designated directories
- **FR-064**: System MUST display ReAct agent progress in real-time: show each Thought as italic text with "🤔 사고:" prefix, show each Action as bold with "⚙️ 행동:" prefix and tool name/parameters, show each Observation as indented block with "👁️ 관찰:" prefix and result, final answer displayed normally
- **FR-065**: System MUST handle tool execution errors gracefully with transparent failure approach: return error description to agent in Observation field (e.g., "문서를 찾을 수 없습니다"), display error in chat interface as part of ReAct flow maintaining visibility, agent must attempt alternative tool/approach OR provide clear guidance to user in Korean explaining limitation and suggesting next steps, all tool errors logged with stack traces for debugging
- **FR-066**: System MUST log all tool executions to audit trail: timestamp, user_id, conversation_id, tool_name, input_parameters (sanitized to remove PII), output_result (truncated to 500 chars), execution_time_ms, success/failure status, accessible to administrators in admin panel for audit purposes
- **FR-067**: System MUST allow administrators to enable/disable individual tools: tool management interface shows list of tools with toggle switches, disabled tools return error "이 도구는 현재 사용할 수 없습니다." if agent attempts to use them, tool availability persists across restarts
- **FR-068**: System MUST load all tool implementations locally: document templates stored as Jinja2 files in `/templates` directory, Korean holiday calendar stored as JSON file locally, no external API calls required for any tool functionality
- **FR-069**: System MUST provide tool usage statistics in admin panel: per-tool usage counts (daily/weekly/monthly), average execution time per tool, error rate per tool, top users by tool usage, for capacity planning and optimization

#### Multi-Agent System Requirements (FR-070 series)

- **FR-070**: System MUST implement orchestrator-based Multi-Agent architecture: orchestrator receives user query, analyzes intent using LLM-based classification (default mode: few-shot prompt with **2 example queries per agent** + brief agent description for accuracy and flexibility, **total prompt budget ≤1000 tokens to reserve ≥1000 tokens for user query in 2048 context window**) OR keyword matching (admin-configurable alternative for performance optimization), routes to appropriate specialized agent, returns agent output to user.

  **Token Budget Breakdown**:
  - Orchestrator system prompt: ~200 tokens
  - 5 agents × 2 examples × ~60 tokens: ~600 tokens
  - Agent descriptions: ~200 tokens
  - **Total reserved**: ~1000 tokens
  - **Available for user query**: 1048 tokens (2048 - 1000)

  **User Query Overflow Handling**:
  - **If user query ≤1000 tokens**: Process normally
  - **If user query >1000 tokens AND ≤1500 tokens**:
    - Truncate query at 1000 tokens (character boundary, not mid-word)
    - Display warning: "질문이 너무 깁니다. 마지막 부분이 잘렸습니다. 더 짧게 나누어 질문해주세요."
    - Continue with orchestrator routing
  - **If user query >1500 tokens**:
    - Reject query with error 400 Bad Request
    - Display error: "질문이 너무 깁니다 (최대 약 3000자). 질문을 2-3개로 나누어 주세요."
    - Return to input state without processing

  **Token Counting**: Use transformers.AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct") for accurate Korean token counting (not character approximation)
- **FR-071**: System MUST provide five specialized agents, initially using task-specific prompt engineering (Phase 10) with optional LoRA (Low-Rank Adaptation) adapters (Phase 14, Post-MVP) if evaluation shows significant improvement:
  1. Citizen Support Agent (민원 지원 에이전트): analyzes citizen inquiries, generates empathetic draft responses, ensures polite tone (존댓말), checks completeness (answers all parts of inquiry)
  2. Document Writing Agent (문서 작성 에이전트): generates government documents (보고서, 안내문, 정책 문서) following standard templates, uses formal language, includes proper sections (제목, 배경, 내용, 결론)
  3. Legal Research Agent (법규 검색 에이전트): searches uploaded regulations/ordinances, cites relevant articles with source references, provides plain-language interpretation (쉬운 설명) alongside legal text
  4. Data Analysis Agent (데이터 분석 에이전트): analyzes uploaded CSV/Excel data, provides summary statistics with Korean formatting (천 단위 쉼표), identifies trends, suggests visualization types suitable for government reports
  5. Review Agent (검토 에이전트): reviews drafted content for errors (factual, grammatical, policy compliance), highlights potential issues with explanations, suggests specific improvements with examples
- **FR-071A** *(DEFERRED TO PHASE 14 POST-MVP - Separated from FR-071 as optional performance optimization)*: **Phase 10 Implementation**: Use prompt engineering only (Zero/Few-shot learning) for all 5 specialized agents without LoRA adapters, avoiding learning data collection complexity per Constitution Principle IV (Simplicity Over Optimization). **Phase 14 (Post-MVP) Activation Criteria**: IF Phase 10 evaluation shows prompt-based agents have insufficient performance (e.g., <80% quality score, excessive latency, poor task-specific accuracy), THEN proceed with LoRA fine-tuning. **LoRA Implementation (if activated)**: System implements dynamic LoRA adapter loading for Multi-Agent system: base model (**PRIMARY**: Qwen3-4B-Instruct, **FALLBACK**: Qwen2.5-1.5B-Instruct for resource-constrained systems) loaded once on startup, each agent loads its specific LoRA adapter on first invocation with adapter caching to minimize overhead, adapter switching latency must be <3 seconds per agent invocation, LLM service uses HuggingFace PEFT library for adapter management, all LoRA adapter weights bundled locally for air-gapped deployment. **Improvement Measurement Methodology**: Compare LoRA-adapted agent vs. base model (prompt-only) on 50 test queries per agent using 3-person blind evaluation (government employees preferred). Calculate composite score = weighted average (Response Quality 50% [correctness, completeness, relevance], Response Time 30% [latency improvement], Task-Specific Accuracy 20% [domain metrics: citation accuracy for Legal, tone appropriateness for Citizen Support, etc.]). **Threshold**: If composite improvement <10% OR quality improvement <5% (even with time gains), remove LoRA infrastructure. **Learning Data Collection (Phase 14 only)**: Requires collection of 500-1000 samples per agent (total 2500-5000 samples) from government employees or public datasets, estimated 4-6 weeks effort. See plan.md LoRA Transition Decision Tree for detailed criteria
- **FR-072**: System MUST support sequential Multi-Agent workflows: orchestrator detects multi-step requests using keyword patterns (e.g., "검색하고... 작성하고... 검토"), creates workflow chain with agent sequence, passes each agent's output as input to next agent, displays progress indicator showing current agent and workflow stage to user
- **FR-073**: System MUST handle agent failures in workflows: if agent fails, subsequent agents receive failure notification, failed agent displays error "이전 단계가 실패하여 작업을 완료할 수 없습니다." with explanation of what was attempted, user can retry entire workflow or individual failed step
- **FR-074**: System MUST display Multi-Agent outputs with clear attribution: each agent's contribution labeled with agent name (e.g., "📋 문서 작성 에이전트:", "⚖️ 법규 검색 에이전트:"), visual separators between agent outputs (horizontal lines), final combined result shown at end for Multi-Agent workflows
- **FR-075**: System MUST track agent workflow execution: log each agent invocation with timestamp, user_id, agent_name, input_summary (first 200 chars), output_summary (first 200 chars), execution_time_ms, success/failure, for performance monitoring and debugging
- **FR-076**: System MUST provide administrator interface for agent management: enable/disable individual agents (disabled agents not available for routing), configure orchestrator routing mode (default: LLM-based classification, alternative: keyword-based rules for performance optimization), edit keyword patterns for each agent's routing rules (used when keyword mode selected), view agent performance metrics (task counts, avg response time, error rate)
- **FR-077**: System MUST implement agent context sharing: agents in same workflow share conversation context (previous messages, uploaded documents), each agent can reference previous agent outputs in the workflow, context limited to current workflow execution (not persisted across different user requests)
- **FR-078**: System MUST support parallel agent execution for independent tasks: if orchestrator detects independent sub-tasks (e.g., "Analyze data AND search regulations"), dispatch to multiple agents simultaneously, wait for all agents to complete, combine outputs in final response with clear attribution
- **FR-079**: System MUST limit agent workflow complexity: maximum 5 agents per workflow chain, maximum 3 parallel agents per request, total workflow execution timeout 5 minutes, display "작업 시간이 초과되었습니다." if timeout reached with partial results shown
- **FR-080**: System MUST load all agent implementations and routing rules locally: agent prompt templates stored in `/prompts` directory as text files (Phase 10 mandatory), agent-specific LoRA adapter weights stored in `/models/lora_adapters/{agent_name}` directories (Phase 14 only if activated per FR-071A, e.g., `/models/lora_adapters/citizen_support/`, `/models/lora_adapters/document_writing/`), routing keyword patterns stored in database or config file, no external API dependencies for agent functionality

#### Common Air-Gapped Requirements (FR-081 series)

- **FR-081**: System MUST bundle all AI models locally: base LLM model (**PRIMARY**: Qwen3-4B-Instruct ~2.5GB Q4_K_M, **FALLBACK**: Qwen2.5-1.5B-Instruct ~1GB Q4_K_M for resource-constrained systems), agent-specific LoRA adapter weights (Phase 14 only if activated per FR-071A: ~100-500MB per adapter, 5 adapters total for Multi-Agent system), safety filter model weights (unitary/toxic-bert, ~400MB), sentence-transformers embedding model for tag matching and PII detection, with all models loaded from local disk on startup without internet access
- **FR-082**: System MUST support CPU-only execution: all safety filter models must support CPU inference with acceptable latency (<2 seconds per check), ReAct tools must not require GPU, Multi-Agent system uses base LLM with prompt engineering (Phase 10) or dynamically loaded LoRA adapters (Phase 14 only if activated per FR-071A, CPU-compatible via PEFT library), with optional GPU acceleration if available for faster inference
- **FR-083**: System MUST log all agent/tool/filter actions for audit: centralized audit log table with timestamp, user_id, action_type (filter/tool/agent), action_details (JSON), result (success/blocked/error), execution_time_ms, administrators can query logs by date range, user, or action type
- **FR-084**: System MUST allow administrators to customize all rule-based systems: safety filter keywords (add/edit/delete per category), ReAct tool availability (enable/disable), agent routing rules (keyword patterns), document templates (upload new .jinja2 files), with changes taking effect immediately or after restart (documented per feature)
- **FR-085**: System MUST provide admin dashboard section for advanced features: safety filter statistics (filter counts by category/day), ReAct tool usage statistics (per tool usage, avg time, error rate), Multi-Agent performance metrics (per agent task count, response time, success rate), combined into existing admin panel as new tabs
- **FR-086**: System MUST enforce resource limits for advanced features: max 10 concurrent ReAct sessions (queue additional requests), max 5 concurrent Multi-Agent workflows (return 503 if exceeded), safety filter timeout 2 seconds (allow message through with warning if timeout), to prevent resource exhaustion
- **FR-087**: System MUST handle graceful degradation: if safety filter model fails to load, fallback to rule-based only with warning to admin, if ReAct tools unavailable, fallback to standard LLM conversation, if Multi-Agent orchestrator fails, route all requests to general LLM, system remains functional even if advanced features fail
- **FR-088**: System MUST document all customization options: administrator guide includes sections for configuring safety filter rules, adding custom document templates, modifying agent routing keywords, adjusting resource limits, stored in `/docs` directory or accessible via admin panel help section
- **FR-089**: System MUST automatically collect and store dashboard metrics at two levels: hourly snapshots for detailed analysis and daily aggregates for long-term trends (Feature 002: Admin Metrics History)
- **FR-090**: System MUST store at minimum the following metrics: active user count, total storage usage, active session count, conversation count, document count, tag count
- **FR-091**: System MUST retain hourly metrics data for at least 30 days and daily aggregate data for at least 90 days
- **FR-092**: Administrators MUST be able to switch between hourly and daily views when examining metrics
- **FR-093**: Administrators MUST be able to view historical metrics as line graphs on the dashboard
- **FR-094**: Administrators MUST be able to select different time ranges for viewing (7 days, 30 days, 90 days)
- **FR-095**: System MUST display current (real-time) metrics alongside historical trends on the same dashboard
- **FR-096**: Graphs MUST show data points with tooltips displaying exact values and timestamps when hovered
- **FR-097**: System MUST handle missing data points by displaying gaps as dotted lines in graphs, with tooltip "이 기간 동안 데이터 수집 실패" when hovered
- **FR-098**: System MUST preserve metric history even when the underlying data changes (e.g., if users are deleted, historical user counts remain accurate)
- **FR-099**: System MUST provide time period comparison functionality allowing admins to overlay two date ranges
- **FR-100**: System MUST calculate and display percentage changes between compared periods
- **FR-101**: System MUST allow exporting metric data to CSV format with a maximum file size of 10MB, automatically downsampling data using LTTB (Largest Triangle Three Buckets) algorithm if necessary to maintain visual fidelity
- **FR-102**: System MUST allow exporting dashboard snapshots to PDF format with a maximum file size of 10MB, automatically downsampling embedded graphs using LTTB algorithm if necessary
- **FR-103**: Metric collection MUST not impact system performance (non-blocking, background task)
- **FR-104**: System MUST automatically clean up metrics older than the retention period to manage storage
- **FR-105**: All metric timestamps MUST be stored in UTC and displayed in admin's local timezone
- **FR-106**: Dashboard MUST show a "Data Collection Status" indicator with the following criteria: **녹색 (정상)** - Last collection completed within 5 minutes AND fewer than 3 failures in the past 24 hours; **노란색 (주의)** - 3-10 collection failures in the past 24 hours OR last collection 5-60 minutes ago; **빨간색 (오류)** - More than 10 failures in the past 24 hours OR no successful collection for over 1 hour; Indicator shows: status color, last successful collection timestamp, recent failure count
- **FR-107**: System MUST automatically retry failed metric collection in the next collection cycle, with a maximum of 3 retry attempts for any missed data point
- **FR-108**: When no historical data exists (new installation), system MUST display empty graphs with message "데이터 수집 중입니다. 첫 데이터는 [next collection time]에 표시됩니다"
- **FR-109**: System MUST automatically downsample data points on the client side to a maximum of 1000 points per graph using LTTB (Largest Triangle Three Buckets) algorithm to ensure responsive rendering while preserving visual characteristics of time-series data

#### Security Hardening Requirements (FR-110 series)

*Note: These requirements address critical security and operational issues discovered during Feature 002 code review (2025-11-04)*

- **FR-110**: System MUST implement CSRF (Cross-Site Request Forgery) protection for all state-changing requests (POST, PUT, DELETE, PATCH) by: generating unique CSRF token per session stored in httpOnly=false cookie (allowing JavaScript read access), validating that CSRF token from cookie matches X-CSRF-Token header on every state-changing request, returning 403 Forbidden with Korean error message "CSRF 토큰이 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요." on validation failure, exempting login (POST /api/v1/auth/login) and initial setup (POST /api/v1/setup) endpoints from CSRF validation to allow initial authentication

- **FR-111**: System MUST register and apply all security middleware in main.py in the following order: CORS middleware → CSRF middleware → Rate Limiting middleware (60 requests/minute per IP) → Resource Limiting middleware (max 10 concurrent ReAct sessions, max 5 concurrent Multi-Agent workflows, return 503 Service Unavailable when limits exceeded) → Performance middleware (track response times) → Metrics middleware, with all middleware active on application startup and properly configured

- **FR-112**: System MUST enhance session token security by: using secure=True for session cookies in production environment (HTTPS-only transmission), using samesite="strict" in production and samesite="lax" in development, adding max_age=1800 (30 minutes) to session cookies, implementing sensitive data filter for all logging that masks session tokens (pattern: `session_token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)` → `session_token=***REDACTED***`), Bearer tokens (pattern: `Bearer\s+([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)` → `Bearer ***REDACTED***`), and passwords (pattern: `password["\']?\s*[:=]\s*["\']?([^"\']+)` → `password=***REDACTED***`), with environment variable ENVIRONMENT={development|production} controlling security settings

- **FR-113**: System MUST ensure metric collection consistency by: collecting all 6 metrics (active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count) within a single database transaction to guarantee identical collected_at timestamp for all metrics in same collection cycle, setting database isolation level to READ COMMITTED explicitly in connection configuration, logging transaction start/end timestamps for debugging, handling individual metric failures without rolling back entire transaction (record failures in metric_collection_failures table while committing successful metrics)

- **FR-114**: System MUST provide cross-platform encoding compatibility for CSV exports by: detecting client operating system from User-Agent header, using UTF-8 with BOM (Byte Order Mark) encoding for Windows clients (User-Agent contains "Windows"), using UTF-8 without BOM for Linux/Mac clients, implementing client-side BOM injection as fallback in frontend JavaScript for browsers that don't correctly report OS, validating exported CSV files open correctly in Windows Excel (no encoding dialog), LibreOffice on Linux (correct Korean display), and Python pandas.read_csv() (no BOM artifacts in column names)

#### Quality & Operational Requirements (FR-115 series)

*Note: These requirements address critical quality and operational issues discovered during post-implementation review (2025-11-04)*

- **FR-115** *(CRITICAL)*: System MUST ensure Korean language resource files are correctly encoded in UTF-8 without corruption by: validating that frontend/src/lib/errorMessages.ts contains only valid UTF-8 characters (no mojibake/��������), all Korean strings display correctly in browser console and UI without replacement characters (���), automated test verifies errorMessages object keys and values are readable Korean text (pattern: /^[\uAC00-\uD7A3\s\w\d.,!?'"()]+$/), implementing pre-commit hook to detect non-UTF-8 characters in .ts/.tsx files, documenting standard procedure for editing Korean content (editor must be set to UTF-8, no BOM for .ts files)

- **FR-116** *(CRITICAL)*: System MUST calculate active user metrics accurately using timezone-aware timestamps by: using datetime.now(timezone.utc) consistently instead of datetime.utcnow() (deprecated), counting active users based on Session.expires_at > current_time (not created_at >= now - 30 minutes), ensuring all database timestamp comparisons use timezone-aware datetime objects, logging timezone information in metric collection debug output for verification

- **FR-117** *(HIGH)*: System MUST capture database query performance metrics for async SQLAlchemy operations by: binding event listeners to both sync_engine (for migrations) and async_engine.sync_engine (for application queries), tracking query execution time for SELECT/INSERT/UPDATE/DELETE separately, updating Prometheus db_query_duration and db_queries_total metrics for async queries, monitoring connection pool metrics from async_engine.sync_engine.pool instead of sync_engine.pool only, validating that /metrics endpoint shows non-zero query counts during normal application operation

- **FR-118** *(HIGH)*: System MUST maintain consistent administrator privilege model by: choosing single source of truth (Option A: User.is_admin flag OR Option B: separate Admin table existence check), if using separate Admin table approach then updating get_current_admin() in backend/app/api/deps.py to verify Admin table record exists for user, implementing migration script to sync existing User.is_admin flags with Admin table records, documenting administrator management procedure in docs/admin/user-management.md, ensuring all admin-only endpoints use consistent privilege check method

- **FR-119** *(MEDIUM)*: System MUST optimize CSRF token lifecycle management by: generating CSRF token only on successful login (not every GET request), storing CSRF token in session with 30-minute expiration matching session timeout, validating CSRF token exists before regenerating on GET requests (if missing or expired, then regenerate), returning same token value for multiple GET requests within session lifetime to prevent token rotation confusion, logging CSRF token generation events (not values) for debugging token mismatch issues

- **FR-120** *(MEDIUM)*: System MUST provide flexible CSRF exemption path matching by: supporting both exact path matching (e.g., "/api/v1/auth/login") and prefix matching (e.g., "/api/v1/setup/*" matches all setup sub-routes), implementing CSRF_EXEMPT_PATTERNS list with tuples (path_pattern, match_type) where match_type is "exact" or "prefix", adding common exempt paths: /docs, /openapi.json, /health, /api/v1/health, /metrics (Prometheus), documenting how to add new exempt paths in code comments and admin guide

- **FR-121** *(MEDIUM)*: System MUST align security test scripts with actual implementation by: updating tests/security_audit.py to match backend/app/core/security.py's direct bcrypt usage (not passlib), verifying password hashing test calls bcrypt.hashpw() and bcrypt.checkpw() directly, ensuring test expectations match bcrypt default rounds (12) from FR-029, adding integration test that validates actual /auth/login endpoint uses correct password verification method, documenting security implementation decisions in tests/README.md

- **FR-122** *(MEDIUM)*: System MUST implement data isolation middleware or update test expectations by: either (Option A) creating backend/app/middleware/data_isolation_middleware.py that validates user_id matches session user for GET/PUT/DELETE on /conversations/{id}, /documents/{id}, /messages/{id} routes, returning 403 Forbidden with message "이 리소스에 접근할 권한이 없습니다." on ownership mismatch, OR (Option B) removing data_isolation_middleware expectations from tests/security_audit.py and documenting that data isolation is handled at API dependency level via get_current_user() in backend/app/api/deps.py, registering middleware in main.py if Option A selected

### Key Entities

- **User**: Government employee who uses the system; has unique credentials, can create conversations, upload documents
- **Administrator**: IT staff member with elevated privileges; can manage user accounts, view system statistics, monitor system health, manage organization-wide tags, configure safety filters, manage ReAct tools and Multi-Agent settings
- **Conversation**: A series of messages between a user and the LLM; has a title, creation timestamp, last modified timestamp, belongs to a single user, can be associated with multiple tags, can contain uploaded documents
- **Message**: Individual query or response within a conversation; contains text content, timestamp, role (user or assistant), limited to 4,000 characters, passes through safety filter before storage/delivery
- **Document**: File uploaded by a user for analysis; has filename, file type, upload timestamp, processed content (extracted text + vector embeddings), belongs to a specific conversation (not shared across conversations), automatically deleted when parent conversation is deleted
- **Session**: Active authenticated connection for a user or administrator; has expiration time, tracks current conversation, tracks last activity timestamp for concurrent session management
- **Tag**: Organization-wide label created by administrators for auto-categorizing conversations; has name, optional keywords for matching, color/icon, creation date, usage count; system automatically assigns tags to conversations based on semantic analysis of message content; users can manually adjust auto-assigned tags
- **SafetyFilterRule**: Keyword pattern or regex rule for content filtering; belongs to a specific category (violence/sexual/hate/dangerous/PII), has pattern text, enabled/disabled status, creation timestamp, last modified by administrator
- **FilterEvent**: Log record of safety filter action; has timestamp, user_id, category, filter_type (input/output), action_taken (blocked/masked), confidence_score, does not store actual message content for privacy
- **Tool**: ReAct agent tool implementation; has name, description, enabled/disabled status, execution timeout, usage statistics (call count, avg execution time, error rate)
- **ToolExecution**: Audit log of ReAct tool invocation; has timestamp, user_id, conversation_id, tool_name, input_parameters (sanitized), output_result (truncated), execution_time_ms, success/failure status
- **Agent**: Specialized AI agent for Multi-Agent system; has name (e.g., CitizenSupportAgent), description, system prompt template, enabled/disabled status, routing keywords, performance metrics
- **AgentWorkflow**: Record of Multi-Agent workflow execution; has workflow_id, user_id, conversation_id, orchestrator_decision (which agents/sequence), start_time, end_time, total_execution_time, success/failure status
- **AgentWorkflowStep**: Individual agent execution within a workflow; has workflow_id, agent_name, step_number, input_summary, output_summary, execution_time_ms, status, links to parent AgentWorkflow
- **AuditLog**: Centralized audit trail for all advanced features; has timestamp, user_id, action_type (filter/tool/agent), action_details (JSON), result, execution_time_ms, queryable by administrators
- **MetricSnapshot**: Represents a point-in-time capture of system metrics (Feature 002); contains timestamp, metric type (active_users/storage_bytes/conversations/documents/tags/sessions), value, granularity (hourly/daily), retry_count; used for time-series graphing and trend analysis
- **MetricCollectionFailure**: Records failed metric collection attempts; contains timestamp, metric_type, error_message, retry_count; helps administrators monitor data collection health and troubleshoot issues

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a query and receive a relevant response within acceptable time for queries under 500 characters:

  **CPU-only baseline** (llama.cpp + Qwen3-4B-Instruct GGUF Q4_K_M):
  - **Test hardware specification**:
    - Minimum: Intel Xeon E5-2680 v4 (14 cores @ 2.4GHz) or AMD EPYC 7302 (16 cores @ 3.0GHz)
    - Recommended: Intel Xeon Gold 6248R (24 cores @ 3.0GHz) or AMD EPYC 7543 (32 cores @ 2.8GHz)
    - RAM: 32GB minimum, 64GB recommended
    - CPU features: AVX2, FMA, F16C support (verified via `lscpu` on Linux or `Get-WmiObject Win32_Processor` on Windows)
  - **Performance targets**:
    - Target: 8 seconds P50 (median)
    - Maximum acceptable: 12 seconds P95 (95th percentile)
  - **Validation**: T037A task must document actual hardware used + measured performance

  **GPU-accelerated environment** (vLLM + Qwen3-4B-Instruct safetensors):
  - **Test hardware**: NVIDIA RTX 3090 (24GB) or A100 (40GB)
  - Target: 3 seconds P50, maximum 8 seconds P95
  - **Note**: Phase 13 optional upgrade

  **Model variants**:
  - Primary: Qwen3-4B-Instruct (~2.5GB Q4_K_M)
  - Fallback: Qwen2.5-1.5B-Instruct (~1GB Q4_K_M) for resource-constrained systems

  **Rationale**: CPU-only deployment prioritizes availability over performance (Assumption #2, Constitution Principle IV). Government procurement typically includes 16+ core Xeon/EPYC servers suitable for this workload.
- **SC-002**: System supports at least 10 concurrent users without response time degradation exceeding 20% (baseline: single-user average 5 seconds per SC-001, target: ≤6 seconds with 10 concurrent users)
- **SC-003**: Users can upload and process a 20-page PDF document within 60 seconds
  - **측정 방법**:
    1. 테스트 문서: 20페이지 한글 PDF (A4 크기, 평균 500자/페이지, ~10,000자 총계)
    2. 측정 구간: 파일 선택 후 "업로드" 버튼 클릭 → "문서 분석 완료" 메시지 표시까지
    3. 처리 단계: 파일 업로드(HTTP) + PDF 텍스트 추출(pdfplumber) + 청킹(500자 단위) + 벡터 임베딩(sentence-transformers) + ChromaDB 저장
    4. 합격 기준: 5회 반복 측정의 중앙값(P50)이 60초 이하
  - **테스트 도구**: `scripts/test-document-upload-performance.py` (Phase 7 추가 예정)
- **SC-004**: 한국어 쿼리의 90%가 문법적으로 정확하고 맥락적으로 적절한 응답을 받음
  - **측정 방법**: 50개 다양한 업무 시나리오 쿼리로 구성된 테스트 세트 사용
  - **평가 기준**: 각 응답을 3가지 차원으로 수동 채점 (각 0-10점)
    1. 문법 정확성: 맞춤법, 조사 사용, 문장 구조
    2. 질문 관련성: 질문에 대한 답변 적절성
    3. 한국어 자연스러움: 어색한 번역체 없이 자연스러운 표현
  - **채점자**: 2-3명의 공무원(또는 한국어 원어민)이 독립적으로 채점
  - **Inter-rater reliability**: 동일 응답에 대한 채점자 간 점수 차이가 3점 이상인 경우 재협의 후 평균 점수 사용
  - **합격 기준**: 50개 쿼리 중 45개 이상이 총 30점 만점에 24점 이상 (90.0% 합격률, 80% 점수)
  - **테스트 도구**: `scripts/test-korean-quality.py` (채점 인터페이스 제공, 점수 수집 및 통계 계산)
  - **데이터셋 생성**: Phase 12 (T238 실행 전), 2-3명의 공무원 또는 한국어 원어민이 50개 다양한 업무 시나리오 쿼리 작성 (민원 처리, 문서 작성, 정책 질문, 일정 계산 등), `backend/tests/data/korean_quality_test_dataset.json`에 저장
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
  - **합격 기준**: 10개 대화 중 9개 이상(90.0%)이 모든 메시지를 데이터베이스에 보존하고, 재개 후 질문이 이전 맥락 반영한 답변 생성
    - 참고: "95% 정확도"는 컨텍스트 보존의 품질 목표를 의미하며, 실제 테스트 합격률은 10개 중 9개(90.0%)로 측정 (SC-004와 동일한 합격률 기준 적용)
  - **테스트 도구**: `scripts/test-context-preservation.py` (Phase 8 추가 예정)
- **SC-008**: Zero unauthorized access incidents to other users' conversations or documents during testing period
- **SC-009**: 85% of employees can complete their first query and receive a response without requiring assistance or training
- **SC-010**: System operates continuously for 30 days in air-gapped environment without requiring external updates or connectivity
- **SC-011**: Administrators can create a new user account in under 1 minute
- **SC-012**: Usage statistics dashboard loads within 3 seconds and displays accurate data
- **SC-013**: System health metrics update in real-time with maximum 30-second delay
- **SC-014**: Safety filter processes user input and AI output within 2 seconds per check, with 95%+ accuracy on test dataset of 100 samples (containing 50 inappropriate samples across 5 categories + 50 legitimate government queries)
  - **Measurement**: Create labeled test dataset, run through safety filter, calculate precision (% of flagged content that is actually inappropriate) and recall (% of inappropriate content that is correctly flagged)
  - **Pass criteria**: Precision ≥90% (minimize false positives), Recall ≥95% (catch inappropriate content), Total processing time ≤2 seconds per message
- **SC-015**: PII masking correctly identifies and masks 100% of standard format personal information (주민등록번호 with dash, phone numbers with/without dashes, email addresses) in test dataset of 50 examples
  - **Measurement**: Create test messages with known PII patterns, verify all are masked correctly
  - **Pass criteria**: 50/50 patterns correctly masked, with masked format preserving structure (e.g., 123456-******* for SSN)
- **SC-016**: ReAct agent completes multi-step tasks requiring 2-3 tool invocations within 30 seconds, with clear step-by-step display visible to user
  - **Test scenario**: "2023년 예산 1,500만원에 5% 증가율을 적용하고, 2024년 회계연도 기준으로 집행 기한을 계산해줘" (requires calculator tool + date tool)
  - **Pass criteria**: Correct final answer, both tools executed successfully, Thought/Action/Observation steps displayed, total time ≤30 seconds
- **SC-017**: All six ReAct tools execute successfully with <10% error rate across 100 test invocations (mix of valid and edge case inputs)
  - **Measurement**: Execute each tool 15-20 times with varied inputs, track success/failure
  - **Pass criteria**: Document Search ≥90% success, Calculator ≥95% success (deterministic), Date/Schedule ≥90%, Data Analysis ≥85% (depends on file format), Document Template 100% (deterministic), Legal Reference ≥90%
- **SC-018**: Multi-agent orchestrator correctly routes user queries to appropriate agent with 85%+ accuracy on test dataset of 50 queries (10 per agent type)
  - **Measurement**: Create labeled queries (e.g., "민원 답변 작성해줘" → Citizen Support Agent), run through orchestrator, compare predicted agent vs. expected agent
  - **Pass criteria**: 43/50 queries routed correctly (85%+), misrouted queries still provide reasonable responses via fallback
- **SC-019**: Multi-agent workflows complete sequential 3-agent tasks (e.g., Legal Research → Document Writing → Review) within 90 seconds with all agents contributing successfully
  - **Test scenario**: "주차 관련 조례를 검색하고, 민원 답변 초안을 작성하고, 검토해줘"
  - **Pass criteria**: All 3 agents execute in order, outputs clearly attributed, total time ≤90 seconds, final combined response meets quality standards
- **SC-020**: 모든 고급 기능(안전 필터, ReAct, 멀티 에이전트)이 폐쇄망 환경에서 외부 네트워크 연결 없이 정상 작동 (Air-gapped Functionality Test)
  - **측정 방법**:
    1. 테스트 서버의 모든 외부 네트워크 인터페이스 비활성화 (물리적 단선 또는 iptables로 차단)
    2. 각 고급 기능의 대표 시나리오 실행 (안전 필터: 부적절한 내용 차단, ReAct: 도구 3개 사용, 멀티 에이전트: 2-agent 워크플로우)
    3. 모든 시나리오가 성공적으로 완료되는지 확인 (타임아웃, 네트워크 오류 없음)
  - **합격 기준**: 3개 고급 기능 모두 외부 네트워크 없이 정상 동작, 모델 로딩 시간 ≤60초, 기능 실행 시간 정상 범위 내
- **SC-021**: Administrators can view 7 days of historical metrics within 2 seconds of loading the dashboard (Feature 002: Metrics History)
- **SC-022**: System successfully collects metrics at configured intervals with 99% reliability (no more than 1% missed collections)
- **SC-023**: Metric collection completes within 5 seconds and does not impact concurrent user operations
- **SC-024**: Administrators can identify trends (increasing/decreasing patterns) within 30 seconds of viewing a metric graph
- **SC-025**: 90% of administrators successfully export metrics data on first attempt without assistance
- **SC-026**: System maintains metric history for 90 days without data loss or corruption
- **SC-027**: Dashboard graphs render any time range within 3 seconds through automatic downsampling (maximum 1000 rendered points)
- **SC-028**: CSRF protection blocks unauthorized state-changing requests with 100% effectiveness: POST/PUT/DELETE requests without X-CSRF-Token header return 403, requests with mismatched CSRF token (cookie ≠ header) return 403, login and setup endpoints function correctly without CSRF token, frontend receives CSRF token in cookie and includes in subsequent requests
- **SC-029**: Middleware enforcement prevents resource exhaustion: 61st API request within 1 minute from same IP returns 429 Too Many Requests, 11th concurrent ReAct session returns 503 Service Unavailable, response headers include X-RateLimit-Limit and X-RateLimit-Remaining, performance metrics are logged for endpoints with >1 second response time
- **SC-030**: Session tokens are protected from interception: production environment cookies have secure=True and samesite=strict flags, development environment cookies have secure=False and samesite=lax, session tokens in application logs are masked as "***REDACTED***" with 100% coverage, session cookies expire after exactly 30 minutes (max_age=1800)
- **SC-031**: Metric data maintains transactional consistency: all 6 metrics collected in same cycle have identical collected_at timestamp (microsecond precision), database connections use READ COMMITTED isolation level, metric dashboard shows mathematically consistent relationships (e.g., active_sessions ≤ active_users × 3 per FR-030), collection transaction logs show <5ms variance between first and last metric within same cycle
- **SC-032**: CSV exports display Korean text correctly across platforms: Windows Excel opens CSV without encoding selection dialog and displays Korean characters correctly, LibreOffice on Linux displays Korean characters correctly, Python pandas.read_csv() parses column names without BOM artifacts (first column name starts with expected text, not '\ufeff' prefix), User-Agent detection achieves >95% accuracy distinguishing Windows from non-Windows clients
- **SC-033**: Korean UI text displays without corruption: frontend error messages show correct Korean characters (no ������ or mojibake), browser DevTools console.log(errorMessages) output shows readable Korean, automated regex test passes for all errorMessages values matching Korean Unicode range [\uAC00-\uD7A3], git diff shows UTF-8 encoding for all .ts/.tsx files
- **SC-034**: Active user metrics match actual session state: active_users count equals number of Session records where expires_at > now (UTC), manual comparison of metrics dashboard value vs direct database query shows 100% match, timezone-aware datetime objects used in all metric calculations (verified by debug logs showing "+00:00" suffix)
- **SC-035**: Async database queries appear in Prometheus /metrics: db_queries_total{query_type="select",status="success"} shows non-zero count after making API requests, db_query_duration histogram shows data for all query types (select/insert/update/delete), connection pool metrics db_connections_active reflects actual async connection usage
- **SC-036**: Administrator privilege checks are consistent: all admin-only endpoints use same privilege verification method (either User.is_admin flag OR Admin table lookup, not mixed), attempting to access /admin/users as non-admin returns 403 Forbidden with correct error message, admin audit log shows who performed admin actions with 100% accuracy
- **SC-037**: CSRF tokens remain stable within session: logging in once generates single CSRF token, making 10 GET requests returns same CSRF token value in cookie (no rotation), CSRF token expires after exactly 30 minutes matching session timeout, token regeneration only occurs on login or expiration (verified by server logs showing <5 token generation events per user session)
- **SC-038**: CSRF exemption supports common paths: /docs and /openapi.json accessible without CSRF token, /api/v1/setup and all sub-routes (/api/v1/setup/init, /api/v1/setup/complete) work without token, Prometheus /metrics endpoint works without authentication or CSRF token, documented list of all exempt paths accessible in code comments
- **SC-039**: Security tests match implementation: tests/security_audit.py password hashing test passes using bcrypt.hashpw(), bcrypt rounds set to 12 per FR-029, integration test successfully logs in with hashed password via /api/v1/auth/login endpoint, no import errors for passlib (not used in implementation)
- **SC-040**: Data isolation prevents unauthorized access: user A cannot access user B's conversations/documents/messages (403 Forbidden returned), admin attempting to read user message content receives appropriate restriction (can view metadata only per FR-032), middleware or dependency-level isolation verified by automated security test suite passing 100% of ownership validation tests

## Assumptions

This specification is based on the following assumptions:

1. **Network Environment**: The local government has an internal network infrastructure that supports web applications, even though it's isolated from the internet
2. **Hardware Resources**: Server hardware meeting minimum specifications is available:
   - **CPU** (Required): 8-core Intel Xeon or equivalent minimum, 16-core recommended for production. CPU-only deployment is the baseline configuration with acceptable performance (8-12 seconds response time per SC-001) using Qwen2.5-1.5B-Instruct (~1GB Q4_K_M) or future Qwen3-4B-Instruct (~2.5GB Q4_K_M)
   - **RAM** (Required): 32GB minimum, 64GB recommended for production
   - **GPU** (Optional): NVIDIA RTX 3090 or A100 with 16GB+ VRAM and CUDA support for acceleration. GPU improves response time (3-8 seconds) and concurrent user capacity (10-16 users vs. 1-3 on CPU), but is NOT required for initial deployment
   - **Storage** (Required): 500GB+ SSD for OS/app/data, NVMe SSD 1TB recommended
   - **Network** (Required): Internal Gigabit Ethernet
3. **User Devices**: Government employees have access to computers with supported browsers (Chrome 90+, Edge 90+, Firefox 88+, minimum 1280x720 resolution, JavaScript enabled). Internet Explorer is not supported.
4. **Data Sensitivity**: While the environment is air-gapped for security, the specific classification level of data that can be processed is not defined
5. **LLM Capabilities**: **Qwen2.5-1.5B-Instruct** will be used for initial implementation (verified available, ~1GB Q4_K_M quantization), providing Korean language support when deployed via HuggingFace Transformers or llama.cpp with 4-bit quantization (CPU-compatible). **Future upgrade path**: Qwen3-4B-Instruct (April 2025 release, ~2.5GB memory footprint, Qwen2.5-72B-level performance with 20-40% improvement in math/coding) when verified available. Both models support CPU-only deployments with acceptable latency (8-12 seconds per SC-001)
6. **User Volume & Storage**: "Small local government" implies approximately 10-50 employees who might use the system. Storage provisioning assumes 10GB per user (500GB total for 50 users), with monthly growth of 1-5GB total. Administrators responsible for storage expansion when capacity warnings occur.
7. **Authentication**: Basic username/password authentication is sufficient; advanced methods like SSO or multi-factor authentication are not required
8. **Maintenance**: Technical staff are available to perform system maintenance, updates, and user management on the local server
9. **Document Scope**: Documents processed are primarily administrative in nature (policies, reports, memos) rather than specialized technical documents
10. **Response Quality**: Users understand that local LLM responses may not match the quality of cloud-based services like ChatGPT but value the security and availability tradeoffs
11. **File Size Limits**: Document uploads will be limited to 50MB per file as a reasonable default for administrative documents

## Dependencies

- Local server infrastructure with CPU-based deployment as baseline (8-core minimum, 16-core recommended), GPU optional for acceleration (NVIDIA RTX 3090/A100 for improved performance)
- **LLM Model**:
  - **Primary Model**: Qwen3-4B-Instruct
    - HuggingFace: `Qwen/Qwen3-4B-Instruct`
    - Size: ~2.5GB Q4_K_M GGUF quantization
    - Korean support: Excellent (Qwen2.5-72B-level performance)
    - Format: HuggingFace Transformers + BitsAndBytes 4-bit quantization OR llama.cpp GGUF
    - Performance: 20-40% improvement over Qwen2.5-1.5B in math/coding tasks
  - **Fallback Model (Resource-Constrained)**: Qwen2.5-1.5B-Instruct
    - HuggingFace: `Qwen/Qwen2.5-1.5B-Instruct`
    - Size: ~1GB Q4_K_M GGUF quantization
    - Use case: Systems with limited RAM (<16GB) or storage constraints
- Vector database (ChromaDB or FAISS) with embedding model for document semantic search
- **Embedding model**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, **default fp32 variant**, ~420MB, supports Korean, CPU-compatible) pre-downloaded for offline installation using `huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --local-dir ./models/embeddings/`, used for both document Q&A (FR-009) and tag auto-matching (FR-043). **Note**: For air-gapped deployment, download includes all files in model repository (pytorch_model.bin, config.json, tokenizer files)
- **Safety Filter Dependencies**:
  - Lightweight toxic content classification model (HuggingFace: `unitary/toxic-bert`, ~400MB, multilingual including Korean, CPU-compatible) pre-downloaded from HuggingFace for offline installation
  - Regex pattern library for PII detection (주민등록번호, phone, email patterns)
  - Optional: sentence-transformers for advanced PII entity recognition if rule-based insufficient
- **ReAct Agent Dependencies**:
  - Korean public holiday calendar (JSON file) for Date/Schedule tool
  - Government document templates (공문서, 보고서 templates in Jinja2 format) stored in `/templates` directory
  - Python libraries: pandas (data analysis), openpyxl (Excel support), sympy or numexpr (calculator)
- **Multi-Agent System Dependencies**:
  - Agent prompt templates (stored as text files in `/prompts` directory for each specialized agent) - **Phase 10 mandatory**
  - Agent-specific LoRA adapter weights: **Phase 14 only if activated per FR-071A** - 5 fine-tuned adapters (~100-500MB each) for Citizen Support, Document Writing, Legal Research, Data Analysis, Review agents optimized for Qwen2.5-1.5B-Instruct (current) or Qwen3-4B-Instruct (future upgrade), pre-downloaded and stored in `/models/lora_adapters/` directory structure
  - HuggingFace PEFT (Parameter-Efficient Fine-Tuning) library for LoRA adapter loading and management (CPU-compatible) - **Phase 14 only if activated per FR-071A**
  - Orchestrator routing configuration: LLM-based few-shot prompt file with **2 example queries per agent** (≤1000 token budget per FR-070) + brief descriptions (default), keyword patterns stored in database or config file (alternative mode)
- Separate storage volume for backups (minimum 1TB recommended, separate from system disk for redundancy)
- Internal network with stable connectivity between employee workstations and the application server
- Browser compatibility with modern web standards for the user interface
- IT staff access to the server for initial deployment, ongoing maintenance, and configuration of advanced features (filter rules, agent settings)
- **Metrics History Dependencies** (Feature 002):
  - APScheduler 3.10+ for background task scheduling (metric collection)
  - pandas 2.1+ for CSV data processing and export
  - ReportLab 4.0+ for PDF report generation
  - Chart.js + react-chartjs-2 for frontend time-series visualization
  - PostgreSQL with sufficient storage for metric history (estimated ~100KB per day, ~3.65MB per year for 6 metrics)
  - LTTB (Largest Triangle Three Buckets) algorithm implementation for data downsampling

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
- **Metrics History Out of Scope** (Feature 002):
  - Predictive analytics or forecasting based on historical trends
  - Real-time streaming metric updates (refresh rate faster than dashboard reload)
  - Per-admin customizable dashboards or personalized metric views
  - Metric alerting, notifications, or threshold-based triggers
  - Integration with external monitoring tools (Prometheus, Grafana, etc.) - Note: Prometheus/Grafana were added separately for performance monitoring, not business metrics
  - User-level metrics (tracking individual user behavior over time)
  - Audit trail for who viewed which metrics when
  - Mobile-optimized metric viewing interface
  - Multi-timezone support for distributed admin teams (assumes single-location deployment)
  - Individual metric drill-down (clicking graph to see detailed breakdown)
