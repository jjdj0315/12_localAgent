# Feature Specification: Local LLM Web Application for Local Government

**Feature Branch**: `001-local-llm-webapp`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "소규모 지방자치단체 공무원 대상, 폐쇄망 환경에서 이용 가능한 Local LLM 웹 애플리케이션 서비스를 구축한다. 이는 ChatGPT, Gemini와 같은 외부 에이전트의 사용이 제한되는 환경에서 업무 지원용 LLM 기반 도구를 제공하기 위함이다."

**Overview**: Air-gapped Local LLM web application for small local government employees using **Qwen3-4B-Instruct** (~2.5GB Q4_K_M quantization, Qwen2.5-72B-level performance) to provide AI assistance for administrative tasks without internet connectivity. Optional fallback to Qwen2.5-1.5B-Instruct (~1GB) for resource-constrained environments.

## Clarifications

### Session 2025-10-28

- Q: Document Q&A implementation strategy - should we use simple text extraction or vector embeddings for document analysis? → A: Vector embeddings + similarity search (Qdrant vector database) to properly support multi-document comparison and accurate source references (User Story 3, Acceptance Scenarios 2 & 4)
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
- Q: 전문 Agent 도구 실패 시 사용자 경험 - 도구 실행 실패 시 사용자에게 어떻게 보여줄지? → A: Transparent failure - 도구 실패 내용을 명확히 표시(예: "문서를 찾을 수 없습니다"), AI Agent가 대안 시도 또는 명확한 안내 제공. 실패를 숨기지 않고 사용자에게 투명하게 전달 (FR-065, User Story 7 Acceptance Scenario 9)
- Q: Orchestrator 기본 라우팅 모드 - keyword-based와 LLM-based 중 시스템 기본 모드는? → A: LLM-based 기본 - Few-shot 예시 기반으로 더 정확한 의도 파악, 새로운 질문 패턴에 유연 대응. Keyword-based는 관리자가 성능 최적화 시 전환 가능 (FR-066, User Story 7)
- Q: LLM-based Orchestrator 프롬프트 전략 - LLM이 6개 Agent + 일반응답 중 선택하도록 하는 구체적 방법은? → A: Few-shot 예시 기반 - 각 Agent별 2-3개 대표 질문 예시를 프롬프트에 포함, 간결한 Agent 설명과 함께 제공. 토큰 효율적이면서 높은 정확도 유지 (FR-066, Dependencies)
- Q: LoRA adapter 동시 사용 전략 - 여러 사용자가 동시에 다른 Agent 호출 시 메모리 관리는? → A: LRU 캐싱 - 최근 사용한 2-3개 LoRA adapter를 메모리에 유지(~500MB-1.5GB 추가), 나머지는 디스크에서 동적 로딩(<3초). 메모리 효율과 응답 속도 밸런스 유지 (FR-070, User Story 7 Acceptance Scenario 8)

### Session 2025-11-02

- Q: LoRA 파인튜닝 학습 데이터 수집 전략 - Specialized Agent 시스템(Phase 10)에서 6개 Agent별 LoRA adapter 학습에 필요한 데이터를 어떻게 수집해야 하나요? → A: 2단계 접근 - Phase 10에서는 LoRA 로딩 인프라만 구현 (identity LoRA 또는 랜덤 초기화), 프롬프트 엔지니어링으로 Agent 동작. Phase 14에서 학습 데이터 수집 (Agent별 500-1000 샘플, 총 3000-6000) + 파인튜닝 진행. Constitution Principle IV (Simplicity Over Optimization) 준수 (FR-070, FR-071)

### Session 2025-11-04

- Q: 한국어 품질 테스트 합격 기준 반올림 - SC-004에서 "90% 이상의 쿼리"가 50개 중 45개(90.0%) vs 44개(88%)인지 불명확. 정확한 합격 개수는? → A: 정확한 개수: 50개 중 45개 이상 합격 (90.0%) - 테스트 재현성과 명확성을 위해 정확한 숫자 기준 사용 (SC-004)
- Q: 문서 생성 모드 키워드 매칭 전략 - FR-017에서 "문서 작성", "초안 생성" 등 키워드 감지 방식이 정확 매칭인지, 부분 매칭 허용인지, LLM 의도 파악인지 불명확. 어떤 전략을 사용하는가? → A: 정확 매칭 (exact substring matching) - 사용자 쿼리에 정의된 키워드 전체가 포함될 경우에만 문서 생성 모드 활성화. 예: "문서 작성해줘" (O), "문서 검색" (X), "초안 생성 부탁" (O), "초안" (X). 오탐지(false positive) 방지 및 예측 가능한 동작 보장 (FR-017, T225A)

### Session 2025-11-05

- Q: Specialized Agent 시스템 아키텍처 변경 - ReAct Agent와 Multi-Agent 구조를 폐지하고 새로운 구조로 전환하는 이유는? → A: 메모리 효율성과 전문성 강화 - Base 모델 1개만 로드하고 Agent별 LoRA를 동적으로 교체하는 방식으로 메모리 사용량 감소 (~2.5GB base + 최대 1.5GB LoRA 캐시 vs 기존 방식). 각 Agent가 전용 LoRA + 템플릿 + 도구를 활용하여 도메인 전문성 향상 (User Story 7)
- Q: RAG(문서 검색) 기능을 별도 Agent로 분리하는 이유는? → A: 전문화된 문서 분석 - 기존 FR-009의 기본 RAG 기능을 전문 RAG Agent로 승격하여 문서 검색/분석에 특화된 LoRA adapter 적용. 복잡한 문서 비교, 다중 문서 추론, 정확한 출처 인용 등 고급 RAG 기능 제공 (FR-068)
- Q: Base 모델 공유 방식 - 6개 Agent가 동일한 base 모델을 어떻게 공유하나? → A: LoRA adapter 동적 교체 - Base 모델(Qwen3-4B-Instruct)은 startup 시 1회만 로드. 각 Agent 호출 시 해당 Agent의 LoRA adapter만 로드/언로드. LRU 캐싱으로 최근 사용 2-3개 adapter를 메모리에 유지하여 스왑 오버헤드 최소화 (<3초) (FR-070)
- Q: Phase 10과 Phase 14의 LoRA 역할 차이는? → A: Phase 10(구조), Phase 14(학습) - Phase 10에서는 LoRA 로딩 인프라(PEFT 라이브러리, adapter 관리, 캐싱)만 구현하고 identity LoRA 또는 프롬프트만 사용. Phase 14에서 학습 데이터 수집(Agent별 500-1000 샘플) + 실제 파인튜닝 진행하여 성능 향상 (FR-071)

### Session 2025-11-07

- Q: Reasoning Path에서 의도 명확화가 실패한 경우(예: LLM 타임아웃, JSON 파싱 오류, 분석 후에도 여전히 애매함) 시스템이 어떻게 동작해야 할까요? → A: Direct 경로로 라우팅하며 명시적 메시지 표시 - "요청을 명확히 파악하지 못했습니다. 구체적으로 알려주세요: [무엇을/어떤/언제]?" 형식으로 사용자에게 안내하여 대화 흐름 유지하면서 투명하게 상황 전달 (FR-132)
- Q: Specialized Path에서 agent 선택이 실패한 경우(예: 의도 분석 결과 agent_type이 null이거나 잘못된 agent 이름) 시스템이 어떻게 동작해야 할까요? → A: Direct path로 폴백하여 base LLM이 직접 처리 - 사용자에게 "일반 모드로 처리합니다" 알림 표시, 실패 로그 기록하여 classification 정확도 개선에 활용 (FR-133)
- Q: Unified Orchestrator의 classification 정확도가 어느 수준에 도달해야 production 배포가 가능한가요? → A: 85% 정확도 달성 + 2주일 모니터링 - 라벨링된 테스트 세트(100개 쿼리)에서 85% 이상 정확도 달성, 2주간 실사용 모니터링으로 회귀 없음 확인 후 배포 (SC-046 기준 활용, FR-135)
- Q: FR-132에서 LLM clarification timeout을 2초로 명시했는데, LLM 서비스 호출 실패 시 재시도 정책은 어떻게 되나요? → A: 최대 3회 재시도 + 지수 백오프 - 100ms → 200ms → 400ms 간격으로 재시도, 총 2초 타임아웃 내에서 실행, 모든 재시도 실패 시 Direct path로 폴백 (FR-132)
- Q: 여러 사용자가 동시에 Unified Orchestrator를 호출할 때 전체 시스템 동시 실행 제한은 얼마인가요? → A: 사용자당 1개 요청 + 전체 동시 실행 제한 50 - 사용자가 이미 처리 중인 요청이 있으면 429 응답, 전체 50개 초과 시에도 429 응답, 대기열(queue) 없음 (FR-135)

### Session 2025-11-08

