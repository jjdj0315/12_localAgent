# 배포 가이드: 관리자 메트릭 히스토리 대시보드

**기능**: 002-admin-metrics-history
**버전**: 1.0.0
**날짜**: 2025-11-02

## 개요

이 가이드는 관리자 메트릭 히스토리 및 그래프 기능을 프로덕션 환경에 배포하는 방법을 설명합니다.

## 사전 요구사항

### 시스템 요구사항
- Python 3.11 이상
- Node.js 18 이상
- PostgreSQL 15 이상
- Docker & Docker Compose (선택사항)

### 기존 기능 요구사항
- Feature 001 (local-llm-webapp) 배포 완료
- 관리자 계정 생성 완료
- PostgreSQL 데이터베이스 실행 중

## 배포 단계

### 1단계: 백엔드 의존성 설치

```bash
cd backend

# 가상환경 활성화 (이미 있는 경우)
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# 새 의존성 설치
pip install apscheduler==3.10.4 pandas==2.1.3 reportlab==4.0.7

# 또는 requirements.txt에서 전체 재설치
pip install -r requirements.txt
```

**에어갭 환경**: 인터넷이 없는 환경에서는 다음 파일들을 사전에 다운로드:
```bash
# 인터넷 연결된 환경에서
pip download -r requirements.txt -d ./packages

# 에어갭 환경에서
pip install --no-index --find-links=./packages -r requirements.txt
```

### 2단계: 프론트엔드 의존성 설치

```bash
cd frontend

# 새 의존성 설치
npm install react-chartjs-2 chart.js chartjs-adapter-date-fns date-fns downsample

# 또는 package.json에서 전체 재설치
npm install
```

**에어갭 환경**:
```bash
# 인터넷 연결된 환경에서
npm pack react-chartjs-2 chart.js chartjs-adapter-date-fns date-fns downsample
# 또는
npm install --offline

# 에어갭 환경에서 .tgz 파일들 설치
npm install ./react-chartjs-2-*.tgz ./chart.js-*.tgz ...
```

### 3단계: 데이터베이스 마이그레이션

```bash
cd backend

# 마이그레이션 상태 확인
python -m alembic current

# 메트릭 테이블 생성
python -m alembic upgrade head

# 마이그레이션 성공 확인
python -m alembic current
# 출력: 20251102_add_metrics_tables (head)
```

**마이그레이션 검증**:
```sql
-- PostgreSQL에 접속하여 확인
\c llm_webapp
\dt metric*

-- 예상 출력:
-- metric_snapshots
-- metric_collection_failures
```

### 4단계: 백엔드 재시작

```bash
cd backend

# 개발 환경
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 환경
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**중요**: 백엔드가 시작되면 APScheduler가 자동으로 초기화되고 메트릭 수집이 시작됩니다.

**로그 확인**:
```bash
# 스케줄러 시작 확인
"Metrics scheduler started"

# 첫 번째 수집 (정시에 발생)
"Hourly metrics collected successfully"
```

### 5단계: 프론트엔드 빌드 및 재시작

```bash
cd frontend

# 프로덕션 빌드
npm run build

# 프로덕션 서버 시작
npm run start
```

### 6단계: 배포 검증

#### 6.1 API 엔드포인트 테스트

```bash
# 관리자 토큰 필요 (로그인 후 획득)
TOKEN="your_admin_token_here"

# 현재 메트릭 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/metrics/current

# 수집 상태 확인
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/metrics/status
```

**예상 응답**:
```json
{
  "last_collection_at": "2025-11-02T10:00:00Z",
  "next_collection_at": "2025-11-02T11:00:00Z",
  "recent_failures": [],
  "failure_count_24h": 0,
  "status": "healthy"
}
```

#### 6.2 웹 UI 접근

1. 브라우저에서 `http://localhost:3000/admin/metrics` 접속
2. 관리자 계정으로 로그인
3. 메트릭 대시보드 확인:
   - ✅ 6개 메트릭 그래프 표시
   - ✅ 시간 범위 선택기 (7/30/90일)
   - ✅ 시간별/일별 토글
   - ✅ 비교 모드 전환
   - ✅ 내보내기 버튼

#### 6.3 첫 데이터 수집 대기

