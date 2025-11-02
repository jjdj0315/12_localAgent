# ReAct Agent vs Multi-Agent Orchestrator 비교

## 핵심 차이점 (3줄 요약)

| | ReAct Agent | Multi-Agent Orchestrator |
|---|---|---|
| **누가** | **1명의 에이전트** + 여러 도구 | **여러 전문 에이전트**들 |
| **무엇을** | 도구를 사용해서 **단계별로 문제 해결** | 전문가들이 **각자 맡은 일 수행** |
| **언제** | 계산, 검색, 날짜 등 **도구가 필요한 작업** | 복잡한 **멀티 도메인 작업** |

---

## 1️⃣ ReAct Agent (단일 에이전트 + 도구)

### 컨셉
```
한 명의 똑똑한 직원이 여러 도구를 사용해서 문제를 해결
```

### 작동 방식 (ReAct Loop)
```
사용자: "2024년 10월 15일부터 30일까지 며칠인가요?"

1. Think (생각):    "날짜 계산이 필요하니 calculator_tool 사용"
2. Action (행동):   calculator_tool(date_diff, 2024-10-15, 2024-10-30)
3. Observe (관찰):  "15일"
4. Think:           "답을 알았으니 종료"
5. Answer (답변):   "15일입니다"
```

### 사용 가능한 도구 (Tools)
- `calculator_tool`: 계산
- `date_schedule_tool`: 날짜/일정 확인
- `document_search_tool`: 문서 검색
- `data_analysis_tool`: 데이터 분석
- `document_template_tool`: 문서 템플릿
- `legal_reference_tool`: 법규 참조

### 예시 요청
```json
{
  "content": "오늘부터 크리스마스까지 며칠 남았나요?",
  "use_react_agent": true
}
```

### 응답 구조
```json
{
  "message": {
    "content": "79일 남았습니다"
  },
  "react_steps": [
    {
      "iteration": 1,
      "thought": "날짜 계산 도구 사용",
      "action": "date_schedule_tool",
      "action_input": {"query": "days_until", "date": "2024-12-25"},
      "observation": "79"
    }
  ],
  "tools_used": ["date_schedule_tool"]
}
```

### 장점
- ✅ 투명성: 사고 과정을 모두 볼 수 있음
- ✅ 도구 활용: 계산, 검색 등 정확한 작업
- ✅ 단계별 확인: 각 단계를 추적 가능

### 단점
- ❌ 단일 관점: 한 에이전트만 판단
- ❌ 전문성 부족: 모든 분야를 똑같이 처리

---

## 2️⃣ Multi-Agent Orchestrator (여러 전문 에이전트)

### 컨셉
```
여러 전문가들이 각자 맡은 분야를 처리하고 협업
```

### 작동 방식
```
사용자: "민원 처리 절차를 문서로 작성해주세요"

[Orchestrator가 판단]
→ 필요한 전문가: citizen_support + document_writing

1. citizen_support:    "민원 처리 절차는..."
2. document_writing:   "[공문서 형식으로 정리]..."
3. 결과 합성:          두 전문가 의견을 합침
```

### 전문 에이전트 (5개)
1. **citizen_support**: 시민 민원 상담 전문가
   - 친절한 답변, 공손한 어투
   - 예: "주민등록증 재발급 방법은?"

2. **document_writing**: 공문서 작성 전문가
   - 표준 양식, 격식 있는 표현
   - 예: "회의록 작성해줘"

3. **legal_research**: 법규 검색 전문가
   - 법령 인용, 조례 해석
   - 예: "개인정보보호법 제15조 설명"

4. **data_analysis**: 데이터 분석 전문가
   - 통계 분석, 트렌드 파악
   - 예: "지난 3개월 민원 통계 분석"

5. **review**: 문서 검토 전문가
   - 오류 확인, 개선 제안
   - 예: "작성한 보고서 검토해줘"

### 워크플로우 타입

#### Type 1: Single (단일)
```
사용자: "주민등록증 재발급 방법은?"
→ citizen_support만 실행
```

#### Type 2: Sequential (순차)
```
사용자: "민원 처리 절차 문서 작성"
→ citizen_support (절차 설명)
   → document_writing (문서 작성, 이전 결과 활용)
```

#### Type 3: Parallel (병렬, 최대 3개)
```
사용자: "법규 검토 + 데이터 분석 + 문서 작성"
→ legal_research ┐
→ data_analysis  ├── 동시 실행
→ document_writing ┘
```

### 예시 요청
```json
{
  "content": "민원 처리 절차를 법규에 맞게 문서로 작성",
  "use_multi_agent": true
}
```

### 응답 구조
```json
{
  "multi_agent_result": {
    "workflow_type": "sequential",
    "agent_outputs": {
      "legal_research": "[법규 검토 결과]...",
      "document_writing": "[공문서 형식]..."
    },
    "execution_log": [
      "legal_research started",
      "legal_research completed (3.2s)",
      "document_writing started (with context)",
      "document_writing completed (5.1s)"
    ],
    "execution_time_ms": 8300
  }
}
```

### 장점
- ✅ 전문성: 각 분야 전문가가 처리
- ✅ 협업: 여러 관점 결합
- ✅ 효율성: 병렬 처리 가능

### 단점
- ❌ 복잡성: 라우팅 오버헤드
- ❌ 비용: 여러 LLM 호출

---

## 실전 비교 예시

### 예시 1: "오늘 날짜는?"

