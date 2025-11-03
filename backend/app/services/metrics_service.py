"""MetricsService for querying historical metrics data

This service provides time series queries and current metric values for the
admin dashboard (Feature 002, FR-017).
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_collection_failures import MetricCollectionFailure
from app.models.metric_type import MetricType
from app.core.errors import (
    METRICS_INVALID_GRANULARITY,
    METRICS_INVALID_TIME_RANGE,
    METRICS_NO_DATA_FOUND,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for querying and retrieving metrics data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_time_series(
        self,
        metric_type: str,
        granularity: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[MetricSnapshot]:
        """Get time series data for a specific metric (FR-017)

        Args:
            metric_type: Type of metric to query
            granularity: 'hourly' or 'daily'
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            list[MetricSnapshot]: Ordered list of metric snapshots

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate granularity
        if granularity not in ('hourly', 'daily'):
            raise ValueError(METRICS_INVALID_GRANULARITY)

        # Validate time range
        if start_time >= end_time:
            raise ValueError(METRICS_INVALID_TIME_RANGE)

        # Validate metric type
        try:
            MetricType(metric_type)
        except ValueError:
            raise ValueError(METRICS_UNKNOWN_TYPE.format(metric_type=metric_type))

        # Query snapshots
        stmt = select(MetricSnapshot).where(
            and_(
                MetricSnapshot.metric_type == metric_type,
                MetricSnapshot.granularity == granularity,
                MetricSnapshot.collected_at >= start_time,
                MetricSnapshot.collected_at <= end_time
            )
        ).order_by(MetricSnapshot.collected_at.asc())

        result = await self.db.execute(stmt)
        snapshots = result.scalars().all()

        logger.info(
            f"시계열 조회 완료: {metric_type} ({granularity}) - {len(snapshots)}개 데이터 포인트"
        )

        return list(snapshots)

    async def get_current_metrics(self) -> dict[str, int | None]:
        """Get current (latest) values for all 6 metrics (FR-007)

        Returns:
            dict: Mapping of metric_type to latest value (None if no data)
        """
        results = {}

        for metric_type in MetricType:
            # Query most recent snapshot (prefer hourly, fallback to daily)
            stmt = select(MetricSnapshot).where(
                MetricSnapshot.metric_type == metric_type.value
            ).order_by(MetricSnapshot.collected_at.desc()).limit(1)

            result = await self.db.execute(stmt)
            snapshot = result.scalar_one_or_none()

            results[metric_type.value] = snapshot.value if snapshot else None

        logger.info(f"현재 메트릭 조회 완료: {len(results)}개 메트릭")
        return results

    async def get_collection_status(self) -> dict:
        """Get metrics collection system status (FR-019)

        Returns:
            dict: Status information including last/next collection times and recent failures
        """
        # Get last successful collection time
        last_collection_stmt = select(
            func.max(MetricSnapshot.collected_at)
        )
        result = await self.db.execute(last_collection_stmt)
        last_collection = result.scalar()

        # Get recent failures (last 24 hours)
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        failures_stmt = select(MetricCollectionFailure).where(
            MetricCollectionFailure.created_at >= cutoff_time
        ).order_by(MetricCollectionFailure.created_at.desc()).limit(10)

        result = await self.db.execute(failures_stmt)
        recent_failures = result.scalars().all()

        # Calculate next scheduled collection (next hour boundary)
        now = datetime.now(timezone.utc)
        next_collection = now.replace(minute=0, second=0, microsecond=0)
        if next_collection <= now:
            next_collection = next_collection.replace(hour=next_collection.hour + 1)

        status = {
            "last_collection_at": last_collection.isoformat() if last_collection else None,
            "next_collection_at": next_collection.isoformat(),
            "recent_failures": [f.to_dict() for f in recent_failures],
            "failure_count_24h": len(recent_failures),
            "status": "healthy" if len(recent_failures) == 0 else "degraded"
        }

        logger.info(f"수집 상태 조회 완료: {status['status']}")
        return status

    async def get_metric_summary(
        self,
        metric_type: str,
        granularity: str,
        start_time: datetime,
        end_time: datetime
    ) -> dict:
        """Get statistical summary for a metric over a time range

        Args:
            metric_type: Type of metric to query
            granularity: 'hourly' or 'daily'
            start_time: Start of time range
            end_time: End of time range

        Returns:
            dict: Statistical summary (min, max, avg, latest)
        """
        snapshots = await self.get_time_series(
            metric_type, granularity, start_time, end_time
        )

        if not snapshots:
            return {
                "metric_type": metric_type,
                "granularity": granularity,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None,
                "data_points": 0
            }

        values = [s.value for s in snapshots]

        return {
            "metric_type": metric_type,
            "granularity": granularity,
            "min": min(values),
            "max": max(values),
            "avg": int(sum(values) / len(values)),
            "latest": values[-1],
            "data_points": len(values)
        }

    async def compare_periods(
        self,
        metric_type: str,
        granularity: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
        period1_label: str = "이번 주",
        period2_label: str = "지난 주"
    ) -> dict:
        """Compare two time periods for a metric (FR-022)

        Args:
            metric_type: Type of metric to compare
            granularity: 'hourly' or 'daily'
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period
            period1_label: Korean label for period 1 (default: "이번 주")
            period2_label: Korean label for period 2 (default: "지난 주")

        Returns:
            dict: Comparison data with snapshots and percentage change
        """
        # Fetch data for both periods
        period1_snapshots = await self.get_time_series(
            metric_type, granularity, period1_start, period1_end
        )
        period2_snapshots = await self.get_time_series(
            metric_type, granularity, period2_start, period2_end
        )

        # Calculate averages
        period1_avg = None
        period2_avg = None

        if period1_snapshots:
            period1_values = [s.value for s in period1_snapshots]
            period1_avg = int(sum(period1_values) / len(period1_values))

        if period2_snapshots:
            period2_values = [s.value for s in period2_snapshots]
            period2_avg = int(sum(period2_values) / len(period2_values))

        # Calculate percentage change ((p1-p2)/p2*100)
        change_percentage = None
        change_direction = None

        if period1_avg is not None and period2_avg is not None and period2_avg != 0:
            change_percentage = ((period1_avg - period2_avg) / period2_avg) * 100

            if abs(change_percentage) < 0.01:
                change_direction = "unchanged"
            elif change_percentage > 0:
                change_direction = "up"
            else:
                change_direction = "down"

        logger.info(
            f"기간 비교 완료: {metric_type} - {period1_label} vs {period2_label} "
            f"({change_percentage:.1f}% {change_direction})" if change_percentage else ""
        )

        return {
            "metric_type": metric_type,
            "granularity": granularity,
            "period1": {
                "start_time": period1_start,
                "end_time": period1_end,
                "label": period1_label,
                "data_points": [s.to_dict() for s in period1_snapshots],
                "average": period1_avg
            },
            "period2": {
                "start_time": period2_start,
                "end_time": period2_end,
                "label": period2_label,
                "data_points": [s.to_dict() for s in period2_snapshots],
                "average": period2_avg
            },
            "change_percentage": change_percentage,
            "change_direction": change_direction
        }