**중요**: 첫 번째 메트릭 데이터는 다음 정시에 수집됩니다.

예: 현재 시각이 14:23이면, 첫 수집은 15:00에 발생합니다.

**빈 상태 메시지 확인**:
```
데이터 수집 중입니다
첫 데이터는 다음 정시에 표시됩니다
```

### 7단계: 수동 수집 (선택사항, 테스트용)

개발/테스트 환경에서 즉시 데이터를 보려면:

```python
# Python 콘솔에서
from app.core.database import get_db
from app.services.metrics_collector import MetricsCollector
from datetime import datetime, timezone

async def manual_collect():
    async for db in get_db():
        collector = MetricsCollector(db)
        results = await collector.collect_all_metrics(granularity="hourly")
        print(f"수집 완료: {results}")
        await db.close()
        break

# 실행
import asyncio
asyncio.run(manual_collect())
```

## Docker Compose 배포

### docker-compose.yml 업데이트

기존 `docker-compose.yml`에 다음 변경사항 없음 (의존성만 추가):

```yaml
services:
  backend:
    # ... 기존 설정 유지
    environment:
      # 메트릭 수집 설정 (선택사항)
      - METRICS_COLLECTION_ENABLED=true
      - METRICS_HOURLY_RETENTION_DAYS=30
      - METRICS_DAILY_RETENTION_DAYS=90
```

### Docker 배포

```bash
# 컨테이너 재빌드 (새 의존성 포함)
docker-compose build backend frontend

# 마이그레이션 실행
docker-compose exec backend python -m alembic upgrade head

# 서비스 재시작
docker-compose restart backend frontend

# 로그 확인
docker-compose logs -f backend
```

## 문제 해결

### 문제 1: 마이그레이션 실패

**증상**:
```
alembic.util.exc.CommandError: Can't locate revision identified by '...'
```

**해결**:
```bash
# 현재 마이그레이션 상태 확인
python -m alembic current

# 이전 버전에서 시작
python -m alembic downgrade -1
python -m alembic upgrade head
```

### 문제 2: 스케줄러가 시작되지 않음

**증상**: 로그에 "Metrics scheduler started" 없음

**해결**:
```bash
# 백엔드 로그 확인
tail -f backend.log | grep -i scheduler

# APScheduler 설치 확인
pip show apscheduler

# 수동 스케줄러 테스트
python -c "from app.core.scheduler import start_scheduler; start_scheduler()"
```

### 문제 3: 첫 데이터가 수집되지 않음

**증상**: 1시간 이상 경과했지만 여전히 빈 그래프

**확인사항**:
```sql
-- PostgreSQL에서 데이터 확인
SELECT COUNT(*) FROM metric_snapshots;

-- 실패 내역 확인
SELECT * FROM metric_collection_failures ORDER BY created_at DESC LIMIT 10;
```

**해결**:
```bash
# 백엔드 로그에서 에러 확인
grep -i "metric" backend.log | grep -i "error"

# 수집 서비스 테스트
python -c "
from app.services.metrics_collector import MetricsCollector
# ... 수동 수집 코드
"
```

### 문제 4: 그래프가 로딩되지 않음

**증상**: "메트릭 데이터를 불러오는데 실패했습니다"

**확인사항**:
1. API 엔드포인트 접근 가능 여부
2. 관리자 인증 토큰 유효성
3. CORS 설정

**해결**:
```bash
# API 직접 테스트
curl -v http://localhost:8000/api/v1/metrics/current

# 브라우저 콘솔에서 네트워크 탭 확인
# F12 -> Network -> 실패한 요청 확인
```

### 문제 5: CSV/PDF 내보내기 실패

**증상**: "데이터 내보내기에 실패했습니다"

**확인사항**:
```bash
# export 디렉토리 권한 확인
ls -la backend/exports

# ReportLab 설치 확인
pip show reportlab

# pandas 설치 확인
pip show pandas
```

## 성능 최적화

### 데이터베이스 인덱스 확인

```sql
-- 인덱스 사용 확인
EXPLAIN ANALYZE
SELECT * FROM metric_snapshots
WHERE metric_type = 'active_users'
  AND granularity = 'hourly'
  AND collected_at >= NOW() - INTERVAL '7 days'
ORDER BY collected_at ASC;

-- 인덱스가 사용되는지 확인 (Index Scan on idx_metric_type_time)
```

