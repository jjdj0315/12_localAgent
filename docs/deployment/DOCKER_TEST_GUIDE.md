# 도커 테스트 가이드 🐳

**현재 완성도**: Phase 1-5 완료 (69.1%) - 핵심 기능 테스트 가능!

---

## 🚀 빠른 시작 (GPU 없이 테스트)

### 1단계: 사전 요구사항 확인

```bash
# Docker와 Docker Compose 설치 확인
docker --version
docker-compose --version
```

**필요한 것:**
- Docker Desktop (Windows) 또는 Docker Engine (Linux)
- 최소 8GB RAM
- 20GB 디스크 공간

### 2단계: 전체 스택 실행

```bash
# 프로젝트 디렉토리로 이동
cd C:\02_practice\12_localAgent

# Mock LLM으로 전체 스택 시작 (GPU 불필요)
docker-compose -f docker-compose.test.yml up --build
```

**처음 실행 시 소요 시간**: 5-10분 (이미지 빌드 + DB 마이그레이션)

### 3단계: 서비스 접속

| 서비스 | URL | 설명 |
|--------|-----|------|
| **프론트엔드** | http://localhost:3000 | 사용자 웹 인터페이스 |
| **백엔드 API** | http://localhost:8000/docs | API 문서 (Swagger UI) |
| **Mock LLM** | http://localhost:8001/health | LLM 서비스 상태 |
| **데이터베이스** | localhost:5432 | PostgreSQL (직접 접속용) |

---

## ✅ 테스트 시나리오

### 시나리오 1: 로그인 및 기본 채팅 (Phase 3)

1. **웹 브라우저에서 접속**: http://localhost:3000
2. **초기 관리자 계정으로 로그인**:
   - Username: `admin`
   - Password: `admin123!` (create_admin.py에서 생성)
3. **채팅 페이지로 이동**: `/chat`
4. **질문 입력**:
   ```
   안녕하세요! 업무 문서 작성에 도움을 주실 수 있나요?
   ```
5. **응답 확인**: Mock LLM이 한국어로 응답

**예상 결과**:
- ✅ 로그인 성공
- ✅ 채팅 인터페이스 표시
- ✅ Mock 응답 실시간 스트리밍
- ✅ 대화 내역 자동 저장

---

### 시나리오 2: 대화 이력 관리 (Phase 4)

1. **대화 이력 페이지**: `/history`
2. **저장된 대화 확인**: 이전에 나눈 대화 목록 표시
3. **대화 검색**: 키워드로 검색
4. **대화 재개**: 클릭해서 이전 대화 이어가기
5. **대화 삭제**: 삭제 버튼으로 제거

**예상 결과**:
- ✅ 대화 목록 페이지네이션
- ✅ 검색 기능 동작
- ✅ 대화 재개 시 컨텍스트 유지
- ✅ 삭제 확인 모달

---

### 시나리오 3: 문서 업로드 및 분석 (Phase 5)

1. **문서 페이지**: `/documents`
2. **테스트 파일 업로드**:
   - PDF, DOCX, TXT 파일 준비
   - 드래그 앤 드롭 또는 클릭 업로드
3. **업로드 진행률 확인**
4. **문서 목록 확인**: 파일명, 크기, 날짜 표시
5. **채팅에서 문서 첨부**:
   - `/chat` 페이지로 이동
   - "문서 첨부" 버튼 클릭
   - 업로드한 문서 선택
   - 질문: `이 문서를 요약해주세요`

**예상 결과**:
- ✅ 파일 업로드 성공
- ✅ 텍스트 추출 완료 (PDF/DOCX/TXT)
- ✅ 문서 기반 LLM 응답
- ✅ 대화 목록에 문서 아이콘 표시

---

### 시나리오 4: 관리자 기능 (Phase 7 - 부분 완성)

1. **관리자 페이지**: `/admin`
2. **사용자 관리**: `/admin/users`
   - 새 사용자 생성
   - 초기 비밀번호 확인
   - 사용자 목록 확인
3. **통계 확인**: `/admin/stats`
   - 활성 사용자 수
   - 쿼리 처리 횟수
   - 평균 응답 시간
4. **시스템 상태**: `/admin/health`
   - CPU, 메모리 사용률
   - 스토리지 현황
   - 서비스 상태

**예상 결과**:
- ✅ 사용자 생성/삭제 가능
- ✅ 통계 대시보드 표시
- ✅ 시스템 상태 모니터링

---

## 🔧 문제 해결

### 문제 1: 포트가 이미 사용 중

```bash
# 실행 중인 컨테이너 확인
docker ps

# 기존 컨테이너 중지
docker-compose -f docker-compose.test.yml down

# 다시 시작
docker-compose -f docker-compose.test.yml up
```

### 문제 2: 데이터베이스 마이그레이션 실패

```bash
# 컨테이너 내부에서 수동 실행
docker exec -it llm-webapp-backend-test bash

# 마이그레이션 실행
alembic upgrade head

# 관리자 생성
python scripts/create_admin.py
```