- Q: 관리자 권한 검증을 위한 단일 진실 공급원(Single Source of Truth)으로 어떤 방법을 사용해야 하나요? → A: Admin 테이블 존재 확인 (Option B) - 정규화된 구조로 권한 관리를 분리하고 감사 추적을 강화. FR-033의 "별도 테이블" 의도와 일치하며 향후 관리자 역할 확장 시 설계 유연성 제공. get_current_admin()는 Admin 테이블 레코드 존재 여부로 검증, User.is_admin 플래그는 마이그레이션 스크립트로 동기화 후 참조용으로만 유지 (FR-118, FR-033)
- Q: Reasoning 경로가 의도를 명확히 하기 위해 컨텍스트를 수집하는 도구를 호출할 수 있나요(예: "어떤 문서?" 질문 전 사용 가능한 문서 확인), 아니면 엄격하게 프롬프트 기반 분석만 사용하나요? → A: 엄격한 프롬프트 기반 (Option A) - Reasoning 경로는 도구 호출 없이 사용자 쿼리에 대한 LLM 분석만 수행. Reasoning과 Specialized 경로 간 명확한 분리 유지로 아키텍처 단순화, 응답 속도 향상 (1-3초 목표). 컨텍스트 수집이 필요한 경우 Specialized 경로로 라우팅. Constitution Principle IV (단순성 우선) 준수 (FR-132)
- Q: 전체 50개 동시 실행 제한이 모든 경로 유형을 동등하게 처리해야 하나요, 아니면 리소스 소비에 따라 가중치를 부여해야 하나요(예: Specialized 경로는 2배 리소스 단위로 계산, Direct는 1배)? → A: 동등한 카운팅 (Option A) - 모든 경로(Direct/Reasoning/Specialized)가 복잡도와 관계없이 50개 제한에 대해 1로 계산. 구현 단순화 및 예측 가능한 동작 보장. 사용자당 1개 활성 요청 제한(FR-135)으로 개별 남용 방지 이미 확보. 경로별 성능 차이는 응답 시간 목표로 관리. Constitution Principle IV (단순성 우선) 준수 (FR-135)
- Q: LoRA 활성화 결정을 위한 "Response Quality" (응답 품질)를 어떻게 측정해야 하나요? (FR-068 Phase 14: 복합 점수 = 응답 품질 50% + 응답 시간 30% + 작업별 정확도 20%, LoRA는 복합 개선 ≥10% AND 품질 개선 ≥5%일 때만 계속 사용) → A: 자동화 메트릭 (Option B) - 참조 답변 대비 BLEU/ROUGE 점수 사용. 각 Agent별 테스트 세트(50-100 쿼리)에 참조 답변 준비, BLEU-4 및 ROUGE-L 점수 평균으로 품질 측정. 재현 가능하고 일관된 측정, 인간 개입 없이 자동 평가 가능. Constitution Principle IV (단순성 우선) 준수 (FR-068, FR-071)
- Q: 메트릭 수집이 단일 트랜잭션(모두 성공 또는 모두 실패)을 사용해야 하나요, 아니면 메트릭별 개별 트랜잭션(부분 성공 허용)을 사용해야 하나요? → A: 단일 트랜잭션, 모두-아니면-아무것도 (Option A) - 모든 6개 메트릭을 단일 트랜잭션 내에서 수집하여 동일한 collected_at 타임스탬프 보장. 개별 메트릭 계산 실패 시 전체 트랜잭션 롤백하고 metric_collection_failures 테이블에 실패 기록, 다음 수집 주기에서 전체 재시도. 데이터 일관성 우선 - 부분적 스냅샷보다 완전한 스냅샷의 무결성이 더 중요. 타임스탬프 동기화로 정확한 시계열 분석 보장 (FR-113)

### Session 2025-11-10

- Q: UnifiedAgentState 생명주기 관리 - 상태 객체가 LangGraph 실행 중에 생성되고 노드 간 전달되는데, 실행 완료 후 메모리 해제는 언제/어떻게 수행되어야 하나요? → A: After finalize node completion (explicit cleanup in _finalize_node) - finalize 노드 완료 후 명시적으로 정리. _finalize_node()에서 state 딕셔너리의 대용량 필드(retrieved_documents, tool_results, intermediate_steps 등)를 del로 명시적 삭제, state 자체는 LangGraph가 invoke() 반환 후 Python GC가 자동 해제, 메모리 누수 방지 및 명시적 리소스 관리 (FR-129, FR-135)
- Q: Reasoning 경로 후속 라우팅 - Reasoning 경로에서 의도를 명확화한 후 direct/specialized 재라우팅이 자동으로 이루어지나요, 아니면 사용자 확인이 필요한가요? → A: 자동 재라우팅 (추론 기반, Option A) - Reasoning 노드가 의도 분석 결과를 기반으로 direct/specialized 중 하나를 자동 선택하여 즉시 실행. 한 번의 쿼리 → 한 번의 응답 (1회 왕복)으로 FR-132의 1-3초 응답 시간 목표 충족. 의도 오해석 시 Direct path 폴백 + 명시적 메시지로 대응. Constitution Principle IV (단순성 우선) 준수 (FR-132)
- Q: Database Connection Pool 크기 설정 - Gunicorn 멀티프로세스 환경(4 workers)에서 PostgreSQL 연결 풀 크기를 어떻게 설정해야 하나요? → A: Worker당 5개 연결 (균형적, Option B) - SQLAlchemy pool_size=5, max_overflow=10 (worker당), 4 workers × (5+10) = 60개 최대 연결, PostgreSQL max_connections=80 (시스템 연결 +20 여유). FR-135의 50개 동시 실행 제한과 조화 (50÷4=12.5 < 15), 메모리 효율적 (~600MB 연결 오버헤드), Constitution Principle IV (단순성 우선) 준수 (FR-123, FR-126, FR-135)
- Q: 저장 공간 정리 부분 실패 처리 - 자동 정리 중 일부 단계가 실패하면 (예: PostgreSQL 삭제 성공 → Qdrant 벡터 삭제 실패) 어떻게 처리해야 하나요? → A: 최선 노력 (Best Effort) + 재시도 (Option B) - PostgreSQL 대화 삭제 먼저 커밋, Qdrant 벡터 삭제 시도 (최대 3회 재시도), 실패 시 cleanup_failures 테이블에 기록하여 다음 정리 주기에서 재시도. 부분 성공 허용으로 외부 서비스 장애가 전체 정리 차단하지 않음, 점진적 정합성(eventual consistency)으로 고아 벡터는 다음 주기에서 정리. PostgreSQL 삭제만으로도 사용자 저장 공간 계산에서 제외. Constitution Principle IV (단순성 우선) 준수 (FR-019, FR-020)
- Q: Production 배포 모니터링 기준 - 2주일 production 모니터링 기간 동안 어떤 메트릭을 추적하고, 배포 성공/실패를 어떻게 판단해야 하나요? → A: 복합 메트릭 (Balanced, Option B) - 4가지 메트릭 일별 추적: (1) Classification 정확도 (≥85%), (2) 응답 시간 P95 (경로별 목표: direct <1.5s, reasoning <3s, specialized <15s), (3) 에러율 (500/429 응답 <1%), (4) 경로별 분포 안정성 (일별 변동 <20%). 합격 기준: 모든 메트릭이 14일 중 12일 이상 목표 달성 + 단일 날짜에 2개 이상 메트릭 목표 미달 발생하지 않음. 기존 metric_snapshots 테이블 확장하여 orchestrator 메트릭 추가. 종합적 품질 보증 + 조기 문제 감지 + Constitution Principle IV 준수 (FR-135)
- Q: Redis 장애 시 Rate Limiting 동작 - Redis 장애로 Rate Limit 카운터를 확인할 수 없을 때, 요청을 허용해야 하나요(fail-open) 차단해야 하나요(fail-closed)? → A: Fail-Open (요청 허용, 가용성 우선, Option A) - Redis 장애 시 Rate Limiting 검사 건너뛰고 요청 처리, 로그 경고 메시지 기록. FR-001 폐쇄망 환경에서 외부 공격자 접근 불가, 신뢰된 사용자(지자체 공무원)만 사용으로 DDoS 위협 낮음. FR-125 Graceful Degradation 철학과 일치하여 가용성 우선. Redis 장애 로그로 관리자 빠른 복구 가능. Constitution Principle IV (단순성 우선) 준수 (FR-124, FR-125)
- Q: Redis 연결 풀 크기 설정 - Gunicorn 멀티프로세스 환경(4 workers)에서 Redis 연결 풀 크기를 어떻게 설정해야 하나요? → A: Worker당 5개 연결 (경량 작업 고려, Option B) - redis-py ConnectionPool max_connections=5 (worker당), 4 workers × 5 = 20개 최대 연결. Redis 작업이 PostgreSQL보다 100배 빠름 (GET/SET/INCR: 0.1ms vs SELECT: 10ms)으로 높은 연결 재사용률. 메모리 효율적 (~20MB), 충분한 처리량 (5개 연결/worker × 10,000 ops/s/connection = 50,000 ops/s/worker). Constitution Principle IV (단순성 우선) 준수 (FR-126)
- Q: Redis Memory Eviction 우선순위 - Redis 메모리가 512MB 한도에 도달했을 때, Rate Limit 카운터와 LLM Cache 중 어떤 데이터를 우선 보호해야 하나요? → A: 동등한 LRU (현재 설정 유지, Option B) - 모든 데이터 단일 Redis DB 0, maxmemory-policy=allkeys-lru 유지. Rate Limit 카운터는 1분 TTL로 자동 만료되어 장기 누적 없음 (~300KB), LLM Cache가 메모리 대부분 차지 (~500MB). Rate Limit 카운터 삭제되어도 fail-open으로 요청 허용 (이전 명확화). 폐쇄망 환경에서 외부 공격 위협 낮아 Rate Limit 절대 보호 불필요. Constitution Principle IV (단순성 우선) 준수 (FR-126)
- Q: LLM Cache 무효화 전략 - LLM 모델이 업데이트되거나 프롬프트가 변경될 때, 기존 LLM Cache를 어떻게 처리해야 하나요? → A: TTL 자동 만료 (Lazy, Option C) - 모델 업데이트 시 명시적 무효화 하지 않음, 1시간 TTL로 자연스럽게 만료 대기. LLM 모델 업데이트는 월 1회 미만으로 낮은 빈도, 1시간 이내 점진적 캐시 갱신은 실사용에 큰 영향 없음. 프롬프트 변경도 Phase 10 이후 최소화. 폐쇄망 환경에서 긴급 배포 압박 낮아 점진적 업데이트 허용 가능. 중요한 업데이트 시 관리자가 선택적으로 수동 무효화 가능 (Redis CLI: DEL 명령 또는 FLUSHDB). Constitution Principle IV (단순성 우선) 준수 (FR-127)

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

## User Story 7 - Specialized Agent System with Orchestration (Priority: P3)

Government employees need the AI system to intelligently route queries to specialized agents (document search, legal research, citizen support, etc.) that provide expert-level responses using domain-specific fine-tuned models and specialized tools, while simple queries are handled directly by the base model for efficiency.

**Why this priority**: Specialized agent system with orchestration provides significant productivity gains for complex domain-specific tasks while maintaining efficient responses for simple queries. Requires stable foundation of P1-P2 features and can be added after core conversation functionality is proven.

**Independent Test**: Can be tested by submitting various query types (general questions, document analysis requests, legal inquiries, citizen complaints, data analysis tasks) and verifying correct agent routing, specialized responses using domain knowledge, and appropriate tool usage.

**Acceptance Scenarios**:

1. **Given** an employee submits a general query (e.g., "What is the weather today?" or "Explain photosynthesis"), **When** the orchestrator analyzes the intent, **Then** the base model responds directly without routing to specialized agents, providing accurate general knowledge responses

2. **Given** an employee requests document search or analysis (e.g., "Find information about budget policy in uploaded documents" or "Summarize the key points from the uploaded regulation"), **When** the orchestrator detects document-related intent, **Then** the system routes to the RAG Agent which uses document search tools and specialized LoRA to provide accurate answers with source citations

3. **Given** an employee submits a citizen inquiry (e.g., "How should I respond to a complaint about parking fines?"), **When** the orchestrator identifies citizen support intent, **Then** the Citizen Support Agent generates an empathetic, clear response with appropriate tone (존댓말) and completeness using its specialized LoRA

