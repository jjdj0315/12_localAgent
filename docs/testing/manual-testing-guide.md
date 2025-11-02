# 수동 테스트 가이드

**프로젝트**: Local LLM Web Application for Local Government
**목적**: Constitution에 따른 수동 acceptance testing 실행 가이드
**대상**: 개발자, QA 담당자, 최종 사용자 (공무원)

---

## 📋 수동 테스트 개요

**Constitution L6 명시사항**:
> "Manual acceptance testing per user story scenarios (spec.md) is MANDATORY per constitution. Automated unit/integration tests are NOT required."

**테스트 우선순위**:
1. **Phase 9 (US7)**: ReAct Agent 기능 테스트 (T166-T171)
2. **Phase 10 (US8)**: Multi-Agent System 테스트 (T197B-T204)

---

## Phase 9: ReAct Agent 테스트 (US7)

### T166: ReAct 에이전트 2-3 도구 작업 완료 시간 테스트

**목표**: SC-016 검증 - 30초 내 완료

**테스트 시나리오**:
```
사용자 입력: "2023년 예산 1,500만원에 5% 증가율을 적용하고, 2024년 회계연도 기준으로 집행 기한을 계산해줘"
```

**예상 결과**:
1. **Thought**: "예산 계산과 회계연도 기한 계산이 필요합니다"
2. **Action**: Calculator(1500만 * 1.05)
3. **Observation**: 1575만원
4. **Action**: DateSchedule(2024 회계연도 집행 기한)
5. **Observation**: 2024-12-31
6. **Final Answer**: "2024년 예산은 1,575만원이며, 집행 기한은 2024년 12월 31일입니다."

**합격 기준**:
- ✅ 총 실행 시간 ≤ 30초
- ✅ 2개 도구 모두 성공적으로 실행
- ✅ Thought/Action/Observation 단계가 명확히 표시됨

**테스트 방법**:
1. 웹 UI에서 새 대화 시작
2. 위 질문 입력
3. Stopwatch로 시간 측정
4. 결과 검증

**기록 양식**:
- [ ] 실행 시간: ____ 초
- [ ] Tool 1 (Calculator): ✅/❌
- [ ] Tool 2 (DateSchedule): ✅/❌
- [ ] UI 표시 상태: ✅/❌

---

### T167: 6개 도구 개별 테스트

**목표**: 각 도구 독립 실행 검증

#### Tool 1: Document Search
```
테스트 시나리오:
1. PDF 문서 업로드 (예: 주차 관련 조례.pdf)
2. 질문: "주차 위반 과태료 규정을 찾아줘"

예상 결과:
- 🤔 Thought: "업로드된 문서에서 과태료 규정을 검색해야 합니다"
- ⚙️ Action: DocumentSearch("과태료")
- 👁️ Observation: "제15조 (과태료) ... [page 5]"
```

**합격**: ✅ 문서 내용 정확히 검색, 페이지 번호 표시

---

#### Tool 2: Calculator
```
테스트 시나리오:
질문: "1,234,567원에 부가세 10%를 더하면?"

예상 결과:
- 🤔 Thought: "금액 계산이 필요합니다"
- ⚙️ Action: Calculator(1234567 * 1.1)
- 👁️ Observation: 1358023.7
```

**합격**: ✅ 정확한 계산 결과, 한국어 통화 기호 처리

---

#### Tool 3: Date/Schedule
```
테스트 시나리오:
질문: "오늘부터 10 영업일 후는 언제야?"

예상 결과:
- 🤔 Thought: "영업일 계산이 필요합니다"
- ⚙️ Action: DateSchedule(today + 10 business days)
- 👁️ Observation: 2025-11-15 (공휴일 제외)
```

**합격**: ✅ 한국 공휴일 제외 정확한 영업일 계산

---

#### Tool 4: Data Analysis
```
테스트 시나리오:
1. CSV 파일 업로드 (예: 예산집행내역.csv)
2. 질문: "월별 예산 집행 합계를 계산해줘"

예상 결과:
- 🤔 Thought: "CSV 데이터 분석이 필요합니다"
- ⚙️ Action: DataAnalysis("sum by month")
- 👁️ Observation: 1월: 1,234,567원, 2월: ...
```

