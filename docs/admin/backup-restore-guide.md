# 백업 및 복원 가이드

**대상**: IT 담당자  
**마지막 업데이트**: 2025-10-31  
**버전**: 1.0

## 개요

이 문서는 Local LLM 웹 애플리케이션의 백업 생성 및 복원 절차를 설명합니다. 백업은 데이터베이스(PostgreSQL)와 업로드된 문서 파일을 포함합니다.

## 백업 전략 (FR-042)

### 일일 증분 백업
- **실행 시간**: 매일 오전 2시
- **대상**: 데이터베이스 + 문서 파일 (변경분만)
- **저장 위치**: `/backup/daily/`
- **보관 기간**: 30일

### 주간 전체 백업
- **실행 시간**: 매주 일요일 오전 2시
- **대상**: 데이터베이스 + 문서 파일 (전체)
- **저장 위치**: `/backup/weekly/`
- **보관 기간**: 최소 4개 전체 백업 유지

### 자동 정리
- 30일 이상 된 백업은 자동 삭제
- cleanup-old-backups.sh 스크립트가 매일 오전 3시 실행

## 백업 스크립트

### 1. 일일 증분 백업 (backup-daily.sh)

```bash
#!/bin/bash
# 일일 증분 백업 스크립트
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/daily"
DB_NAME="llm_webapp"

# 데이터베이스 백업
pg_dump -F c -d $DB_NAME -f $BACKUP_DIR/db_$DATE.dump

# 문서 파일 증분 백업 (rsync)
rsync -a --link-dest=../previous /uploads/ $BACKUP_DIR/uploads_$DATE/

# 백업 로그
echo "[$(date)] Daily backup completed: db_$DATE.dump" >> /var/log/llm-backup.log
```

### 2. 주간 전체 백업 (backup-weekly.sh)

```bash
#!/bin/bash
# 주간 전체 백업 스크립트
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/weekly"
DB_NAME="llm_webapp"

# 데이터베이스 전체 백업
pg_dump -F c -d $DB_NAME -f $BACKUP_DIR/db_full_$DATE.dump

# 문서 파일 전체 백업
tar -czf $BACKUP_DIR/uploads_full_$DATE.tar.gz /uploads/

# 백업 로그
echo "[$(date)] Weekly full backup completed" >> /var/log/llm-backup.log
```

### 3. 오래된 백업 정리 (cleanup-old-backups.sh)

```bash
#!/bin/bash
# 30일 이상 된 백업 삭제
find /backup/daily -name "*.dump" -mtime +30 -delete
find /backup/daily -type d -name "uploads_*" -mtime +30 -exec rm -rf {} +
find /backup/weekly -name "*.tar.gz" -mtime +30 -delete

echo "[$(date)] Old backups cleaned up" >> /var/log/llm-backup.log
```

## 백업 설정 (Cron)

다음 내용을 `/etc/cron.d/llm-backup`에 추가:

```cron
# 일일 백업 (매일 오전 2시)
0 2 * * * root /opt/llm-webapp/scripts/backup-daily.sh

# 주간 백업 (매주 일요일 오전 2시)
0 2 * * 0 root /opt/llm-webapp/scripts/backup-weekly.sh

# 오래된 백업 정리 (매일 오전 3시)
0 3 * * * root /opt/llm-webapp/scripts/cleanup-old-backups.sh
```

## 복원 절차

### 복원 전 확인사항
- 복원할 백업 파일 확인
- 현재 데이터 백업 권장
- 애플리케이션 중지 필요

### 데이터베이스 복원

```bash
# 1. 애플리케이션 중지
cd /opt/llm-webapp
docker-compose down

# 2. 데이터베이스 복원
pg_restore -c -d llm_webapp /backup/daily/db_20251031.dump

# 3. 권한 확인
psql -d llm_webapp -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO llm_user;"
```

### 문서 파일 복원

