# Quick Start: Admin Dashboard Metrics History

**Feature**: 002-admin-metrics-history
**Audience**: Developers implementing this feature
**Prerequisites**: Feature 001 (local-llm-webapp) deployed and running

## Overview

This guide walks through setting up historical metrics tracking from scratch, including database migrations, background tasks, API endpoints, and frontend components.

## Setup Checklist

- [ ] Backend dependencies installed
- [ ] Database migration applied
- [ ] Background scheduler configured
- [ ] Frontend charting library installed
- [ ] API routes registered
- [ ] Manual acceptance testing completed

## 1. Backend Setup (30 minutes)

### 1.1 Install Dependencies

```powershell
# Navigate to backend directory
cd backend

# Add to requirements.txt
@"
apscheduler==3.10.4
pandas==2.1.3
reportlab==4.0.7
"@ | Add-Content requirements.txt

# Install
pip install -r requirements.txt
```

### 1.2 Run Database Migration

```powershell
# Generate migration
alembic revision --autogenerate -m "Add metrics tracking tables"

# Review generated migration in alembic/versions/
# Verify it matches data-model.md schema

# Apply migration
alembic upgrade head

# Verify tables created
```powershell
docker exec -it local-llm-webapp-db psql -U postgres -d llm_db -c "\d metric_snapshots"
```

Expected output:
```
Column      | Type                        | Modifiers
------------+-----------------------------+----------
id          | integer                     | not null
metric_type | character varying(50)       | not null
value       | bigint                      | not null
granularity | character varying(10)       | not null
collected_at| timestamp with time zone    | not null
retry_count | smallint                    | default 0
created_at  | timestamp with time zone    | default now()
```

### 1.3 Create Models

Create `backend/app/models/metric_snapshot.py`:

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
```

Create `backend/app/models/metric_type.py`:

```python
from enum import Enum

class MetricType(str, Enum):
    ACTIVE_USERS = "active_users"
    STORAGE_BYTES = "storage_bytes"
    ACTIVE_SESSIONS = "active_sessions"
    CONVERSATION_COUNT = "conversation_count"
    DOCUMENT_COUNT = "document_count"
    TAG_COUNT = "tag_count"
```

### 1.4 Implement Metrics Collector

Create `backend/app/services/metrics_collector.py`:

```python
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_type import MetricType
from app.models import User, Session, Conversation, Document, Tag  # Existing models
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_all_metrics(self, granularity: str = "hourly") -> dict:
        """Collect all metrics and store snapshots"""
        collected_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        results = {}

        for metric_type in MetricType:
            try:
                value = await self._collect_metric(metric_type)
                snapshot = MetricSnapshot(
                    metric_type=metric_type.value,
                    value=value,
                    granularity=granularity,
                    collected_at=collected_at,
                    retry_count=0
                )
                self.db.add(snapshot)
                results[metric_type.value] = value
                logger.info(f"Collected {metric_type.value}={value}")
            except Exception as e:
                logger.error(f"Failed to collect {metric_type.value}: {e}")
                results[metric_type.value] = None

        await self.db.commit()
        return results

    async def _collect_metric(self, metric_type: MetricType) -> int:
        """Calculate current value for a metric type"""
        if metric_type == MetricType.ACTIVE_USERS:
            # Count users with active sessions
            result = await self.db.execute(
                func.count(func.distinct(Session.user_id)).where(Session.is_active == True)
            )
            return result.scalar() or 0

        elif metric_type == MetricType.STORAGE_BYTES:
            # Sum of all document file sizes
            result = await self.db.execute(
                func.sum(Document.file_size_bytes)
            )
            return result.scalar() or 0

        elif metric_type == MetricType.ACTIVE_SESSIONS:
            result = await self.db.execute(
                func.count(Session.id).where(Session.is_active == True)
            )
            return result.scalar() or 0

        elif metric_type == MetricType.CONVERSATION_COUNT:
            result = await self.db.execute(func.count(Conversation.id))
            return result.scalar() or 0

        elif metric_type == MetricType.DOCUMENT_COUNT:
            result = await self.db.execute(func.count(Document.id))
            return result.scalar() or 0

        elif metric_type == MetricType.TAG_COUNT:
            result = await self.db.execute(func.count(Tag.id))
            return result.scalar() or 0

        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
```

### 1.5 Configure Background Scheduler

Modify `backend/app/core/scheduler.py`:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.core.database import get_db
from app.services.metrics_collector import MetricsCollector
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

async def collect_hourly_metrics():
    """Scheduled task: collect hourly metrics"""
    async for db in get_db():
        try:
            collector = MetricsCollector(db)
            await collector.collect_all_metrics(granularity="hourly")
            logger.info("Hourly metrics collected successfully")
        except Exception as e:
            logger.error(f"Hourly collection failed: {e}")
        finally:
            await db.close()

