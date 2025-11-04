#!/usr/bin/env python3
"""
수동 인수 테스트 자동화 스크립트
Feature 002: Admin Dashboard Metrics History & Graphs

이 스크립트는 브라우저 테스트를 대신하여 백엔드 API와 데이터베이스를 검증합니다.
실제 UI 인수 테스트는 관리자가 브라우저에서 수행해야 합니다.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import app modules
sys.path.insert(0, '/app')
from app.core.database import get_db_session
from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_type import MetricType
from app.services.metrics_service import MetricsService
from app.services.metrics_collector import MetricsCollector

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0
}

def log_pass(test_name: str, detail: str = ""):
    global test_results
    test_results['passed'] += 1
    print(f"{GREEN}✅ PASS{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def log_fail(test_name: str, detail: str = ""):
    global test_results
    test_results['failed'] += 1
    print(f"{RED}❌ FAIL{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def log_warn(test_name: str, detail: str = ""):
    global test_results
    test_results['warnings'] += 1
    print(f"{YELLOW}⚠️  WARN{RESET}: {test_name}")
    if detail:
        print(f"   {detail}")

def log_info(message: str):
    print(f"{BLUE}ℹ️  INFO{RESET}: {message}")

async def test_as_1_1_metrics_data_exists():
    """AS-1.1: 7일 그래프 데이터 존재 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AS-1.1: 7일 그래프 데이터 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    async for session in get_db_session():
        try:
            # Check all 6 metric types exist
            metric_types = [mt.value for mt in MetricType]

            for metric_type in metric_types:
                result = await session.execute(
                    select(func.count(MetricSnapshot.id))
                    .where(MetricSnapshot.metric_type == metric_type)
                )
                count = result.scalar()

                if count > 0:
                    log_pass(f"메트릭 타입 '{metric_type}' 데이터 존재", f"{count}개 스냅샷")
                else:
                    log_fail(f"메트릭 타입 '{metric_type}' 데이터 없음")

            # Check data range
            result = await session.execute(
                select(
                    func.min(MetricSnapshot.collected_at),
                    func.max(MetricSnapshot.collected_at)
                )
            )
            min_date, max_date = result.first()

            if min_date and max_date:
                data_range = (max_date - min_date).total_seconds() / 3600
                log_pass(f"데이터 시간 범위", f"{data_range:.1f}시간 ({min_date} ~ {max_date})")

                if data_range < 6:
                    log_warn("데이터 범위가 6시간 미만", "시스템이 최근에 시작되었을 수 있습니다")
            else:
                log_fail("데이터 시간 범위 없음")

        except Exception as e:
            log_fail("데이터베이스 쿼리 실패", str(e))

async def test_as_1_2_current_values_display():
    """AS-1.2: 현재 값 표시 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AS-1.2: 현재 값 표시 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    service = MetricsService()

    try:
        current_metrics = await service.get_current_metrics()

        if current_metrics and len(current_metrics) == 6:
            log_pass("현재 메트릭 조회", f"{len(current_metrics)}개 메트릭")

            for metric in current_metrics:
                log_info(f"{metric['metric_type']}: {metric['value']}")
        else:
            log_fail("현재 메트릭 조회 실패", f"예상: 6개, 실제: {len(current_metrics) if current_metrics else 0}개")

    except Exception as e:
        log_fail("현재 메트릭 서비스 오류", str(e))

async def test_as_1_3_time_range_selection():
    """AS-1.3: 시간 범위 선택 기능 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AS-1.3: 시간 범위 선택 기능 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    service = MetricsService()

    # Test different time ranges
    time_ranges = [7, 30, 90]

    for days in time_ranges:
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            data = await service.get_time_series(
                metric_type=MetricType.ACTIVE_USERS,
                granularity='hourly',
                start_time=start_time,
                end_time=end_time
            )

            log_pass(f"{days}일 범위 데이터 조회", f"{len(data)}개 데이터 포인트")

        except Exception as e:
            log_fail(f"{days}일 범위 조회 실패", str(e))

