# Scripts Directory

이 디렉토리에는 프로젝트 운영 및 배포를 위한 스크립트가 포함되어 있습니다.

## 디렉토리 구조

```
scripts/
├── README.md                    # 이 파일
├── offline-install.sh           # 에어갭 오프라인 설치 스크립트 (T222)
├── bundle-offline-deps.sh       # 오프라인 의존성 번들링
├── backup/                      # 백업 관련 스크립트
│   ├── backup-daily.sh          # 일일 증분 백업
│   ├── backup-weekly.sh         # 주간 전체 백업
│   ├── restore-from-backup.sh   # 백업 복원
│   └── cleanup-old-backups.sh   # 오래된 백업 정리
└── dev/                         # 개발용 스크립트 (git에서 제외됨)
    ├── start-mvp.bat            # MVP 빠른 시작 (레거시)
    ├── start-local-dev.bat      # 로컬 개발 시작
    ├── stop-mvp.bat             # MVP 중지
    ├── rebuild.bat              # 재빌드
    ├── test_conversations_api.bat  # API 테스트 (Windows)
    └── test_conversations_api.sh   # API 테스트 (Linux/Mac)
```

## 프로덕션 스크립트

### 오프라인 설치 (Air-gapped Deployment)

**offline-install.sh**
- 에어갭 환경에서 전체 애플리케이션 설치
- Python 의존성, Node.js 패키지, LLM 모델 설치
- 참조: `docs/deployment/air-gapped-deployment.md`

```bash
# 사용법
chmod +x scripts/offline-install.sh
./scripts/offline-install.sh
```

**bundle-offline-deps.sh**
- 오프라인 설치를 위한 의존성 번들 생성
- pip wheels, npm packages, 모델 파일 포함
- 인터넷 연결된 환경에서 실행

```bash
# 사용법 (인터넷 연결된 환경)
./scripts/bundle-offline-deps.sh
# 생성: offline-bundle.tar.gz
```

## 백업 스크립트 (`scripts/backup/`)

### 일일 증분 백업

**backup-daily.sh**
- 증분 백업 (변경된 데이터만)
- PostgreSQL pg_dump + rsync
- 참조: FR-042

```bash
# 사용법
./scripts/backup/backup-daily.sh

# Cron 설정 예제 (매일 새벽 2시)
0 2 * * * /path/to/scripts/backup/backup-daily.sh >> /var/log/backup-daily.log 2>&1
```

### 주간 전체 백업

**backup-weekly.sh**
- 전체 데이터 백업
- PostgreSQL full dump + 모든 파일
- 참조: FR-042

```bash
# 사용법
./scripts/backup/backup-weekly.sh

# Cron 설정 예제 (매주 일요일 새벽 3시)
0 3 * * 0 /path/to/scripts/backup/backup-weekly.sh >> /var/log/backup-weekly.log 2>&1
```

### 백업 복원

**restore-from-backup.sh**
- 백업에서 데이터 복원
- 대화형 프롬프트로 백업 파일 선택

```bash
# 사용법
./scripts/backup/restore-from-backup.sh
```

### 백업 정리

**cleanup-old-backups.sh**
- 오래된 백업 파일 자동 삭제
- 설정 가능한 보존 기간

```bash
# 사용법
./scripts/backup/cleanup-old-backups.sh

# Cron 설정 예제 (매일 새벽 4시)
0 4 * * * /path/to/scripts/backup/cleanup-old-backups.sh
```

## 개발 스크립트 (`scripts/dev/`)

⚠️ **주의**: 이 디렉토리는 `.gitignore`에서 제외됩니다. 개발자 개인 스크립트를 여기에 저장하세요.

### 레거시 스크립트

이 스크립트들은 이전 MVP 단계에서 사용되었으며, 현재는 루트의 `start.bat`/`stop.bat`를 사용하는 것을 권장합니다.

- **start-mvp.bat** - MVP 빠른 시작 (docker-compose.dev.yml 사용)
- **start-local-dev.bat** - 로컬 개발 환경 시작
- **stop-mvp.bat** - MVP 중지
- **rebuild.bat** - 컨테이너 재빌드

### 테스트 스크립트

- **test_conversations_api.bat** - Windows용 API 테스트
- **test_conversations_api.sh** - Linux/Mac용 API 테스트

## 루트 스크립트 (권장)

프로젝트 루트에 사용자 친화적인 스크립트가 있습니다:

### start.bat (Windows)
```batch
start.bat
```
- Docker Compose로 전체 애플리케이션 시작
- 데이터베이스 마이그레이션 자동 실행
- 관리자 계정 자동 생성 (admin/Admin123!)

### stop.bat (Windows)
```batch
stop.bat
```
- 모든 Docker 컨테이너 중지

## 모범 사례

### 1. 프로덕션 환경
- **백업**: Cron으로 자동화된 백업 스케줄 설정
- **로그**: 모든 스크립트 실행 결과를 로그 파일에 기록
- **모니터링**: 백업 성공/실패 알림 설정

### 2. 개발 환경
- **개인 스크립트**: `scripts/dev/`에 저장 (git 추적 안 됨)
- **공유 스크립트**: 루트 또는 `scripts/`에 저장

### 3. 오프라인 배포
1. 인터넷 연결 환경에서 `bundle-offline-deps.sh` 실행
2. `offline-bundle.tar.gz`를 에어갭 환경으로 전송
3. 에어갭 환경에서 `offline-install.sh` 실행

## 참고 문서

- **백업 가이드**: `docs/admin/backup-restore-guide.md`
- **배포 가이드**: `docs/deployment/deployment-guide.md`
- **에어갭 배포**: `docs/deployment/air-gapped-deployment.md`
- **에어갭 검증**: `docs/deployment/air-gapped-verification-checklist.md`

## 문제 해결

### 권한 오류 (Linux/Mac)
```bash
chmod +x scripts/*.sh
chmod +x scripts/backup/*.sh
```

### Windows에서 .sh 스크립트 실행
- Git Bash 사용
- WSL (Windows Subsystem for Linux) 사용
- 또는 해당 .bat 스크립트 사용

### Docker 오류
```bash
# Docker가 실행 중인지 확인
docker ps

# Docker 재시작
# Windows: Docker Desktop 재시작
# Linux: sudo systemctl restart docker
```
