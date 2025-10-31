# ReAct Agent 테스트 가이드

**목표**: Phase 9 (ReAct 에이전트) 기능을 수동 테스트하여 정상 작동 확인

**테스트 기간**: 2-3시간 예상
**환경**: 로컬 개발 환경 또는 Docker Compose

---

## 📋 테스트 체크리스트 (tasks.md T166-T171 기준)

### T166: ReAct 에이전트 2-3 도구 작업 완료 (<30초)

**Success Criteria**: SC-016
> ReAct agent completes multi-step tasks requiring 2-3 tool invocations within 30 seconds, with clear step-by-step display visible to user

#### 테스트 시나리오 1: 계산기 + 날짜 도구
```
사용자 질문:
"2023년 예산 1,500만원에 5% 증가율을 적용하고, 2024년 회계연도 기준으로 집행 기한을 계산해줘"

예상 동작:
1. 🤔 Thought: "예산 계산과 회계연도 기한을 계산해야 합니다"
2. ⚙️ Action: calculator(1500만원 * 1.05)
3. 👁️ Observation: "1575만원"
4. 🤔 Thought: "2024년 회계연도 집행 기한을 확인합니다"
5. ⚙️ Action: date_schedule("2024 회계연도 종료일")
6. 👁️ Observation: "2024년 12월 31일"
7. 최종 답변: "2024년 예산은 1,575만원이며, 집행 기한은 2024년 12월 31일까지입니다."

검증 항목:
- [ ] ReActDisplay 컴포넌트에 단계별 표시
- [ ] 이모지(🤔/⚙️/👁️) 정상 표시
- [ ] 도구 파라미터 접기/펼치기 동작
- [ ] 전체 실행 시간 30초 이내
- [ ] 최종 답변 정확성
```

#### 테스트 시나리오 2: 문서 검색 + 법규 참조
```
사용자 질문:
"업로드한 주차 관련 조례에서 주차 요금 관련 조항을 찾아줘"

사전 준비:
- 주차 관련 조례 문서(PDF) 업로드 필요

예상 동작:
1. 🤔 Thought: "업로드된 문서에서 주차 요금 조항을 검색합니다"
2. ⚙️ Action: document_search("주차 요금")
3. 👁️ Observation: "제5조 (주차요금) ..."
4. 🤔 Thought: "법규 참조 도구로 정확한 조항을 확인합니다"
5. ⚙️ Action: legal_reference("제5조")
6. 👁️ Observation: "제5조 전문 내용..."
7. 최종 답변: 조항 내용 + 해석

검증 항목:
- [ ] 문서 업로드 후 검색 정상 작동
- [ ] 법규 참조 도구 정확한 인용
- [ ] 실행 시간 30초 이내
```

---

### T167: 6개 도구 개별 테스트

**Success Criteria**: SC-017
> All six ReAct tools execute successfully with <10% error rate across 100 test invocations

각 도구별 최소 15-20회 테스트 (유효한 입력 + 엣지 케이스)

#### 1. Document Search Tool

**정상 케이스**:
```
질문: "업로드한 문서에서 '예산' 키워드를 찾아줘"
예상: 문서에서 예산 관련 구절 반환 (파일명, 페이지 번호 포함)
```

**엣지 케이스**:
```
- 문서 없을 때: "업로드된 문서가 없습니다" 에러
- 검색 결과 없을 때: "검색 결과를 찾을 수 없습니다"
- 특수문자 검색: 정규식 에러 없이 처리
```

**검증**:
- [ ] 검색 정확도 90% 이상
- [ ] 출처 참조 정확 (파일명, 페이지)
- [ ] 타임아웃 없이 30초 내 완료

#### 2. Calculator Tool

**정상 케이스**:
```
입력: "1,500만원 + 300만원"
예상: "18,000,000"
```

**엣지 케이스**:
```
- 한국어 단위: "1000원", "500만원" → 숫자 변환
- 백분율: "15% of 100" → 15
- 나눗셈: "100 / 0" → 에러 처리
```

**검증**:
- [ ] 성공률 95% 이상 (결정적 연산)
- [ ] 한국어 화폐 단위 처리
- [ ] 0 나눗셈 등 예외 처리

#### 3. Date/Schedule Tool

**정상 케이스**:
```
질문: "2024년 3월 1일부터 20 영업일 후는 언제?"
예상: 공휴일/주말 제외한 정확한 날짜
```

**엣지 케이스**:
```
- 공휴일 확인: "2024년 3월 1일은 공휴일인가요?"
- 회계연도: "2024년 회계연도 시작일은?"
- 과거 날짜: 과거 날짜 계산도 정상 작동
```

