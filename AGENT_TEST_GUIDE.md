# 에이전트 작동 확인 가이드

## 빠른 테스트 (5분)

### 1단계: 서버 준비 확인
```bash
docker-compose ps
# 모든 서비스가 Up 상태인지 확인

curl http://localhost:8000/health
# {"status":"healthy"} 확인
```

### 2단계: 기본 LLM 테스트
**프론트엔드**: http://localhost:3000
- 로그인: admin / admin123!
- 메시지: "안녕하세요"
- 결과: 스트리밍 응답 (10-15초)

### 3단계: ReAct Agent 테스트
```bash
python test_react_agent.py
```

또는 수동:
```bash
# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123!"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['session_token'])" \
  > token.txt

# ReAct 테스트
TOKEN=$(cat token.txt)
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"오늘 날짜는?","use_react_agent":true}' \
  | python -m json.tool
```

**성공 예시**:
```json
{
  "react_steps": [
    {
      "action": "date_tool",
      "observation": "2025-11-02"
    }
  ],
  "tools_used": ["date_tool"]
}
```

### 4단계: Multi-Agent 테스트
```bash
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"민원 처리 절차 문서 작성","use_multi_agent":true}' \
  | python -m json.tool
```

**성공 예시**:
```json
{
  "multi_agent_result": {
    "workflow_type": "sequential",
    "agent_outputs": {
      "citizen_support": "...",
      "document_writing": "..."
    }
  }
}
```

---

## 에러 해결

### 에러 1: "Model failed to load"
**원인**: 모델 파일 없음
**해결**:
```bash
ls -lh models/qwen3-4b-instruct-q4_k_m.gguf
# 2.4GB 파일 확인
```

### 에러 2: "RuntimeWarning: coroutine was never awaited"
**원인**: ReAct Agent async 문제
**해결**: 방금 수정 완료 (chat.py:83-99)

### 에러 3: "401 Unauthorized"
**원인**: 토큰 만료
**해결**: 재로그인

---

## 로그 확인

### 실시간 모니터링
```bash
docker-compose logs -f backend
```

### 특정 패턴 검색
```bash
# ReAct 관련
docker-compose logs backend | grep -i "react"

# Multi-Agent 관련
docker-compose logs backend | grep -i "orchestrator"

# 에러만
docker-compose logs backend | grep -i "error"

# LLM 로딩
docker-compose logs backend | grep -i "llamacpp"
```

---

## 성능 벤치마크

### 예상 응답 시간
- **첫 요청** (모델 로딩 포함): 30-60초
- **일반 LLM**: 10-15초
- **ReAct Agent** (도구 1개): 15-20초
- **Multi-Agent** (2개 에이전트): 20-30초

### 허용 범위
- 단일 사용자: 8-12초 (T204A 목표)
- 동시 10명: <14.4초 평균 (현재 달성)

---

## 테스트 자동화

### 전체 테스트 실행
```bash
# 1. 서버 시작
docker-compose up -d

# 2. 서버 준비 대기
sleep 30

# 3. 모든 테스트 실행
python test_llm_performance.py  # T204A 성능 테스트
python test_react_agent.py      # ReAct Agent
python test_api.py               # 기본 API

# 4. 로그 확인
docker-compose logs backend | grep -i "error" | tail -20
```

---

## 요약

**✅ 기본 LLM**: 프론트엔드에서 일반 메시지
**✅ ReAct Agent**: `use_react_agent: true` (날짜/계산 질문)
**✅ Multi-Agent**: `use_multi_agent: true` (복합 작업)

**로그 키워드**:
- `[LlamaCpp]`: 모델 로딩
- `[ReAct]`: ReAct Agent 실행
- `[Orchestrator]`: Multi-Agent 라우팅
