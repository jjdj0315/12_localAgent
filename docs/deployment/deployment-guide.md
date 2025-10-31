# 배포 가이드

**버전**: 1.0  
**마지막 업데이트**: 2025-10-31

## 목차
1. [하드웨어 요구사항](#하드웨어-요구사항)
2. [설치 절차](#설치-절차)
3. [환경 설정](#환경-설정)
4. [배포 실행](#배포-실행)
5. [검증](#검증)
6. [문제 해결](#문제-해결)

---

## 하드웨어 요구사항

### 최소 사양
- **CPU**: 8 코어 (Intel Xeon 또는 동급)
- **RAM**: 16GB
- **디스크**: 100GB SSD
- **네트워크**: 내부망 연결

### 권장 사양
- **CPU**: 16 코어
- **RAM**: 32GB
- **디스크**: 500GB SSD (백업용 추가 스토리지)
- **네트워크**: 1Gbps

### 동시 사용자 수에 따른 사양
| 사용자 수 | CPU | RAM | 디스크 |
|----------|-----|-----|--------|
| ~10명 | 8코어 | 16GB | 100GB |
| ~30명 | 16코어 | 32GB | 250GB |
| ~50명 | 32코어 | 64GB | 500GB |

---

## 설치 절차

### 1. 사전 요구사항 설치

#### Docker & Docker Compose
```bash
# Docker 설치 (Ubuntu 22.04)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 버전 확인
docker --version
docker compose version
```

#### Git
```bash
sudo apt-get install git
```

### 2. 애플리케이션 다운로드

```bash
# 프로젝트 클론
cd /opt
sudo git clone <repository-url> llm-webapp
cd llm-webapp

# 권한 설정
sudo chown -R $USER:$USER /opt/llm-webapp
```

### 3. 환경 설정 파일 생성

```bash
# .env 파일 생성
cp backend/.env.example .env

# .env 파일 편집
nano .env
```

필수 환경 변수:
```bash
# 데이터베이스
POSTGRES_USER=llm_app
POSTGRES_PASSWORD=<강력한_비밀번호>
POSTGRES_DB=llm_webapp

# 애플리케이션
SECRET_KEY=<랜덤_시크릿_키>
SESSION_SECRET=<랜덤_세션_시크릿>

# LLM 설정
LLM_BACKEND=llama_cpp
GGUF_MODEL_PATH=/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

### 4. 모델 파일 준비

```bash
# 모델 디렉토리 생성
mkdir -p models

# GGUF 모델 다운로드 (폐쇄망 환경)
# 외부에서 다운로드 후 USB/네트워크로 전송
# 모델 파일을 models/ 디렉토리에 배치
```

---

## 배포 실행

### 1. Docker 빌드

```bash
# 이미지 빌드
docker compose build

# 빌드 시간: 약 10-15분
```

### 2. 데이터베이스 초기화

```bash
# 데이터베이스 마이그레이션
docker compose run --rm backend alembic upgrade head

# 초기 관리자 계정 생성
docker compose run --rm backend python scripts/create_admin.py
```

### 3. 애플리케이션 시작

```bash
# 백그라운드로 실행
docker compose up -d

# 로그 확인
docker compose logs -f
```

### 4. 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8000/api/v1/health

# 상세 헬스 체크
curl http://localhost:8000/api/v1/health/detailed
```

---

## 검증

### 1. 서비스 상태 확인

```bash
# 컨테이너 상태
docker compose ps

# 예상 출력:
# NAME                  STATUS
# llm-webapp-postgres   Up (healthy)
# llm-webapp-backend    Up
# llm-webapp-frontend   Up
```

### 2. 기능 테스트

#### 웹 인터페이스 접속
```
http://<서버-IP>:3000
```

#### API 테스트
```bash
# 헬스 체크
curl http://localhost:8000/api/v1/health

# 관리자 로그인 테스트
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<비밀번호>"}'
```

### 3. 로그 확인

```bash
# 백엔드 로그
docker compose logs backend | tail -50

# 프론트엔드 로그
docker compose logs frontend | tail -50

# 데이터베이스 로그
docker compose logs postgres | tail -50
```

---

## 운영

### 서비스 관리

```bash
# 중지
docker compose stop

# 시작
docker compose start

# 재시작
docker compose restart

# 완전 종료
docker compose down

# 완전 종료 + 볼륨 삭제 (주의!)
docker compose down -v
```

### 로그 관리

```bash
# 실시간 로그
docker compose logs -f

# 특정 서비스 로그
docker compose logs -f backend

# 최근 100줄
docker compose logs --tail=100
```

### 백업

```bash
# 자동 백업 (cron 설정됨)
# 일일: 매일 02:00
# 주간: 일요일 02:00

# 수동 백업
./scripts/backup-daily.sh

# 백업 확인
ls -lh /backup/daily/
ls -lh /backup/weekly/
```

---

## 업데이트

### 애플리케이션 업데이트

```bash
# 1. 백업
./scripts/backup-daily.sh

# 2. 코드 업데이트
git pull origin main

# 3. 재빌드 & 재시작
docker compose down
docker compose build
docker compose up -d

# 4. 마이그레이션
docker compose run --rm backend alembic upgrade head

# 5. 헬스 체크
curl http://localhost:8000/api/v1/health/detailed
```

---

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker compose logs

# 컨테이너 상태
docker compose ps -a

# 특정 컨테이너 재시작
docker compose restart backend
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
docker compose exec postgres pg_isready

# 데이터베이스 접속 테스트
docker compose exec postgres psql -U llm_app -d llm_webapp

# 연결 정보 확인
docker compose exec backend env | grep POSTGRES
```

### LLM 모델 로딩 실패

```bash
# 모델 파일 확인
docker compose exec backend ls -la /models/

# 환경 변수 확인
docker compose exec backend env | grep GGUF

# 백엔드 로그 확인
docker compose logs backend | grep -i "model\|llm"
```

### 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# Docker 정리
docker system prune -a

# 오래된 백업 삭제
find /backup/daily -mtime +30 -delete
```

### 성능 저하

```bash
# 시스템 리소스 확인
docker stats

# CPU/메모리 사용량
top

# 네트워크 연결
netstat -an | grep 8000
```

---

## 보안

### 방화벽 설정

```bash
# UFW 설정 (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSL/TLS 설정

nginx를 사용한 HTTPS 설정:
```bash
# nginx 설치
sudo apt-get install nginx

# Let's Encrypt 인증서
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 모니터링

### 헬스 체크 자동화

```bash
# 헬스 체크 스크립트
cat > /opt/llm-webapp/scripts/health-check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/api/v1/health/ready || exit 1
EOF

chmod +x /opt/llm-webapp/scripts/health-check.sh

# Cron 설정 (5분마다)
*/5 * * * * /opt/llm-webapp/scripts/health-check.sh
```

### 로그 모니터링

```bash
# 에러 로그 모니터링
docker compose logs backend | grep -i error

# 성능 로그
docker compose logs backend | grep "X-Response-Time"
```

---

## 참고 자료

- 백업 및 복원: docs/admin/backup-restore-guide.md
- 고급 기능: docs/admin/advanced-features-manual.md
- 커스터마이징: docs/admin/customization-guide.md
- 사용자 매뉴얼: docs/user/user-guide-ko.md

---

## 지원

문제 발생 시:
1. 로그 확인
2. 헬스 체크 실행
3. 문제 해결 섹션 참조
4. 시스템 관리자에게 문의
