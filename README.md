# Local LLM Web Application for Local Government

**폐쇄망 환경에서 이용 가능한 Local LLM 웹 애플리케이션**

소규모 지방자치단체 공무원을 위한 AI 기반 업무 지원 도구입니다. ChatGPT, Gemini와 같은 외부 서비스 사용이 제한되는 환경에서 로컬로 실행되는 LLM을 제공합니다.

## 주요 기능

- ✅ **기본 채팅**: LLM과의 대화형 인터페이스
- ✅ **대화 이력 관리**: 대화 저장, 검색, 태그 기능
- ✅ **문서 분석**: PDF, DOCX, TXT 파일 업로드 및 Q&A
- ✅ **다중 사용자 지원**: 개별 계정 및 데이터 격리
- ✅ **관리자 대시보드**: 사용자 관리 및 시스템 모니터링

## 기술 스택

**Frontend**:
- Next.js 14 (App Router)
- React 18 + TypeScript
- TailwindCSS
- React Query

**Backend**:
- FastAPI (Python 3.11+)
- PostgreSQL 15
- SQLAlchemy 2.0
- Alembic

**LLM**:
- Meta-Llama-3-8B
- vLLM (inference engine)
- Server-Sent Events (streaming)

**Deployment**:
- Docker + Docker Compose
- On-premises (air-gapped)
- NVIDIA GPU support

## 프로젝트 구조

```
local-llm-webapp/
├── frontend/          # Next.js 애플리케이션
├── backend/           # FastAPI 백엔드
├── llm-service/       # vLLM 추론 서비스
├── docker/            # Docker 설정 파일
├── specs/             # 기획 및 설계 문서
│   └── 001-local-llm-webapp/
│       ├── spec.md           # 요구사항 명세서
│       ├── plan.md           # 구현 계획서
│       ├── tasks.md          # 작업 목록
│       ├── data-model.md     # 데이터베이스 설계
│       ├── research.md       # 기술 조사
│       ├── quickstart.md     # 배포 가이드
│       └── contracts/        # API 명세
└── docker-compose.yml
```

## 빠른 시작

### 사전 요구사항

- Docker 24+ with Docker Compose
- NVIDIA GPU (16GB+ VRAM)
- NVIDIA Container Toolkit
- 200GB+ 저장 공간

### 개발 환경 설정

1. **저장소 클론**
```bash
git clone <repository-url>
cd local-llm-webapp
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 비밀번호 등 설정
```

3. **서비스 시작**
```bash
docker-compose up -d
```

4. **데이터베이스 마이그레이션**
```bash
docker-compose exec backend alembic upgrade head
```

5. **관리자 계정 생성**
```bash
docker-compose exec backend python scripts/create_admin.py \
  --username admin \
  --password <your-password>
```

6. **애플리케이션 접속**
- 웹 UI: http://localhost:3000
- API 문서: http://localhost:8000/docs

## 폐쇄망 배포

자세한 배포 가이드는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참고하세요.

추가 배포 문서: [specs/001-local-llm-webapp/quickstart.md](specs/001-local-llm-webapp/quickstart.md)

### 요약

1. **인터넷 연결된 환경**에서:
   - Docker 이미지 빌드
   - Llama-3-8B 모델 다운로드
   - 모든 파일을 tar로 패키징

2. **폐쇄망 서버**로 전송 (USB 등)

3. **폐쇄망 서버**에서:
   - Docker 이미지 로드
   - 서비스 시작
   - 초기 설정

## 개발 가이드

### Backend 개발

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements-dev.txt

# 코드 포맷팅
black app/
ruff check app/

# 타입 체크
mypy app/

# 테스트
pytest
```

### Frontend 개발

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 린팅
npm run lint

# 포맷팅
npm run format
```

## 문서

- **요구사항 명세**: [specs/001-local-llm-webapp/spec.md](specs/001-local-llm-webapp/spec.md)
- **구현 계획**: [specs/001-local-llm-webapp/plan.md](specs/001-local-llm-webapp/plan.md)
- **작업 목록**: [specs/001-local-llm-webapp/tasks.md](specs/001-local-llm-webapp/tasks.md)
- **데이터베이스 설계**: [specs/001-local-llm-webapp/data-model.md](specs/001-local-llm-webapp/data-model.md)
- **API 명세**: [specs/001-local-llm-webapp/contracts/api-spec.yaml](specs/001-local-llm-webapp/contracts/api-spec.yaml)
- **배포 가이드**: [specs/001-local-llm-webapp/quickstart.md](specs/001-local-llm-webapp/quickstart.md)

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 지원

문제가 발생하면 issue를 생성해주세요.
