/**
 * TypeScript interfaces for metrics feature (Feature 002)
 */

/**
 * Metric types tracked by the system
 */
export type MetricType =
  | 'active_users'
  | 'storage_bytes'
  | 'active_sessions'
  | 'conversation_count'
  | 'document_count'
  | 'tag_count';

/**
 * Granularity levels for metric snapshots
 */
export type MetricGranularity = 'hourly' | 'daily';

/**
 * Single metric data point (FR-017)
 */
export interface MetricSnapshot {
  metric_type: MetricType;
  value: number;
  granularity: MetricGranularity;
  timestamp: string; // ISO 8601 format
}

/**
 * Time range filter for metric queries (FR-017)
 */
export interface MetricTimeRange {
  metric_type: MetricType;
  granularity: MetricGranularity;
  start_time: string; // ISO 8601 format
  end_time: string; // ISO 8601 format
}

/**
 * Failed metric collection record (FR-019)
 */
export interface MetricCollectionFailure {
  metric_type: MetricType;
  attempted_at: string; // ISO 8601 format
  error_message: string;
}

/**
 * Metric configuration for UI display
 */
export interface MetricConfig {
  type: MetricType;
  displayName: string;
  unit: string;
  color: string; // Chart color
  formatValue: (value: number) => string; // Custom formatter (e.g., bytes to MB)
}

/**
 * Chart data structure for react-chartjs-2 (FR-017)
 */
export interface MetricChartData {
  labels: string[]; // Timestamps
  datasets: {
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
    fill: boolean;
  }[];
}

/**
 * Period comparison data (FR-022)
 */
export interface PeriodComparisonData {
  metric_type: MetricType;
  current_period: {
    start: string;
    end: string;
    snapshots: MetricSnapshot[];
  };
  previous_period: {
    start: string;
    end: string;
    snapshots: MetricSnapshot[];
  };
  change_percentage: number; // Percentage change between periods
}

/**
 * Export format options (FR-024)
 */
export type ExportFormat = 'csv' | 'pdf';

/**
 * Export request parameters (FR-024, FR-025)
 */
export interface ExportRequest {
  metric_types: MetricType[];
  granularity: MetricGranularity;
  start_time: string; // ISO 8601 format
  end_time: string; // ISO 8601 format
  format: ExportFormat;
  include_chart?: boolean; // Only for PDF format
}

/**
 * API response wrapper for metric queries (FR-017)
 */
export interface MetricsResponse {
  data: MetricSnapshot[];
  total: number;
  granularity: MetricGranularity;
}

/**
 * API response for collection failures (FR-019)
 */
export interface FailuresResponse {
  failures: MetricCollectionFailure[];
  total: number;
}

/**
 * Downsampling options for chart performance (FR-018)
 */
export interface DownsampleOptions {
  enabled: boolean;
  threshold: number; // Max data points before downsampling
  algorithm: 'lttb'; // Largest-Triangle-Three-Buckets
}