**합격**: ✅ CSV 데이터 정확히 분석, 천 단위 쉼표 표시

---

#### Tool 5: Document Template
```
테스트 시나리오:
질문: "주차 위반 민원 답변 공문서를 작성해줘"

예상 결과:
- 🤔 Thought: "공문서 템플릿이 필요합니다"
- ⚙️ Action: DocumentTemplate("민원답변", "주차 위반")
- 👁️ Observation: [표준 공문서 형식]
  - 제목: 주차 위반 관련 민원 답변
  - 수신: [민원인]
  - 내용: ...
  - 발신: [담당 부서]
```

**합격**: ✅ 정확한 공문서 형식, 한국어 공문 용어 사용

---

#### Tool 6: Legal Reference
```
테스트 시나리오:
1. 조례 문서 업로드 (예: 주차장설치및관리조례.pdf)
2. 질문: "주차장 설치 기준을 찾아줘"

예상 결과:
- 🤔 Thought: "법규 조항 검색이 필요합니다"
- ⚙️ Action: LegalReference("설치 기준")
- 👁️ Observation: "제5조 (설치 기준) ... [조례 명칭]"
```

**합격**: ✅ 조항 번호 정확히 인용, 조례명 명시

---

### T168: 도구 실행 성공률 테스트

**목표**: SC-017 검증 - <10% 오류율

**테스트 방법**:
각 도구당 15-20회 실행 (유효한 입력 + 엣지 케이스)

**합격 기준**:
| 도구 | 목표 성공률 | 실제 성공률 | 상태 |
|------|------------|------------|------|
| Document Search | ≥90% | __% | ✅/❌ |
| Calculator | ≥95% | __% | ✅/❌ |
| Date/Schedule | ≥90% | __% | ✅/❌ |
| Data Analysis | ≥85% | __% | ✅/❌ |
| Document Template | 100% | __% | ✅/❌ |
| Legal Reference | ≥90% | __% | ✅/❌ |

---

### T169: ReAct 5회 반복 제한 테스트

**테스트 시나리오**:
```
질문: "존재하지 않는 문서에서 정보를 계속 찾아줘"
```

**예상 결과**:
1. Action: DocumentSearch("정보") → 실패
2. Action: DocumentSearch("데이터") → 실패
3. Action: DocumentSearch("내용") → 실패
4. Action: DocumentSearch("문서") → 실패
5. Action: DocumentSearch("파일") → 실패
6. **시스템 중단**: "작업이 너무 복잡합니다. 질문을 단순화해주세요."
7. **요약 표시**: 5번 시도 내역 표시

**합격**: ✅ 정확히 5회 반복 후 중단, 유용한 요약 제공

---

### T170: 도구 실패 시 투명한 오류 표시

**테스트 시나리오**:
```
질문: "문서를 검색해줘" (문서 업로드 없이)
```

**예상 결과**:
- 🤔 Thought: "문서 검색이 필요합니다"
- ⚙️ Action: DocumentSearch()
- 👁️ Observation: **"문서를 찾을 수 없습니다"** (빨간색 표시)
- 🤔 Thought: "업로드된 문서가 없으므로 검색할 수 없습니다. 문서를 업로드해주세요."

**합격**: ✅ 오류가 숨겨지지 않고 명확히 표시, 대안 제공

---

### T171: 도구 실행 감사 로그 검증

**테스트 방법**:
1. 관리자 계정으로 로그인
2. 고급 기능 대시보드 → 감사 로그 메뉴
3. 최근 도구 실행 로그 확인

**검증 항목**:
- [ ] Timestamp 기록됨
- [ ] User ID 기록됨
- [ ] Tool name 정확함
- [ ] Input parameters 표시 (개인정보는 삭제됨)
- [ ] Output result (500자 제한)
- [ ] Execution time (ms)
- [ ] Success/Failure status

**합격**: ✅ 모든 필드가 정확히 로깅됨, PII 삭제 확인

---

## Phase 10: Multi-Agent System 테스트 (US8)

### T197B: GGUF 모델 로딩 테스트

**목표**: Qwen3-4B-Instruct Q4_K_M 모델 로딩 검증

