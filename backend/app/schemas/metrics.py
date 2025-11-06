"""Pydantic schemas for metrics API endpoints

This module defines request/response models for the metrics feature
(Feature 002).
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Time Series Query Schemas (FR-017)
# ============================================================================

class MetricsQueryParams(BaseModel):
    """Query parameters for time series endpoint"""
    metric_type: str = Field(..., description="Metric type to query")
    granularity: Literal['hourly', 'daily'] = Field(..., description="Data granularity")
    start_time: datetime = Field(..., description="Start of time range (inclusive)")
    end_time: datetime = Field(..., description="End of time range (inclusive)")

    @field_validator('start_time', 'end_time')
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware"""
        if v.tzinfo is None:
            raise ValueError("시간대 정보가 필요합니다 (ISO 8601 형식)")
        return v


class MetricDataPoint(BaseModel):
    """Single metric data point"""
    metric_type: str
    value: int
    granularity: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricsTimeSeriesResponse(BaseModel):
    """Response for time series query"""
    metric_type: str
    granularity: str
    start_time: datetime
    end_time: datetime
    data_points: list[MetricDataPoint]
    total: int = Field(..., description="Total number of data points")


# ============================================================================
# Current Metrics Schemas (FR-007)
# ============================================================================

class CurrentMetricValue(BaseModel):
    """Current value for a single metric"""
    metric_type: str
    value: int | None = Field(..., description="Latest value, null if no data collected yet")
    display_name: str = Field(..., description="Korean display name")
    unit: str = Field(..., description="Unit of measurement")


class CurrentMetricsResponse(BaseModel):
    """Response for current metrics endpoint"""
    metrics: list[CurrentMetricValue]
    collected_at: datetime | None = Field(..., description="Timestamp of latest collection")


# ============================================================================
# Collection Status Schemas (FR-019)
# ============================================================================

class MetricFailureInfo(BaseModel):
    """Information about a failed collection"""
    metric_type: str
    attempted_at: datetime
    error_message: str


class MetricsCollectionStatusResponse(BaseModel):
    """Response for collection status endpoint"""
    last_collection_at: datetime | None
    next_collection_at: datetime
    recent_failures: list[MetricFailureInfo]
    failure_count_24h: int
    status: Literal['healthy', 'degraded']


# ============================================================================
# Summary Statistics Schemas
# ============================================================================

class MetricSummary(BaseModel):
    """Statistical summary for a metric over a time range"""
    metric_type: str
    granularity: str
    min: int | None
    max: int | None
    avg: int | None
    latest: int | None
    data_points: int


# ============================================================================
# Period Comparison Schemas (FR-022) - User Story 2
# ============================================================================

class PeriodInfo(BaseModel):
    """Information about a comparison period"""
    start_time: datetime
    end_time: datetime
    label: str = Field(..., description="Korean label (e.g., '이번 주', '지난 주')")
    data_points: list[MetricDataPoint]
    average: int | None


class MetricsComparisonResponse(BaseModel):
    """Response for period comparison endpoint"""
    metric_type: str
    granularity: str
    period1: PeriodInfo
    period2: PeriodInfo
    change_percentage: float | None = Field(
        ...,
        description="Percentage change from period2 to period1 ((p1-p2)/p2*100)"
    )
    change_direction: Literal['up', 'down', 'unchanged'] | None


# ============================================================================
# Export Schemas (FR-024, FR-025) - User Story 3
# ============================================================================

class ExportRequest(BaseModel):
    """Request for exporting metrics data"""
    metric_types: list[str] = Field(..., min_length=1, max_length=6)
    granularity: Literal['hourly', 'daily']
    start_time: datetime
    end_time: datetime
    format: Literal['csv', 'pdf']
    include_chart: bool = Field(
        default=False,
        description="Include chart in PDF export (ignored for CSV)"
    )

    @field_validator('start_time', 'end_time')
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware"""
        if v.tzinfo is None:
            raise ValueError("시간대 정보가 필요합니다 (ISO 8601 형식)")
        return v


class ExportResponse(BaseModel):
    """Response for export request"""
    export_id: str = Field(..., description="Unique export identifier")
    filename: str = Field(..., description="Generated filename")
    download_url: str = Field(..., description="URL to download the file")
    file_size_bytes: int
    expires_at: datetime = Field(..., description="Expiration time (1 hour from creation)")
    downsampled: bool = Field(
        default=False,
        description="Whether data was downsampled due to size limit"
    )
