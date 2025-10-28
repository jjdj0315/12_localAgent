# Plan.md 업데이트 완료 보고서

**작업 일시**: 2025-10-28
**작업 내용**: spec.md의 새로운 요구사항 (FR-029 ~ FR-041)을 plan.md에 반영

---

## 📋 업데이트 요약

spec.md에 추가된 13개 새로운 요구사항과 6개 수정사항을 plan.md의 구현 계획에 반영했습니다.

---

## 🔄 업데이트된 섹션

### 1. Technical Context

#### LLM Infrastructure 섹션
**이전**:
```
- Context Management: In-memory conversation context with 4,000 character response limit
```

**업데이트**:
```
- Context Management: 10-message window (5 user + 5 AI), 2,048 token limit, FIFO removal when exceeded (FR-036)
- Response Limits: Default 4,000 characters / Document generation mode 10,000 characters (FR-017)
```

#### Authentication & Security 섹션 (대폭 확장)
**추가된 내용**:
- ✅ bcrypt cost factor 12 명시 (FR-029)
- ✅ 비밀번호 복잡도 정책 (FR-029)
- ✅ 동시 로그인 3개 세션 제한 (FR-030)
- ✅ 세션 타임아웃 상세 설명 (30분, 3분 전 경고, 임시 저장) (FR-012)
- ✅ 로그인 보호 메커니즘 (계정 잠금, IP 속도 제한) (FR-031)
- ✅ 데이터 격리 3단계 (DB, API, Admin) (FR-032)
- ✅ 권한 상승 방지 (별도 admin 테이블) (FR-033)

#### Target Platform 섹션
**추가된 내용**:
- ✅ 서버 최소 하드웨어 사양 명시
- ✅ 브라우저 호환성 구체화 (Chrome 90+, Edge 90+, Firefox 88+)
- ✅ 최소 해상도 및 JavaScript 필수 명시
- ✅ Internet Explorer 미지원 명시 (FR-040)

#### Constraints 섹션
**업데이트된 내용**:
- ✅ 응답 길이: 기본 4,000 / 문서 생성 10,000 (FR-017)
- ✅ 대화 길이 제한: 1,000개 메시지 (FR-041)
- ✅ 컨텍스트 윈도우: 10개 메시지, 2,048 토큰 (FR-036)

---

### 2. Project Structure

#### Frontend 컴포넌트 구조 확장

**추가된 컴포넌트**:

**chat/ 디렉토리**:
- `ChatInput.tsx` - 6가지 UI 상태 처리 (FR-035)
- `MessageList.tsx` - 메시지 목록 및 스트리밍
- `LoadingIndicator.tsx` - 처리 중 스피너
- `StreamingMessage.tsx` - 실시간 응답 표시

**admin/ 디렉토리**:
- `UserManagement.tsx` - 사용자 CRUD
- `StatsDashboard.tsx` - 사용량 메트릭 대시보드 (FR-038)
- `SystemHealth.tsx` - 시스템 상태 모니터링
- `StorageMetrics.tsx` - 저장소 사용량 표시

**ui/ 디렉토리**:
- `ErrorMessage.tsx` - 표준화된 한국어 오류 메시지 (FR-037)
- `EmptyState.tsx` - 빈 상태 UI (FR-039)
- `SessionWarningModal.tsx` - 타임아웃 경고 모달 (FR-012)

**lib/ 디렉토리**:
- `errorMessages.ts` - 오류 메시지 포매터 (FR-037)
- `localStorage.ts` - 임시 저장 메시지 복구 (FR-012)

**hooks/ 디렉토리** (신규):
- `useSessionTimeout.ts` - 세션 관리
- `useChatState.ts` - 채팅 UI 상태 머신 (FR-035)

**types/ 디렉토리 세분화**:
- `chat.ts` - 채팅 관련 타입
- `admin.ts` - 관리자 관련 타입
- `api.ts` - API 응답 타입

---

#### Backend 구조 확장

**추가된 Models**:
- `admin.py` - 별도 관리자 테이블 (FR-033)
- `session.py` - 동시 로그인 지원 (FR-030)
- `login_attempt.py` - 로그인 시도 추적 (FR-031)

**conversation.py 업데이트**:
- 1,000개 메시지 제한 (FR-041)

**추가된 Schemas**:
- `stats.py` - 통계 스키마 (FR-038)
- `setup.py` - 초기 설정 스키마 (FR-034)

**추가된 API Routes**:
- `setup.py` - 초기 설정 마법사 엔드포인트 (FR-034)