4. **Given** an employee requests document creation (e.g., "Draft a report on last quarter's budget execution" or "Create a policy announcement about the new recycling program"), **When** the orchestrator detects document writing intent, **Then** the Document Writing Agent generates structured content following government standards with proper formatting, sections (제목, 배경, 내용, 결론), and professional language using document template tools and specialized LoRA

5. **Given** an employee needs legal or regulatory information (e.g., "Find regulations about public procurement" or "Cite relevant ordinances for building permits"), **When** the orchestrator detects legal research intent, **Then** the Legal Research Agent searches uploaded regulations using legal reference tools, cites articles with source references, and provides plain-language interpretation using specialized LoRA

6. **Given** an employee asks for data analysis (e.g., "Analyze the trends in this year's civil complaint data" or "Calculate the average processing time from this CSV"), **When** the orchestrator routes to the Data Analysis Agent, **Then** the agent uses data analysis tools to load CSV/Excel files, provides summary statistics, identifies trends, and suggests visualizations using specialized LoRA

7. **Given** an employee requests review or quality check (e.g., "Review this draft document for errors" or "Check this response for policy compliance"), **When** the orchestrator detects review intent, **Then** the Review Agent checks for errors (factual, grammatical, policy compliance), highlights issues, and suggests specific improvements using specialized LoRA

8. **Given** multiple users simultaneously request different specialized agents, **When** the system processes concurrent requests, **Then** the system manages LoRA adapter swapping using LRU caching (keeps 2-3 most recently used adapters loaded) with <3 second adapter loading time

9. **Given** an agent needs to use specialized tools (calculator, date/schedule, templates), **When** processing a query, **Then** the agent can invoke shared tool library functions (document search, calculator, date/schedule, data analysis, document template, legal reference tools) and display results clearly

10. **Given** an administrator manages the system, **When** they access the agent management interface, **Then** they can enable/disable individual agents, configure orchestrator routing (LLM-based few-shot classification is default), view agent performance metrics (task counts, average response times, LoRA swap times, error rates), and manage LoRA adapter loading policies

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

**EC-015: Agent Tool Infinite Loop**
- **Scenario**: Specialized agent repeatedly attempts the same failed tool invocation or calls tools in infinite loop
- **Handling**: Track tool usage per agent request. If same tool called 3+ times consecutively with identical parameters, force stop with error message "도구 실행이 반복되고 있습니다. 다른 방법을 시도해주세요." (Tool execution is repeating. Please try a different approach.) Agent must then provide response without tool or explain limitation to user.
- **Covered by**: FR-061 (tool execution safety)

**EC-016: Tool Execution Timeout**
- **Scenario**: Document Search Tool takes >30 seconds due to large document corpus or complex semantic query
- **Handling**: Set tool execution timeout at 30 seconds (configurable by administrator per FR-061). If exceeded, return timeout error to agent with message "도구 실행 시간 초과" (Tool execution timeout). Agent should explain limitation to user ("문서 검색 시간이 초과되었습니다. 더 구체적인 키워드로 다시 시도해주세요.") or attempt alternative approach.
- **Covered by**: FR-061

**EC-017: Calculator Tool Malformed Expression**
- **Scenario**: Specialized agent (e.g., Data Analysis Agent) generates invalid calculation expression (e.g., "계산기(1000 원 + 500 원)" with Korean text)
- **Handling**: Parse expressions to extract numbers only, ignore currency symbols (원) and Korean text. If parsing fails completely, return error "잘못된 계산식입니다." (Invalid calculation expression) to agent. Agent should reformulate calculation with proper numeric format or ask user for clarification.
- **Covered by**: FR-060 (Calculator Tool specification)

**EC-018: Orchestrator Routing Failure**
- **Scenario**: User query is ambiguous and orchestrator cannot determine routing decision (direct response vs. which specialized agent)
- **Handling**: Default to base model direct response without specialized agent routing (per FR-073 routing error handling). Log routing failure for administrator review. If query pattern repeats, suggest adding to orchestrator few-shot examples or keyword patterns.
- **Covered by**: FR-066 (orchestrator), FR-073 (routing error handling)

**EC-019: Sequential Agent Workflow Failure (Phase 11 Feature)**
- **Scenario**: In multi-step workflow, Legal Research Agent fails (no documents found), but workflow requires its output for Document Writing Agent in next step
- **Handling**: Downstream agent (Document Writing) receives upstream failure notification. Display error: "이전 단계가 실패하여 작업을 완료할 수 없습니다." (Cannot complete task due to previous step failure) with explanation of what Legal Research Agent attempted. User can retry entire workflow with modified query or skip failed step. Sequential workflows are Phase 11 feature (FR-074), not MVP.
- **Covered by**: FR-074 (sequential workflows)

**EC-020: Safety Filter Blocking Tool Output**
- **Scenario**: Document Search Tool or Legal Reference Tool returns content containing PII or inappropriate content, which is then flagged by safety filter before agent can use it
- **Handling**: Apply safety filter to all tool outputs before passing to agent (FR-062 transparent failure approach). Mask PII in tool results (e.g., 주민등록번호 → 123456-*******). If tool output is entirely inappropriate, replace with "[도구 결과에 부적절한 내용이 포함되어 필터링되었습니다.]" (Tool output contained inappropriate content and was filtered). Agent receives filtered result and must handle gracefully in response generation.
- **Covered by**: FR-050 (safety filter), FR-051 (PII masking), FR-062 (tool error handling)

## Requirements *(mandatory)*

### Functional Requirements

**Numbering Convention**: FR numbers are organized by feature area with intentional gaps for future expansion:
- FR-001~FR-043: Core functionality (basic chat, document upload, auth, admin)
- FR-044~FR-049: *Reserved for future core features*
- FR-050~FR-058: Safety Filter requirements
- FR-059: *Reserved for future safety features*
- FR-060~FR-065: Shared Tool Library requirements
- FR-066~FR-075: Orchestrator and Agent System requirements
- FR-076~FR-080: Advanced Agent System requirements (parallel execution, workflow limits)
- FR-081~FR-088: Common Air-Gapped requirements
- FR-089~FR-109: Admin Metrics History (Feature 002)
- FR-110~FR-114: Security Hardening (Feature 002 Patch)
- FR-115~FR-122: Quality & Operational (Post-Implementation Review)

#### Core Functional Requirements

- **FR-001**: System MUST operate entirely within a closed network environment without requiring internet connectivity
- **FR-002**: System MUST provide a web-based interface accessible through standard web browsers on the internal network
- **FR-003**: Users MUST be able to submit text queries and receive LLM-generated responses
- **FR-004**: System MUST display a visual indicator when processing user queries
- **FR-005**: System MUST support conversational context, allowing follow-up questions within the same session *(See FR-036 for technical implementation details: 10-message window, 2048 token limit)*
- **FR-006**: System MUST allow users to create, view, and delete their saved conversations
- **FR-007**: System MUST support searching or filtering through saved conversations
- **FR-008**: System MUST accept document uploads in common formats (PDF, TXT, DOCX)
- **FR-009**: System MUST process uploaded documents using vector embeddings (Qdrant vector database) for semantic search, enable question-answering based on document content with accurate source references (page numbers, sections), and support multi-document comparison queries within the same conversation (documents are scoped to individual conversations, accessible only within that conversation, and automatically deleted when the conversation is deleted)
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

#### Shared Tool Library Requirements (FR-060 series)

- **FR-060**: System MUST provide a shared tool library accessible to all specialized agents containing six government-specialized tools for domain-specific tasks:
  1. **Document Search Tool**: searches uploaded documents in current conversation using vector similarity (Qdrant), returns text snippets with source references (filename, page number, section), supports semantic queries in Korean
  2. **Calculator Tool**: evaluates mathematical expressions (addition, subtraction, multiplication, division, percentages, exponents), handles Korean currency symbols (원), Korean number formats (천 단위 쉼표), returns numeric result with proper formatting
  3. **Date/Schedule Tool**: calculates business days excluding weekends/Korean public holidays, fiscal year conversions (회계연도), deadline calculations from start date + duration, supports Korean date formats (YYYY년 MM월 DD일)
  4. **Data Analysis Tool**: loads CSV/Excel files from conversation uploads, provides summary statistics (mean, median, sum, count, std dev), basic filtering and grouping operations, outputs Korean-formatted results (천 단위 쉼표)
  5. **Document Template Tool**: generates structured Korean government documents (공문서, 보고서, 안내문, 회의록) using Jinja2 templates, includes standard headers, sections (제목, 배경, 내용, 결론), signature blocks, proper formatting per government standards
  6. **Legal Reference Tool**: searches uploaded regulations/ordinances for specific articles using keyword and semantic search (Qdrant), returns citations with article numbers and full text, supports Korean legal terminology
- **FR-061**: System MUST implement tool execution safety: 30-second timeout per tool call (configurable by administrator), sandbox tool execution to prevent system access beyond designated directories (`/uploads`, `/templates`, `/data`), track identical tool calls (if same tool + same parameters called 3+ times consecutively, force stop with error "도구 실행이 반복되고 있습니다.")
- **FR-062**: System MUST handle tool execution errors with transparent failure approach: return error description in Korean (e.g., "문서를 찾을 수 없습니다", "파일 형식이 지원되지 않습니다"), log errors with stack traces for debugging, agent must attempt alternative tool/approach OR provide clear guidance to user explaining limitation and suggesting next steps
- **FR-063**: System MUST log all tool executions to audit trail: timestamp, user_id, conversation_id, agent_name (which agent invoked tool), tool_name, input_parameters (sanitized to remove PII), output_result (truncated to 500 chars), execution_time_ms, success/failure status, accessible to administrators in admin panel for audit and optimization purposes
- **FR-064**: System MUST allow administrators to enable/disable individual tools: tool management interface shows list of 6 tools with toggle switches and usage statistics, disabled tools return error "이 도구는 현재 사용할 수 없습니다." if any agent attempts to use them, tool availability configuration persists across server restarts
- **FR-065**: System MUST load all tool implementations locally for air-gapped operation: document templates stored as Jinja2 files in `/templates/government_docs/` directory (공문서.jinja2, 보고서.jinja2, 안내문.jinja2, 회의록.jinja2), Korean holiday calendar stored as JSON file in `/data/korean_holidays.json` (updated annually), no external API calls required for any tool functionality

#### Orchestrator and Specialized Agent System Requirements (FR-066 series)

