"""APScheduler configuration and lifecycle management

This module initializes the background task scheduler for metrics collection
and cleanup (Feature 002).
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance

    Returns:
        AsyncIOScheduler: The scheduler instance

    Raises:
        RuntimeError: If scheduler not initialized
    """
    if _scheduler is None:
        raise RuntimeError("스케줄러가 초기화되지 않았습니다. start_scheduler()를 먼저 호출하세요.")
    return _scheduler


def start_scheduler() -> AsyncIOScheduler:
    """Initialize and start the APScheduler

    Returns:
        AsyncIOScheduler: Started scheduler instance
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("스케줄러가 이미 실행 중입니다.")
        return _scheduler

    # Configure job stores and executors
    jobstores = {
        'default': MemoryJobStore()
    }

    executors = {
        'default': AsyncIOExecutor()
    }

    job_defaults = {
        'coalesce': True,  # Combine missed runs into one
        'max_instances': 1,  # Only one instance per job
        'misfire_grace_time': 300  # 5 minutes grace period
    }

    _scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='Asia/Seoul'
    )

    _scheduler.start()
    logger.info("APScheduler 시작됨 (시간대: Asia/Seoul)")

    # Register scheduled tasks
    from app.tasks.scheduled_tasks import register_scheduled_tasks
    register_scheduled_tasks(_scheduler)

    return _scheduler


def stop_scheduler():
    """Stop the APScheduler gracefully"""
    global _scheduler

    if _scheduler is None:
        logger.warning("스케줄러가 실행 중이 아닙니다.")
        return

    _scheduler.shutdown(wait=True)
    logger.info("APScheduler 정지됨")
    _scheduler = None
