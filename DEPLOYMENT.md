# Local LLM 웹 애플리케이션 배포 가이드

폐쇄망 환경에서 Local LLM 웹 애플리케이션을 배포하기 위한 가이드입니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [모델 다운로드 및 준비](#모델-다운로드-및-준비)
3. [환경 설정](#환경-설정)
4. [데이터베이스 초기화](#데이터베이스-초기화)
5. [관리자 계정 생성](#관리자-계정-생성)
6. [서비스 시작](#서비스-시작)
7. [접속 및 확인](#접속-및-확인)
8. [문제 해결](#문제-해결)

## 사전 요구사항

### 하드웨어
- CPU: 4코어 이상 권장
- RAM: 16GB 이상 권장
- GPU: NVIDIA GPU (CUDA 지원, 8GB VRAM 이상 권장)
- 저장공간: 50GB 이상 (모델 파일 포함)

### 소프트웨어
- Docker 20.10 이상
- Docker Compose 2.0 이상
- NVIDIA Container Toolkit (GPU 사용 시)

### GPU 드라이버 설치 (GPU 사용 시)

```bash
# NVIDIA 드라이버 설치 확인
nvidia-smi

# NVIDIA Container Toolkit 설치 (Ubuntu)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## 모델 다운로드 및 준비

**중요:** 폐쇄망 환경이므로 인터넷이 연결된 별도 시스템에서 모델을 다운로드한 후 USB/네트워크를 통해 전송해야 합니다.

### 1. 인터넷 연결된 시스템에서 모델 다운로드

```bash
# Hugging Face CLI 설치
pip install huggingface-hub

# 모델 다운로드
huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct \
  --local-dir ./Meta-Llama-3-8B-Instruct \
  --local-dir-use-symlinks False
```

**참고:** Meta Llama 모델은 라이선스 동의가 필요합니다. Hugging Face에서 먼저 모델 접근 권한을 받으세요.

### 2. 모델 파일 전송

다운로드한 `Meta-Llama-3-8B-Instruct` 폴더를 폐쇄망 시스템으로 전송합니다.

### 3. 모델 위치 설정

```bash
# 프로젝트 루트에 models 디렉토리 생성
mkdir -p models

# 다운로드한 모델을 models 디렉토리로 이동
mv Meta-Llama-3-8B-Instruct models/
```

## 환경 설정

### 1. 환경 변수 파일 생성

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env
```

### 2. .env 파일 수정

```bash
# 필수 변경 사항
SECRET_KEY=your-very-secure-random-secret-key-here  # 최소 32자 랜덤 문자열
POSTGRES_PASSWORD=your-secure-database-password     # 강력한 비밀번호 설정

# 선택적 변경 사항
# DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/localllm
# LLM_SERVICE_URL=http://llm-service:8001
```

**보안 주의사항:**
- `SECRET_KEY`는 반드시 랜덤하고 예측 불가능한 값으로 설정하세요
- `POSTGRES_PASSWORD`는 강력한 비밀번호로 설정하세요
- `.env` 파일은 절대 Git에 커밋하지 마세요

### 3. SECRET_KEY 생성

```bash
# Python으로 안전한 SECRET_KEY 생성
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 데이터베이스 초기화

### 1. 데이터베이스 컨테이너 시작

```bash
docker-compose up -d postgres
```

### 2. 데이터베이스 마이그레이션 실행

```bash
# 백엔드 컨테이너에 들어가서 마이그레이션 실행
docker-compose run --rm backend alembic upgrade head
```

또는 로컬에서 직접 실행:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

## 관리자 계정 생성

서비스를 사용하려면 최소 1명의 관리자 계정이 필요합니다.

```bash
# Docker를 통해 관리자 계정 생성
docker-compose run --rm backend python scripts/create_admin.py \
  --username admin \
  --password YourSecurePassword123!

# 또는 로컬에서 직접 실행
cd backend
python scripts/create_admin.py --username admin --password YourSecurePassword123!
```

**보안 주의사항:**
- 기본 관리자 비밀번호는 최소 8자 이상이어야 합니다
- 첫 로그인 후 즉시 비밀번호를 변경하세요

## 서비스 시작

### 1. 모든 서비스 시작

```bash
# 모든 컨테이너를 백그라운드에서 시작
docker-compose up -d
```

### 2. 서비스 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f backend
docker-compose logs -f llm-service
docker-compose logs -f frontend
```

### 3. 서비스 헬스 체크

```bash
# PostgreSQL 확인
docker-compose exec postgres pg_isready

# 백엔드 API 확인
curl http://localhost:8000/health

# LLM 서비스 확인
curl http://localhost:8001/health

# 프론트엔드 확인
curl http://localhost:3000
```

## 접속 및 확인

### 웹 브라우저로 접속

1. 브라우저를 열고 `http://localhost:3000` (또는 서버 IP) 접속
2. 생성한 관리자 계정으로 로그인
3. 채팅 인터페이스에서 테스트 메시지 입력

### 테스트 질문 예시

```
안녕하세요. 지방자치단체 문서 작성을 도와주세요.
```

## 문제 해결

### GPU가 인식되지 않음

```bash
# NVIDIA GPU 상태 확인
nvidia-smi

# Docker에서 GPU 접근 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# LLM 서비스 로그 확인
docker-compose logs llm-service
```

### 데이터베이스 연결 오류

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# PostgreSQL 로그 확인
docker-compose logs postgres

# 데이터베이스 연결 테스트
docker-compose exec postgres psql -U postgres -d localllm -c "SELECT 1;"
```

### 백엔드 API 오류

```bash
# 백엔드 로그 확인
docker-compose logs backend

# 백엔드 컨테이너 재시작
docker-compose restart backend

# 백엔드 환경 변수 확인
docker-compose exec backend env | grep DATABASE_URL
```

### LLM 서비스가 응답하지 않음

```bash
# LLM 서비스 로그 확인
docker-compose logs llm-service

# 모델 파일 존재 확인
ls -lh models/Meta-Llama-3-8B-Instruct/

# LLM 서비스 재시작
docker-compose restart llm-service
```

### 프론트엔드 빌드 오류

```bash
# 프론트엔드 로그 확인
docker-compose logs frontend

# 프론트엔드 재빌드
docker-compose build frontend
docker-compose up -d frontend
```

### 메모리 부족

```bash
# Docker 메모리 사용량 확인
docker stats

# LLM 서비스 메모리 설정 조정
# llm-service/config.yaml에서 gpu_memory_utilization 값 낮추기 (예: 0.7)
```

### 전체 재시작

```bash
# 모든 서비스 중지
docker-compose down

# 볼륨 포함 전체 삭제 (주의: 데이터 삭제됨!)
docker-compose down -v

# 다시 시작
docker-compose up -d
```

## 로그 수집

문제 발생 시 다음 명령으로 로그를 수집하여 분석:

```bash
# 모든 서비스 로그를 파일로 저장
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt

# 특정 시간대 로그만 확인
docker-compose logs --since 30m

# 실시간 로그 모니터링
docker-compose logs -f --tail=100
```

## 백업

### 데이터베이스 백업

```bash
# PostgreSQL 데이터 백업
docker-compose exec postgres pg_dump -U postgres localllm > backup_$(date +%Y%m%d).sql

# 백업 복원
docker-compose exec -T postgres psql -U postgres localllm < backup_20251021.sql
```

### 파일 백업

```bash
# 업로드된 문서 백업
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz backend/uploads/
```

## 업그레이드

```bash
# 최신 코드 가져오기
git pull

# 컨테이너 재빌드
docker-compose build

# 데이터베이스 마이그레이션
docker-compose run --rm backend alembic upgrade head

# 서비스 재시작
docker-compose up -d
```

## 성능 튜닝

### LLM 서비스 최적화

`llm-service/config.yaml` 파일에서 다음 설정을 조정:

- `gpu_memory_utilization`: GPU 메모리 사용률 (기본 0.9)
- `max_model_len`: 최대 컨텍스트 길이 (기본 8192)
- `tensor_parallel_size`: 멀티 GPU 설정

### 데이터베이스 최적화

`.env` 파일에서 PostgreSQL 설정 조정:

```env
POSTGRES_MAX_CONNECTIONS=100
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

## 보안 권장사항

1. 정기적으로 비밀번호 변경
2. 관리자 계정 최소화
3. 로그 정기 검토
4. 백업 정기 수행
5. 시스템 업데이트 정기 적용

## 지원

문제가 지속되면 다음 정보와 함께 문의:
- 시스템 사양 (CPU, RAM, GPU)
- Docker 버전
- 오류 로그
- 수행한 단계
