# Data Model: Admin Dashboard Metrics History

**Feature**: 002-admin-metrics-history
**Date**: 2025-11-02
**Phase**: 1 (Design & Contracts)

## Overview

This document defines the data structures for storing, querying, and exporting historical metrics. The model uses a single denormalized table with granularity discriminator for simplicity and efficient querying.

## Database Schema

### 1. metric_snapshots Table

**Purpose**: Stores point-in-time metric values at hourly and daily granularity

```sql
CREATE TABLE metric_snapshots (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    value BIGINT NOT NULL,
    granularity VARCHAR(10) NOT NULL CHECK (granularity IN ('hourly', 'daily')),
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    retry_count SMALLINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_metric_snapshot UNIQUE (metric_type, granularity, collected_at)
);

-- Performance indexes
CREATE INDEX idx_metric_type_time ON metric_snapshots (metric_type, granularity, collected_at DESC);
CREATE INDEX idx_cleanup_hourly ON metric_snapshots (collected_at) WHERE granularity = 'hourly';
CREATE INDEX idx_cleanup_daily ON metric_snapshots (collected_at) WHERE granularity = 'daily';
```

**Columns**:
- `id`: Auto-incrementing primary key
- `metric_type`: Enum-like string identifier (see MetricType enum below)
- `value`: Numeric value (BIGINT to support large storage byte counts)
- `granularity`: Discriminator for hourly vs daily aggregates
- `collected_at`: Timestamp when metric was captured (UTC)
- `retry_count`: Number of retry attempts before successful collection (for observability)
- `created_at`: Database insertion timestamp

**Constraints**:
- `UNIQUE (metric_type, granularity, collected_at)`: Prevents duplicate snapshots for same metric/time
- `CHECK (granularity IN ('hourly', 'daily'))`: Enforces valid granularity values

**Retention Policy** (enforced by scheduled cleanup task):
- Hourly: Delete rows where `granularity='hourly' AND collected_at < NOW() - INTERVAL '30 days'`
- Daily: Delete rows where `granularity='daily' AND collected_at < NOW() - INTERVAL '90 days'`

### 2. metric_collection_failures Table

**Purpose**: Tracks failed metric collections for status indicator (FR-019)

```sql
CREATE TABLE metric_collection_failures (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    granularity VARCHAR(10) NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    error_message TEXT,
    retry_count SMALLINT DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_failures_recent ON metric_collection_failures (created_at DESC) LIMIT 1000;
```

**Columns**:
- `metric_type`: Which metric failed
- `granularity`: Which collection cycle failed (hourly or daily)
- `attempted_at`: When the final retry attempt occurred
- `error_message`: Korean error message for debugging
- `retry_count`: Always 3 (max retries exhausted)

**Retention**: Keep last 1000 failures only (for dashboard status widget)

## Application Models

### MetricType Enum (Python)

```python
from enum import Enum

class MetricType(str, Enum):
    """Metric types tracked by the system (from FR-002)"""
    ACTIVE_USERS = "active_users"
    STORAGE_BYTES = "storage_bytes"
    ACTIVE_SESSIONS = "active_sessions"
    CONVERSATION_COUNT = "conversation_count"
    DOCUMENT_COUNT = "document_count"
    TAG_COUNT = "tag_count"

    @property
    def display_name_ko(self) -> str:
        """Korean display name for UI"""
        return {
            "active_users": "활성 사용자",
            "storage_bytes": "저장 공간",
            "active_sessions": "활성 세션",
            "conversation_count": "대화 수",
            "document_count": "문서 수",
            "tag_count": "태그 수",
        }[self.value]

    @property
    def unit(self) -> str:
        """Unit of measurement"""
        return {
            "active_users": "명",
            "storage_bytes": "bytes",
            "active_sessions": "개",
            "conversation_count": "개",
            "document_count": "개",
            "tag_count": "개",
        }[self.value]
```

### MetricSnapshot SQLAlchemy Model (Python)

```python
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, SmallInteger, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(BigInteger, nullable=False)
    granularity = Column(String(10), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    retry_count = Column(SmallInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('metric_type', 'granularity', 'collected_at', name='unique_metric_snapshot'),
        CheckConstraint("granularity IN ('hourly', 'daily')", name='check_granularity'),
    )

    def to_dict(self):
        """Convert to API response format"""
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "granularity": self.granularity,
            "timestamp": self.collected_at.isoformat(),
        }
```

### TypeScript Interfaces (Frontend)

