# 데이터베이스 마이그레이션 가이드

## 개요

이 문서는 Local LLM 웹 애플리케이션의 데이터베이스 마이그레이션 절차를 설명합니다.

## 사전 요구사항

- Docker Desktop 설치 및 실행
- Git 저장소 클론 완료
- `.env` 파일 설정 완료

## 마이그레이션 히스토리

### Migration 004: User Lockout Fields (2025-11-01)

**목적**: FR-031 계정 잠금 기능 구현을 위한 User 모델 확장

**추가되는 필드**:
- `email` (VARCHAR 255, nullable): 사용자 이메일 주소
- `is_active` (BOOLEAN, default true): 계정 활성화 상태
- `is_locked` (BOOLEAN, default false): 계정 잠금 상태
- `locked_until` (TIMESTAMP, nullable): 잠금 해제 시간
- `failed_login_attempts` (INTEGER, default 0): 로그인 실패 횟수

**파일**: `backend/alembic/versions/004_add_user_lockout_fields.py`

## 마이그레이션 실행 절차

### 1. Docker Compose로 PostgreSQL 시작

```bash
# 프로젝트 루트 디렉토리에서 실행
docker-compose up -d postgres
```

**확인**:
```bash
docker-compose ps
# postgres 컨테이너가 "healthy" 상태인지 확인
```

### 2. 데이터베이스 연결 테스트

```bash
docker-compose exec postgres pg_isready -U llm_app
# 출력: localhost:5432 - accepting connections
```

### 3. 현재 마이그레이션 상태 확인

```bash
cd backend
alembic current
```

**예상 출력** (Migration 004 실행 전):
```
003 (head)
```

### 4. 마이그레이션 실행

```bash
alembic upgrade head
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, add user lockout fields
```

### 5. 마이그레이션 완료 확인

```bash
alembic current
```

**예상 출력**:
```
004 (head)
```

### 6. 데이터베이스 스키마 확인

```bash
docker-compose exec postgres psql -U llm_app -d llm_webapp -c "\d users"
```

**확인사항**:
- `email` 컬럼 존재
- `is_active` 컬럼 존재 (default true)
- `is_locked` 컬럼 존재 (default false)
- `locked_until` 컬럼 존재
- `failed_login_attempts` 컬럼 존재 (default 0)

## 롤백 절차 (필요 시)

### 1단계 롤백 (Migration 004 → 003)

```bash
cd backend
alembic downgrade -1
```

### 특정 버전으로 롤백

```bash
alembic downgrade 003
```

### 전체 롤백 (주의!)

```bash
alembic downgrade base
```

## 트러블슈팅

### 문제 1: Docker Desktop이 실행되지 않음

**증상**:
```
error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/...
```

**해결**:
1. Windows 시작 메뉴에서 "Docker Desktop" 실행
2. Docker Desktop이 완전히 시작될 때까지 대기 (1-2분)
3. `docker ps` 명령으로 Docker 연결 확인

### 문제 2: PostgreSQL 컨테이너가 시작되지 않음

**증상**:
```
postgres exited with code 1
```

**해결**:
```bash
# 로그 확인
docker-compose logs postgres

# 컨테이너 재시작
docker-compose restart postgres

# 볼륨 초기화 (주의: 데이터 삭제됨)
docker-compose down -v
docker-compose up -d postgres
```

### 문제 3: 마이그레이션 실패

**증상**:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateColumn) column "email" of relation "users" already exists
```

**해결**:
```bash
# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history

# 필요시 수동으로 마이그레이션 버전 설정
alembic stamp 004
```

### 문제 4: 데이터베이스 연결 실패

**증상**:
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed
```

**해결**:
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# healthcheck 확인
docker-compose exec postgres pg_isready -U llm_app

# 환경 변수 확인
docker-compose config | grep POSTGRES
```

## 환경별 설정

### 개발 환경 (.env.development)

```env
POSTGRES_USER=llm_app
POSTGRES_PASSWORD=devpassword
POSTGRES_DB=llm_webapp_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 프로덕션 환경 (.env.production)

```env
POSTGRES_USER=llm_app
POSTGRES_PASSWORD=<강력한-패스워드>
POSTGRES_DB=llm_webapp
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

## 백업 권장사항

마이그레이션 실행 전 데이터베이스 백업:

```bash
# PostgreSQL 덤프 생성
docker-compose exec postgres pg_dump -U llm_app llm_webapp > backup_$(date +%Y%m%d_%H%M%S).sql

# 복원 (필요 시)
cat backup_20251101_115000.sql | docker-compose exec -T postgres psql -U llm_app llm_webapp
```

## 참고 자료

- Alembic 공식 문서: https://alembic.sqlalchemy.org/
- PostgreSQL Docker 이미지: https://hub.docker.com/_/postgres
- FR-031: 계정 잠금 기능 명세 (`specs/001-local-llm-webapp/spec.md`)