**테스트 방법**:
```bash
# Backend 로그 확인
docker-compose logs -f backend

# 예상 로그:
# INFO: Loading GGUF model: qwen3-4b-instruct-q4_k_m.gguf
# INFO: Model size: ~2.5GB
# INFO: Load time: <1 second
# INFO: CPU optimizations: AVX2, FMA, F16C enabled
```

**합격 기준**:
- [ ] 모델 로드 성공
- [ ] 파일 크기: 2.4-2.6GB
- [ ] 로드 시간: <1초
- [ ] CPU 최적화 활성화 확인

---

### T197C: Dummy LoRA 어댑터 감지

**테스트 방법**:
```bash
ls models/lora_adapters/

# 예상 출력:
# citizen_support/
# document_writing/
# (기타 에이전트 디렉토리)
```

**검증**:
- [ ] 5개 에이전트 디렉토리 존재
- [ ] Dummy 파일 감지 시 오류 없이 진행
- [ ] 로그에 "LoRA adapter optional" 메시지 표시

---

### T198: Orchestrator 라우팅 정확도 테스트

**목표**: SC-021 검증 - 85%+ 정확도

**테스트 데이터셋** (50개 쿼리, 각 에이전트당 10개):

#### Citizen Support Agent (10개)
1. "주차 위반 과태료 민원에 대한 답변을 작성해줘"
2. "소음 신고 민원인에게 어떻게 답변해야 하나요?"
3. "재산세 납부 문의에 대한 친절한 답변 초안을 만들어줘"
4. (7개 더 추가)

#### Document Writing Agent (10개)
1. "2024년 예산 보고서를 작성해줘"
2. "주민 대상 코로나 방역 안내문을 만들어줘"
3. "청사 공사 공고문 초안을 작성해줘"
4. (7개 더 추가)

#### Legal Research Agent (10개)
1. "주차장 설치 기준 조례를 찾아줘"
2. "개인정보 보호 관련 법규를 검색해줘"
3. "재산세 부과 기준을 조례에서 찾아줘"
4. (7개 더 추가)

#### Data Analysis Agent (10개)
1. "지난달 예산 집행 통계를 분석해줘"
2. "민원 유형별 건수를 집계해줘"
3. "분기별 수입 추이를 시각화해줘"
4. (7개 더 추가)

#### Review Agent (10개)
1. "이 민원 답변에 오류가 있는지 검토해줘"
2. "보고서 초안을 검토하고 개선점을 알려줘"
3. "공문서 형식이 맞는지 확인해줘"
4. (7개 더 추가)

**테스트 실행**:
```python
# scripts/test_orchestrator_routing.py 실행
python scripts/test_orchestrator_routing.py

# 예상 출력:
# Correct routes: 43/50 (86%)
# ✅ PASS: Routing accuracy ≥85%
```

**합격**: ✅ 43개 이상 정확 라우팅 (86%)

---

### T199: 순차적 3-에이전트 워크플로우 테스트

**목표**: SC-022 검증 - 90초 내 완료

**테스트 시나리오**:
```
질문: "주차 관련 조례를 검색하고, 민원 답변 초안을 작성하고, 검토해줘"
```

**예상 워크플로우**:
1. **Orchestrator**: 3-agent workflow 생성
   - Legal Research → Document Writing → Review
2. **Legal Research Agent** (30초):
   - 조례 검색 결과 반환
3. **Document Writing Agent** (40초):
   - Legal Research 결과 활용하여 초안 작성
4. **Review Agent** (20초):
   - 초안 검토, 개선점 제안
5. **Final Output**: 3개 에이전트 기여 분명히 표시

**합격 기준**:
- [ ] 총 실행 시간: ≤90초
- [ ] 3개 에이전트 모두 성공
- [ ] 각 에이전트 출력 명확히 구분됨
- [ ] 품질: 실제 사용 가능한 답변

---

### T200: 병렬 에이전트 실행 테스트

**테스트 시나리오**:
```
질문: "예산 데이터를 분석하고, 동시에 관련 조례를 검색해줘"
```

**예상 워크플로우**:
1. **Orchestrator**: 2-agent parallel dispatch
   - Data Analysis Agent (병렬)
   - Legal Research Agent (병렬)
2. **동시 실행** (max 3 parallel):
   - 두 에이전트가 동시에 작업