async def test_as_2_1_comparison_mode():
    """AS-2.1: 비교 모드 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AS-2.1: 비교 모드 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    service = MetricsService()

    try:
        now = datetime.utcnow()

        # This week vs last week
        period1_end = now
        period1_start = now - timedelta(days=7)
        period2_end = period1_start
        period2_start = period1_start - timedelta(days=7)

        comparison = await service.compare_periods(
            metric_type=MetricType.ACTIVE_USERS,
            granularity='hourly',
            period1_start=period1_start,
            period1_end=period1_end,
            period2_start=period2_start,
            period2_end=period2_end
        )

        if comparison:
            log_pass("기간 비교 데이터 조회 성공")
            log_info(f"Period 1: {len(comparison['period1'])}개 포인트")
            log_info(f"Period 2: {len(comparison['period2'])}개 포인트")

            if 'percentage_change' in comparison:
                log_info(f"변화율: {comparison['percentage_change']:.1f}%")
        else:
            log_warn("기간 비교 데이터 부족", "시스템 실행 시간이 짧아 비교 데이터가 부족할 수 있습니다")

    except Exception as e:
        log_fail("기간 비교 실패", str(e))

async def test_as_3_1_export_functionality():
    """AS-3.1: 내보내기 기능 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AS-3.1: CSV/PDF 내보내기 기능 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    from app.services.export_service import ExportService

    service = ExportService()

    try:
        # Test CSV export
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)

        csv_result = await service.export_to_csv(
            metric_types=[MetricType.ACTIVE_USERS, MetricType.STORAGE_BYTES],
            granularity='hourly',
            start_time=start_time,
            end_time=end_time
        )

        if csv_result and 'file_path' in csv_result:
            log_pass("CSV 내보내기 성공", f"파일: {csv_result['file_path']}")
            log_info(f"파일 크기: {csv_result.get('file_size_bytes', 0) / 1024:.1f} KB")
        else:
            log_fail("CSV 내보내기 실패")

    except Exception as e:
        log_fail("내보내기 서비스 오류", str(e))

async def test_collection_status():
    """메트릭 수집 상태 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}메트릭 수집 상태 확인{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    service = MetricsService()

    try:
        status = await service.get_collection_status()

        if status:
            status_color = GREEN if status['status'] == 'healthy' else YELLOW
            log_pass(f"수집 상태: {status_color}{status['status']}{RESET}")

            if status.get('last_collection_at'):
                log_info(f"마지막 수집: {status['last_collection_at']}")

            if status.get('failure_count_24h', 0) > 0:
                log_warn(f"24시간 내 실패: {status['failure_count_24h']}건")
            else:
                log_pass("24시간 내 실패 없음")
        else:
            log_fail("수집 상태 조회 실패")

    except Exception as e:
        log_fail("수집 상태 서비스 오류", str(e))

async def test_data_retention():
    """데이터 보존 정책 확인"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}데이터 보존 정책 확인 (FR-003){RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    async for session in get_db_session():
        try:
            # Check hourly data retention
            hourly_cutoff = datetime.utcnow() - timedelta(days=30)
            result = await session.execute(
                select(func.count(MetricSnapshot.id))
                .where(
                    MetricSnapshot.granularity == 'hourly',
                    MetricSnapshot.collected_at < hourly_cutoff
                )
            )
            old_hourly_count = result.scalar()

            if old_hourly_count == 0:
                log_pass("30일 이상 된 시간별 데이터 없음", "정리 정책 작동 중")
            else:
                log_warn(f"30일 이상 된 시간별 데이터 {old_hourly_count}건 존재",
                        "정리 작업이 아직 실행되지 않았을 수 있습니다")

        except Exception as e:
            log_fail("데이터 보존 확인 실패", str(e))

async def main():
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Feature 002: 수동 인수 테스트 자동화{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    # Run all tests
    await test_as_1_1_metrics_data_exists()
    await test_as_1_2_current_values_display()
    await test_as_1_3_time_range_selection()
    await test_as_2_1_comparison_mode()
    await test_as_3_1_export_functionality()
    await test_collection_status()
    await test_data_retention()

    # Print summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}테스트 결과 요약{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    print(f"{GREEN}통과{RESET}: {test_results['passed']}")
    print(f"{RED}실패{RESET}: {test_results['failed']}")
    print(f"{YELLOW}경고{RESET}: {test_results['warnings']}")
    print(f"\n총 테스트: {test_results['passed'] + test_results['failed'] + test_results['warnings']}")

    success_rate = (test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100) if (test_results['passed'] + test_results['failed']) > 0 else 0
    print(f"성공률: {success_rate:.1f}%\n")

    if test_results['failed'] == 0:
        print(f"{GREEN}✅ 모든 자동화 테스트 통과!{RESET}\n")
        print(f"{YELLOW}참고: UI 인수 테스트는 브라우저에서 수동으로 수행해야 합니다.{RESET}")
        return 0
    else:
        print(f"{RED}❌ 일부 테스트 실패{RESET}\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
