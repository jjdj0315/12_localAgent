# Phase 9/10 수동 테스트 가이드

## 환경 제약사항

**Cygwin Bash + Windows Python 호환성 문제**로 인해 백엔드 서버를 자동으로 시작할 수 없습니다. 백엔드는 **Windows CMD 또는 PowerShell**에서 직접 실행해야 합니다.

## 완료된 작업 ✅

1. **T165**: ReActDisplay 컴포넌트 프론트엔드 통합 완료
   - 파일: `frontend/src/app/chat/page.tsx`
   - ReAct 에이전트 모드 토글 UI 추가
   - ReAct 단계, 사용된 도구 표시 기능

2. **T197**: MultiAgentDisplay 컴포넌트 프론트엔드 통합 완료
   - 파일: `frontend/src/app/chat/page.tsx`
   - Multi-Agent 모드 토글 UI 추가
   - 워크플로 타입, 에이전트 기여도, 실행 시간 표시

3. **T197A, T197B**: LLM 서비스 팩토리 및 모델 로딩 검증 완료
   - Qwen2.5-3B-Instruct GGUF 모델 (2GB, Q4_K_M 양자화)
   - 로딩 시간: 435ms
   - CPU 최적화: AVX2, FMA, F16C

4. **PostgreSQL** 컨테이너 시작 완료
   - 컨테이너: `llm-webapp-postgres`
   - 상태: Running (포트 5432)

5. **데이터베이스** 마이그레이션 완료
   - Alembic 마이그레이션 성공

6. **관리자 계정** 확인
   - Username: `admin`
   - Password: `admin123!`

## 수동 테스트 실행 방법

### 1단계: 백엔드 서버 시작

**새 PowerShell 또는 CMD 창을 열고** 다음 실행:

```powershell
cd C:\02_practice\12_localAgent\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**예상 출력**:
```
[LLM Factory] Initializing LLM backend: llama_cpp
[LLM Factory] Loading llama.cpp service (Test mode)
[LlamaCpp] Initializing with:
  Model: C:/02_practice/12_localAgent/models/qwen2.5-3b-instruct-q4_k_m.gguf
  Context: 2048 tokens
  Threads: 12
  GPU layers: 0
[LlamaCpp] Loading model... (this may take 30-60 seconds)
[LlamaCpp] [OK] Model loaded successfully!
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2단계: API 테스트 (옵션 A - 자동)

**다른 터미널에서** 테스트 스크립트 실행:

```powershell
cd C:\02_practice\12_localAgent
python test_api.py
```

**테스트 항목**:
- ✓ TEST 1: 관리자 로그인
- ✓ TEST 2: 기본 채팅 (일반 모드)
- ✓ TEST 3: ReAct 에이전트 모드
- ✓ TEST 4: Multi-Agent 모드

### 2단계: 웹 UI 테스트 (옵션 B - 수동)

#### 백엔드 API 확인
브라우저에서 http://127.0.0.1:8000/docs 열기

#### 프론트엔드 시작
```powershell
cd C:\02_practice\12_localAgent\frontend
npm run dev
```

브라우저에서 http://localhost:3000 열기

#### 테스트 시나리오

**T166-T171: ReAct 에이전트 테스트**

1. 로그인: `admin` / `admin123!`
2. **ReAct 모드 활성화** (토글 버튼 클릭)
3. 테스트 질문:
   - "1234 곱하기 567은 얼마인가요?" (계산기 도구)
   - "오늘 날짜는 언제인가요?" (날짜 도구)
   - "법령 123호의 내용을 알려주세요" (법규 참조 도구)

**확인사항**:
- [ ] ReAct 단계가 표시되는가? (Thought → Action → Observation)
- [ ] 사용된 도구가 표시되는가?
- [ ] 2-3개 도구 사용 시 30초 이내 완료되는가? (T166)
- [ ] 최대 5번 반복 후 종료되는가? (T169)
- [ ] 에러 발생 시 명확한 메시지가 표시되는가? (T170)

**T198-T204: Multi-Agent 시스템 테스트**

1. **Multi-Agent 모드 활성화** (토글 버튼 클릭)
2. 테스트 질문:
   - "지자체 예산 관련 공문서 작성 방법을 알려주세요" (문서 작성 에이전트)
   - "민원인이 건축 허가에 대해 문의했습니다" (민원 지원 에이전트)
   - "최근 5년간 예산 집행률 데이터를 분석해주세요" (데이터 분석 에이전트)

**확인사항**:
- [ ] 워크플로 타입이 표시되는가? (single/sequential/parallel)
- [ ] 각 에이전트의 기여도가 표시되는가?
- [ ] 에이전트별 아이콘과 색상이 구분되는가?
- [ ] 실행 시간이 표시되는가?
- [ ] 순차 워크플로가 90초 이내 완료되는가? (T199)
- [ ] 병렬 실행 시 최대 3개 에이전트가 동시 실행되는가? (T200)

## 남은 테스트 항목

### Phase 9: ReAct Agent (T166-T171)