**API Routes 업데이트**:
- `chat.py` - 컨텍스트 관리 추가
- `admin.py` - 통계 엔드포인트 추가 (FR-038)

**추가된 Services**:
- `password_service.py` - 비밀번호 검증 및 해싱 (FR-029)
- `rate_limit_service.py` - IP 속도 제한 (FR-031)
- `stats_service.py` - 사용량 통계 (FR-038)
- `setup_service.py` - 초기 설정 마법사 (FR-034)

**Services 업데이트**:
- `llm_service.py` - 컨텍스트 관리 로직 추가 (FR-036)
- `admin_service.py` - 사용자 관리, 계정 잠금

**추가된 Middleware** (신규 디렉토리):
- `session_timeout.py` - 세션 타임아웃 (FR-012)
- `rate_limiter.py` - IP 기반 속도 제한 (FR-031)
- `data_isolation.py` - 데이터베이스 레벨 필터링 (FR-032)

**Core 업데이트**:
- `security.py` - bcrypt cost factor 12 명시
- `database.py` - 필터링 로직 추가
- `config.py` - 설정 잠금 파일 체크

**Utils 추가**:
- `error_formatter.py` - 한국어 오류 메시지 (FR-037)
- `validators.py` - 입력 검증

---

### 3. Design Considerations (신규 섹션)

plan.md 끝에 새로운 섹션 추가: **"Design Considerations for New Requirements"**

이 섹션에는 각 새로운 요구사항의 구체적인 구현 전략이 포함됩니다:

#### 📝 포함된 내용

**Security Implementation (FR-029 ~ FR-033)**:
- Password Management: bcrypt 사용 이유, cost factor 12 고정
- Session Management: PostgreSQL 세션 테이블 구조, 백그라운드 정리 작업
- Login Protection: 로그인 시도 테이블, 계정 잠금 메커니즘
- Data Isolation: ORM 이벤트 리스너, API 의존성 주입
- Privilege Escalation: 별도 admins 테이블 설계

**UI State Management (FR-035)**:
- 6개 상태 머신 설계 (idle, typing, processing, streaming, completed, error)
- useReducer 기반 React hook 구현
- 상태 전환 액션 정의

**Context Management (FR-036)**:
- 구현 전략 Python 코드 예시 포함
- 최근 10개 메시지 로드
- 2,048 토큰 제한 및 FIFO 제거 로직

**Error Message Formatting (FR-037)**:
- TypeScript 오류 메시지 매핑 예시
- Python 백엔드 오류 포매터 예시
- 한국어 메시지 표준 형식

**Usage Statistics (FR-038)**:
- 메트릭 수집 전략 (실시간 vs 히스토리)
- Dashboard API 엔드포인트 예시 코드
- 퍼센타일 계산 방법

**Initial Setup Wizard (FR-034)**:
- 설정 플로우 5단계
- 잠금 파일 메커니즘
- 미들웨어 구현 예시

**Browser Compatibility (FR-040)**:
- 브라우저 감지 TypeScript 코드
- IE 감지 및 경고
- 최소 버전 체크 로직

---

## 📊 통계

### 파일 수정
- **plan.md**: 7개 섹션 업데이트, 1개 신규 섹션 추가 (+215줄)

### 추가된 구성 요소
- **프론트엔드 컴포넌트**: 13개
- **프론트엔드 Hooks**: 2개
- **백엔드 Models**: 3개
- **백엔드 Services**: 4개
- **백엔드 Middleware**: 3개 (신규 디렉토리)
- **백엔드 Schemas**: 2개
- **백엔드 API Routes**: 1개
- **유틸리티**: 4개

**총합**: 32개의 새로운 파일/모듈 계획

---

## 🎯 설계 결정 사항

### 보안 (FR-029 ~ FR-033)

1. **bcrypt 선택 이유**:
   - argon2 대신 bcrypt 사용
   - 이유: 더 나은 호환성, 안정성, 에코시스템
   - Cost factor 12 고정 (설정 불가)

2. **세션 저장소**:
   - PostgreSQL 사용 (Redis 아님)
   - 이유: 추가 의존성 없이 단순성 유지
   - 백그라운드 작업으로 만료된 세션 정리

3. **속도 제한**:
   - 인메모리 캐시 사용 (Python dict + TTL)
   - Redis 사용 가능 시 Redis로 업그레이드
   - 이유: 폐쇄망 환경에서 단순성 우선

4. **데이터 격리 3단계**:
   - ORM 레벨: SQLAlchemy 이벤트 리스너
   - API 레벨: 의존성 주입 (deps.py)
   - Admin 레벨: 별도 서비스, 삭제만 허용