#### ReAct Agent ✅ (적합)
```
Think: 날짜 도구 사용
Action: date_schedule_tool("today")
Observe: "2025-11-02"
Answer: "2025년 11월 2일입니다"

→ 도구 1개 사용, 1회 반복
```

#### Multi-Agent ❌ (과함)
```
Orchestrator: citizen_support 선택
citizen_support LLM: "죄송합니다만 정확한 날짜를..."

→ LLM 호출, 부정확할 수 있음
```

**결론**: **ReAct Agent 사용**

---

### 예시 2: "민원 처리 절차를 법규에 맞게 문서로 작성"

#### ReAct Agent ❌ (부족)
```
한 에이전트가:
1. 법규 검색 도구 사용
2. 문서 템플릿 도구 사용
3. 일반적인 답변 생성

→ 법규 전문성 부족, 문서 양식 부정확
```

#### Multi-Agent ✅ (적합)
```
Orchestrator: sequential workflow 선택
1. legal_research: 관련 법규 조회 (전문 프롬프트)
2. document_writing: 공문서 형식 작성 (전문 프롬프트)

→ 각 분야 전문가가 처리, 높은 품질
```

**결론**: **Multi-Agent 사용**

---

### 예시 3: "100 + 200은?"

#### ReAct Agent ✅ (적합)
```
Think: 계산 도구 사용
Action: calculator_tool(100 + 200)
Observe: "300"
Answer: "300입니다"

→ 정확한 계산
```

#### Multi-Agent ❌ (과함)
```
Orchestrator: data_analysis 선택?
LLM: "100 더하기 200은 300입니다"

→ LLM이 계산, 부정확할 수 있음
```

**결론**: **ReAct Agent 사용**

---

## 선택 가이드

### ReAct Agent를 사용하세요:
- ✅ 계산이 필요한 경우
- ✅ 날짜/일정 확인
- ✅ 문서 검색
- ✅ 단계별 추론이 필요한 경우
- ✅ "정확한 답"이 중요한 경우

**키워드**: 계산, 날짜, 검색, 며칠, 몇 개, 찾아줘

---

### Multi-Agent를 사용하세요:
- ✅ 복잡한 복합 작업
- ✅ 여러 전문 분야 필요
- ✅ 문서 작성 + 법규 검토
- ✅ 민원 상담 + 데이터 분석
- ✅ "전문성"이 중요한 경우

**키워드**: 작성, 검토, 분석, 상담, ~에 맞게, ~를 고려해서

---

## 함께 사용하기 (하이브리드)

두 시스템을 **조합**할 수도 있습니다:

```
사용자: "지난 3개월 민원 데이터를 분석하고 보고서 작성"

1. ReAct Agent:
   - data_analysis_tool로 데이터 추출
   - 통계 계산

2. Multi-Agent:
   - data_analysis: 트렌드 해석
   - document_writing: 보고서 작성
```

---

## 코드에서 사용법

### ReAct Agent
```python
# API 호출
POST /api/v1/chat/send
{
  "content": "오늘부터 연말까지 며칠?",
  "use_react_agent": true  // ← 이것만 추가
}
```

### Multi-Agent
```python
# API 호출
POST /api/v1/chat/send
{
  "content": "민원 절차 문서 작성",
  "use_multi_agent": true  // ← 이것만 추가
}
```

### 둘 다 사용 안 함 (기본 LLM)
```python
# API 호출
POST /api/v1/chat/send
{
  "content": "안녕하세요"
  // 플래그 없음 → 일반 LLM 응답
}
```

---

## 내부 구조 비교

### ReAct Agent 구조
```
ReActAgentService
├── Tools (도구들)
│   ├── calculator_tool
│   ├── date_schedule_tool
│   ├── document_search_tool
│   ├── data_analysis_tool
│   ├── document_template_tool
│   └── legal_reference_tool
├── LangGraph State Machine
│   ├── think_node (생각)
│   ├── act_node (행동)
│   └── should_continue (반복 여부)
└── execute_react_loop()
    → max 5 iterations
```

### Multi-Agent 구조
```
MultiAgentOrchestrator
├── Agents (전문가들)
│   ├── CitizenSupportAgent (시민상담)
│   ├── DocumentWritingAgent (문서작성)
│   ├── LegalResearchAgent (법규검색)
│   ├── DataAnalysisAgent (데이터분석)
│   └── ReviewAgent (검토)
├── LangGraph Workflow
│   ├── classify_intent_node (의도 파악)
│   ├── route_node (라우팅)
│   ├── execute_sequential_node (순차 실행)
│   └── execute_parallel_node (병렬 실행)
└── route_and_execute()
```

---

## 정리

| 비유 | ReAct Agent | Multi-Agent |
|------|-------------|-------------|
| **사람** | 만능 직원 1명 + 도구함 | 전문가 팀 5명 |
| **회사** | 총무부 직원 | 프로젝트 팀 |
| **요리** | 한 명의 셰프 + 조리도구 | 주방 + 홀 + 매니저 |
| **공사** | 다재다능 기술자 + 공구 | 전기/배관/목공 전문가들 |

**간단히**:
- **ReAct**: 도구 쓰는 똑똑한 1명
- **Multi-Agent**: 협업하는 전문가 여러명

**언제 뭘 써야할까?**:
- 계산/검색/날짜 → **ReAct**
- 복잡한 전문 작업 → **Multi-Agent**
- 일반 대화 → **둘 다 안 씀** (기본 LLM)