**검증**:
- [ ] 한국 공휴일 정확 반영 (`backend/data/korean_holidays.json` 사용)
- [ ] 영업일 계산 정확도 90% 이상
- [ ] 회계연도 로직 정확

#### 4. Data Analysis Tool

**정상 케이스**:
```
질문: "업로드한 CSV 파일의 예산 열 합계를 계산해줘"
사전 준비: 예산 데이터 CSV 업로드

예상: 합계, 평균, 중앙값 등 통계
```

**엣지 케이스**:
```
- 빈 파일: "데이터가 없습니다"
- 잘못된 컬럼명: "해당 컬럼을 찾을 수 없습니다"
- Excel 파일: .xlsx 확장자 지원
```

**검증**:
- [ ] CSV/Excel 파일 정상 로드
- [ ] 통계 계산 정확도 85% 이상
- [ ] 한국어 천 단위 쉼표 포매팅

#### 5. Document Template Tool

**정상 케이스**:
```
질문: "주차장 이용 안내문을 작성해줘"
예상: 공문서 형식 템플릿 (제목, 배경, 내용, 결론)
```

**엣지 케이스**:
```
- 보고서 템플릿: "월간 보고서 양식"
- 공문: "민원 답변 공문"
```

**검증**:
- [ ] 템플릿 100% 성공 (결정적 생성)
- [ ] Jinja2 템플릿 (`backend/templates/`) 정상 로드
- [ ] 한국어 공문서 형식 준수

#### 6. Legal Reference Tool

**정상 케이스**:
```
질문: "주차장 조례 제5조를 인용해줘"
사전 준비: 조례 문서 업로드

예상: 제5조 전문 + 조항 번호
```

**엣지 케이스**:
```
- 존재하지 않는 조항: "해당 조항을 찾을 수 없습니다"
- 범위 검색: "제5조부터 제10조까지"
```

**검증**:
- [ ] 조항 검색 정확도 90% 이상
- [ ] 인용 형식 정확 (조항 번호 + 내용)
- [ ] 쉬운 설명(plain-language) 제공

---

### T168: 도구 실행 성공률 <10% 에러

**Success Criteria**: SC-017
> All six ReAct tools execute successfully with <10% error rate across 100 test invocations

#### 테스트 방법:
1. 위 6개 도구 × 15-20회 = 총 90-120회 실행
2. 성공/실패 기록
3. 각 도구별 성공률 계산

**목표 성공률**:
- Document Search: ≥90%
- Calculator: ≥95%
- Date/Schedule: ≥90%
- Data Analysis: ≥85%
- Document Template: 100%
- Legal Reference: ≥90%

**실패 케이스 분류**:
- 타임아웃 (>30초)
- 파싱 에러
- 도구 실행 예외
- 잘못된 결과

---

### T169: ReAct 에이전트 5회 반복 제한

**Success Criteria**: FR-062
> Maximum 5 reasoning-action cycles per user query

#### 테스트 시나리오:
```
질문: "매우 복잡한 다단계 작업을 요청합니다.
문서 검색 → 계산 → 날짜 확인 → 데이터 분석 → 템플릿 생성 → 법규 참조를 모두 수행해주세요"

예상 동작:
- 5단계까지 실행 후 자동 중단
- 중단 메시지: "작업이 너무 복잡합니다. 질문을 단순화해주세요."
- 지금까지 수행한 단계 요약 표시
```

**검증**:
- [ ] 정확히 5단계에서 중단
- [ ] 중단 메시지 한국어로 표시
- [ ] 부분 결과 표시

---

### T170: 도구 실패 시 투명한 에러 표시

**Success Criteria**: FR-065
> Transparent failure - display error in Observation, agent provides alternative

#### 테스트 시나리오:
```
질문: "존재하지 않는 문서에서 검색해줘"

예상 동작:
1. 🤔 Thought: "문서를 검색합니다"
2. ⚙️ Action: document_search("키워드")
3. 👁️ Observation: "문서를 찾을 수 없습니다" (에러 표시)
4. 🤔 Thought: "문서가 없으므로 업로드를 요청합니다"
5. 최종 답변: "검색할 문서가 없습니다. 문서를 먼저 업로드해주세요."
```

**검증**:
- [ ] 에러가 Observation에 표시
- [ ] 에러 숨기지 않고 투명하게 표시
- [ ] AI가 대안 제시 또는 명확한 안내
- [ ] 시스템 크래시 없음

---