### 메모리 사용량 모니터링

```bash
# 백엔드 메모리 사용량
ps aux | grep uvicorn

# 프론트엔드 빌드 크기
du -sh frontend/.next
```

### 응답 시간 측정

```bash
# 시계열 API 응답 시간
time curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/metrics/timeseries?metric_type=active_users&granularity=hourly&start_time=2025-10-26T00:00:00Z&end_time=2025-11-02T00:00:00Z"

# 목표: < 500ms
```

## 유지보수

### 정기 작업

**일일**:
- 메트릭 수집 상태 모니터링 (failure_count_24h < 5)
- 내보내기 파일 정리 (자동, 1시간 후 삭제)

**주간**:
- 데이터베이스 크기 확인
- 오래된 메트릭 정리 상태 확인

**월간**:
- 성능 지표 검토 (SC-001, SC-007, SC-003)
- 스토리지 사용량 추이 분석

### 백업

메트릭 데이터는 `metric_snapshots` 및 `metric_collection_failures` 테이블에 저장됩니다.

```bash
# 메트릭 데이터만 백업
pg_dump -U postgres -d llm_webapp -t metric_snapshots -t metric_collection_failures > metrics_backup.sql

# 복원
psql -U postgres -d llm_webapp < metrics_backup.sql
```

### 로그 모니터링

중요 로그 메시지:

```
✅ "Metrics scheduler started" - 스케줄러 정상 시작
✅ "Hourly metrics collected successfully" - 시간별 수집 성공
✅ "다운샘플링 완료: X -> Y 행" - 내보내기 시 다운샘플링
⚠️ "메트릭 수집 최대 재시도 횟수 초과" - 수집 실패 (3회 재시도 후)
⚠️ "CSV 크기 초과 (X bytes), 다운샘플링 적용" - 대용량 내보내기
```

## 롤백 절차

문제 발생 시 이전 버전으로 롤백:

### 1. 데이터베이스 롤백

```bash
# 마이그레이션 되돌리기
python -m alembic downgrade -1

# 확인
python -m alembic current
```

### 2. 코드 롤백

```bash
# Git으로 이전 버전 체크아웃
git checkout <previous_commit_hash>

# 의존성 재설치
pip install -r requirements.txt
npm install

# 재시작
docker-compose restart
```

**주의**: 메트릭 데이터는 유지되므로, 롤백 후 다시 업그레이드 가능합니다.

## 보안 고려사항

1. **관리자 전용**: 모든 메트릭 엔드포인트는 관리자 인증 필요
2. **데이터 격리**: 메트릭은 시스템 전체 집계만 포함 (사용자별 데이터 없음)
3. **내보내기 파일**: 1시간 후 자동 삭제로 민감 데이터 노출 최소화
4. **에어갭 안전**: 외부 API 호출 없음

## 추가 리소스

- **기능 명세**: `specs/002-admin-metrics-history/spec.md`
- **데이터 모델**: `specs/002-admin-metrics-history/data-model.md`
- **API 문서**: `specs/002-admin-metrics-history/contracts/openapi.yaml`
- **빠른 시작 가이드**: `specs/002-admin-metrics-history/quickstart.md`

## 지원

문제 발생 시:

1. 로그 파일 확인 (`backend.log`, `frontend.log`)
2. 데이터베이스 상태 확인 (`SELECT * FROM metric_collection_failures`)
3. GitHub Issues에 보고 (로그 첨부)

---

**배포 체크리스트**:

- [ ] 백엔드 의존성 설치 완료
- [ ] 프론트엔드 의존성 설치 완료
- [ ] 데이터베이스 마이그레이션 실행 완료
- [ ] 백엔드 재시작 완료 (스케줄러 시작 확인)
- [ ] 프론트엔드 재시작 완료
- [ ] API 엔드포인트 테스트 통과
- [ ] 웹 UI 접근 가능
- [ ] 첫 메트릭 수집 확인 (정시 후)
- [ ] 그래프 렌더링 확인
- [ ] CSV 내보내기 테스트
- [ ] PDF 내보내기 테스트 (한글 폰트 확인)

**배포 완료!** 🎉