- **FR-066**: System MUST implement orchestrator-based architecture where base LLM model analyzes user query intent and routes to either direct response or specialized agent:

  **Orchestrator Decision Logic**:
  - Receives user query and analyzes intent using Few-shot LLM-based classification (default) OR keyword matching (admin-configurable alternative)
  - **Routing Options**:
    1. **Direct Response**: For general knowledge queries not requiring domain expertise (e.g., "What is photosynthesis?", "Explain gravity") → base model responds without agent routing
    2. **Specialized Agent**: For domain-specific tasks requiring expert knowledge/tools → route to appropriate agent (RAG, Citizen Support, Document Writing, Legal Research, Data Analysis, Review)

  **LLM-based Classification (Default)**:
  - Few-shot prompt with 2 example queries per routing option (7 options: direct + 6 agents = 14 examples total)
  - Brief routing option descriptions (~150 tokens)
  - **Total prompt budget ≤1000 tokens** to reserve ≥1000 tokens for user query in 2048 context window

  **Token Budget Breakdown**:
  - Orchestrator system prompt: ~200 tokens
  - 7 routing options × 2 examples × ~50 tokens: ~700 tokens
  - Routing option descriptions: ~100 tokens
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

  **Keyword Matching Alternative**: Administrator can configure keyword-based routing for performance optimization (lower latency, deterministic routing), with keyword patterns stored in database or config file
- **FR-067**: System MUST provide six specialized agents using shared base model with agent-specific LoRA adapters, prompt templates, and tool access:

  **1. RAG Agent (문서 검색 및 분석 에이전트)**:
  - **Purpose**: Advanced document search and analysis using uploaded documents in conversation
  - **LoRA Specialization**: Trained for document understanding, multi-document reasoning, accurate source citation
  - **Tools**: Document Search Tool, Legal Reference Tool
  - **Capabilities**: Semantic document search, cross-document comparison, precise source references (filename, page, section), summarization, key information extraction
  - **Template**: RAG-specific prompts for citation accuracy and source attribution

  **2. Citizen Support Agent (민원 지원 에이전트)**:
  - **Purpose**: Generate empathetic, clear responses to citizen inquiries
  - **LoRA Specialization**: Trained for empathetic tone, polite Korean (존댓말), citizen service best practices
  - **Tools**: Document Template Tool (for formal response letters)
  - **Capabilities**: Analyze citizen complaints/inquiries, draft polite responses, ensure completeness (address all concerns), maintain appropriate government-citizen communication tone
  - **Template**: Citizen service response templates with tone guidelines

  **3. Document Writing Agent (문서 작성 에이전트)**:
  - **Purpose**: Generate structured government documents following official standards
  - **LoRA Specialization**: Trained for formal government document writing, structure, official language
  - **Tools**: Document Template Tool, Date/Schedule Tool
  - **Capabilities**: Create 보고서 (reports), 안내문 (announcements), 정책 문서 (policy documents), 회의록 (meeting minutes) with proper sections (제목, 배경, 내용, 결론), official formatting, professional language
  - **Template**: Government document structure templates per document type

  **4. Legal Research Agent (법규 검색 에이전트)**:
  - **Purpose**: Search regulations/ordinances and provide legal interpretations
  - **LoRA Specialization**: Trained for Korean legal terminology, citation formats, plain-language explanation
  - **Tools**: Legal Reference Tool, Document Search Tool
  - **Capabilities**: Find relevant legal articles, cite with proper format (법률명, 조항, 항), provide plain-language interpretation (쉬운 설명) alongside legal text, reference multiple related regulations
  - **Template**: Legal citation and interpretation templates

  **5. Data Analysis Agent (데이터 분석 에이전트)**:
  - **Purpose**: Analyze CSV/Excel data and provide statistical insights
  - **LoRA Specialization**: Trained for statistical interpretation, Korean data formatting, visualization recommendations
  - **Tools**: Data Analysis Tool, Calculator Tool
  - **Capabilities**: Load and analyze uploaded data files, compute summary statistics (mean, median, std dev, percentiles), identify trends and patterns, suggest appropriate visualizations (bar charts, line graphs, pie charts), format numbers in Korean style (천 단위 쉼표)
  - **Template**: Data analysis report templates with statistical terminology

  **6. Review Agent (검토 에이전트)**:
  - **Purpose**: Review drafted content for errors and suggest improvements
  - **LoRA Specialization**: Trained for error detection (factual, grammatical, stylistic), constructive feedback
  - **Tools**: No specific tools (pure analysis)
  - **Capabilities**: Check factual accuracy, grammatical correctness, policy compliance, tone appropriateness, highlight specific issues with explanations, suggest concrete improvements with examples
  - **Template**: Review checklists and feedback templates per content type

- **FR-068**: System MUST implement LoRA adapter management with the following architecture:

  **Phase 10 Implementation (MVP)**:
  - Implement LoRA loading infrastructure using HuggingFace PEFT library
  - Base model (PRIMARY: Qwen3-4B-Instruct, FALLBACK: Qwen2.5-1.5B-Instruct) loaded once on application startup
  - **Identity LoRA or minimal initialization** for all 6 agents (no actual fine-tuning yet)
  - Agent behavior relies on prompt engineering (few-shot examples, detailed instructions)
  - LoRA adapter file structure created: `/models/lora_adapters/{agent_name}/` directories for future use

  **Phase 14 Implementation (Post-MVP)**:
  - Collect training data: 500-1000 samples per agent (total 3000-6000 samples) from government employees or public datasets, estimated 4-6 weeks effort
  - Fine-tune LoRA adapters for each agent using collected data
  - Replace identity LoRA with trained adapters
  - **Improvement Measurement**: Compare LoRA-adapted vs. prompt-only on 50-100 test queries per agent with reference answers
  - **Response Quality Measurement (Session 2025-11-08 clarification)**: Automated metrics using BLEU-4 and ROUGE-L scores against reference answers. Score = average(BLEU-4, ROUGE-L) normalized to 0-100 scale. Enables reproducible, consistent measurement without human evaluation overhead.
  - **Composite Score** = weighted average (Response Quality 50%, Response Time 30%, Task-Specific Accuracy 20%)
  - **Activation Threshold**: Continue using LoRA only if composite improvement ≥10% AND quality improvement ≥5%

  **LoRA Adapter Switching**:
  - Each agent invocation dynamically loads its LoRA adapter if not already in memory
  - **LRU Caching**: Keep 2-3 most recently used adapters loaded (~500MB-1.5GB additional memory)
  - Adapter loading latency <3 seconds per swap
  - All LoRA adapter weights bundled locally for air-gapped deployment

  **Memory Management**:
  - Base model: ~2.5GB (Qwen3-4B-Instruct Q4_K_M)
  - Per LoRA adapter: ~100-500MB (rank=16 or rank=32)
  - LRU cache: 2-3 adapters = ~500MB-1.5GB
  - **Total peak memory**: ~3.0-4.0GB (base + cache)
- **FR-069**: System MUST display agent outputs with clear attribution: agent responses labeled with agent name and icon (e.g., "📄 RAG Agent:", "👤 Citizen Support Agent:", "📋 Document Writing Agent:", "⚖️ Legal Research Agent:", "📊 Data Analysis Agent:", "✓ Review Agent"), visual separators or cards for multi-agent outputs, clear indication when base model responds directly without agent routing
- **FR-070**: System MUST track all agent invocations for monitoring and debugging: log each invocation with timestamp, user_id, conversation_id, routing_decision (direct response OR agent_name), query_summary (first 200 chars), response_summary (first 200 chars), lora_adapter_loaded (boolean, which adapter if any), adapter_load_time_ms, total_execution_time_ms, tools_used (list), success/failure status, accessible to administrators in agent analytics dashboard
- **FR-071**: System MUST provide administrator interface for agent system management:
  - **Agent Control**: Enable/disable individual agents (disabled agents not available in orchestrator routing), restart required indicator for configuration changes
  - **Routing Configuration**: Toggle between LLM-based (default, Few-shot classification) and keyword-based routing, edit keyword patterns per agent when in keyword mode
  - **LoRA Management**: View loaded adapters in cache, manually warm up specific adapters (pre-load), view adapter loading statistics (swap count, average load time)
  - **Agent Performance Metrics**: Per-agent task counts (daily/weekly/monthly), average response time, LoRA swap overhead, tool usage statistics, error rates, user satisfaction ratings (if implemented)
  - **Tool Statistics**: Tool usage counts per agent, tool execution times, tool error rates
- **FR-072**: System MUST implement agent context and resource management:
  - **Context Sharing**: Current conversation history (last 10 messages per FR-036) available to all agents, uploaded documents in current conversation accessible to all agents
  - **Resource Limits**: Maximum 5 concurrent agent requests across all users (queue additional requests with estimated wait time), single agent per user query (no parallel agent execution in MVP), total agent execution timeout 2 minutes per query
  - **Graceful Degradation**: If agent system unavailable (LoRA loading failure, timeout), fallback to base model direct response with warning "전문 에이전트를 사용할 수 없어 기본 모델이 응답합니다."
- **FR-073**: System MUST handle agent execution errors transparently:
  - **Tool Errors**: Display tool error messages in Korean (per FR-062), agent attempts alternative approach or provides clear user guidance
  - **LoRA Loading Errors**: If adapter fails to load, fallback to prompt-only mode for that agent with warning logged, retry adapter loading on next invocation
  - **Agent Timeout**: If agent exceeds 2-minute timeout, return partial response with message "응답 생성 시간이 초과되었습니다. 질문을 더 구체적으로 나누어 주세요."
  - **Routing Errors**: If orchestrator fails to classify query, default to base model direct response
- **FR-074**: System MUST support sequential agent workflows (Phase 11, not MVP):
  - **Multi-step Detection**: Orchestrator detects multi-step requests using keyword patterns (e.g., "검색하고... 작성하고... 검토")
  - **Workflow Chaining**: Create agent sequence, pass each agent's output as input to next agent
  - **Progress Indication**: Display current agent and workflow stage to user
  - **Failure Handling**: If agent in chain fails, display error "이전 단계가 실패하여 작업을 완료할 수 없습니다." with retry option
- **FR-075**: System MUST load all agent implementations locally for air-gapped deployment:
  - **Prompt Templates**: Agent-specific prompt templates stored in `/prompts/agents/{agent_name}.txt` (e.g., `/prompts/agents/rag_agent.txt`, `/prompts/agents/citizen_support.txt`)
  - **LoRA Adapters**: Stored in `/models/lora_adapters/{agent_name}/` directories (e.g., `/models/lora_adapters/rag_agent/adapter_model.bin`, `/models/lora_adapters/citizen_support/adapter_config.json`)
  - **Routing Configuration**: Orchestrator few-shot examples and keyword patterns stored in database `agent_routing_config` table or `/config/agent_routing.json` file
  - **No External Dependencies**: All agent functionality works without internet connectivity

