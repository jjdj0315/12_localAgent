# agent-chat-ui 통합 테스트 가이드

## 개요

LangGraph Streaming 기능과 agent-chat-ui를 완전히 통합했습니다. 이 가이드는 통합 테스트 방법을 안내합니다.

## 구현 사항

### 1. 백엔드 LangGraph Server API 어댑터
- **파일**: `backend/app/api/v1/langgraph_adapter.py`
- **엔드포인트**:
  - `GET /api/info` - 서버 정보
  - `GET /api/assistants/unified-agent` - 어시스턴트 정보
  - `POST /api/threads` - 대화 생성
  - `GET /api/threads/{thread_id}` - 대화 조회
  - `POST /api/threads/{thread_id}/runs/stream` - 스트리밍 실행 (SSE)

### 2. 프론트엔드 교체
- **기존 frontend**: `frontend.backup.20251110_165718`로 백업
- **새 frontend**: [agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) 적용
- **환경 변수**: `frontend/.env.local`
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000/api
  NEXT_PUBLIC_ASSISTANT_ID=unified-agent
  ```

### 3. 스트리밍 통합
- **stream_mode**: `["updates", "messages", "custom"]`
- **SSE 이벤트**:
  - `metadata`: run_id
  - `updates`: 노드 상태 업데이트
  - `custom`: get_stream_writer()를 통한 진행 상황
  - `messages/0/content`: LLM 토큰 스트리밍
  - `end`: 실행 완료

## 테스트 절차

### 1. 서비스 시작 확인

```bash
# 작업 디렉토리로 이동
cd /mnt/c/02_practice/12_localAgent

# 컨테이너 상태 확인
docker compose ps

# 모든 컨테이너가 running 상태여야 합니다:
# - llm-webapp-postgres (healthy)
# - llm-webapp-redis (healthy)
# - llm-webapp-qdrant
# - llm-webapp-backend
# - llm-webapp-frontend
# - llm-webapp-prometheus
# - llm-webapp-grafana
```

### 2. 백엔드 API 테스트

```bash
# Health check
curl http://localhost:8000/health
# 예상 응답: {"status":"healthy","version":"0.1.0"}

# LangGraph Server API - 서버 정보
curl http://localhost:8000/api/info | python3 -m json.tool
# 예상 응답:
# {
#   "version": "1.0.0",
#   "server_type": "unified-agent",
#   "capabilities": ["streaming", "progress_tracking", "tool_calls"]
# }

# LangGraph Server API - 어시스턴트 정보
curl http://localhost:8000/api/assistants/unified-agent | python3 -m json.tool
# 예상 응답:
# {
#   "assistant_id": "unified-agent",
#   "graph_id": "unified_orchestrator",
#   "name": "Unified Agent",
#   "description": "3-way intelligent routing agent (Direct/Reasoning/Specialized)",
#   ...
# }
```

### 3. 프론트엔드 접속

**Windows 브라우저에서 접속**:
1. 브라우저 열기 (Chrome, Edge 등)
2. `http://localhost:3000` 접속
3. agent-chat-ui 로그인 화면 확인

**예상 화면**:
- LangGraph 로고
- "Agent Chat" 제목
- Deployment URL 입력 폼 (이미 설정된 경우 바로 대화 화면)

### 4. 통합 테스트

#### 4.1 초기 설정 (최초 접속 시)
환경 변수가 설정되어 있으므로 자동으로 연결됩니다. 만약 설정 폼이 나타나면:
- **Deployment URL**: `http://localhost:8000/api`
- **Assistant / Graph ID**: `unified-agent`
- **LangSmith API Key**: (비워둠 - 로컬 개발용)

#### 4.2 대화 테스트

**테스트 1: Direct Path (명확하고 간단한 질문)**
```
사용자: 안녕하세요
기대 결과:
- 빠른 응답 (0.5-1s)
- 토큰 단위 스트리밍 표시
- 진행 상황 표시 (classify → direct → finalize)
```

