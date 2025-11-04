#!/usr/bin/env python3
"""
Feature 002: 수동 인수 테스트 간편 스크립트
데이터베이스 직접 쿼리로 검증
"""

import subprocess
import json
from datetime import datetime

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

test_results = {'passed': 0, 'failed': 0, 'warnings': 0}

def log_pass(test_name, detail=""):
    test_results['passed'] += 1
    print(f"{GREEN}✅ PASS{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def log_fail(test_name, detail=""):
    test_results['failed'] += 1
    print(f"{RED}❌ FAIL{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def log_warn(test_name, detail=""):
    test_results['warnings'] += 1
    print(f"{YELLOW}⚠️  WARN{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def run_sql(query):
    """Run SQL query in PostgreSQL container"""
    cmd = [
        'docker', 'exec', 'llm-webapp-postgres',
        'psql', '-U', 'llm_app', '-d', 'llm_webapp',
        '-t', '-c', query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

print(f"\n{BLUE}{'='*80}{RESET}")
print(f"{BLUE}Feature 002: 수동 인수 테스트{RESET}")
print(f"{BLUE}{'='*80}{RESET}\n")

# AS-1.1: 메트릭 데이터 존재 확인
print(f"{BLUE}AS-1.1: 메트릭 데이터 존재 확인{RESET}\n")

metric_types = ['active_users', 'storage_bytes', 'active_sessions',
                'conversation_count', 'document_count', 'tag_count']

for metric_type in metric_types:
    query = f"SELECT COUNT(*) FROM metric_snapshots WHERE metric_type='{metric_type}';"
    count = run_sql(query)
    if count and int(count) > 0:
        log_pass(f"메트릭 '{metric_type}' 데이터 존재", f"{count.strip()}개 스냅샷")
    else:
        log_fail(f"메트릭 '{metric_type}' 데이터 없음")

# 데이터 시간 범위 확인
query = """
SELECT
    EXTRACT(EPOCH FROM (MAX(collected_at) - MIN(collected_at)))/3600 as hours,
    MIN(collected_at) as earliest,
    MAX(collected_at) as latest
FROM metric_snapshots;
"""
result = run_sql(query)
if result:
    parts = result.split('|')
    if len(parts) >= 3:
        hours = float(parts[0].strip())
        log_pass(f"데이터 시간 범위", f"{hours:.1f}시간")
        if hours < 6:
            log_warn("데이터 범위가 6시간 미만", "시스템이 최근에 시작됨")
else:
    log_fail("데이터 시간 범위 확인 실패")

# AS-1.2: 현재 값 확인
print(f"\n{BLUE}AS-1.2: 최신 메트릭 값 확인{RESET}\n")

for metric_type in metric_types:
    query = f"""
    SELECT value, collected_at
    FROM metric_snapshots
    WHERE metric_type='{metric_type}'
    ORDER BY collected_at DESC
    LIMIT 1;
    """
    result = run_sql(query)
    if result and '|' in result:
        value, timestamp = result.split('|')
        log_pass(f"{metric_type} 최신 값", f"{value.strip()} (수집: {timestamp.strip()})")
    else:
        log_fail(f"{metric_type} 최신 값 없음")

# AS-1.3: 세분화 확인 (시간별/일별)
print(f"\n{BLUE}AS-1.3: 세분화 (hourly/daily) 확인{RESET}\n")

query = "SELECT granularity, COUNT(*) FROM metric_snapshots GROUP BY granularity;"
result = run_sql(query)
if result:
    for line in result.split('\n'):
        if '|' in line:
            gran, count = line.split('|')
            log_pass(f"{gran.strip()} 데이터", f"{count.strip()}개")
else:
    log_fail("세분화 데이터 확인 실패")

# AS-2.1: 비교를 위한 충분한 데이터
print(f"\n{BLUE}AS-2.1: 기간 비교 가능 여부{RESET}\n")

query = """
SELECT
    COUNT(DISTINCT DATE_TRUNC('day', collected_at)) as days_with_data
FROM metric_snapshots;
"""
result = run_sql(query)
if result:
    days = int(result.strip())
    if days >= 14:
        log_pass("기간 비교 가능", f"{days}일치 데이터 존재")
    elif days >= 7:
        log_warn("제한적 기간 비교", f"{days}일치 데이터 (14일 이상 권장)")
    else:
        log_fail("기간 비교 불가", f"{days}일치 데이터만 존재 (최소 7일 필요)")
else:
    log_fail("기간 비교 데이터 확인 실패")

# AS-3.1: 수집 상태 확인
print(f"\n{BLUE}AS-3.1: 메트릭 수집 상태{RESET}\n")

query = "SELECT COUNT(*) FROM metric_collection_failures;"
failures = run_sql(query)
if failures is not None:
    failure_count = int(failures.strip())
    if failure_count == 0:
        log_pass("수집 실패 없음", "모든 수집 성공")
    else:
        log_warn(f"수집 실패 {failure_count}건 기록됨")
else:
    log_fail("수집 실패 기록 확인 불가")

# 테이블 구조 확인
print(f"\n{BLUE}데이터베이스 구조 확인{RESET}\n")

query = """
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'metric_snapshots'
ORDER BY indexname;
"""
result = run_sql(query)
if result:
    index_count = len([l for l in result.split('\n') if l.strip()])
    log_pass("인덱스 생성 확인", f"{index_count}개 인덱스")
else:
    log_warn("인덱스 확인 실패")

# Summary
print(f"\n{BLUE}{'='*80}{RESET}")
print(f"{BLUE}테스트 결과 요약{RESET}")
print(f"{BLUE}{'='*80}{RESET}\n")
print(f"{GREEN}통과{RESET}: {test_results['passed']}")
print(f"{RED}실패{RESET}: {test_results['failed']}")
print(f"{YELLOW}경고{RESET}: {test_results['warnings']}")
total = test_results['passed'] + test_results['failed'] + test_results['warnings']
print(f"\n총 테스트: {total}")

if test_results['failed'] == 0:
    success_rate = test_results['passed'] / (test_results['passed'] + test_results['warnings']) * 100
    print(f"성공률: {success_rate:.1f}%\n")
    print(f"{GREEN}✅ 자동화 테스트 통과!{RESET}\n")
    print(f"{YELLOW}📝 참고: UI 인수 테스트는 브라우저에서 직접 수행해야 합니다:{RESET}")
    print(f"   1. http://localhost:3000/admin 접속")
    print(f"   2. '시스템 메트릭 히스토리' 섹션 확인")
    print(f"   3. 그래프 마우스 호버로 툴팁 확인")
    print(f"   4. '비교' 모드 테스트")
    print(f"   5. CSV/PDF 내보내기 테스트\n")
else:
    print(f"\n{RED}❌ 일부 테스트 실패 - 상세 내용 확인 필요{RESET}\n")
