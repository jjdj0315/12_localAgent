"""Scheduled tasks for metrics collection and cleanup

This module defines the background tasks that run on APScheduler
(Feature 002, FR-018, FR-019, FR-021).
"""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.metrics_collector import MetricsCollector
from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_collection_failures import MetricCollectionFailure

# Import Prometheus business metrics updater
from app.core.business_metrics import update_all_business_metrics

logger = logging.getLogger(__name__)


async def collect_hourly_metrics():
    """Collect hourly metrics snapshots (FR-018)

    Scheduled to run at the start of every hour (e.g., 00:00, 01:00, 02:00)
    """
    logger.info("시간별 메트릭 수집 작업 시작")

    async with AsyncSessionLocal() as db:
        try:
            collector = MetricsCollector(db)
            results = await collector.collect_all_metrics(granularity="hourly")

            success_count = sum(1 for v in results.values() if v is not None)
            failure_count = sum(1 for v in results.values() if v is None)

            logger.info(
                f"시간별 메트릭 수집 완료 - 성공: {success_count}, 실패: {failure_count}"
            )
        except Exception as e:
            logger.error(f"시간별 메트릭 수집 작업 오류: {str(e)}")


async def aggregate_daily_metrics():
    """Aggregate daily metrics from hourly snapshots (FR-018)

    Scheduled to run once per day at 00:05 (after hourly collection)
    Computes average values for each metric type from the previous day's hourly data.
    """
    logger.info("일별 메트릭 집계 작업 시작")

    async with AsyncSessionLocal() as db:
        try:
            # Get yesterday's date (00:00 - 23:00)
            now = datetime.now(timezone.utc)
            yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59)

            # Import here to avoid circular dependency
            from app.models.metric_type import MetricType

            for metric_type in MetricType:
                try:
                    # Query hourly snapshots for yesterday
                    stmt = select(MetricSnapshot).where(
                        MetricSnapshot.metric_type == metric_type.value,
                        MetricSnapshot.granularity == "hourly",
                        MetricSnapshot.collected_at >= yesterday_start,
                        MetricSnapshot.collected_at <= yesterday_end
                    )
                    result = await db.execute(stmt)
                    hourly_snapshots = result.scalars().all()

                    if not hourly_snapshots:
                        logger.warning(
                            f"일별 집계 건너뜀 (데이터 없음): {metric_type.value}"
                        )
                        continue

                    # Calculate average value
                    avg_value = int(sum(s.value for s in hourly_snapshots) / len(hourly_snapshots))

                    # Create daily snapshot (timestamp = yesterday 00:00)
                    daily_snapshot = MetricSnapshot(
                        metric_type=metric_type.value,
                        value=avg_value,
                        granularity="daily",
                        collected_at=yesterday_start,
                        retry_count=0
                    )

                    db.add(daily_snapshot)
                    await db.commit()

                    logger.info(
                        f"일별 메트릭 집계 완료: {metric_type.value} = {avg_value} "
                        f"(시간별 데이터 {len(hourly_snapshots)}개 평균)"
                    )

                except Exception as e:
                    logger.error(f"일별 집계 오류 ({metric_type.value}): {str(e)}")
                    await db.rollback()

            logger.info("일별 메트릭 집계 작업 완료")

        except Exception as e:
            logger.error(f"일별 메트릭 집계 작업 오류: {str(e)}")


async def cleanup_old_metrics():
    """Delete old metric snapshots and failures (FR-021)

    Scheduled to run once per day at 02:00
    Retention periods are configurable via environment variables:
    - METRICS_HOURLY_RETENTION_DAYS (default: 30)
    - METRICS_DAILY_RETENTION_DAYS (default: 90)
    - METRICS_FAILURES_RETENTION_DAYS (default: 30)
    """
    logger.info("오래된 메트릭 정리 작업 시작")

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            # Delete hourly snapshots older than retention period
            hourly_cutoff = now - timedelta(days=settings.METRICS_HOURLY_RETENTION_DAYS)
            hourly_stmt = delete(MetricSnapshot).where(
                MetricSnapshot.granularity == "hourly",
                MetricSnapshot.collected_at < hourly_cutoff
            )
            hourly_result = await db.execute(hourly_stmt)
            hourly_deleted = hourly_result.rowcount

            # Delete daily snapshots older than retention period
            daily_cutoff = now - timedelta(days=settings.METRICS_DAILY_RETENTION_DAYS)
            daily_stmt = delete(MetricSnapshot).where(
                MetricSnapshot.granularity == "daily",
                MetricSnapshot.collected_at < daily_cutoff
            )
            daily_result = await db.execute(daily_stmt)
            daily_deleted = daily_result.rowcount

            # Delete old collection failures
            failures_cutoff = now - timedelta(days=settings.METRICS_FAILURES_RETENTION_DAYS)
            failures_stmt = delete(MetricCollectionFailure).where(
                MetricCollectionFailure.created_at < failures_cutoff
            )
            failures_result = await db.execute(failures_stmt)
            failures_deleted = failures_result.rowcount

            await db.commit()

            logger.info(
                f"메트릭 정리 완료 - 시간별: {hourly_deleted}개, "
                f"일별: {daily_deleted}개, 실패 기록: {failures_deleted}개 삭제"
            )

        except Exception as e:
            logger.error(f"메트릭 정리 작업 오류: {str(e)}")
            await db.rollback()