### T171: 도구 실행 감사 로그 검증

**Success Criteria**: FR-066
> All tool executions logged with timestamp, user_id, tool_name, sanitized params, result

#### 테스트 방법:

1. **몇 가지 도구 실행**:
   - 계산기 3회
   - 문서 검색 2회
   - 날짜 도구 1회

2. **관리자 대시보드에서 로그 확인**:
   - `/admin/tools/stats` 또는 `/admin/tools/executions/recent` 접속

3. **검증 항목**:
   - [ ] timestamp 정확
   - [ ] user_id 기록
   - [ ] tool_name 정확
   - [ ] input_parameters에 PII 없음 (sanitized)
   - [ ] output_result 500자 이내로 truncated
   - [ ] execution_time_ms 기록
   - [ ] success/failure 상태 정확

4. **PII 제거 확인**:
```sql
-- PostgreSQL에서 직접 확인
SELECT input_parameters, output_result
FROM tool_executions
ORDER BY created_at DESC
LIMIT 10;
```
   - 주민등록번호, 이메일 등 PII가 마스킹되었는지 확인

---

## 🚀 테스트 실행 절차

### 1단계: 환경 시작

```bash
# Docker Compose 환경 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 프론트엔드 접속
http://localhost:3000
```

### 2단계: 관리자 로그인

```
1. 관리자 계정으로 로그인
2. /admin/dashboard 접속
3. "ReAct 도구 관리" 메뉴 확인
```

### 3단계: 사용자 계정으로 테스트

```
1. 일반 사용자 계정으로 로그인
2. 새 대화 시작
3. 위 테스트 시나리오 순서대로 실행
4. 각 단계마다 스크린샷 캡처
```

### 4단계: 결과 기록

`REACT_TEST_RESULTS.md` 파일에 기록:

```markdown
# ReAct Agent 테스트 결과

## 실행 일시
2025-10-30 14:00

## 테스트 환경
- OS: Windows 11
- Docker: 25.0.0
- 브라우저: Chrome 120

## T166: 2-3 도구 작업 (30초 이내)
- ✅ 시나리오 1 통과 (실행 시간: 12초)
- ✅ 시나리오 2 통과 (실행 시간: 18초)

## T167: 6개 도구 개별 테스트
- ✅ Document Search: 18/20 성공 (90%)
- ✅ Calculator: 20/20 성공 (100%)
- ✅ Date/Schedule: 17/20 성공 (85%)
- ❌ Data Analysis: 14/20 성공 (70%) → 목표 미달 (85%)
  - 실패 원인: Excel 파일 인코딩 문제 6건
- ✅ Document Template: 20/20 성공 (100%)
- ✅ Legal Reference: 19/20 성공 (95%)

## 발견된 이슈
1. Data Analysis Tool: Excel 파일 한글 인코딩 오류
2. ...
```

---

## 📊 성공 기준 요약

| 테스트 | 목표 | 통과 기준 |
|--------|------|-----------|
| T166 | 2-3 도구 작업 30초 이내 | 실행 시간 <30초 + 정확한 답변 |
| T167 | 6개 도구 개별 테스트 | 각 도구 성공률 목표치 이상 |
| T168 | 전체 에러율 <10% | 90-120회 실행 중 성공률 >90% |
| T169 | 5회 반복 제한 | 5단계 자동 중단 + 메시지 |
| T170 | 투명한 에러 표시 | Observation에 에러 표시 + 대안 제시 |
| T171 | 감사 로그 | 관리자 대시보드에서 로그 확인 가능 |

---

## 🐛 이슈 발견 시 조치

1. **GitHub Issue 생성**: `12_localAgent` 저장소
2. **재현 단계 기록**
3. **스크린샷/로그 첨부**
4. **Priority 라벨 추가**:
   - P0: 시스템 크래시
   - P1: 기능 완전 실패
   - P2: 부분 실패
   - P3: UX 개선

---

## ✅ 테스트 완료 후

모든 테스트 통과 시:
1. `REACT_TEST_RESULTS.md` 작성
2. Phase 9 완료 마크 (`tasks.md` 업데이트)
3. 데모 준비:
   - 대표 시나리오 3개 선정
   - 스크린샷/비디오 녹화
   - 데모 스크립트 작성

**예상 소요 시간**: 2-3시간

이슈 발견 시:
1. 우선순위 분류
2. 긴급 수정 (P0, P1) 또는
3. Phase 10 진행 후 수정 (P2, P3)

---

**다음 단계**: Phase 10 (Multi-Agent System) 또는 프로덕션 배포 준비