#### Advanced Agent System Requirements (FR-076 series)

*Note: These requirements address advanced multi-agent orchestration patterns (Phase 11+, not MVP)*

- **FR-076**: *Reserved for future agent features*
- **FR-077**: *Reserved for future agent features*
- **FR-078**: System SHOULD support parallel agent execution for independent sub-tasks (Phase 11+, not MVP):
  - **Parallel Execution**: Orchestrator detects independent sub-tasks that can be executed simultaneously (e.g., "Search regulations AND analyze budget data")
  - **Concurrency Limit**: Maximum 3 agents running in parallel per user query to prevent resource exhaustion
  - **Task Independence Detection**: Use dependency analysis to determine which agents can run concurrently without data dependencies
  - **Result Aggregation**: Combine parallel agent outputs into coherent final response
  - **Error Handling**: If one parallel agent fails, continue with successful agent results and indicate partial completion
  - **Performance Target**: Parallel execution should complete in time of slowest agent + aggregation overhead (<30 seconds total)
- **FR-079**: System MUST implement workflow complexity limits to prevent resource exhaustion:
  - **Agent Chain Limit**: Maximum 5 agents in a single workflow sequence (prevents infinite loops)
  - **Parallel Agent Limit**: Maximum 3 agents executing simultaneously per FR-078 (if parallel execution enabled)
  - **Total Workflow Timeout**: 5 minutes maximum per workflow (includes all sequential and parallel steps)
  - **Timeout Enforcement**: Use asyncio.wait_for() or equivalent mechanism to enforce timeout, return partial results with error message if exceeded
  - **Admin Configuration**: Administrators can adjust limits via admin panel (with reasonable bounds: 3-10 agents, 2-10 parallel, 3-10 minute timeout)
- **FR-080**: *Reserved for future agent features*

#### Common Air-Gapped Requirements (FR-081 series)

- **FR-081**: System MUST bundle all AI models locally: base LLM model (**PRIMARY**: Qwen3-4B-Instruct ~2.5GB Q4_K_M, **FALLBACK**: Qwen2.5-1.5B-Instruct ~1GB Q4_K_M for resource-constrained systems), agent-specific LoRA adapter weights (Phase 14: ~100-500MB per adapter, **6 adapters total** for Specialized Agent System - RAG, Citizen Support, Document Writing, Legal Research, Data Analysis, Review), safety filter model weights (unitary/toxic-bert, ~400MB), sentence-transformers embedding model for tag matching and PII detection, with all models loaded from local disk on startup without internet access
- **FR-082**: System MUST support CPU-only execution: all safety filter models must support CPU inference with maximum 2-second latency per check (measured at P95), shared tool library must not require GPU, Specialized Agent system uses base LLM with prompt engineering (Phase 10 MVP) or dynamically loaded LoRA adapters (Phase 14, CPU-compatible via HuggingFace PEFT library), with optional GPU acceleration if available for faster LLM inference
- **FR-083**: System MUST log all agent/tool/filter actions for audit: centralized audit log table with timestamp, user_id, action_type (filter/tool/agent/orchestrator), action_details (JSON), result (success/blocked/error/routed), execution_time_ms, administrators can query logs by date range, user, action type, or agent name in admin panel audit log viewer
- **FR-084**: System MUST allow administrators to customize rule-based systems: safety filter keywords (add/edit/delete per category via admin interface), tool availability (enable/disable individual tools per FR-064), agent routing rules (keyword patterns when in keyword mode per FR-071), document templates (upload new .jinja2 files to `/templates/government_docs/`), with changes taking effect immediately for runtime configs or after restart for file-based configs (documented per feature)
- **FR-085**: System MUST provide admin dashboard section for advanced features as new tabs in existing admin panel:
  - **Safety Filter Tab**: Filter event counts by category/day, PII masking statistics, false positive reports, top filtered users
  - **Tool Library Tab**: Per-tool usage counts (daily/weekly/monthly), average execution time per tool, error rate per tool, top users by tool usage (from FR-063 logs)
  - **Agent System Tab**: Per-agent task counts, average response time, LoRA swap overhead statistics, routing accuracy metrics (if available), tool usage by agent, error rates per agent (from FR-070 logs)
- **FR-086**: System MUST enforce resource limits for advanced features to prevent resource exhaustion:
  - **Agent System**: Maximum 5 concurrent agent requests system-wide (queue additional with estimated wait time per FR-072), 2-minute timeout per agent invocation (per FR-072)
  - **Tool Library**: 30-second timeout per tool call (per FR-061), maximum 3 identical tool calls consecutively (per FR-061)
  - **Safety Filter**: 2-second timeout per filter check (allow message through with logged warning if timeout, per FR-082)
- **FR-087**: System MUST handle graceful degradation when advanced features fail:
  - **Safety Filter Failure**: If model fails to load, fallback to rule-based keyword filtering only with warning logged to admin dashboard, system continues operating
  - **Tool Library Failure**: If tool unavailable (disabled or error), agent receives error message and must provide response without tool or explain limitation to user
  - **Agent System Failure**: If LoRA adapter fails to load, fallback to prompt-only mode for that agent (per FR-073), if orchestrator fails, fallback to base model direct response (per FR-073), system remains functional for basic Q&A
- **FR-088**: System MUST document all customization options in administrator guide (`/docs/admin/customization-guide.md` or admin panel help section):
  - Configuring safety filter rules (keywords, PII patterns, category thresholds)
  - Adding custom document templates (Jinja2 syntax, variable names, template structure)
  - Modifying agent routing rules (keyword patterns, few-shot examples)
  - Adjusting resource limits (concurrent requests, timeouts, queue sizes)
  - Managing LoRA adapters (manual loading, cache management, troubleshooting)
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

- **FR-113**: System MUST ensure metric collection consistency by: collecting all 6 metrics (active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count) within a single database transaction to guarantee identical collected_at timestamp for all metrics in same collection cycle, setting database isolation level to READ COMMITTED explicitly in connection configuration, logging transaction start/end timestamps for debugging, **using atomic all-or-nothing approach (Session 2025-11-08 clarification)** - if any individual metric calculation fails, rollback entire transaction and record complete failure details in metric_collection_failures table, retry full collection in next scheduled cycle. This prioritizes data consistency (identical timestamps for complete snapshots) over partial success, ensuring accurate time-series analysis.

- **FR-114**: System MUST provide cross-platform encoding compatibility for CSV exports by: detecting client operating system from User-Agent header, using UTF-8 with BOM (Byte Order Mark) encoding for Windows clients (User-Agent contains "Windows"), using UTF-8 without BOM for Linux/Mac clients, implementing client-side BOM injection as fallback in frontend JavaScript for browsers that don't correctly report OS, validating exported CSV files open correctly in Windows Excel (no encoding dialog), LibreOffice on Linux (correct Korean display), and Python pandas.read_csv() (no BOM artifacts in column names)

#### Quality & Operational Requirements (FR-115 series)

*Note: These requirements address critical quality and operational issues discovered during post-implementation review (2025-11-04)*