**테스트 2: Reasoning Path (모호한 질문)**
```
사용자: 그거 어떻게 하는 건지 알려줘
기대 결과:
- 의도 확인 요청
- 진행 상황 표시 (classify → reasoning → reroute)
- 응답 시간 1-3s
```

**테스트 3: Specialized Path (복잡한 작업)**
```
사용자: 문서를 검색하고 계산을 수행해줘
기대 결과:
- 도메인 전문가 에이전트 활성화
- 도구 사용 표시
- 진행 상황 표시 (classify → specialized → execute_agents → finalize)
- 응답 시간 5-15s
```

#### 4.3 스트리밍 확인
- 토큰이 실시간으로 표시되는지 확인
- 진행 상황 이벤트가 표시되는지 확인 (브라우저 개발자 도구 Network 탭에서 SSE 확인)

#### 4.4 대화 히스토리
- 새 대화 생성 버튼 클릭
- 이전 대화 목록 확인
- 특정 대화 선택 및 이어가기

## 최신 업데이트

### 2025-11-10: CSRF 보호 예외 추가
- **문제**: agent-chat-ui가 POST 요청 시 403 CSRF 오류 발생
- **원인**: LangGraph Server API 엔드포인트(`/api/threads`, `/api/assistants` 등)가 CSRF 토큰 없이 Bearer 토큰 인증만 사용
- **해결**: CSRF 미들웨어에 LangGraph API 경로 예외 추가
  ```python
  CSRF_EXEMPT_PREFIXES = [
      "/api/info",       # LangGraph Server API: server info
      "/api/assistants/",  # LangGraph Server API: assistant endpoints
      "/api/threads",    # LangGraph Server API: thread (conversation) endpoints
  ]
  ```
- **파일**: `backend/app/middleware/csrf_middleware.py:45-47`
- **결과**: agent-chat-ui가 정상적으로 대화 생성 및 스트리밍 가능

## 문제 해결

### 백엔드가 시작되지 않는 경우

```bash
# 로그 확인
docker compose logs backend --tail 100

# 일반적인 문제:
# 1. DB migration 실패 -> alembic 로그 확인
# 2. 모델 파일 없음 -> /models/qwen3-0.6b-q8_0.gguf 확인
# 3. Import 오류 -> Python 스택 트레이스 확인
```

### 프론트엔드 연결 오류

```bash
# 프론트엔드 로그 확인
docker compose logs frontend --tail 50

# .env.local 파일 확인
cat frontend/.env.local

# CORS 오류 시 백엔드 환경 변수 확인
docker compose exec backend env | grep CORS
```

### SSE 스트리밍 작동하지 않음

브라우저 개발자 도구 (F12) → Network 탭:
1. `/api/threads/{id}/runs/stream` 요청 찾기
2. 타입이 `eventsource`인지 확인
3. Response 탭에서 SSE 이벤트 확인

## 성능 기대치

| 경로 | 응답 시간 (P95) | 특징 |
|------|----------------|------|
| Direct | <1.5s | 명확한 질문, 에이전트 오버헤드 없음 |
| Reasoning | 1-3s | 의도 확인 후 재라우팅 |
| Specialized | 5-15s | 멀티 에이전트 + 도구 사용 |

## 다음 단계

1. **인증 통합**: agent-chat-ui에 기존 인증 시스템 연결
2. **커스터마이징**: UI 테마 및 브랜딩 적용
3. **추가 기능**: 파일 업로드, 이미지 표시 등
4. **프로덕션 배포**: 환경 변수 보안 강화, HTTPS 적용

## 참고 자료

- [agent-chat-ui GitHub](https://github.com/langchain-ai/agent-chat-ui)
- [LangGraph Server API 문서](https://langchain-ai.github.io/langgraph/reference/server/)
- [LangGraph Streaming 가이드](https://langchain-ai.github.io/langgraph/how-tos/stream-values/)