```typescript
// frontend/src/types/metrics.ts

export enum MetricType {
  ACTIVE_USERS = 'active_users',
  STORAGE_BYTES = 'storage_bytes',
  ACTIVE_SESSIONS = 'active_sessions',
  CONVERSATION_COUNT = 'conversation_count',
  DOCUMENT_COUNT = 'document_count',
  TAG_COUNT = 'tag_count',
}

export interface MetricDataPoint {
  timestamp: string; // ISO 8601 format
  value: number;
}

export interface MetricSnapshot {
  metric_type: MetricType;
  value: number;
  granularity: 'hourly' | 'daily';
  timestamp: string;
}

export interface MetricsTimeSeriesResponse {
  metric_type: MetricType;
  granularity: 'hourly' | 'daily';
  data: MetricDataPoint[];
  start_date: string;
  end_date: string;
  total_points: number;
}

export interface MetricsComparisonResponse {
  metric_type: MetricType;
  period_1: {
    label: string;
    data: MetricDataPoint[];
    start_date: string;
    end_date: string;
  };
  period_2: {
    label: string;
    data: MetricDataPoint[];
    start_date: string;
    end_date: string;
  };
  change_percentage: number;
}

export interface CollectionStatus {
  is_collecting: boolean;
  last_collection: string; // ISO 8601
  next_collection: string; // ISO 8601
  recent_failures: {
    metric_type: MetricType;
    attempted_at: string;
    error_message: string;
  }[];
}

export interface ExportRequest {
  metric_types: MetricType[];
  start_date: string;
  end_date: string;
  granularity: 'hourly' | 'daily';
  format: 'csv' | 'pdf';
}

export interface ExportResponse {
  download_url: string;
  file_size_bytes: number;
  expires_at: string; // ISO 8601
}
```

## Relationships

### Entity Relationship Diagram

```
┌─────────────────────────┐
│  metric_snapshots       │
│─────────────────────────│
│  id (PK)                │
│  metric_type            │◄──── MetricType enum (application-level)
│  value                  │
│  granularity            │
│  collected_at           │
│  retry_count            │
│  created_at             │
└─────────────────────────┘
          │
          │ (soft reference)
          ▼
┌─────────────────────────────┐
│  metric_collection_failures │
│─────────────────────────────│
│  id (PK)                    │
│  metric_type                │
│  granularity                │
│  attempted_at               │
│  error_message              │
│  retry_count                │
└─────────────────────────────┘
```

**Notes**:
- No foreign key between tables (failures are independent records)
- MetricType is an application-level enum, not a separate table (simplicity principle)
- No user/admin FK (metrics are system-wide aggregates per spec assumptions)

## Data Lifecycle

### 1. Hourly Collection Flow

```
┌───────────────┐
│ APScheduler   │
│ Hourly Trigger│
└───────┬───────┘
        │
        ▼
┌────────────────────────────────────┐
│ metrics_collector.py               │
│ - Query DB for current counts      │
│ - Calculate storage sum            │
│ - Retry logic (max 3 attempts)     │
└────────┬───────────────────────────┘
         │ Success
         ▼
┌────────────────────────────────────┐
│ INSERT INTO metric_snapshots       │
│ (granularity='hourly')             │
└────────────────────────────────────┘
         │ Failure (after 3 retries)
         ▼
┌────────────────────────────────────┐
│ INSERT INTO metric_collection_     │
│ failures                           │
└────────────────────────────────────┘
```

### 2. Daily Aggregation Flow

```
┌───────────────┐
│ APScheduler   │
│ Daily Trigger │ (00:00 UTC)
└───────┬───────┘
        │
        ▼
┌────────────────────────────────────┐
│ Compute daily aggregates           │
│ SELECT AVG(value)                  │
│ FROM metric_snapshots              │
│ WHERE granularity='hourly'         │
│ AND collected_at >= yesterday      │
│ GROUP BY metric_type               │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ INSERT INTO metric_snapshots       │
│ (granularity='daily')              │
└────────────────────────────────────┘
```

### 3. Cleanup Flow

```
┌───────────────┐
│ APScheduler   │
│ Daily Trigger │ (01:00 UTC)
└───────┬───────┘
        │
        ▼
┌────────────────────────────────────┐
│ DELETE FROM metric_snapshots       │
│ WHERE granularity='hourly'         │
│ AND collected_at < NOW() - 30 days │
└────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│ DELETE FROM metric_snapshots       │
│ WHERE granularity='daily'          │
│ AND collected_at < NOW() - 90 days │
└────────────────────────────────────┘
```

## Validation Rules

### Business Rules (from FR)

1. **Unique Snapshots** (DB-enforced):
   - No duplicate snapshots for same `(metric_type, granularity, collected_at)` combination

2. **Granularity Values** (DB-enforced):
   - Only 'hourly' or 'daily' allowed

3. **Retention Periods** (application-enforced):
   - Hourly data: Maximum 30 days old
   - Daily data: Maximum 90 days old

4. **Retry Limits** (application-enforced):
   - Maximum 3 retry attempts per collection failure