```bash
# 증분 백업에서 복원
rsync -a /backup/daily/uploads_20251031/ /uploads/

# 또는 전체 백업에서 복원
tar -xzf /backup/weekly/uploads_full_20251027.tar.gz -C /
```

### 애플리케이션 재시작

```bash
# Docker Compose로 재시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 헬스 체크
curl http://localhost:8000/api/v1/health
```

## 자동 복원 스크립트 (restore-from-backup.sh)

```bash
#!/bin/bash
# 사용법: ./restore-from-backup.sh YYYYMMDD

if [ -z "$1" ]; then
  echo "Usage: $0 YYYYMMDD"
  echo "Example: $0 20251031"
  exit 1
fi

DATE=$1
BACKUP_DIR="/backup/daily"

echo "복원 시작: $DATE"

# 1. 애플리케이션 중지
cd /opt/llm-webapp
docker-compose down

# 2. 데이터베이스 복원
echo "데이터베이스 복원 중..."
pg_restore -c -d llm_webapp $BACKUP_DIR/db_$DATE.dump

if [ $? -eq 0 ]; then
  echo "데이터베이스 복원 완료"
else
  echo "데이터베이스 복원 실패"
  exit 1
fi

# 3. 문서 파일 복원
echo "문서 파일 복원 중..."
rsync -a $BACKUP_DIR/uploads_$DATE/ /uploads/

if [ $? -eq 0 ]; then
  echo "문서 파일 복원 완료"
else
  echo "문서 파일 복원 실패"
  exit 1
fi

# 4. 애플리케이션 재시작
echo "애플리케이션 재시작 중..."
docker-compose up -d

# 5. 헬스 체크
sleep 10
curl -f http://localhost:8000/api/v1/health

if [ $? -eq 0 ]; then
  echo "복원 완료 및 애플리케이션 정상 작동"
else
  echo "애플리케이션 헬스 체크 실패 - 로그 확인 필요"
  docker-compose logs backend
fi
```

## 문제 해결

### 백업 실패 시
- 디스크 공간 확인: `df -h /backup`
- PostgreSQL 접근 권한 확인
- 백업 로그 확인: `tail -f /var/log/llm-backup.log`

### 복원 실패 시
- 백업 파일 무결성 확인: `pg_restore --list backup.dump`
- 데이터베이스 연결 확인
- 파일 권한 확인: `ls -la /uploads`

### 디스크 공간 부족
- 오래된 백업 수동 삭제
- 백업 보관 기간 단축 (cron 설정 수정)
- 백업 저장소 확장

## 백업 모니터링

### 백업 상태 확인
```bash
# 최근 백업 목록
ls -lh /backup/daily/ | tail -5
ls -lh /backup/weekly/ | tail -5

# 백업 로그 확인
tail -n 50 /var/log/llm-backup.log

# 백업 파일 크기 확인
du -sh /backup/*
```

### 관리자 패널에서 확인
- 백업 이력 테이블에서 최근 백업 상태 확인
- 실패한 백업이 있는지 확인
- 백업 저장소 용량 모니터링

## 재해 복구 계획

### 전체 시스템 복구 절차
1. 새 서버에 Docker 및 PostgreSQL 설치
2. 백업 파일 복사
3. 애플리케이션 소스 코드 배포
4. 데이터베이스 및 파일 복원
5. 환경 변수 설정
6. 애플리케이션 시작 및 검증

### 복구 시간 목표 (RTO)
- 목표: 4시간 이내 복구
- 데이터 손실 목표 (RPO): 최대 24시간 (일일 백업 기준)

## 참고사항

- 백업 파일은 암호화되지 않으므로 물리적 보안 중요
- 백업 저장소는 시스템 디스크와 별도 볼륨 사용 권장
- 정기적으로 복원 테스트 수행 (분기별 1회 권장)
- 백업 스크립트 실행 권한 확인: `chmod +x scripts/*.sh`

## 문의

백업 관련 문제 발생 시 시스템 관리자에게 문의하세요.