5. **Admin 테이블 분리**:
   - `is_admin` 불린 플래그 대신 별도 `admins` 테이블
   - 이유: 권한 상승 공격 방지, 명확한 권한 분리

### UI/UX (FR-035, FR-037, FR-039)

1. **상태 관리**:
   - useReducer 기반 커스텀 hook
   - 이유: 복잡한 상태 전환 로직 관리, 예측 가능성

2. **오류 메시지**:
   - 중앙 집중식 매핑 (errorMessages.ts, error_formatter.py)
   - 이유: 일관성, 유지보수성, 다국어 지원 용이

3. **빈 상태 UI**:
   - 재사용 가능한 EmptyState 컴포넌트
   - 이유: 디자인 일관성, 코드 재사용

### 시스템 (FR-034, FR-036, FR-038)

1. **초기 설정 잠금 파일**:
   - `/config/initial-setup.lock` 사용
   - 이유: 단순, 파일 시스템 기반, 재설정 방지

2. **컨텍스트 관리**:
   - 데이터베이스에서 최근 10개 로드
   - 토큰 근사치: 1 토큰 ≈ 4 한글 문자
   - 이유: 한국어 특성 고려, 단순한 계산

3. **통계 수집**:
   - 실시간: 인메모리 카운터
   - 히스토리: PostgreSQL 집계 쿼리
   - 이유: 성능과 정확성의 균형

---

## ✅ 검증 체크리스트

- [x] 모든 새로운 요구사항 (FR-029 ~ FR-041) plan.md에 반영
- [x] 기술 스택 섹션 업데이트
- [x] 프로젝트 구조에 새 파일/디렉토리 추가
- [x] 구현 전략 및 예시 코드 제공
- [x] 설계 결정 사항 문서화
- [x] 한국어 오류 메시지 표준 정의
- [x] 보안 요구사항 상세 설계
- [x] 브라우저 호환성 체크 로직 정의

---

## 🚀 다음 단계

1. **data-model.md 작성** (선택사항)
   - 새로운 테이블 스키마 정의
   - 특히: `admins`, `sessions`, `login_attempts`

2. **tasks.md 생성**
   - `/speckit.tasks` 명령 실행
   - FR-029 ~ FR-041에 대한 구현 작업 자동 생성

3. **API 계약 작성** (선택사항)
   - `contracts/api-spec.yaml` 업데이트
   - 새로운 엔드포인트 추가: `/api/v1/setup`, `/api/v1/admin/stats`

4. **팀 리뷰**
   - 설계 결정 검토
   - 특히 보안 구현 전략 검토

---

## 📝 참고 사항

### spec.md와 plan.md 동기화 완료

| 요구사항 | spec.md | plan.md | 동기화 상태 |
|---------|---------|---------|------------|
| FR-029 | ✅ | ✅ | 완료 |
| FR-030 | ✅ | ✅ | 완료 |
| FR-031 | ✅ | ✅ | 완료 |
| FR-032 | ✅ | ✅ | 완료 |
| FR-033 | ✅ | ✅ | 완료 |
| FR-034 | ✅ | ✅ | 완료 |
| FR-035 | ✅ | ✅ | 완료 |
| FR-036 | ✅ | ✅ | 완료 |
| FR-037 | ✅ | ✅ | 완료 |
| FR-038 | ✅ | ✅ | 완료 |
| FR-039 | ✅ | ✅ | 완료 |
| FR-040 | ✅ | ✅ | 완료 |
| FR-041 | ✅ | ✅ | 완료 |

### 영향을 받는 기존 계획

**긍정적 영향**:
- 보안 강화로 엔터프라이즈 배포 준비도 향상
- 명확한 UI 상태로 프론트엔드 개발 속도 향상
- 상세한 설계로 구현 오류 감소 예상

**추가 작업 필요**:
- 초기 설정 마법사 UI 개발 (+1-2일)
- 통계 대시보드 구현 (+2-3일)
- 보안 테스트 케이스 작성 (+1-2일)

**예상 추가 시간**: 4-7일

---

## 🎉 결론

spec.md의 모든 새로운 요구사항이 plan.md에 성공적으로 반영되었습니다.

**주요 성과**:
- 13개 새로운 요구사항 → 32개 새로운 파일/모듈 계획
- 보안 강화 (5개 요구사항)
- UI/UX 개선 (3개 요구사항)
- 시스템 관리 강화 (5개 요구사항)

**준비 완료**: 이제 tasks.md 생성 및 구현 시작 준비 완료

다음 단계: `/speckit.tasks` 실행하여 구현 작업 목록 생성
