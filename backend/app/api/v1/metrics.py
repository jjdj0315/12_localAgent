"""API endpoints for metrics feature

This module provides REST endpoints for querying and exporting metrics data
(Feature 002, User Stories 1-3).
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_admin
from app.services.metrics_service import MetricsService
from app.services.export_service import ExportService
from app.models.metric_type import MetricType
from app.schemas.metrics import (
    MetricsTimeSeriesResponse,
    MetricDataPoint,
    CurrentMetricsResponse,
    CurrentMetricValue,
    MetricsCollectionStatusResponse,
    MetricsComparisonResponse,
    ExportRequest,
    ExportResponse,
)
from app.core.errors import (
    METRICS_INVALID_GRANULARITY,
    METRICS_INVALID_TIME_RANGE,
    METRICS_NO_DATA_FOUND,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/timeseries",
    response_model=MetricsTimeSeriesResponse,
    summary="Get time series data for a metric",
    description="Retrieve historical metric snapshots within a time range (FR-017)"
)
async def get_metrics_timeseries(
    metric_type: str = Query(..., description="Metric type (active_users, storage_bytes, etc.)"),
    granularity: str = Query(..., description="Granularity: 'hourly' or 'daily'"),
    start_time: datetime = Query(..., description="Start time (ISO 8601)"),
    end_time: datetime = Query(..., description="End time (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Get time series data for a specific metric (FR-017)

    **Admin only** - Requires admin authentication

    **Time Range Limits:**
    - Hourly data: Retained for 30 days
    - Daily data: Retained for 90 days
    """
    try:
        service = MetricsService(db)
        snapshots = await service.get_time_series(
            metric_type=metric_type,
            granularity=granularity,
            start_time=start_time,
            end_time=end_time
        )

        # Convert to response format
        data_points = [
            MetricDataPoint(
                metric_type=s.metric_type,
                value=s.value,
                granularity=s.granularity,
                timestamp=s.collected_at
            )
            for s in snapshots
        ]

        return MetricsTimeSeriesResponse(
            metric_type=metric_type,
            granularity=granularity,
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            total=len(data_points)
        )

    except ValueError as e:
        logger.warning(f"잘못된 메트릭 조회 요청: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"메트릭 시계열 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="메트릭 데이터 조회에 실패했습니다")