### 문제 3: 프론트엔드가 백엔드에 연결 안 됨

```bash
# 백엔드 로그 확인
docker logs llm-webapp-backend-test -f

# 백엔드 헬스 체크
curl http://localhost:8000/health
```

### 문제 4: Mock LLM 응답이 없음

```bash
# Mock LLM 로그 확인
docker logs llm-webapp-llm-mock -f

# Mock LLM 헬스 체크
curl http://localhost:8001/health
```

---

## 📊 서비스 상태 확인

### 모든 서비스 헬스 체크

```bash
# Postgres
docker exec llm-webapp-postgres-test pg_isready -U llm_app

# Backend
curl http://localhost:8000/health

# Mock LLM
curl http://localhost:8001/health

# Frontend
curl http://localhost:3000
```

### 로그 확인

```bash
# 모든 서비스 로그 (실시간)
docker-compose -f docker-compose.test.yml logs -f

# 특정 서비스만
docker-compose -f docker-compose.test.yml logs -f backend
docker-compose -f docker-compose.test.yml logs -f frontend
docker-compose -f docker-compose.test.yml logs -f llm-mock
```

---

## 🧹 정리

### 서비스 중지 (데이터 유지)

```bash
docker-compose -f docker-compose.test.yml down
```

### 완전 삭제 (데이터 포함)

```bash
# 컨테이너, 볼륨, 네트워크 모두 삭제
docker-compose -f docker-compose.test.yml down -v

# 이미지까지 삭제
docker-compose -f docker-compose.test.yml down --rmi all -v
```

---

## 🎯 다음 단계

테스트가 완료되면:

1. **Phase 6 구현**: 멀티유저 동시 접속 최적화
2. **Phase 7 완성**: 관리자 기능 완성
3. **Phase 8**: 프로덕션 배포 준비

---

## 📝 테스트 체크리스트

현재 테스트 가능한 기능:

- [x] ✅ **Phase 1**: 프로젝트 구조 (100%)
- [x] ✅ **Phase 2**: 기본 인프라 (100%)
- [ ] ⚠️ **Phase 3**: 기본 채팅 (86% - 헌법 검증 제외)
  - [x] 로그인/로그아웃
  - [x] 채팅 인터페이스
  - [x] LLM 응답 스트리밍
  - [x] 대화 컨텍스트 유지
  - [ ] Air-gap 검증 스크립트 (T058)
  - [ ] 한국어 품질 테스트 (T059)
- [x] ✅ **Phase 4**: 대화 이력 관리 (100%)
- [x] ✅ **Phase 5**: 문서 업로드 및 분석 (100%)
- [ ] 🔄 **Phase 6**: 멀티유저 (40%)
  - [x] 기본 사용자 격리
  - [x] 세션 관리
  - [ ] 요청 큐잉 및 UX
- [ ] 🔄 **Phase 7**: 관리자 (54%)
  - [x] 사용자 관리
  - [x] 기본 통계
  - [x] 시스템 상태 모니터링
  - [ ] 스토리지 quota 관리
  - [ ] 문서 보존 정책

---

## 🌟 주요 테스트 포인트

### ✅ 현재 동작하는 기능

1. **인증 및 세션**
   - 로그인/로그아웃
   - 세션 타임아웃 (30분)
   - 사용자 격리

2. **채팅**
   - 실시간 스트리밍 응답
   - 대화 컨텍스트 유지
   - 한국어 지원

3. **대화 관리**
   - 대화 저장/조회/삭제
   - 검색 및 필터링
   - 태그 관리

4. **문서 처리**
   - PDF/DOCX/TXT 업로드
   - 텍스트 추출
   - 문서 기반 Q&A
   - 다중 문서 비교

5. **관리자**
   - 사용자 CRUD
   - 사용 통계
   - 시스템 모니터링

### ⏳ 아직 미구현

1. **요청 큐잉**: 동시 사용자 많을 때 대기열
2. **스토리지 관리**: quota 경고, 보존 정책
3. **프로덕션 기능**: 백업, 로깅, 보안 강화

---

## 💡 팁

- **개발 중 핫 리로드**: 코드 수정 시 자동 재시작 (volumes 마운트됨)
- **데이터베이스 접속**: `psql -h localhost -U llm_app -d llm_webapp`
- **API 문서**: http://localhost:8000/docs (Swagger UI 자동 생성)
- **React Query Devtools**: 프론트엔드에서 데이터 흐름 디버깅 가능

---

## 🎉 성공 예시

모든 서비스가 정상 실행되면:

```
✅ llm-webapp-postgres-test    ... healthy
✅ llm-webapp-llm-mock          ... healthy
✅ llm-webapp-backend-test      ... running
✅ llm-webapp-frontend-test     ... running
```

웹 브라우저에서 http://localhost:3000 접속 시:
- 로그인 페이지 표시
- 로그인 후 채팅 인터페이스
- 한국어 UI 및 응답
- 문서 업로드 가능
- 관리자 페이지 접근 가능

**축하합니다! 🎊 로컬 LLM 웹 애플리케이션이 동작합니다!**
