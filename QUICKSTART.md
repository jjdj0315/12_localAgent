# 빠른 시작 가이드 (Windows)

MVP를 빠르게 실행하기 위한 가이드입니다.

## 1. Docker Desktop 설치

### 다운로드 및 설치
1. https://www.docker.com/products/docker-desktop/ 접속
2. "Download for Windows" 클릭
3. 다운로드한 `Docker Desktop Installer.exe` 실행
4. 설치 마법사 따라 진행
5. 설치 완료 후 컴퓨터 재부팅

### Docker Desktop 시작 확인
```powershell
# PowerShell 또는 CMD에서 실행
docker --version
docker-compose --version
```

정상적으로 버전이 표시되면 설치 완료입니다.

## 2. 환경 설정 확인

`.env` 파일이 프로젝트 루트에 생성되어 있어야 합니다.

```bash
# 파일 확인
dir .env
```

이미 생성되어 있으므로 그대로 사용하면 됩니다.

## 3. Docker 컨테이너 실행

### 개발 모드 (LLM 서비스 제외)

GPU가 없거나 빠른 테스트를 위해 LLM 서비스 없이 실행:

```bash
# 컨테이너 빌드 및 시작
docker-compose -f docker-compose.dev.yml up --build -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f
```

**실행되는 서비스:**
- PostgreSQL (포트 5432)
- Backend API (포트 8000)
- Frontend (포트 3000)

### 프로덕션 모드 (전체 서비스)

GPU가 있고 LLM 모델이 준비된 경우:

```bash
# 모델 다운로드 필요 (DEPLOYMENT.md 참조)
# docker-compose up --build -d
```

## 4. 데이터베이스 초기화

컨테이너가 실행된 후, 데이터베이스 마이그레이션을 실행합니다:

```bash
# 백엔드 컨테이너에서 마이그레이션 실행
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

**예상 출력:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
```

## 5. 관리자 계정 생성

```bash
# 관리자 계정 생성 (비밀번호는 원하는 것으로 변경)
docker-compose -f docker-compose.dev.yml exec backend python scripts/create_admin.py --username admin --password Admin123!
```

**예상 출력:**
```
✅ Admin user 'admin' created successfully!
   Username: admin
   Is Admin: True
```

## 6. 애플리케이션 접속

브라우저를 열고 다음 주소로 접속:

- **프론트엔드**: http://localhost:3000
- **백엔드 API 문서**: http://localhost:8000/docs
- **백엔드 Health Check**: http://localhost:8000/health

### 로그인
- 사용자 이름: `admin`
- 비밀번호: `Admin123!` (또는 설정한 비밀번호)

## 7. 테스트

1. 로그인 페이지에서 관리자 계정으로 로그인
2. 채팅 페이지로 자동 이동
3. 메시지 입력란에 "안녕하세요" 입력
4. 전송 버튼 클릭

**참고**: 현재 개발 모드에서는 LLM 서비스가 없으므로, 실제 AI 응답은 작동하지 않습니다.
백엔드 API와 프론트엔드 UI만 테스트할 수 있습니다.

## 8. 컨테이너 관리

### 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker-compose -f docker-compose.dev.yml ps

# 로그 확인
docker-compose -f docker-compose.dev.yml logs backend
docker-compose -f docker-compose.dev.yml logs frontend
docker-compose -f docker-compose.dev.yml logs postgres
```

### 컨테이너 중지
```bash
# 모든 컨테이너 중지
docker-compose -f docker-compose.dev.yml down

# 볼륨까지 삭제 (데이터베이스 데이터 삭제됨!)
docker-compose -f docker-compose.dev.yml down -v
```

### 컨테이너 재시작
```bash
# 특정 서비스만 재시작
docker-compose -f docker-compose.dev.yml restart backend

# 모든 서비스 재시작
docker-compose -f docker-compose.dev.yml restart
```

## 9. 문제 해결

### 포트가 이미 사용 중
```
Error: port is already allocated
```

**해결방법:**
1. 다른 프로그램이 포트를 사용 중인지 확인
2. 해당 프로그램 종료 후 다시 시작

```bash
# Windows에서 포트 사용 확인
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432
```

### Docker Desktop이 실행되지 않음
```
error during connect: This error may indicate that the docker daemon is not running
```

**해결방법:**
1. Docker Desktop 애플리케이션 실행
2. 시스템 트레이에서 Docker 아이콘 확인
3. "Docker Desktop is running" 상태 확인

### 컨테이너 빌드 실패

**해결방법:**
```bash
# 캐시 없이 다시 빌드
docker-compose -f docker-compose.dev.yml build --no-cache

# 기존 이미지 삭제 후 재빌드
docker-compose -f docker-compose.dev.yml down --rmi all
docker-compose -f docker-compose.dev.yml up --build -d
```

### 데이터베이스 연결 오류

**해결방법:**
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose -f docker-compose.dev.yml ps postgres

# PostgreSQL 로그 확인
docker-compose -f docker-compose.dev.yml logs postgres

# PostgreSQL 재시작
docker-compose -f docker-compose.dev.yml restart postgres
```

### 백엔드 API 오류

**해결방법:**
```bash
# 백엔드 로그 확인
docker-compose -f docker-compose.dev.yml logs backend

# 백엔드 컨테이너에 접속하여 디버깅
docker-compose -f docker-compose.dev.yml exec backend bash
```

## 10. 개발 워크플로우

코드를 수정하면 자동으로 반영됩니다:

### 백엔드 코드 수정
- `backend/app/` 디렉토리의 Python 파일 수정
- uvicorn의 `--reload` 옵션으로 자동 재시작됨

### 프론트엔드 코드 수정
- `frontend/src/` 디렉토리의 파일 수정
- Next.js 개발 서버가 자동으로 Hot Reload

### 데이터베이스 스키마 변경
```bash
# 1. backend/app/models/ 에서 모델 수정
# 2. 마이그레이션 생성
docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "Description"

# 3. 마이그레이션 적용
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

## 다음 단계

- LLM 서비스 추가: [DEPLOYMENT.md](./DEPLOYMENT.md) 참조
- 전체 시스템 배포: [DEPLOYMENT.md](./DEPLOYMENT.md) 참조
- 개발 가이드: [README.md](./README.md) 참조

## 요약

```bash
# 1. Docker Desktop 설치 및 실행

# 2. 컨테이너 시작
docker-compose -f docker-compose.dev.yml up --build -d

# 3. 데이터베이스 마이그레이션
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# 4. 관리자 생성
docker-compose -f docker-compose.dev.yml exec backend python scripts/create_admin.py --username admin --password Admin123!

# 5. 브라우저로 접속
# http://localhost:3000
```