async def cleanup_expired_exports():
    """Delete expired export files (FR-024, FR-025)

    Scheduled to run every hour at :30
    Retention period is configurable via METRICS_EXPORT_RETENTION_HOURS (default: 1)
    """
    logger.info("만료된 내보내기 파일 정리 작업 시작")

    try:
        export_dir = Path("backend/exports")

        # Create export directory if it doesn't exist
        if not export_dir.exists():
            export_dir.mkdir(parents=True, exist_ok=True)
            logger.info("내보내기 디렉토리 생성됨")
            return

        now = datetime.now(timezone.utc)
        cutoff_timestamp = (now - timedelta(hours=settings.METRICS_EXPORT_RETENTION_HOURS)).timestamp()
        deleted_count = 0
        freed_bytes = 0

        # Iterate through all files in export directory
        for file_path in export_dir.glob("*"):
            if not file_path.is_file():
                continue

            try:
                file_mtime = file_path.stat().st_mtime

                # Delete if older than 1 hour
                if file_mtime < cutoff_timestamp:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    freed_bytes += file_size
                    logger.debug(f"만료된 파일 삭제: {file_path.name}")

            except Exception as e:
                logger.warning(f"파일 삭제 실패 ({file_path.name}): {str(e)}")

        if deleted_count > 0:
            freed_mb = freed_bytes / (1024 * 1024)
            logger.info(
                f"만료된 내보내기 파일 정리 완료 - "
                f"{deleted_count}개 파일 삭제, {freed_mb:.2f}MB 확보"
            )
        else:
            logger.info("정리할 만료된 내보내기 파일 없음")

    except Exception as e:
        logger.error(f"내보내기 파일 정리 작업 오류: {str(e)}")


def register_scheduled_tasks(scheduler):
    """Register all scheduled tasks with APScheduler

    Args:
        scheduler: AsyncIOScheduler instance
    """
    # Hourly metrics collection (every hour at :00)
    scheduler.add_job(
        collect_hourly_metrics,
        'cron',
        hour='*',
        minute=0,
        id='collect_hourly_metrics',
        replace_existing=True
    )
    logger.info("등록됨: 시간별 메트릭 수집 (매시 정각)")

    # Daily aggregation (every day at 00:05)
    scheduler.add_job(
        aggregate_daily_metrics,
        'cron',
        hour=0,
        minute=5,
        id='aggregate_daily_metrics',
        replace_existing=True
    )
    logger.info("등록됨: 일별 메트릭 집계 (매일 00:05)")

    # Cleanup old metrics (every day at 02:00)
    scheduler.add_job(
        cleanup_old_metrics,
        'cron',
        hour=2,
        minute=0,
        id='cleanup_old_metrics',
        replace_existing=True
    )
    logger.info("등록됨: 메트릭 정리 (매일 02:00)")

    # Cleanup expired export files (every hour at :30)
    scheduler.add_job(
        cleanup_expired_exports,
        'cron',
        hour='*',
        minute=30,
        id='cleanup_expired_exports',
        replace_existing=True
    )
    logger.info("등록됨: 만료된 내보내기 파일 정리 (매시 30분)")

    # Update Prometheus business metrics (every 5 minutes)
    scheduler.add_job(
        update_all_business_metrics,
        'interval',
        minutes=5,
        id='update_business_metrics',
        replace_existing=True
    )
    logger.info("등록됨: Prometheus 비즈니스 메트릭 업데이트 (5분마다)")