- [ ] **T166**: 2-3 도구 작업 30초 내 완료
- [ ] **T167**: 6개 도구 개별 테스트
  - [ ] 계산기 도구
  - [ ] 날짜/일정 도구
  - [ ] 문서 검색 도구
  - [ ] 데이터 분석 도구
  - [ ] 문서 템플릿 도구
  - [ ] 법규 참조 도구
- [ ] **T168**: 도구 실행 성공률 테스트 (100회, <10% 에러)
- [ ] **T169**: 최대 반복 횟수 (5회 제한)
- [ ] **T170**: 투명한 에러 표시
- [ ] **T171**: 도구 실행 감사 로그 검증

### Phase 10: Multi-Agent System (T197C-T204)

- [ ] **T197C**: Dummy LoRA 어댑터 감지
- [ ] **T198**: 오케스트레이터 라우팅 정확도 (50개 쿼리, 85%+)
- [ ] **T199**: 순차 3-에이전트 워크플로 (90초 이내)
- [ ] **T200**: 병렬 에이전트 실행 (최대 3개)
- [ ] **T201**: 에이전트 실패 처리
- [ ] **T202**: 워크플로 복잡도 한계 테스트
- [ ] **T203**: 에이전트 속성 표시 검증
- [ ] **T204**: CPU 성능 테스트

## 테스트 데이터 수집

각 테스트 항목에 대해 다음 정보를 기록하세요:

```markdown
### T166: 2-3 도구 작업 30초 내 완료

**테스트 일시**: 2025-10-31 11:00
**테스트 질문**: "1234 곱하기 567은?"
**사용된 도구**: calculator
**실행 시간**: 2.3초
**결과**: PASS ✓
**비고**: 정상 동작
```

## 문제 해결

### 백엔드가 시작되지 않을 때

1. PostgreSQL 컨테이너 확인:
   ```bash
   docker ps | grep postgres
   ```

2. 포트 8000 사용 중인지 확인:
   ```powershell
   netstat -ano | findstr :8000
   ```

3. .env 파일 확인:
   ```bash
   cat backend/.env
   ```

### 테스트 실패 시

1. 백엔드 로그 확인
2. 프론트엔드 개발자 콘솔 확인 (F12)
3. 네트워크 탭에서 API 요청/응답 확인

## 참고사항

- 이 문서는 Cygwin bash 환경 제약으로 인한 수동 테스트 가이드입니다.
- 프로덕션 환경에서는 Docker Compose로 전체 스택을 실행할 수 있습니다.
- 모든 기능 구현은 완료되었으며, 테스트만 수동으로 진행하면 됩니다.

---

## Feature 002: Admin Metrics History Dashboard 수동 테스트 (Phase 11.5)

### Prerequisites
- 백엔드 서버 실행 중 (APScheduler 자동 시작됨)
- Admin 계정으로 로그인
- Admin 대시보드 페이지 접속 (`/admin` 또는 `/admin/dashboard`)

### T205O: 시간별/일별 메트릭 수집 테스트 (SC-022: 99% reliability)
**목적**: 자동 메트릭 수집이 정상 작동하는지 확인

