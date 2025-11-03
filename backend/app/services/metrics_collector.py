"""MetricsCollector service for collecting system metrics

This service collects current metric values and stores them in the database
with retry logic (Feature 002, FR-020).
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_collection_failures import MetricCollectionFailure
from app.models.metric_type import MetricType

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores system metrics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_all_metrics(self, granularity: str = "hourly") -> dict:
        """Collect all metrics and store snapshots

        Args:
            granularity: 'hourly' or 'daily'

        Returns:
            dict: Mapping of metric_type to value (None if failed)
        """
        collected_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        results = {}

        for metric_type in MetricType:
            value = await self._collect_metric_with_retry(metric_type, collected_at, granularity)
            results[metric_type.value] = value

        return results

    async def _collect_metric_with_retry(
        self,
        metric_type: MetricType,
        collected_at: datetime,
        granularity: str,
        max_retries: int = 3
    ) -> int | None:
        """Collect a single metric with retry logic (FR-020)

        Args:
            metric_type: Type of metric to collect
            collected_at: Timestamp for collection
            granularity: 'hourly' or 'daily'
            max_retries: Maximum retry attempts (default 3)

        Returns:
            int: Metric value, or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                value = await self._collect_metric(metric_type)

                # Store successful collection
                snapshot = MetricSnapshot(
                    metric_type=metric_type.value,
                    value=value,
                    granularity=granularity,
                    collected_at=collected_at,
                    retry_count=attempt
                )
                self.db.add(snapshot)
                await self.db.commit()

                logger.info(f"메트릭 수집 성공: {metric_type.value}={value} (시도 {attempt+1}/{max_retries})")
                return value

            except Exception as e:
                wait_seconds = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"메트릭 수집 실패 (시도 {attempt+1}/{max_retries}): {metric_type.value} - {str(e)}"
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_seconds)
                else:
                    # All retries exhausted - record failure
                    logger.error(f"최대 재시도 횟수 초과: {metric_type.value}")
                    await self._record_collection_failure(metric_type, collected_at, granularity, str(e))
                    return None

    async def _collect_metric(self, metric_type: MetricType) -> int:
        """Calculate current value for a metric type

        Args:
            metric_type: Type of metric to collect

        Returns:
            int: Current metric value

        Raises:
            Exception: If metric collection fails
        """
        try:
            if metric_type == MetricType.ACTIVE_USERS:
                # Count distinct users with active sessions (not expired)
                # Import here to avoid circular imports
                from app.models.session import Session as UserSession
                now = datetime.now(timezone.utc)
                stmt = select(func.count(func.distinct(UserSession.user_id))).where(
                    UserSession.expires_at > now
                )
                result = await self.db.execute(stmt)
                return result.scalar() or 0

            elif metric_type == MetricType.STORAGE_BYTES:
                # Sum of all document file sizes
                from app.models.document import Document
                stmt = select(func.sum(Document.file_size))
                result = await self.db.execute(stmt)
                return result.scalar() or 0

            elif metric_type == MetricType.ACTIVE_SESSIONS:
                # Count active sessions (not expired)
                from app.models.session import Session as UserSession
                now = datetime.now(timezone.utc)
                stmt = select(func.count(UserSession.id)).where(
                    UserSession.expires_at > now
                )
                result = await self.db.execute(stmt)
                return result.scalar() or 0

            elif metric_type == MetricType.CONVERSATION_COUNT:
                # Total conversations
                from app.models.conversation import Conversation
                stmt = select(func.count(Conversation.id))
                result = await self.db.execute(stmt)
                return result.scalar() or 0

            elif metric_type == MetricType.DOCUMENT_COUNT:
                # Total documents
                from app.models.document import Document
                stmt = select(func.count(Document.id))
                result = await self.db.execute(stmt)
                return result.scalar() or 0

            elif metric_type == MetricType.TAG_COUNT:
                # Total unique tags
                # Note: Tag model not yet implemented, return 0 for now
                # TODO: Implement when Tag feature is added
                return 0

            else:
                raise ValueError(f"알 수 없는 메트릭 타입: {metric_type}")

        except SQLAlchemyError as e:
            logger.error(f"데이터베이스 쿼리 오류: {metric_type.value} - {str(e)}")
            raise

    async def _record_collection_failure(
        self,
        metric_type: MetricType,
        attempted_at: datetime,
        granularity: str,
        error_message: str
    ):
        """Record a failed collection attempt

        Args:
            metric_type: Type of metric that failed
            attempted_at: When the final attempt occurred
            granularity: 'hourly' or 'daily'
            error_message: Error description
        """
        try:
            failure = MetricCollectionFailure(
                metric_type=metric_type.value,
                granularity=granularity,
                attempted_at=attempted_at,
                error_message=error_message,
                retry_count=3
            )
            self.db.add(failure)
            await self.db.commit()
        except Exception as e:
            logger.error(f"실패 기록 저장 오류: {str(e)}")