5. **Value Ranges** (application-enforced):
   - All metric values must be >= 0
   - Storage bytes: 0 to max(BIGINT) = 9,223,372,036,854,775,807 bytes (~9 EB)

### API Validation (Pydantic Schemas)

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Literal

class MetricsQueryParams(BaseModel):
    metric_type: MetricType
    granularity: Literal['hourly', 'daily']
    start_date: datetime
    end_date: datetime

    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @validator('start_date')
    def not_too_old(cls, v, values):
        if 'granularity' in values:
            max_age = timedelta(days=30 if values['granularity'] == 'hourly' else 90)
            if v < datetime.now() - max_age:
                raise ValueError(f'start_date exceeds retention period for {values["granularity"]} data')
        return v

class ExportRequestSchema(BaseModel):
    metric_types: list[MetricType] = Field(min_items=1, max_items=6)
    start_date: datetime
    end_date: datetime
    granularity: Literal['hourly', 'daily']
    format: Literal['csv', 'pdf']

    @validator('end_date')
    def max_range(cls, v, values):
        if 'start_date' in values:
            if (v - values['start_date']).days > 90:
                raise ValueError('Export range cannot exceed 90 days')
        return v
```

## Migration Script

```python
# alembic/versions/{timestamp}_add_metrics_tables.py

"""Add metrics tracking tables

Revision ID: {generated_id}
Revises: {previous_revision}
Create Date: 2025-11-02
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create metric_snapshots table
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.BigInteger(), nullable=False),
        sa.Column('granularity', sa.String(length=10), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retry_count', sa.SmallInteger(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_type', 'granularity', 'collected_at', name='unique_metric_snapshot'),
        sa.CheckConstraint("granularity IN ('hourly', 'daily')", name='check_granularity')
    )

    op.create_index('idx_metric_type_time', 'metric_snapshots', ['metric_type', 'granularity', sa.text('collected_at DESC')])
    op.create_index('idx_cleanup_hourly', 'metric_snapshots', ['collected_at'], postgresql_where=sa.text("granularity = 'hourly'"))
    op.create_index('idx_cleanup_daily', 'metric_snapshots', ['collected_at'], postgresql_where=sa.text("granularity = 'daily'"))

    # Create metric_collection_failures table
    op.create_table(
        'metric_collection_failures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('granularity', sa.String(length=10), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.SmallInteger(), server_default='3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_failures_recent', 'metric_collection_failures', [sa.text('created_at DESC')])

def downgrade():
    op.drop_index('idx_failures_recent', table_name='metric_collection_failures')
    op.drop_table('metric_collection_failures')

    op.drop_index('idx_cleanup_daily', table_name='metric_snapshots')
    op.drop_index('idx_cleanup_hourly', table_name='metric_snapshots')
    op.drop_index('idx_metric_type_time', table_name='metric_snapshots')
    op.drop_table('metric_snapshots')
```

## Storage Estimates

### Hourly Data (30 days)
- 6 metric types × 24 hours/day × 30 days = 4,320 rows
- Row size: ~100 bytes (rough estimate with indexes)
- Total: **432 KB**

### Daily Data (90 days)
- 6 metric types × 90 days = 540 rows
- Row size: ~100 bytes
- Total: **54 KB**

### Failures (last 1000)
- 1000 rows × ~200 bytes = **200 KB**

**Total Storage**: ~686 KB (aligns with spec assumption of ~100KB/day)

## Query Patterns

### 1. Get Time Series for Graph

```sql
SELECT metric_type, value, collected_at
FROM metric_snapshots
WHERE metric_type = 'active_users'
  AND granularity = 'hourly'
  AND collected_at >= $start_date
  AND collected_at <= $end_date
ORDER BY collected_at ASC;
```

**Index Used**: `idx_metric_type_time`

### 2. Get Current Value

```sql
SELECT value
FROM metric_snapshots
WHERE metric_type = 'storage_bytes'
  AND granularity = 'hourly'
ORDER BY collected_at DESC
LIMIT 1;
```

**Index Used**: `idx_metric_type_time` (DESC order)

### 3. Cleanup Old Hourly Data

```sql
DELETE FROM metric_snapshots
WHERE granularity = 'hourly'
  AND collected_at < NOW() - INTERVAL '30 days';
```

**Index Used**: `idx_cleanup_hourly` (partial index)

## Summary

- ✅ Single denormalized table for simplicity (Constitution Principle IV)
- ✅ Granularity discriminator avoids table explosion
- ✅ Composite indexes for efficient time-range queries
- ✅ Retention policies enforced via scheduled cleanup
- ✅ Korean display names in application layer
- ✅ Storage estimate aligns with spec assumptions (~100KB/day)
- ✅ Migration script ready for deployment
