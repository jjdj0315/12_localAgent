'use client';

/**
 * Admin Metrics Dashboard Page (Feature 002, User Stories 1-2)
 *
 * NOTE: This page has been integrated into the main admin dashboard (/admin).
 * This standalone page is kept for backward compatibility and reference.
 * Redirecting to main admin page...
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function MetricsPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to main admin page where metrics are now integrated
    router.push('/admin');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">메인 관리자 대시보드로 이동 중...</p>
      </div>
    </div>
  );
}

/* ORIGINAL STANDALONE METRICS PAGE - NOW INTEGRATED INTO /admin

import React, { useState, useEffect } from 'react';
import MetricsGraph from '@/components/admin/MetricsGraph';
import MetricsComparison from '@/components/admin/MetricsComparison';
import MetricsTimeRange from '@/components/admin/MetricsTimeRange';
import MetricsGranularityToggle from '@/components/admin/MetricsGranularityToggle';
import MetricsExport from '@/components/admin/MetricsExport';
import {
  getMetricsTimeSeries,
  getCurrentMetrics,
  getCollectionStatus,
} from '@/lib/metricsApi';
import {
  downsampleMetrics,
  getPresetDateRange,
  formatMetricValue,
  getMetricDisplayName,
  COMPARISON_PRESETS,
  getComparisonDateRanges,
} from '@/lib/chartUtils';
import type { MetricType, MetricGranularity, MetricSnapshot } from '@/types/metrics';

const METRIC_TYPES: MetricType[] = [
  'active_users',
  'storage_bytes',
  'active_sessions',
  'conversation_count',
  'document_count',
  'tag_count',
];

export default function MetricsPageOriginal() {
  // State
  const [viewMode, setViewMode] = useState<'normal' | 'comparison'>('normal');
  const [selectedDays, setSelectedDays] = useState(7);
  const [granularity, setGranularity] = useState<MetricGranularity>('hourly');
  const [comparisonPreset, setComparisonPreset] = useState<'week' | 'month'>('week');
  const [metricsData, setMetricsData] = useState<Record<MetricType, MetricSnapshot[]>>({
    active_users: [],
    storage_bytes: [],
    active_sessions: [],
    conversation_count: [],
    document_count: [],
    tag_count: [],
  });
  const [currentValues, setCurrentValues] = useState<Record<string, number | null>>({});
  const [collectionStatus, setCollectionStatus] = useState<{
    status: 'healthy' | 'degraded';
    last_collection_at: string | null;
    next_collection_at: string;
    failure_count_24h: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch metrics data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const { start, end } = getPresetDateRange(selectedDays);

        // Fetch time series for all metrics in parallel
        const promises = METRIC_TYPES.map(async (metricType) => {
          try {
            const data = await getMetricsTimeSeries(metricType, granularity, start, end);
            // Apply downsampling if needed (FR-018)
            const downsampled = downsampleMetrics(data, 1000);
            return { metricType, data: downsampled };
          } catch (err) {
            console.error(`Failed to fetch ${metricType}:`, err);
            return { metricType, data: [] };
          }
        });

        const results = await Promise.all(promises);

        // Update metrics data
        const newMetricsData: Record<MetricType, MetricSnapshot[]> = {
          active_users: [],
          storage_bytes: [],
          active_sessions: [],
          conversation_count: [],
          document_count: [],
          tag_count: [],
        };

        results.forEach(({ metricType, data }) => {
          newMetricsData[metricType] = data;
        });

        setMetricsData(newMetricsData);

        // Fetch current values (FR-007)
        const currentData = await getCurrentMetrics();
        const currentValuesMap: Record<string, number | null> = {};
        currentData.metrics.forEach((m) => {
          currentValuesMap[m.metric_type] = m.value;
        });
        setCurrentValues(currentValuesMap);

        // Fetch collection status (FR-019)
        const status = await getCollectionStatus();
        setCollectionStatus(status);
      } catch (err) {
        console.error('Failed to fetch metrics:', err);
        setError(err instanceof Error ? err.message : '메트릭 데이터를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDays, granularity]);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">시스템 메트릭 대시보드</h1>
        <p className="mt-2 text-gray-600">시스템 메트릭의 과거 데이터를 조회하고 분석합니다</p>
      </div>

      {/* Controls */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        {/* View Mode Toggle (FR-022) */}
        <div className="mb-4 flex items-center gap-4 pb-4 border-b border-gray-200">
          <span className="text-sm font-medium text-gray-700">보기 모드:</span>
          <div className="inline-flex rounded-lg border border-gray-300 bg-gray-50 p-1">
            <button
              onClick={() => setViewMode('normal')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'normal'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              일반
            </button>
            <button
              onClick={() => setViewMode('comparison')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'comparison'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              비교
            </button>
          </div>
        </div>

        {/* Mode-specific controls */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          {viewMode === 'normal' ? (
            <>
              <MetricsTimeRange selectedDays={selectedDays} onRangeChange={setSelectedDays} />
              <MetricsGranularityToggle
                granularity={granularity}
                onGranularityChange={setGranularity}
              />
            </>
          ) : (
            <>
              {/* Comparison preset selector */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">비교 기간:</span>
                <div className="flex gap-2">
                  {COMPARISON_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      onClick={() => setComparisonPreset(preset.value)}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        comparisonPreset === preset.value
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
              <MetricsGranularityToggle
                granularity={granularity}
                onGranularityChange={setGranularity}
              />
            </>
          )}
        </div>
      </div>

      {/* Collection Status Widget (FR-019) */}
      {collectionStatus && (
        <div
          className={`mb-6 p-4 rounded-lg border ${
            collectionStatus.status === 'healthy'
              ? 'bg-green-50 border-green-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-3 h-3 rounded-full ${
                  collectionStatus.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                }`}
              />
              <span className="font-medium text-gray-900">
                {collectionStatus.status === 'healthy' ? '정상 수집 중' : '일부 수집 실패'}
              </span>
            </div>
            <div className="text-sm text-gray-600">
              {collectionStatus.last_collection_at && (
                <span>
                  마지막 수집:{' '}
                  {new Date(collectionStatus.last_collection_at).toLocaleString('ko-KR')}
                </span>
              )}
              {collectionStatus.failure_count_24h > 0 && (
                <span className="ml-4 text-yellow-700 font-medium">
                  최근 24시간 실패: {collectionStatus.failure_count_24h}건
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">⚠️ {error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">메트릭 데이터를 불러오는 중...</p>
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      {!loading && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {METRIC_TYPES.map((metricType) => {
              const currentValue = currentValues[metricType];
              const data = metricsData[metricType];

              return (
                <div
                  key={metricType}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
                >
                  {/* Metric Header */}
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {getMetricDisplayName(metricType)}
                    </h3>
                    {viewMode === 'normal' && (
                      <div className="text-right">
                        <p className="text-sm text-gray-500">현재 값</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {currentValue !== null && currentValue !== undefined
                            ? formatMetricValue(metricType, currentValue)
                            : '-'}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Graph or Comparison */}
                  {viewMode === 'normal' ? (
                    <MetricsGraph
                      metricType={metricType}
                      granularity={granularity}
                      data={data}
                      height={250}
                      showLegend={false}
                    />
                  ) : (
                    <MetricsComparison
                      metricType={metricType}
                      granularity={granularity}
                      period1={getComparisonDateRanges(comparisonPreset).period1}
                      period2={getComparisonDateRanges(comparisonPreset).period2}
                      height={250}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Export Section (FR-024, FR-025) */}
          {viewMode === 'normal' && (
            <div className="mt-8">
              <MetricsExport
                granularity={granularity}
                startTime={getPresetDateRange(selectedDays).start}
                endTime={getPresetDateRange(selectedDays).end}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

*/