3. **결과 병합**:
   - 두 에이전트 출력 결합하여 표시

**합격**: ✅ 병렬 실행 확인 (단일 에이전트 대비 시간 단축)

---

### T201: 에이전트 실패 처리 테스트

**테스트 시나리오**:
```
1. 업로드된 문서 없이 Legal Research 요청
2. Legal Research 실패
3. Document Writing Agent로 전달
```

**예상 결과**:
- ⚖️ **Legal Research Agent**: "문서를 찾을 수 없습니다" (실패)
- 📋 **Document Writing Agent**: "이전 단계가 실패하여 작업을 완료할 수 없습니다"
- **사용자 안내**: "조례 문서를 업로드하고 다시 시도해주세요"

**합격**: ✅ 실패 전파 확인, 명확한 사용자 안내

---

### T202: 워크플로우 복잡도 제한 테스트

**테스트 시나리오**:
```
질문: "6개 에이전트를 사용해서 복잡한 작업 수행해줘"
(Legal → Data → Document → Review → Citizen → Legal)
```

**예상 결과**:
- **Error**: "작업 시간이 초과되었습니다"
- **Limit**: 5 agents/chain, 3 parallel, 5-minute timeout
- **Partial results**: 5개 에이전트까지의 결과 표시

**합격**: ✅ 제한 적용됨, 부분 결과 표시

---

### T203: 에이전트 기여 Attribution 검증

**테스트 방법**:
웹 UI에서 multi-agent 응답 확인

**예상 UI**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ 법규 검색 에이전트:
주차장 설치 기준은 제5조에 명시되어 있습니다...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 문서 작성 에이전트:
민원 답변 초안을 작성했습니다...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 검토 에이전트:
초안을 검토한 결과, 다음 개선이 필요합니다...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**합격**: ✅ 각 에이전트 명확히 표시, 구분선 사용

---

### T204: CPU 성능 테스트

**테스트 환경**:
- CPU: 8-16 core Intel/AMD
- RAM: 32GB
- No GPU

**테스트 방법**:
1. 단일 쿼리 응답 시간 측정
2. 3-agent workflow 시간 측정

**합격 기준**:
- [ ] 단일 쿼리: 8-12초 (SC-001 CPU baseline)
- [ ] 3-agent workflow: ≤90초 (SC-022)
- [ ] CPU 사용률: 70-90% (효율적 활용)

---

## 📝 테스트 결과 기록 양식

### Phase 9 (ReAct Agent) 요약

| 작업 ID | 테스트 항목 | 상태 | 실행일 | 담당자 | 비고 |
|---------|-----------|------|--------|--------|------|
| T166 | 2-3 tool task ≤30s | ⬜ | | | |
| T167 | 6 tools individual | ⬜ | | | |
| T168 | Tool success rate >90% | ⬜ | | | |
| T169 | 5-iteration limit | ⬜ | | | |
| T170 | Transparent error | ⬜ | | | |
| T171 | Audit log verification | ⬜ | | | |

### Phase 10 (Multi-Agent) 요약

| 작업 ID | 테스트 항목 | 상태 | 실행일 | 담당자 | 비고 |
|---------|-----------|------|--------|--------|------|
| T197B | GGUF model loading | ⬜ | | | |
| T197C | LoRA adapter detection | ⬜ | | | |
| T198 | Routing accuracy ≥85% | ⬜ | | | |
| T199 | 3-agent workflow ≤90s | ⬜ | | | |
| T200 | Parallel execution | ⬜ | | | |
| T201 | Failure handling | ⬜ | | | |
| T202 | Complexity limits | ⬜ | | | |
| T203 | Agent attribution | ⬜ | | | |
| T204 | CPU performance | ⬜ | | | |

---

## ✅ 최종 합격 기준

**Phase 9 (ReAct Agent)**:
- ✅ 6/6 테스트 통과

**Phase 10 (Multi-Agent)**:
- ✅ 9/9 테스트 통과

**Overall**:
- ✅ 15/15 수동 테스트 통과
- ✅ SC-016, SC-017, SC-021, SC-022 모두 충족
- ✅ Constitution 수동 테스트 요구사항 준수

---

**작성일**: 2025-11-01
**버전**: 1.0
**다음 업데이트**: 테스트 완료 후 결과 기록
