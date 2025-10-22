# 로컬 개발 환경 빠른 시작 가이드

이 가이드는 Docker 없이 로컬에서 애플리케이션을 실행하는 방법을 안내합니다.

## 사전 요구사항

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (또는 SQLite로 테스트)

## 1. Backend 설정 및 실행

### 1.1 가상환경 생성 및 의존성 설치

```bash
cd backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 1.2 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```env
# Database
POSTGRES_USER=llm_app
POSTGRES_PASSWORD=changeme
POSTGRES_DB=llm_webapp
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# 또는 SQLite 사용 (테스트용)
DATABASE_URL=sqlite+aiosqlite:///./test.db

# Security
SECRET_KEY=your-secret-key-change-in-production
SESSION_TIMEOUT_MINUTES=30

# LLM Service (Mock for testing)
LLM_SERVICE_URL=http://localhost:8001
MAX_RESPONSE_LENGTH=4000
```

### 1.3 데이터베이스 마이그레이션

```bash
# Alembic 마이그레이션 실행
cd backend
alembic upgrade head
```

### 1.4 관리자 계정 생성

```bash
# backend 디렉토리에서
python -m scripts.create_admin

# 프롬프트에 따라 입력:
# - Username: admin
# - Password: admin1234 (최소 8자)
```

### 1.5 Backend 서버 실행

```bash
# backend 디렉토리에서
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 서버가 시작되면:
# http://localhost:8000 에서 API 접근 가능
# http://localhost:8000/docs 에서 API 문서 확인
```

## 2. Frontend 설정 및 실행

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 환경 변수 설정

`frontend/.env.local` 파일 생성:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2.3 Frontend 서버 실행

```bash
npm run dev

# 서버가 시작되면:
# http://localhost:3000 에서 접근 가능
```

## 3. LLM 서비스 (Mock)

실제 LLM 서비스 없이 테스트하려면 간단한 Mock 서버를 만들 수 있습니다:

### 3.1 Mock LLM 서버 생성

`llm-service/mock_server.py` 파일:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.post("/generate")
async def generate(request: dict):
    """Mock LLM response"""
    prompt = request.get("prompt", "")
    return {
        "text": f"Mock 응답: {prompt}에 대한 답변입니다. 이것은 테스트 응답입니다."
    }

@app.post("/generate_stream")
async def generate_stream(request: dict):
    """Mock streaming response"""
    async def stream():
        response = "안녕하세요! Mock LLM 응답입니다. 실제 환경에서는 Llama-3-8B 모델이 동작합니다."
        for char in response:
            yield f"data: {char}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 3.2 Mock 서버 실행

```bash
cd llm-service
python mock_server.py

# http://localhost:8001 에서 실행됨
```

## 4. 애플리케이션 사용

### 4.1 로그인

1. 브라우저에서 `http://localhost:3000` 접속
2. 로그인 페이지에서 생성한 관리자 계정으로 로그인:
   - Username: `admin`
   - Password: `admin1234`

### 4.2 채팅 테스트

1. 로그인 후 자동으로 채팅 페이지로 이동
2. 메시지 입력창에 한국어 질문 입력:
   - 예: "행정 업무에서 공문서를 작성할 때 주의사항이 무엇인가요?"
3. Enter 키를 눌러 전송
4. AI 응답 확인

## 5. 문제 해결

### Backend 서버가 시작되지 않는 경우

```bash
# 포트 충돌 확인
netstat -ano | findstr :8000

# 다른 포트 사용
uvicorn app.main:app --reload --port 8080
```

### Frontend 빌드 오류

```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

### 데이터베이스 연결 오류

```bash
# SQLite로 임시 테스트
# .env 파일에서:
DATABASE_URL=sqlite+aiosqlite:///./test.db

# 테이블 재생성
alembic downgrade base
alembic upgrade head
```

## 6. 전체 서비스 구조

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend       │────▶│   LLM Service   │
│  (Next.js)      │     │   (FastAPI)      │     │    (vLLM)       │
│  localhost:3000 │     │  localhost:8000  │     │  localhost:8001 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │ localhost:5432│
                        └──────────────┘
```

## 7. Docker로 전체 실행 (권장)

로컬 설정이 복잡하다면 Docker Compose 사용을 권장합니다:

```bash
# Docker Desktop 실행 후
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 관리자 계정 생성
docker-compose exec backend python -m scripts.create_admin

# 서비스 중지
docker-compose down
```

## 다음 단계

- Phase 4: Conversation History Management 구현
- Phase 5: Document Upload and Analysis 구현
- Phase 6: Multi-User Access 구현
- Phase 7: Administrator Dashboard 구현