- **FR-115** *(CRITICAL)*: System MUST ensure Korean language resource files are correctly encoded in UTF-8 without corruption by: validating that frontend/src/lib/errorMessages.ts contains only valid UTF-8 characters (no mojibake/��������), all Korean strings display correctly in browser console and UI without replacement characters (���), automated test verifies errorMessages object keys and values are readable Korean text (pattern: /^[\uAC00-\uD7A3\s\w\d.,!?'"()]+$/), implementing pre-commit hook to detect non-UTF-8 characters in .ts/.tsx files, documenting standard procedure for editing Korean content (editor must be set to UTF-8, no BOM for .ts files)

- **FR-116** *(CRITICAL)*: System MUST calculate active user metrics accurately using timezone-aware timestamps by: using datetime.now(timezone.utc) consistently instead of datetime.utcnow() (deprecated), counting active users based on Session.expires_at > current_time (not created_at >= now - 30 minutes), ensuring all database timestamp comparisons use timezone-aware datetime objects, logging timezone information in metric collection debug output for verification

- **FR-117** *(HIGH)*: System MUST capture database query performance metrics for async SQLAlchemy operations by: binding event listeners to both sync_engine (for migrations) and async_engine.sync_engine (for application queries), tracking query execution time for SELECT/INSERT/UPDATE/DELETE separately, updating Prometheus db_query_duration and db_queries_total metrics for async queries, monitoring connection pool metrics from async_engine.sync_engine.pool instead of sync_engine.pool only, validating that /metrics endpoint shows non-zero query counts during normal application operation

- **FR-118** *(HIGH)*: System MUST maintain consistent administrator privilege model by: using Admin table existence check as single source of truth (Session 2025-11-08 clarification: Option B selected for better separation of concerns and audit trail), updating get_current_admin() in backend/app/api/deps.py to verify Admin table record exists for user (primary check), implementing migration script to sync existing User.is_admin flags with Admin table records, maintaining User.is_admin flag as denormalized reference only (synchronized via trigger or application logic), documenting administrator management procedure in docs/admin/user-management.md, ensuring all admin-only endpoints use consistent Admin table privilege check method

- **FR-119** *(MEDIUM)*: System MUST optimize CSRF token lifecycle management by: generating CSRF token only on successful login (not every GET request), storing CSRF token in session with 30-minute expiration matching session timeout, validating CSRF token exists before regenerating on GET requests (if missing or expired, then regenerate), returning same token value for multiple GET requests within session lifetime to prevent token rotation confusion, logging CSRF token generation events (not values) for debugging token mismatch issues

- **FR-120** *(MEDIUM)*: System MUST provide flexible CSRF exemption path matching by: supporting both exact path matching (e.g., "/api/v1/auth/login") and prefix matching (e.g., "/api/v1/setup/*" matches all setup sub-routes), implementing CSRF_EXEMPT_PATTERNS list with tuples (path_pattern, match_type) where match_type is "exact" or "prefix", adding common exempt paths: /docs, /openapi.json, /health, /api/v1/health, /metrics (Prometheus), documenting how to add new exempt paths in code comments and admin guide

- **FR-121** *(MEDIUM)*: System MUST align security test scripts with actual implementation by: updating tests/security_audit.py to match backend/app/core/security.py's direct bcrypt usage (not passlib), verifying password hashing test calls bcrypt.hashpw() and bcrypt.checkpw() directly, ensuring test expectations match bcrypt default rounds (12) from FR-029, adding integration test that validates actual /auth/login endpoint uses correct password verification method, documenting security implementation decisions in tests/README.md

- **FR-122** *(MEDIUM)*: System MUST implement data isolation middleware or update test expectations by: either (Option A) creating backend/app/middleware/data_isolation_middleware.py that validates user_id matches session user for GET/PUT/DELETE on /conversations/{id}, /documents/{id}, /messages/{id} routes, returning 403 Forbidden with message "이 리소스에 접근할 권한이 없습니다." on ownership mismatch, OR (Option B) removing data_isolation_middleware expectations from tests/security_audit.py and documenting that data isolation is handled at API dependency level via get_current_user() in backend/app/api/deps.py, registering middleware in main.py if Option A selected

#### Multiprocess & Distributed State Requirements (FR-123 series)

*Note: These requirements enable horizontal scalability and shared state management for production deployments (2025-11-06)*

- **FR-123** *(HIGH)*: System MUST support multiprocess deployment using Gunicorn with Uvicorn workers by: installing gunicorn>=21.2.0 as production WSGI server, configuring worker count based on CPU cores (formula: `workers = (2 * cpu_count) + 1` with default 4 workers), using UvicornWorker class for async FastAPI compatibility, implementing graceful shutdown with timeout=120 seconds for LLM inference completion, enabling preload_app=True for Copy-on-Write memory sharing of LLM model across workers, configuring max_requests=1000 and max_requests_jitter=50 for automatic worker recycling to prevent memory leaks, logging worker lifecycle events (spawn, restart, abort) for monitoring

- **FR-124** *(HIGH)*: System MUST integrate Redis for distributed state management by: deploying Redis 7+ with AOF persistence enabled, configuring maxmemory=512mb with allkeys-lru eviction policy for automatic memory management, storing data in Redis DB 0 (default), implementing connection pooling with redis-py library (connection pool size: 10), handling Redis connection failures gracefully with circuit breaker pattern (fallback to local memory cache for non-critical features), monitoring Redis health via healthcheck (redis-cli ping every 10s), documenting Redis data structures and key patterns in docs/architecture/redis-schema.md

- **FR-125** *(HIGH)*: System MUST implement distributed rate limiting using Redis by: migrating rate_limit_middleware.py from in-memory dict to Redis sorted sets for request timestamp tracking, using Redis key pattern `ratelimit:{client_ip}` with 60-second TTL, implementing sliding window algorithm with ZADD + ZREMRANGEBYSCORE + ZCARD for accurate request counting across workers, ensuring atomic operations using Redis transactions (MULTI/EXEC), maintaining backward compatibility (system functions without Redis by falling back to in-memory rate limiting with warning log), testing rate limit enforcement works correctly across multiple Gunicorn workers (request from worker 1 counted by worker 2)

- **FR-126** *(MEDIUM)*: System MAY implement LLM response caching using Redis to improve response time for repeated queries by: storing completed LLM responses in Redis with key pattern `llm_cache:{hash(prompt)}`, using SHA256 hash of normalized prompt (lowercased, whitespace trimmed) as cache key, setting cache TTL to 1 hour (3600 seconds) for frequently asked questions, implementing cache invalidation on admin request or system update, limiting cache entry size to 50KB to prevent memory bloat, monitoring cache hit rate via Prometheus metric `llm_cache_hit_rate`, allowing users to bypass cache with `?nocache=1` query parameter, documenting caching behavior in user guide with examples of when cache is beneficial (FAQ, policy queries) vs not beneficial (personalized document generation)

- **FR-127** *(MEDIUM)*: System MUST provide observability for multiprocess deployment by: exposing per-worker metrics via /metrics endpoint with worker_id label, aggregating metrics across workers in Prometheus (sum by endpoint for request counts, avg for latencies), logging worker PID and ID in all application logs for debugging, implementing health check endpoint /health/worker that returns worker-specific status, monitoring worker CPU/memory usage via cgroup metrics, alerting on worker restart frequency (>3 restarts/hour indicates issue), documenting troubleshooting guide for common multiprocess issues (worker timeout, memory leak, uneven load distribution)

- **FR-128** *(LOW)*: System SHOULD implement session affinity (sticky sessions) for WebSocket connections if real-time features are added in future by: configuring Nginx upstream with ip_hash directive for consistent routing, storing active WebSocket connections in Redis set with key pattern `websocket:{worker_id}`, implementing graceful worker shutdown that notifies clients to reconnect, documenting session affinity configuration in deployment guide

#### Unified Orchestrator Requirements (FR-129 series)

*Note: These requirements unify the existing separate ReAct Agent and Multi-Agent systems into a single intelligent routing architecture with automatic path selection (2025-11-07)*

- **FR-129** *(HIGH)*: System MUST implement Unified Orchestrator with 3-way intelligent routing architecture that automatically selects optimal execution path based on query intent clarity:

  **Routing Paths**:
  1. **Direct Path** (Route 1): Base LLM responds directly to clear and simple queries
     - Use case: Clear intent, simple conversation, straightforward questions
     - Examples: "안녕하세요", "감사합니다", "LLM이란 무엇인가요?", "오늘 날짜 알려줘" (with current date context)
     - Performance: 0.5-1 second (fastest path, minimal overhead)
     - Processing: No intermediate steps, direct LLM generation

  2. **Reasoning Path** (Route 2): Intent clarification for ambiguous queries
     - Use case: Ambiguous intent, missing context, unclear requirements
     - Examples: "분석해줘" (what data?), "검색해줘" (search what?), "도와줘" (help with what?)
     - Performance: 1-3 seconds (LLM clarification overhead)
     - Processing: LLM analyzes intent → Reclassifies to Direct OR Specialized
     - **Note**: This path does NOT use tools or agents directly, only clarifies intent
     - Output: Refined query + route decision (direct or specialized with specific agent type)

  3. **Specialized Path** (Route 3): Domain expert agents with optional tool usage
     - Use case: Complex tasks requiring domain expertise, document generation, data analysis, legal research
     - Examples: "2023년 매출 데이터 분석 보고서 작성", "민원처리법 제19조 검색 후 쉬운 말로 설명", "회의록 작성"
     - Performance: 5-15 seconds (agent execution + optional tool usage)
     - Agents available: RAG, Citizen Support, Document Writing, Legal Research, Data Analysis, Review
     - **Tool Usage**: Each agent uses ReAct pattern to invoke tools as needed from shared library (calculator, date_schedule, document_search, data_analysis, document_template, legal_reference)

  **Architecture Benefits**:
  - Intent-driven routing: Ambiguity resolved before expensive agent execution
  - Cost reduction: Clarification step prevents unnecessary agent invocations
  - Latency minimization: Clear queries skip clarification overhead
  - Flexibility: Agents autonomously decide tool usage based on task requirements

- **FR-130** *(HIGH)*: System MUST implement two-stage classification strategy for routing decision based on intent clarity:

  **Stage 1 - Fast Keyword Classification** (No LLM call, <10ms):
  - Maintain keyword dictionaries for each route based on intent clarity:
    - **Clear & Simple** (Direct): ["안녕", "감사", "고마워", "이란", "무엇", "설명", "정의", "의미"]
    - **Ambiguous Intent** (Reasoning): ["해줘", "좀", "부탁", "도와", "확인", "알아봐", "처리"] (without specific object)
    - **Clearly Complex** (Specialized): ["작성", "보고서", "공문", "법령", "조례", "검토", "분석+데이터", "민원+처리"]
  - Scoring algorithm: Evaluate intent clarity, not task complexity
  - High-confidence routing rules:
    - Query length <10 chars + greeting → Direct (confidence 0.95)
    - Vague action verbs without object → Reasoning (confidence 0.85)
    - 2+ specialized task keywords → Specialized (confidence 0.85)
    - Complete sentence with clear intent → Direct or Specialized based on complexity
  - If confidence <0.7 OR ambiguous → Proceed to Stage 2

  **Stage 2 - LLM Classification** (Fallback for borderline cases):
  - Invoke lightweight classification prompt (≤150 tokens)
  - Prompt focus: "Is the user's intent clear? If ambiguous, classify as REASONING for clarification."
  - Expected response: Single word "DIRECT", "REASONING", or "SPECIALIZED"
  - Temperature: 0.1 (consistent classification)
  - Timeout: 2 seconds
  - If Stage 2 fails → Default to Reasoning path (safe fallback to clarify intent)

  **Classification Metadata**:
  - Log classification method used (keyword/llm)
  - Store confidence score (0.0-1.0)
  - Track classification accuracy for continuous improvement
  - Record whether Reasoning path resulted in reroute to Direct or Specialized

- **FR-131** *(HIGH)*: System MUST implement Direct Path execution with minimal overhead:

  **Execution Flow**:
  1. Receive classified query with route="direct"
  2. Build simple prompt with conversation history (last 5 messages)
  3. Call base LLM with standard parameters (max_tokens=1000, temperature=0.7)
  4. Stream response directly to client via SSE
  5. Log execution time and update metrics

  **Optimizations**:
  - Skip orchestrator overhead (no agent routing)
  - Skip tool initialization
  - Skip specialized prompt loading
  - Use connection pooling for LLM service
  - Cache common responses (optional, FR-126)

  **Performance Target**: 95th percentile response time <1.5 seconds for queries <100 characters

- **FR-132** *(HIGH)*: System MUST implement Reasoning Path as intent clarification and rerouting mechanism:

  **Clarification Process**:
  ```
  START → analyze_intent_node → reclassify_node → [route to Direct or Specialized]
  ```

  **Principle (Session 2025-11-08 clarification)**: Reasoning Path is **strictly prompt-based** with NO tool invocation. It only analyzes user query via LLM to clarify intent, then reroutes to Direct (for simple queries) or Specialized (for tool-requiring complex tasks). This maintains clear architectural separation: Direct = base LLM response, Reasoning = intent analysis, Specialized = tool execution. If context gathering (e.g., document list, tag list) is needed for clarification, that query belongs in Specialized path instead.

  **Node Responsibilities**:
  - **analyze_intent_node**: LLM analyzes ambiguous query to extract true intent
    - Input: Ambiguous query (e.g., "분석해줘", "검색해줘")
    - Prompt: "What does the user want? What information is missing? What is the actual task?"
    - Output: Clarified intent, identified missing context, recommended action
  - **reclassify_node**: Determine final route based on clarified intent
    - If simple question with missing context → Direct (with clarified query)
    - If complex task requiring expertise → Specialized (with identified agent type + clarified requirements)

  **Clarification Prompt Template**:
  ```
  User query: "{original_query}"
  Context: {conversation_history}

  Analyze:
  1. What is the user's actual intent?
  2. What information/context is missing?
  3. Is this a simple question or complex task?
  4. If complex, which domain expert is needed?

  Output JSON:
  {
    "clarified_intent": "...",
    "missing_context": [...],
    "complexity": "simple" | "complex",
    "recommended_route": "direct" | "specialized",
    "agent_type": null | "rag" | "data_analysis" | "document_writing" | ...,
    "refined_query": "..."
  }
  ```

  **State Management**:
  - Reasoning state: {original_query, clarified_intent, complexity, recommended_route, agent_type, refined_query}
  - Parent state receives: route (updated), query (refined), agent_type (if specialized)

  **Rerouting Logic**:
  - Simple + missing context → Direct with clarification response (e.g., "어떤 데이터를 분석할까요?")
  - Complex + clear requirements → Specialized with specific agent
  - Still ambiguous after clarification → Direct with request for more information

  **Retry Policy**:
  - LLM service call failure → Retry up to 3 times with exponential backoff (100ms → 200ms → 400ms)
  - **Per-attempt timeout**: 2 seconds per LLM call attempt (each of the 3 retries has 2s timeout)
  - **Total operation timeout**: Maximum 3 attempts with backoff = ~6.7 seconds worst case (2s×3 + 0.7s backoff)
  - Retry on: Connection errors, timeout errors, 5xx server errors
  - No retry on: 4xx client errors, JSON structure issues
  - Note: In practice, first success usually completes in <2s; retries only for transient failures

  **Failure Handling**:
  - All retries exhausted / per-attempt timeout exceeded → Fallback to Direct path with message: "요청을 명확히 파악하지 못했습니다. 구체적으로 알려주세요: [무엇을/어떤/언제]?"
  - JSON parsing error → Fallback to Direct path with same guidance message
  - Unable to clarify intent → Fallback to Direct path, ask user for more specific details
  - **Principle**: Maintain conversation flow, never block user with hard errors
  - Log all failures for classification accuracy monitoring

  **Performance Target**: Intent clarification typically completes in <2 seconds (first attempt success). With retries for transient failures, worst case <7 seconds before fallback.

- **FR-133** *(HIGH)*: System MUST implement Specialized Path where domain expert agents autonomously use tools via ReAct pattern:

  **Agent Execution Structure**:
  ```
  START → select_agent → execute_agent_with_tools → [workflow_type?]
                                                      ├─> single → END
                                                      ├─> sequential → next_agent → ...
                                                      └─> parallel → concurrent_agents → merge → END
  ```

  **Agent Tool Usage (ReAct Pattern)**:
  Each specialized agent internally executes ReAct loop when needed:
  ```
  Agent receives task → [ReAct Loop]
    1. Think: Analyze task, decide if tools needed
    2. Act: Select tool + parameters OR generate direct response
    3. Observe: Tool result OR skip if no tool used
    4. Repeat: Continue until task complete (max 5 iterations)
  ```

  **Example: Data Analysis Agent**:
  ```
  User: "2023년 매출 분석해줘"
  Agent think: "Need to load data file and calculate statistics"
  Agent act: data_analysis_tool(file_path="2023_sales.csv", operation="statistics")
  Agent observe: {"mean": 1000000, "max": 5000000, "trend": "increasing"}
  Agent think: "Now format with Korean locale and provide insights"
  Agent act: Generate response with formatted numbers and analysis
  Final output: "2023년 매출 분석 결과
    - 평균 매출: 1,000,000원
    - 최고 매출: 5,000,000원 (4분기)
    - 트렌드: 연중 상승세..."
  ```

  **Workflow Types**:
  - **Single**: One agent handles entire task (e.g., "보고서 작성" → DocumentWritingAgent uses document_template tool)
  - **Sequential**: Chain agents with context sharing (e.g., "법령 검색 후 공문 작성" → LegalResearch uses legal_reference tool → DocumentWriting uses result + document_template tool)
  - **Parallel**: Execute independent agents concurrently (max 3, each may use different tools simultaneously)

  **Shared Tool Library Access**:
  All agents have access to 6 tools, used autonomously based on task:
  - calculator, date_schedule, document_search, data_analysis, document_template, legal_reference
  - Tool safety: 30s timeout, sandboxed execution, audit logging per FR-061

  **State Management**:
  - Agent state: {task, react_steps: [{thought, action, observation}], tools_used: [], final_output}
  - Workflow state: {agent_sequence, agent_outputs: {}, workflow_type, total_tools_used: [], execution_log[]}
  - Parent state receives: agent_outputs, workflow_type, total_tools_used, execution_log, processing_time_ms

  **Agent Selection Failure Handling**:
  - Invalid agent_type (null, unknown name) → Fallback to Direct path
  - Notify user: "일반 모드로 처리합니다"
  - Log failure: {timestamp, query, attempted_agent_type, fallback_route: "direct"}
  - Use failure logs to improve classification accuracy over time
  - **Principle**: Never leave user without response, transparent degradation

  **Performance**:
  - Single agent: 5-15 seconds (depends on tool usage)
  - Sequential: 10-30 seconds (agent count × average agent time)
  - Parallel: 5-15 seconds (slowest agent time)

- **FR-134** *(HIGH)*: System MUST implement LangGraph state management for unified orchestrator:

  **UnifiedAgentState Schema**:
  ```python
  {
    # Input
    "query": str,                              # Original user query
    "user_id": UUID,
    "conversation_id": UUID,
    "conversation_history": List[Dict],

    # Routing
    "route": Literal["direct", "reasoning", "specialized"],
    "complexity": Literal["simple", "ambiguous", "complex"],
    "classification_confidence": float,         # 0.0-1.0
    "classification_method": Literal["keyword", "llm"],

    # Processing
    "messages": List[Dict],                     # LangGraph message history
    "intermediate_results": Dict[str, Any],

    # Reasoning specific (intent clarification path)
    "clarified_intent": Optional[str],          # Clarified user intent
    "missing_context": Optional[List[str]],     # Identified missing information
    "refined_query": Optional[str],             # Refined query after clarification
    "rerouted_to": Optional[Literal["direct", "specialized"]],  # Final route after reasoning

    # Specialized specific (agent execution path)
    "agent_type": Optional[str],                # Selected agent (rag, data_analysis, etc.)
    "agent_sequence": List[str],                # For sequential/parallel workflows
    "agent_outputs": Dict[str, str],            # {agent_name: output}
    "workflow_type": Optional[str],             # single, sequential, parallel
    "tools_used": List[str],                    # Tools used by agents (aggregated)

    # Output
    "final_response": str,
    "processing_time_ms": int,
    "error": Optional[str],

    # Metadata
    "execution_log": List[Dict]                 # Trace of all nodes executed
  }
  ```

  **State Transitions**:
  - **classify_node** updates: route, complexity, classification_confidence, classification_method
  - **direct_node** updates: final_response, processing_time_ms
  - **reasoning_node** updates: clarified_intent, missing_context, refined_query, rerouted_to, route (updated), query (updated)
    - Then routes to direct_node OR specialized_node based on rerouted_to
  - **specialized_node** updates: agent_type, agent_outputs, workflow_type, tools_used, final_response
  - **finalize_node** updates: execution_log (complete trace)

  **State Persistence**:
  - State NOT persisted to database (in-memory only during execution)
  - execution_log stored in AuditLog table for administrator review
  - Route and performance metrics stored for analytics
  - Reasoning path rerouting tracked for classification accuracy improvement

- **FR-135** *(HIGH)*: System MUST optimize performance with fast-path execution and caching:

  **Fast-Path Optimizations**:
  - Keyword classification bypasses LLM (saves ~200ms)
  - Direct path skips agent initialization (saves ~500ms)
  - Connection pooling for LLM service (reuse connections)
  - Lazy loading: Only load agent resources when needed

  **Concurrency Limits**:
  - Per-user limit: 1 active orchestrator request at a time
  - Global limit: 50 concurrent orchestrator executions (all routes combined)
  - **Counting method (Session 2025-11-08 clarification)**: Equal counting - all routes (Direct/Reasoning/Specialized) count as 1 toward the 50 limit regardless of complexity. No weighted counting or separate pools. Simplifies implementation and provides predictable behavior.
  - Enforcement: Return HTTP 429 (Too Many Requests) when limits exceeded
  - No queueing: Reject immediately rather than queuing requests
  - Rationale: 8-core CPU can handle ~50 concurrent requests (6-7 per core) without degradation. Per-user limit prevents individual abuse. Route-specific performance managed via response time targets.
  - User experience: Duplicate requests prevented, system overload avoided

  **Response Caching** (Optional, requires FR-126 Redis):
  - Cache Direct path responses for common queries
  - Cache key: SHA256(normalized_query) where normalized = lowercase + whitespace trimmed
  - Cache TTL: 1 hour for FAQ-type queries
  - Cache bypass: User can force fresh response with ?nocache=1
  - Cache invalidation: On admin request or system update

  **Performance Targets by Route**:
  - Direct path: P95 <1.5s (0.5s typical)
  - Reasoning path: P95 <3s (1-2s typical, intent clarification overhead)
  - Specialized path: P95 <15s (5-10s typical, depends on agent execution and tool usage)

  **Monitoring**:
  - Track route distribution: % of queries per route (expect 60% direct, 25% reasoning, 15% specialized)
  - Track classification accuracy: Monitor misrouted queries via user feedback
  - Track latency per route: Identify performance regressions

  **Production Deployment Criteria**:
  - Classification accuracy ≥85% on labeled test set (100 queries)
  - 2-week monitoring period with no accuracy regression
  - Route distribution within ±10% of expected values (60%/25%/15%)
  - P95 latency targets met for all routes
  - Failure fallback mechanisms verified (reasoning/agent selection failures)

- **FR-136** *(MEDIUM)*: System MUST provide backward compatibility with legacy routing flags:

  **Legacy API Support**:
  - Accept `use_react_agent: true` → Force Reasoning path (intent clarification, bypass classification)
  - Accept `use_multi_agent: true` → Force Specialized path (agent execution with tools, bypass classification)
  - Accept `use_unified_routing: true` (default) → Use 3-way intelligent routing
  - If multiple flags set → Priority order: unified > multi_agent > react_agent
  - **Note**: Legacy `use_react_agent` flag name is historical; it now triggers intent clarification path, not tool-based ReAct execution

  **Migration Path**:
  - Phase 1 (Current): Both systems coexist, unified_routing=false by default
  - Phase 2 (2 weeks): unified_routing=true by default, legacy flags still work
  - Phase 3 (1 month): Deprecation warning when legacy flags used
  - Phase 4 (3 months): Remove legacy flags, unified_routing only

  **Response Metadata**:
  - Always include `route_type` in response: "direct" | "reasoning" | "specialized" | "legacy_react" | "legacy_multi"
  - Include `classification_confidence` for unified routing
  - Include `agents_used` list for specialized path
  - Include `tools_used` list for specialized path (tools invoked by agents)
  - Include `clarified_intent` for reasoning path (intent clarification result)

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
    3. 처리 단계: 파일 업로드(HTTP) + PDF 텍스트 추출(pdfplumber) + 청킹(500자 단위) + 벡터 임베딩(sentence-transformers) + Qdrant 저장
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
- **SC-041**: Multiprocess deployment handles concurrent load without worker timeout: 4 Gunicorn workers successfully process 20 concurrent requests within 15 seconds (5 requests per worker average), no worker timeout errors in logs during load test, graceful shutdown completes all in-progress LLM requests within 120 seconds, memory sharing via preload_app reduces total RAM usage by >40% compared to non-shared deployment (measured: 2.5GB base + 4×0.5GB = 4.5GB total vs 4×2.5GB = 10GB without sharing)
- **SC-042**: Redis distributed rate limiting enforces limits across all workers: making 61 requests from same IP within 60 seconds returns 429 Too Many Requests regardless of which worker receives request, rate limit counters persist across worker restarts (stored in Redis, not in-memory), Redis failure triggers graceful degradation to in-memory rate limiting with warning log, automated test makes 100 requests distributed across 4 workers and verifies exactly 60 succeed + 40 fail with 429
- **SC-043**: Worker lifecycle management prevents data loss: worker receiving SIGTERM completes current request before shutdown (verified by checking response status = 200 for requests sent during shutdown), worker restart does not affect other workers' operations (isolated process failure), worker recycling after max_requests=1000 executes without dropping connections, Prometheus metrics show worker_restarts_total incrementing as expected with jitter variance
- **SC-044**: LLM cache improves response time for repeated queries: cache hit rate >30% for FAQ-style queries measured over 1-hour load test with 100 unique prompts (30 repeated 3 times each), cached response returns within 500ms (vs 8 seconds for uncached), cache TTL expires after exactly 1 hour, cache invalidation clears all entries immediately, exported cache metrics show llm_cache_hits and llm_cache_misses with correct ratio
- **SC-045**: Multiprocess observability provides per-worker visibility: /metrics endpoint includes worker_id label for all application metrics (http_requests_total{worker_id="1"}), Prometheus aggregation query sum(rate(http_requests_total[5m])) by (endpoint) correctly combines all workers, health check /health/worker returns JSON with worker PID and status, logs include worker ID in all entries for request tracing, troubleshooting guide documents how to identify worker-specific issues (memory leak, CPU spike, timeout)

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
- **Vector Database**: Qdrant 1.7+ for document semantic search
  - Docker deployment: qdrant/qdrant:v1.7.4 image for air-gapped environment
  - Collection: documents (768 dimensions, Cosine similarity, HNSW index)
  - Data isolation: payload filtering by conversation_id for user-scoped queries
  - Backup: Snapshot API for periodic vector data backups
  - Memory: ~100-200MB base + vector data (proportional to document count)
- **Embedding model**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, **default fp32 variant**, ~420MB, supports Korean, CPU-compatible) pre-downloaded for offline installation using `huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --local-dir ./models/embeddings/`, used for both document Q&A (FR-009) and tag auto-matching (FR-043). **Note**: For air-gapped deployment, download includes all files in model repository (pytorch_model.bin, config.json, tokenizer files)
- **Safety Filter Dependencies**:
  - Lightweight toxic content classification model (HuggingFace: `unitary/toxic-bert`, ~400MB, multilingual including Korean, CPU-compatible) pre-downloaded from HuggingFace for offline installation
  - Regex pattern library for PII detection (주민등록번호, phone, email patterns)
  - Optional: sentence-transformers for advanced PII entity recognition if rule-based insufficient
- **Shared Tool Library Dependencies**:
  - Korean public holiday calendar (JSON file `/data/korean_holidays.json`) for Date/Schedule Tool, updated annually
  - Government document templates (공문서.jinja2, 보고서.jinja2, 안내문.jinja2, 회의록.jinja2) stored in `/templates/government_docs/` directory
  - Python libraries:
    - **pandas 2.1+**: Data Analysis Tool (CSV/Excel processing)
    - **openpyxl 3.1+**: Excel file support
    - **sympy** or **numexpr**: Calculator Tool expression evaluation
    - **jinja2 3.1+**: Document Template Tool rendering
  - Qdrant: Document Search Tool and Legal Reference Tool vector search
- **Multiprocess Deployment Dependencies** (FR-123 through FR-128):
  - **Gunicorn 21.2.0+**: Production WSGI server for multiprocess deployment, supports Uvicorn workers for FastAPI async compatibility
  - **Redis 7+**: Distributed cache and state management
    - Configuration: AOF persistence enabled, maxmemory=512mb, maxmemory-policy=allkeys-lru
    - Use cases: Distributed rate limiting (primary), LLM response caching (optional), session store (future)
  - **redis-py 5.0.1+**: Python Redis client with connection pooling support
  - **hiredis 2.3.2+**: High-performance Redis protocol parser (optional but recommended for performance)
  - **APScheduler 3.10+**: Background task scheduling for metrics collection (already required for Feature 002)
- **Specialized Agent System Dependencies**:
  - **Agent Prompt Templates** (Phase 10 mandatory): Stored as text files in `/prompts/agents/` directory for each specialized agent:
    - `/prompts/agents/rag_agent.txt`: RAG Agent prompts for document search and citation
    - `/prompts/agents/citizen_support.txt`: Citizen Support Agent prompts for empathetic responses
    - `/prompts/agents/document_writing.txt`: Document Writing Agent prompts for formal document generation
    - `/prompts/agents/legal_research.txt`: Legal Research Agent prompts for legal interpretation
    - `/prompts/agents/data_analysis.txt`: Data Analysis Agent prompts for statistical analysis
    - `/prompts/agents/review.txt`: Review Agent prompts for content review
  - **LoRA Adapter Weights** (Phase 14 only): **6 fine-tuned adapters** (~100-500MB each, rank=16 or rank=32) optimized for Qwen3-4B-Instruct (primary) or Qwen2.5-1.5B-Instruct (fallback):
    - `/models/lora_adapters/rag_agent/`: RAG Agent adapter for document understanding
    - `/models/lora_adapters/citizen_support/`: Citizen Support Agent adapter for empathetic tone
    - `/models/lora_adapters/document_writing/`: Document Writing Agent adapter for formal writing
    - `/models/lora_adapters/legal_research/`: Legal Research Agent adapter for legal terminology
    - `/models/lora_adapters/data_analysis/`: Data Analysis Agent adapter for statistical interpretation
    - `/models/lora_adapters/review/`: Review Agent adapter for error detection
  - **HuggingFace PEFT** (Parameter-Efficient Fine-Tuning) library 0.7.0+: LoRA adapter loading, management, and LRU caching (CPU-compatible)
  - **Orchestrator Routing Configuration**:
    - **LLM-based (default)**: Few-shot prompt file with **2 example queries per routing option** (7 options: direct response + 6 agents = 14 examples total, ≤1000 token budget per FR-066)
    - **Keyword-based (alternative)**: Keyword patterns per agent stored in database table `agent_routing_config` or config file `/config/agent_routing.json`
  - **Memory Requirements**:
    - Base model: ~2.5GB (Qwen3-4B-Instruct Q4_K_M)
    - LoRA cache: ~500MB-1.5GB (2-3 adapters cached via LRU)
    - Total: ~3.0-4.0GB peak memory (per FR-068)
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

## Hardware Requirements

### Minimum Configuration (Baseline)
- **CPU**: 8-core (Intel Xeon or AMD EPYC recommended)
  - Rationale: Supports 50 concurrent orchestrator executions (~6-7 requests per core) without degradation (FR-135)
  - Architecture: x86_64 (Intel/AMD)
- **RAM**: 16GB
  - Base LLM model: ~2.5GB (Qwen3-4B-Instruct Q4_K_M)
  - LoRA adapters cache: ~1.5GB (2-3 adapters in memory)
  - Application processes (FastAPI, Next.js, Redis, PostgreSQL): ~2GB
  - Vector database (Qdrant): ~100-200MB + document data
  - OS + buffers: ~10GB
- **Storage**: 100GB SSD
  - LLM models + dependencies: ~20GB
  - Vector database: ~10GB (scales with document count)
  - Logs + backups: ~30GB
  - User data (10GB × 5 users): ~50GB
  - OS + system files: ~20GB
- **Network**: Gigabit Ethernet (폐쇄망 내부 통신용)

### Recommended Configuration (Production)
- **CPU**: 16-core (better concurrent request handling)
- **RAM**: 32GB (supports more concurrent sessions and larger LoRA cache)
- **Storage**: 500GB SSD (longer retention, more users, extended backup history)
- **GPU (Optional)**: NVIDIA RTX 3090 or A100 for 3-5x inference acceleration

### Scalability Notes
- **Horizontal scaling**: Not supported in MVP (monolithic deployment per Constitution IV - Simplicity Over Optimization)
- **Vertical scaling**: Add CPU cores for higher concurrency, add RAM for more LoRA adapter cache
- **Concurrency limit calibration**: 50 concurrent executions (FR-135) calibrated for 8-core baseline
  - Adjust proportionally for different core counts: 16-core → ~100 concurrent, 4-core → ~25 concurrent
- **User capacity**: Baseline supports 50-100 active users (peak concurrent usage ~10-20%)
  - Add 16GB RAM for each additional 100 users if higher concurrency expected

## Out of Scope

This feature specification explicitly excludes:

- Integration with external cloud services or APIs
- Real-time collaboration features (multiple users editing the same conversation simultaneously)
- Advanced analytics or usage reporting dashboards
- Mobile application support (tablet/smartphone apps)
- Integration with existing government IT systems (HR, document management, etc.)
- Full-scale LLM model training from scratch or extensive fine-tuning on government-specific data (Note: Lightweight LoRA adapter fine-tuning is **in scope** for Phase 14 per FR-068, limited to adapters for 6 specialized agents with 500-1000 samples per agent)
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