**테스트 절차**:
1. 백엔드 로그에서 `"시간별 메트릭 수집 작업 시작"` 메시지 확인 (매시 정각)
2. Admin API에서 collection status 확인:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/metrics/status
   ```
3. `last_collection_at` 값이 최근 5분 이내인지 확인
4. `failure_count_24h` 값이 3개 미만인지 확인

**성공 기준**: ✅ 
- 시간별 수집이 매시 정각에 자동 실행
- 실패율 <1% (24시간 동안 1개 이하 실패)

---

### T205P: 수집 성능 테스트 (SC-023: <5초, non-blocking)
**목적**: 메트릭 수집이 사용자 작업에 영향을 주지 않는지 확인

**테스트 절차**:
1. 백엔드 로그에서 수집 작업 시작/종료 시간 확인:
   ```
   [시간별 메트릭 수집 작업 시작]
   [시간별 메트릭 수집 완료 - 성공: 6, 실패: 0]  # <-- 이 두 줄 사이 시간차 확인
   ```
2. Chat page에서 LLM 응답 요청 (수집 중)
3. 응답 속도가 정상인지 확인 (10초 이내)

**성공 기준**: ✅
- 메트릭 수집 완료 시간 <5초
- Chat 응답 속도 영향 없음 (백그라운드 실행)

---

### T205Q: 7일 메트릭 로딩 성능 테스트 (SC-021: <2초)
**목적**: 시계열 데이터 조회가 빠르게 로딩되는지 확인

**테스트 절차**:
1. Admin 대시보드 페이지 접속
2. 브라우저 DevTools Network 탭 열기 (F12)
3. Time range를 "7일"로 선택
4. `/api/v1/metrics/timeseries` API 호출 시간 확인

**성공 기준**: ✅ Response time <2초

---

### T205R: 트렌드 식별 테스트 (SC-024: 30초 이내)
**목적**: 관리자가 메트릭 트렌드를 빠르게 파악할 수 있는지 확인

**테스트 절차**:
1. Admin 대시보드에서 MetricsGraph 컴포넌트 확인
2. 다음 질문에 30초 이내 답변 가능한지 확인:
   - "최근 7일간 active_users가 증가했는가, 감소했는가?"
   - "storage_bytes 증가율이 가장 높은 날은 언제인가?"
   - "conversation_count가 급증한 시점이 있는가?"

**성공 기준**: ✅ 
- 그래프가 명확하게 표시됨 (Chart.js)
- Tooltip에 정확한 값과 timestamp 표시 (한글 형식)
- 30초 이내에 트렌드 파악 가능

---

### T205S: CSV/PDF 내보내기 테스트 (SC-025: 첫 시도 성공)
**목적**: 도움 없이 데이터 내보내기가 가능한지 확인

**테스트 절차**:
1. Admin 대시보드에서 "내보내기" 버튼 클릭
2. CSV 형식 선택, 메트릭 타입 선택 (1개 이상), 시간 범위 선택
3. "다운로드" 버튼 클릭
4. 다운로드된 CSV 파일 열기 (Excel 또는 텍스트 편집기)
5. 동일한 절차로 PDF 내보내기 테스트

**성공 기준**: ✅
- 도움 없이 첫 시도에 성공
- CSV: 데이터가 올바른 형식으로 내보내기됨
- PDF: 한글 폰트가 정상 표시됨 (NanumGothic)
- 파일 크기 <10MB (자동 LTTB downsampling 적용)

---

### T205T: 90일 데이터 보관 테스트 (SC-026: corruption 없음)
**목적**: 장기 데이터 보관이 corruption 없이 유지되는지 확인

**테스트 절차**:
1. 데이터베이스에서 metric_snapshots 테이블 조회:
   ```sql
   SELECT granularity, MIN(collected_at), MAX(collected_at), COUNT(*) 
   FROM metric_snapshots 
   GROUP BY granularity;
   ```
2. Hourly 데이터: 최대 30일 보관 확인
3. Daily 데이터: 최대 90일 보관 확인
4. 데이터 무결성 확인 (NULL 값, 중복 레코드 없음):
   ```sql
   SELECT COUNT(*) FROM metric_snapshots WHERE value IS NULL;
   ```

**성공 기준**: ✅
- Hourly: 30일 이내 데이터만 존재
- Daily: 90일 이내 데이터만 존재
- NULL 값 0개
- unique_metric_snapshot constraint 위반 0건

---

### T205U: 클라이언트 다운샘플링 테스트 (SC-027: <3초 렌더링)
**목적**: 대용량 데이터도 빠르게 렌더링되는지 확인

**테스트 절차**:
1. Admin 대시보드에서 time range를 "90일" (daily) 선택
2. 브라우저 Performance 탭 (F12) 열기
3. "Recording" 시작 후 그래프 렌더링 시간 측정
4. DevTools Console에서 다운샘플링 로그 확인:
   ```
   [Metrics] Downsampled 2000 points to 1000 points using LTTB
   ```

**성공 기준**: ✅
- 렌더링 시간 <3초
- 데이터 포인트 >1000개일 경우 자동 다운샘플링 적용
- 그래프 시각적 특성 유지 (LTTB 알고리즘)

---

### T205V: 수집 상태 표시기 테스트 (FR-106: 색상 기준)
**목적**: 수집 상태 표시기가 올바른 색상을 표시하는지 확인

**테스트 절차**:
1. Admin 대시보드에서 MetricsCollectionStatus 컴포넌트 확인
2. 정상 상태 (Green):
   - 최근 수집: <5분 전
   - 24시간 실패: <3건
3. 경고 상태 (Yellow) 시뮬레이션:
   - 스케줄러 일시 중단 후 5-60분 대기
   - 또는 3-10회 실패 기록 생성
4. 위험 상태 (Red) 시뮬레이션:
   - 스케줄러 1시간 이상 중단
   - 또는 10회 이상 실패 기록

**성공 기준**: ✅
- Green: last_collection <5min AND failures <3
- Yellow: failures 3-10 OR 5-60min ago
- Red: failures >10 OR >1hr ago
- 30초마다 자동 갱신

---

## Feature 002 테스트 완료 체크리스트

- [ ] T205O: 시간별/일별 메트릭 수집 (99% reliability)
- [ ] T205P: 수집 성능 (<5초, non-blocking)
- [ ] T205Q: 7일 메트릭 로딩 (<2초)
- [ ] T205R: 트렌드 식별 (30초 이내)
- [ ] T205S: CSV/PDF 내보내기 (첫 시도 성공)
- [ ] T205T: 90일 데이터 보관 (corruption 없음)
- [ ] T205U: 클라이언트 다운샘플링 (<3초 렌더링)
- [ ] T205V: 수집 상태 표시기 (색상 기준)

**모든 테스트 통과 시**: Phase 11.5 완료 ✅

