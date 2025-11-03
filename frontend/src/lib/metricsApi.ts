/**
 * API client for metrics endpoints (Feature 002)
 */

import type {
  MetricType,
  MetricGranularity,
  MetricSnapshot,
  MetricCollectionFailure,
  ExportRequest,
} from '@/types/metrics';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Response from /api/v1/metrics/timeseries endpoint
 */
interface MetricsTimeSeriesResponse {
  metric_type: string;
  granularity: string;
  start_time: string;
  end_time: string;
  data_points: MetricSnapshot[];
  total: number;
}

/**
 * Response from /api/v1/metrics/current endpoint
 */
interface CurrentMetricValue {
  metric_type: string;
  value: number | null;
  display_name: string;
  unit: string;
}

interface CurrentMetricsResponse {
  metrics: CurrentMetricValue[];
  collected_at: string | null;
}

/**
 * Response from /api/v1/metrics/status endpoint
 */
interface MetricsCollectionStatusResponse {
  last_collection_at: string | null;
  next_collection_at: string;
  recent_failures: MetricCollectionFailure[];
  failure_count_24h: number;
  status: 'healthy' | 'degraded';
}

/**
 * Get authentication token from localStorage
 * Metrics endpoints require admin authentication only
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem('admin_token');
  if (!token) {
    throw new Error('관리자 권한이 필요합니다. 관리자로 로그인해주세요.');
  }
  return token;
}

/**
 * Fetch time series data for a specific metric (FR-017)
 */
export async function getMetricsTimeSeries(
  metricType: MetricType,
  granularity: MetricGranularity,
  startTime: Date,
  endTime: Date
): Promise<MetricSnapshot[]> {
  const token = getAuthToken();

  const params = new URLSearchParams({
    metric_type: metricType,
    granularity: granularity,
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
  });

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/timeseries?${params}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '메트릭 데이터 조회에 실패했습니다');
  }

  const data: MetricsTimeSeriesResponse = await response.json();
  return data.data_points;
}

/**
 * Get current (latest) values for all 6 metrics (FR-007)
 */
export async function getCurrentMetrics(): Promise<CurrentMetricsResponse> {
  const token = getAuthToken();

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/current`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '현재 메트릭 조회에 실패했습니다');
  }

  return await response.json();
}

/**
 * Get metrics collection system status (FR-019)
 */
export async function getCollectionStatus(): Promise<MetricsCollectionStatusResponse> {
  const token = getAuthToken();

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/status`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '수집 상태 조회에 실패했습니다');
  }

  return await response.json();
}

/**
 * Get statistical summary for a metric over a time range
 */
export async function getMetricSummary(
  metricType: MetricType,
  granularity: MetricGranularity,
  startTime: Date,
  endTime: Date
): Promise<{
  metric_type: string;
  granularity: string;
  min: number | null;
  max: number | null;
  avg: number | null;
  latest: number | null;
  data_points: number;
}> {
  const token = getAuthToken();

  const params = new URLSearchParams({
    metric_type: metricType,
    granularity: granularity,
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
  });

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/summary?${params}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '메트릭 요약 조회에 실패했습니다');
  }

  return await response.json();
}

/**
 * Compare two time periods for a metric (FR-022)
 */
export async function compareMetricPeriods(
  metricType: MetricType,
  granularity: MetricGranularity,
  period1Start: Date,
  period1End: Date,
  period2Start: Date,
  period2End: Date,
  period1Label: string = '이번 주',
  period2Label: string = '지난 주'
): Promise<{
  metric_type: string;
  granularity: string;
  period1: {
    start_time: string;
    end_time: string;
    label: string;
    data_points: MetricSnapshot[];
    average: number | null;
  };
  period2: {
    start_time: string;
    end_time: string;
    label: string;
    data_points: MetricSnapshot[];
    average: number | null;
  };
  change_percentage: number | null;
  change_direction: 'up' | 'down' | 'unchanged' | null;
}> {
  const token = getAuthToken();

  const params = new URLSearchParams({
    metric_type: metricType,
    granularity: granularity,
    period1_start: period1Start.toISOString(),
    period1_end: period1End.toISOString(),
    period2_start: period2Start.toISOString(),
    period2_end: period2End.toISOString(),
    period1_label: period1Label,
    period2_label: period2Label,
  });

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/comparison?${params}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '기간 비교에 실패했습니다');
  }

  return await response.json();
}

/**
 * Export metrics data to CSV or PDF (FR-024, FR-025)
 */
export async function exportMetrics(request: ExportRequest): Promise<{
  export_id: string;
  filename: string;
  download_url: string;
  file_size_bytes: number;
  expires_at: string;
  downsampled: boolean;
}> {
  const token = getAuthToken();

  const response = await fetch(`${API_BASE_URL}/api/v1/metrics/export`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...request,
      start_time: request.start_time,
      end_time: request.end_time,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '데이터 내보내기에 실패했습니다');
  }

  return await response.json();
}