async def collect_daily_aggregates():
    """Scheduled task: compute daily aggregates from hourly data"""
    # Implementation: aggregate previous day's hourly data
    # (See data-model.md for aggregation query)
    pass

async def cleanup_old_metrics():
    """Scheduled task: delete expired metrics"""
    # Implementation: delete hourly >30 days, daily >90 days
    pass

def start_scheduler():
    """Initialize and start background scheduler"""
    # Hourly metrics collection (every hour at :00)
    scheduler.add_job(
        collect_hourly_metrics,
        trigger=IntervalTrigger(hours=1),
        id='collect_hourly',
        name='Collect hourly metrics',
        replace_existing=True
    )

    # Daily aggregates (midnight UTC)
    scheduler.add_job(
        collect_daily_aggregates,
        trigger=CronTrigger(hour=0, minute=0),
        id='daily_aggregates',
        name='Compute daily aggregates',
        replace_existing=True
    )

    # Cleanup (1 AM UTC daily)
    scheduler.add_job(
        cleanup_old_metrics,
        trigger=CronTrigger(hour=1, minute=0),
        id='cleanup_metrics',
        name='Cleanup old metrics',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Metrics scheduler started")

def stop_scheduler():
    """Gracefully shut down scheduler"""
    scheduler.shutdown()
```

Add to `backend/app/main.py`:

```python
from app.core.scheduler import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
```

### 1.6 Test Backend

```powershell
# Run backend
cd backend
uvicorn app.main:app --reload

# Trigger manual collection (create test endpoint)
# Or wait for next hour :00 mark

# Verify data inserted
docker exec -it local-llm-webapp-db psql -U postgres -d llm_db -c "SELECT * FROM metric_snapshots ORDER BY collected_at DESC LIMIT 5;"
```

## 2. Frontend Setup (45 minutes)

### 2.1 Install Dependencies

```powershell
cd frontend

npm install react-chartjs-2 chart.js chartjs-adapter-date-fns date-fns downsample
```

### 2.2 Create TypeScript Types

Create `frontend/src/types/metrics.ts`:

```typescript
export enum MetricType {
  ACTIVE_USERS = 'active_users',
  STORAGE_BYTES = 'storage_bytes',
  ACTIVE_SESSIONS = 'active_sessions',
  CONVERSATION_COUNT = 'conversation_count',
  DOCUMENT_COUNT = 'document_count',
  TAG_COUNT = 'tag_count',
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricsTimeSeriesResponse {
  metric_type: MetricType;
  granularity: 'hourly' | 'daily';
  data: MetricDataPoint[];
  start_date: string;
  end_date: string;
  total_points: number;
  downsampled?: boolean;
}
```

### 2.3 Create API Client

Create `frontend/src/lib/metricsApi.ts`:

```typescript
import { MetricType, MetricsTimeSeriesResponse } from '@/types/metrics';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function getMetricsTimeSeries(
  metricType: MetricType,
  granularity: 'hourly' | 'daily',
  startDate: Date,
  endDate: Date
): Promise<MetricsTimeSeriesResponse> {
  const params = new URLSearchParams({
    metric_type: metricType,
    granularity,
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString(),
  });

  const response = await fetch(`${API_BASE}/metrics/timeseries?${params}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('메트릭 데이터를 불러올 수 없습니다.');
  }

  return response.json();
}
```

### 2.4 Create Chart Component

Create `frontend/src/components/admin/MetricsGraph.tsx`:

```typescript
'use client';

import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { ko } from 'date-fns/locale';
import { MetricsTimeSeriesResponse } from '@/types/metrics';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface MetricsGraphProps {
  data: MetricsTimeSeriesResponse;
  title: string;
}

export default function MetricsGraph({ data, title }: MetricsGraphProps) {
  const chartData = {
    labels: data.data.map(d => new Date(d.timestamp)),
    datasets: [
      {
        label: title,
        data: data.data.map(d => d.value),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    locale: 'ko-KR',
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: title,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y.toLocaleString('ko-KR')}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: data.granularity === 'hourly' ? 'hour' : 'day',
        },
        adapters: {
          date: {
            locale: ko,
          },
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => value.toLocaleString('ko-KR'),
        },
      },
    },
  };

  return (
    <div style={{ height: '400px' }}>
      <Line data={chartData} options={options} />
    </div>
  );
}
```

### 2.5 Create Metrics Page

Create `frontend/src/app/admin/metrics/page.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { MetricType, MetricsTimeSeriesResponse } from '@/types/metrics';
import { getMetricsTimeSeries } from '@/lib/metricsApi';
import MetricsGraph from '@/components/admin/MetricsGraph';

export default function MetricsPage() {
  const [data, setData] = useState<MetricsTimeSeriesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7);

        const response = await getMetricsTimeSeries(
          MetricType.ACTIVE_USERS,
          'hourly',
          startDate,
          endDate
        );

        setData(response);
      } catch (error) {
        console.error('Failed to load metrics:', error);
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  if (loading) return <div>로딩 중...</div>;
  if (!data) return <div>데이터를 불러올 수 없습니다.</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">메트릭 히스토리</h1>
      <MetricsGraph data={data} title="활성 사용자" />
    </div>
  );
}
```

### 2.6 Test Frontend

```powershell
cd frontend
npm run dev

# Navigate to http://localhost:3000/admin/metrics
# Verify graph displays with last 7 days of data
```

## 3. Acceptance Testing (spec.md)

### User Story 1: View Historical Metrics

**Test AS-1.1**: Admin views 7-day graph
- [ ] Login as admin
- [ ] Navigate to /admin/metrics
- [ ] Verify graph shows last 7 days of active users
- [ ] Verify current metric displayed alongside historical

**Test AS-1.2**: Hover shows tooltip
- [ ] Hover over any data point
- [ ] Verify tooltip shows exact value and timestamp in Korean

**Test AS-1.3**: Change time range
- [ ] Select "30 days" from time range selector
- [ ] Verify graph updates to show 30-day history

### User Story 2: Compare Time Periods

**Test AS-2.1**: Week-over-week comparison
- [ ] Click "비교" (Compare) mode
- [ ] Select "이번 주" and "지난 주" presets
- [ ] Verify two lines overlaid on graph with different colors

**Test AS-2.2**: View percentage change
- [ ] In comparison mode
- [ ] Verify summary shows percentage change (e.g., "+19%")
- [ ] Verify up/down arrow indicator

### User Story 3: Export Data

**Test AS-3.1**: Export to CSV
- [ ] Click "CSV 내보내기" button
- [ ] Verify file downloads
- [ ] Open in Excel, verify Korean headers, data matches graph

**Test AS-3.2**: Export respects date range
- [ ] Select custom 14-day range
- [ ] Export to CSV
- [ ] Verify file contains only 14 days of data

**Test AS-3.3**: PDF export
- [ ] Click "PDF 내보내기"
- [ ] Verify PDF contains graphs and summary statistics
- [ ] Verify Korean font renders correctly

## 4. Troubleshooting

### Issue: No data in graph

**Check**:
```powershell
# Verify scheduler is running
docker logs local-llm-webapp-backend | Select-String "Metrics scheduler started"

# Check database for records
docker exec -it local-llm-webapp-db psql -U postgres -d llm_db -c "SELECT COUNT(*) FROM metric_snapshots;"
```

**Fix**: If count is 0, manually trigger collection or wait for next hour.

### Issue: Korean characters not displaying

**Check**: Frontend locale settings in Chart.js

**Fix**: Verify `locale: 'ko-KR'` in chart options and `ko` imported from date-fns

### Issue: Graph rendering too slow

**Check**: Number of data points being rendered

**Fix**: Implement downsampling in `chartUtils.ts`:

```typescript
import { LTTB } from 'downsample';

export function downsampleMetrics(data: MetricDataPoint[], target: number = 1000) {
  if (data.length <= target) return data;

  const xy = data.map(d => [new Date(d.timestamp).getTime(), d.value]);
  const downsampled = LTTB(xy, target);

  return downsampled.map(([ts, val]) => ({
    timestamp: new Date(ts).toISOString(),
    value: val,
  }));
}
```

## 5. Next Steps

After completing quick start:

1. **Implement remaining metrics**: Currently only `active_users` shown, add other 5 metric types
2. **Add time range selector**: Create `MetricsTimeRange.tsx` component
3. **Implement comparison mode**: Create `MetricsComparison.tsx`
4. **Add export functionality**: Implement `ExportService` in backend
5. **Add collection status widget**: Show FR-019 status indicator
6. **Run `/speckit.tasks`**: Generate detailed implementation tasks

## Reference Documentation

- **Feature Spec**: `specs/002-admin-metrics-history/spec.md`
- **Data Model**: `specs/002-admin-metrics-history/data-model.md`
- **API Contracts**: `specs/002-admin-metrics-history/contracts/openapi.yaml`
- **Research**: `specs/002-admin-metrics-history/research.md`
- **Constitution**: `.specify/memory/constitution.md`

## Estimated Time to MVP

- Backend implementation: **2-3 days**
- Frontend implementation: **2-3 days**
- Testing & refinement: **1 day**
- **Total**: ~5-7 days for single developer