@router.get(
    "/current",
    response_model=CurrentMetricsResponse,
    summary="Get current values for all metrics",
    description="Retrieve latest snapshot values for all 6 metric types (FR-007)"
)
async def get_current_metrics(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Get current (latest) values for all metrics (FR-007)

    **Admin only** - Requires admin authentication

    Returns the most recent collected value for each of the 6 metric types:
    - active_users: Number of users with active sessions
    - storage_bytes: Total document storage size
    - active_sessions: Number of active sessions
    - conversation_count: Total conversations
    - document_count: Total documents
    - tag_count: Total tags
    """
    try:
        service = MetricsService(db)
        current_values = await service.get_current_metrics()

        # Build response with Korean display names and units
        metrics = []
        latest_timestamp = None

        for metric_type_enum in MetricType:
            metric_type = metric_type_enum.value
            value = current_values.get(metric_type)

            metrics.append(
                CurrentMetricValue(
                    metric_type=metric_type,
                    value=value,
                    display_name=metric_type_enum.display_name_ko,
                    unit=metric_type_enum.unit
                )
            )

        return CurrentMetricsResponse(
            metrics=metrics,
            collected_at=latest_timestamp
        )

    except Exception as e:
        logger.error(f"현재 메트릭 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="현재 메트릭 조회에 실패했습니다")


@router.get(
    "/status",
    response_model=MetricsCollectionStatusResponse,
    summary="Get metrics collection system status",
    description="Retrieve collection status, last/next collection times, and recent failures (FR-019)"
)
async def get_collection_status(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Get metrics collection system status (FR-019)

    **Admin only** - Requires admin authentication

    Returns:
    - Last collection timestamp
    - Next scheduled collection timestamp
    - Recent failures (last 24 hours)
    - Overall system health status
    """
    try:
        service = MetricsService(db)
        status = await service.get_collection_status()

        return MetricsCollectionStatusResponse(**status)

    except Exception as e:
        logger.error(f"수집 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="수집 상태 조회에 실패했습니다")


@router.get(
    "/summary",
    summary="Get statistical summary for a metric",
    description="Retrieve min/max/avg statistics for a metric over a time range"
)
async def get_metric_summary(
    metric_type: str = Query(..., description="Metric type"),
    granularity: str = Query(..., description="Granularity: 'hourly' or 'daily'"),
    start_time: datetime = Query(..., description="Start time (ISO 8601)"),
    end_time: datetime = Query(..., description="End time (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Get statistical summary for a metric

    **Admin only** - Requires admin authentication

    Returns min, max, average, and latest values for the specified metric
    within the given time range.
    """
    try:
        service = MetricsService(db)
        summary = await service.get_metric_summary(
            metric_type=metric_type,
            granularity=granularity,
            start_time=start_time,
            end_time=end_time
        )

        return summary

    except ValueError as e:
        logger.warning(f"잘못된 요약 조회 요청: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"메트릭 요약 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="메트릭 요약 조회에 실패했습니다")


@router.get(
    "/comparison",
    response_model=MetricsComparisonResponse,
    summary="Compare two time periods for a metric",
    description="Retrieve and compare metrics between two time periods with percentage change (FR-022)"
)
async def compare_metric_periods(
    metric_type: str = Query(..., description="Metric type"),
    granularity: str = Query(..., description="Granularity: 'hourly' or 'daily'"),
    period1_start: datetime = Query(..., description="Period 1 start time (ISO 8601)"),
    period1_end: datetime = Query(..., description="Period 1 end time (ISO 8601)"),
    period2_start: datetime = Query(..., description="Period 2 start time (ISO 8601)"),
    period2_end: datetime = Query(..., description="Period 2 end time (ISO 8601)"),
    period1_label: str = Query("이번 주", description="Korean label for period 1"),
    period2_label: str = Query("지난 주", description="Korean label for period 2"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Compare two time periods for a metric (FR-022)

    **Admin only** - Requires admin authentication

    Compares metric values between two time periods and calculates:
    - Average values for each period
    - Percentage change from period 2 to period 1
    - Change direction (up/down/unchanged)

    Common use cases:
    - This week vs last week
    - This month vs last month
    - Custom date range comparisons
    """
    try:
        service = MetricsService(db)
        comparison = await service.compare_periods(
            metric_type=metric_type,
            granularity=granularity,
            period1_start=period1_start,
            period1_end=period1_end,
            period2_start=period2_start,
            period2_end=period2_end,
            period1_label=period1_label,
            period2_label=period2_label
        )

        return MetricsComparisonResponse(**comparison)

    except ValueError as e:
        logger.warning(f"잘못된 비교 요청: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"기간 비교 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="기간 비교에 실패했습니다")


# Export directory setup
EXPORT_DIR = Path("./exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/export",
    response_model=ExportResponse,
    summary="Export metrics data to CSV or PDF",
    description="Export metric snapshots to downloadable file with automatic downsampling (FR-024, FR-025)"
)
async def export_metrics(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Export metrics data to CSV or PDF (FR-024, FR-025)

    **Admin only** - Requires admin authentication

    Exports metric data for specified time range and metric types.
    Automatically downsamples data if file size exceeds 10MB limit.

    Supported formats:
    - CSV: UTF-8 encoded with BOM, includes metadata header
    - PDF: Tabular format with optional chart (chart not implemented in MVP)

    Files expire after 1 hour and are automatically cleaned up.
    """
    try:
        # Validate metric types count (FR-024)
        if len(request.metric_types) > 6:
            raise HTTPException(
                status_code=400,
                detail="한 번에 최대 6개의 메트릭만 내보낼 수 있습니다"
            )

        metrics_service = MetricsService(db)
        export_service = ExportService(EXPORT_DIR)

        # Fetch data for all requested metrics
        all_snapshots = []
        for metric_type in request.metric_types:
            snapshots = await metrics_service.get_time_series(
                metric_type=metric_type,
                granularity=request.granularity,
                start_time=request.start_time,
                end_time=request.end_time
            )
            all_snapshots.extend(snapshots)

        if not all_snapshots:
            raise HTTPException(
                status_code=404,
                detail="선택한 기간 동안 메트릭 데이터가 없습니다"
            )

        # Generate export file
        export_id = str(uuid.uuid4())
        downsampled = False

        if request.format == 'csv':
            # Combine metric type names for filename
            metric_names = '_'.join(request.metric_types[:3])  # Limit filename length
            filename = f"metrics_{metric_names}_{request.granularity}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

            file_data, downsampled = export_service.export_to_csv(
                snapshots=all_snapshots,
                metric_type=request.metric_types[0],  # Primary metric for metadata
                granularity=request.granularity,
                include_metadata=True
            )

        elif request.format == 'pdf':
            metric_names = '_'.join(request.metric_types[:3])
            filename = f"metrics_{metric_names}_{request.granularity}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"

            file_data, downsampled = export_service.export_to_pdf(
                snapshots=all_snapshots,
                metric_type=request.metric_types[0],
                granularity=request.granularity,
                include_chart=request.include_chart
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="잘못된 내보내기 형식입니다. 'csv' 또는 'pdf'만 허용됩니다"
            )

        # Save file
        file_path = export_service.save_export_file(file_data, filename, export_id)

        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Generate download URL
        download_url = f"/api/v1/metrics/exports/{export_id}_{filename}"

        logger.info(f"내보내기 생성 완료: {filename} ({len(file_data)} bytes)")

        return ExportResponse(
            export_id=export_id,
            filename=filename,
            download_url=download_url,
            file_size_bytes=len(file_data),
            expires_at=expires_at,
            downsampled=downsampled
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"잘못된 내보내기 요청: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"내보내기 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="데이터 내보내기에 실패했습니다")


@router.get(
    "/exports/{filename}",
    summary="Download exported file",
    description="Download previously generated export file (FR-024)"
)
async def download_export(
    filename: str,
    _: dict = Depends(get_current_admin)
):
    """Download export file (FR-024)

    **Admin only** - Requires admin authentication

    Downloads a previously generated export file.
    Files are automatically deleted after 1 hour.
    """
    try:
        file_path = EXPORT_DIR / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="파일을 찾을 수 없습니다. 파일이 만료되었거나 삭제되었을 수 있습니다"
            )

        # Determine media type
        if filename.endswith('.csv'):
            media_type = 'text/csv'
        elif filename.endswith('.pdf'):
            media_type = 'application/pdf'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename.split('_', 1)[1] if '_' in filename else filename  # Remove export_id prefix
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 다운로드에 실패했습니다")
