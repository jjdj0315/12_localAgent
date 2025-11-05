/**
 * Chart utilities for metrics visualization (Feature 002)
 *
 * Includes LTTB (Largest-Triangle-Three-Buckets) downsampling algorithm
 * for efficient rendering of large datasets (FR-018).
 */

import { LTTB } from 'downsample';
import type { MetricSnapshot, MetricType } from '@/types/metrics';

/**
 * Maximum data points before downsampling is applied (FR-018)
 */
const MAX_CHART_POINTS = 1000;

/**
 * Downsample metric data using LTTB algorithm (FR-018)
 *
 * The LTTB algorithm preserves visual characteristics while reducing
 * the number of data points for better chart rendering performance.
 *
 * @param snapshots - Original metric snapshots
 * @param threshold - Target number of points (default: 1000)
 * @returns Downsampled snapshots
 */
export function downsampleMetrics(
  snapshots: MetricSnapshot[],
  threshold: number = MAX_CHART_POINTS
): MetricSnapshot[] {
  if (snapshots.length <= threshold) {
    return snapshots;
  }

  // Convert to LTTB-compatible format: [x, y] pairs
  const data: [number, number][] = snapshots.map((s) => [
    new Date(s.timestamp).getTime(),
    s.value,
  ]);

  // Apply LTTB downsampling
  const downsampled = LTTB(data, threshold);

  // Convert back to MetricSnapshot format
  return downsampled.map(([timestamp, value]) => {
    // Find the closest original snapshot to preserve metadata
    const originalIndex = snapshots.findIndex(
      (s) => new Date(s.timestamp).getTime() >= timestamp
    );
    const original = snapshots[originalIndex] || snapshots[snapshots.length - 1];

    return {
      ...original,
      timestamp: new Date(timestamp).toISOString(),
      value: Math.round(value),
    };
  });
}

/**
 * Format metric value with appropriate unit (FR-008)
 *
 * @param metricType - Type of metric
 * @param value - Raw value
 * @returns Formatted string with unit
 */
export function formatMetricValue(metricType: MetricType, value: number): string {
  switch (metricType) {
    case 'storage_bytes':
      return formatBytes(value);
    case 'active_users':
      return `${value.toLocaleString('ko-KR')}명`;
    case 'active_sessions':
    case 'conversation_count':
    case 'document_count':
    case 'tag_count':
      return `${value.toLocaleString('ko-KR')}개`;
    default:
      return value.toLocaleString('ko-KR');
  }
}

/**
 * Format bytes to human-readable format (KB, MB, GB)
 *
 * @param bytes - Size in bytes
 * @returns Formatted string (e.g., "1.5 GB")
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Get Korean display name for metric type
 *
 * @param metricType - Type of metric
 * @returns Korean display name
 */
export function getMetricDisplayName(metricType: MetricType): string {
  const names: Record<MetricType, string> = {
    active_users: '활성 사용자',
    storage_bytes: '저장 공간',
    active_sessions: '활성 세션',
    conversation_count: '대화 수',
    document_count: '문서 수',
    tag_count: '태그 수',
  };
  return names[metricType] || metricType;
}

/**
 * Get color for metric type (Chart.js compatible)
 *
 * @param metricType - Type of metric
 * @returns Hex color code
 */
export function getMetricColor(metricType: MetricType): string {
  const colors: Record<MetricType, string> = {
    active_users: '#3B82F6', // Blue
    storage_bytes: '#10B981', // Green
    active_sessions: '#F59E0B', // Amber
    conversation_count: '#8B5CF6', // Purple
    document_count: '#EC4899', // Pink
    tag_count: '#14B8A6', // Teal
  };
  return colors[metricType] || '#6B7280';
}

/**
 * Format timestamp for chart label (FR-008)
 *
 * @param timestamp - ISO 8601 timestamp
 * @param granularity - 'hourly' or 'daily'
 * @returns Formatted date string in Korean
 */
export function formatChartLabel(timestamp: string, granularity: 'hourly' | 'daily'): string {
  const date = new Date(timestamp);

  if (granularity === 'hourly') {
    return date.toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } else {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}

/**
 * Calculate percentage change between two values
 *
 * @param current - Current period value
 * @param previous - Previous period value
 * @returns Percentage change (null if previous is 0)
 */
export function calculatePercentageChange(
  current: number,
  previous: number
): number | null {
  if (previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

/**
 * Determine change direction
 *
 * @param change - Percentage change value
 * @returns 'up', 'down', or 'unchanged'
 */
export function getChangeDirection(
  change: number | null
): 'up' | 'down' | 'unchanged' {
  if (change === null || Math.abs(change) < 0.01) return 'unchanged';
  return change > 0 ? 'up' : 'down';
}

/**
 * Generate time range presets for metrics UI (FR-017)
 */
export const TIME_RANGE_PRESETS = [
  { label: '최근 7일', days: 7 },
  { label: '최근 30일', days: 30 },
  { label: '최근 90일', days: 90 },
] as const;

/**
 * Calculate start/end dates for a preset
 *
 * @param days - Number of days to look back
 * @returns Start and end Date objects
 */
export function getPresetDateRange(days: number): { start: Date; end: Date } {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);

  return { start, end };
}

/**
 * Comparison period presets (FR-022)
 */
export const COMPARISON_PRESETS = [
  { label: '이번 주 vs 지난 주', value: 'week' },
  { label: '이번 달 vs 지난 달', value: 'month' },
] as const;

/**
 * Get date ranges for period comparison
 *
 * @param preset - Comparison preset type ('week' or 'month')
 * @returns Two periods with start/end dates and labels
 */
export function getComparisonDateRanges(preset: 'week' | 'month'): {
  period1: { start: Date; end: Date; label: string };
  period2: { start: Date; end: Date; label: string };
} {
  const now = new Date();

  if (preset === 'week') {
    // This week: last 7 days
    const period1End = now;
    const period1Start = new Date();
    period1Start.setDate(period1Start.getDate() - 7);

    // Last week: 7-14 days ago
    const period2End = new Date();
    period2End.setDate(period2End.getDate() - 7);
    const period2Start = new Date();
    period2Start.setDate(period2Start.getDate() - 14);

    return {
      period1: { start: period1Start, end: period1End, label: '이번 주' },
      period2: { start: period2Start, end: period2End, label: '지난 주' },
    };
  } else {
    // This month: last 30 days
    const period1End = now;
    const period1Start = new Date();
    period1Start.setDate(period1Start.getDate() - 30);

    // Last month: 30-60 days ago
    const period2End = new Date();
    period2End.setDate(period2End.getDate() - 30);
    const period2Start = new Date();
    period2Start.setDate(period2Start.getDate() - 60);

    return {
      period1: { start: period1Start, end: period1End, label: '이번 달' },
      period2: { start: period2Start, end: period2End, label: '지난 달' },
    };
  }
}
