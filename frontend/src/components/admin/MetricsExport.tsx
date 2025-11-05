'use client';

/**
 * MetricsExport component - Export metrics to CSV or PDF (FR-024, FR-025)
 */

import React, { useState } from 'react';
import type { MetricType, MetricGranularity, ExportFormat } from '@/types/metrics';
import { exportMetrics } from '@/lib/metricsApi';
import { getMetricDisplayName } from '@/lib/chartUtils';

const METRIC_TYPES: MetricType[] = [
  'active_users',
  'storage_bytes',
  'active_sessions',
  'conversation_count',
  'document_count',
  'tag_count',
];

interface MetricsExportProps {
  granularity: MetricGranularity;
  startTime: Date;
  endTime: Date;
}

export default function MetricsExport({
  granularity,
  startTime,
  endTime,
}: MetricsExportProps) {
  const [selectedMetrics, setSelectedMetrics] = useState<MetricType[]>(['active_users']);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [includeChart, setIncludeChart] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const toggleMetric = (metric: MetricType) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric]
    );
  };

  const handleExport = async () => {
    if (selectedMetrics.length === 0) {
      setError('최소 1개의 메트릭을 선택해주세요');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await exportMetrics({
        metric_types: selectedMetrics,
        granularity: granularity,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        format: selectedFormat,
        include_chart: includeChart,
      });

      // Trigger download
      const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${response.download_url}`;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = response.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSuccess(
        `파일이 생성되었습니다 (${(response.file_size_bytes / 1024).toFixed(1)} KB)${
          response.downsampled ? ' - 다운샘플링 적용됨' : ''
        }`
      );
    } catch (err) {
      console.error('Export failed:', err);
      setError(err instanceof Error ? err.message : '내보내기에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">데이터 내보내기</h3>

      {/* Metric Selection */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">내보낼 메트릭 선택:</p>
        <div className="grid grid-cols-2 gap-2">
          {METRIC_TYPES.map((metric) => (
            <label
              key={metric}
              className="flex items-center gap-2 p-2 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedMetrics.includes(metric)}
                onChange={() => toggleMetric(metric)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">{getMetricDisplayName(metric)}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Format Selection */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">파일 형식:</p>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="csv"
              checked={selectedFormat === 'csv'}
              onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
              className="w-4 h-4 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">CSV</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="pdf"
              checked={selectedFormat === 'pdf'}
              onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
              className="w-4 h-4 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">PDF</span>
          </label>
        </div>
      </div>

      {/* PDF Options */}
      {selectedFormat === 'pdf' && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeChart}
              onChange={(e) => setIncludeChart(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">차트 포함 (향후 지원 예정)</span>
          </label>
        </div>
      )}

      {/* Export Info */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-xs text-blue-800">
          선택한 기간: {startTime.toLocaleDateString('ko-KR')} ~{' '}
          {endTime.toLocaleDateString('ko-KR')}
        </p>
        <p className="text-xs text-blue-800 mt-1">
          세분성: {granularity === 'hourly' ? '시간별' : '일별'}
        </p>
        <p className="text-xs text-blue-700 mt-2">
          ⓘ 파일이 10MB를 초과하면 자동으로 다운샘플링됩니다
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800">⚠️ {error}</p>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-800">✓ {success}</p>
        </div>
      )}

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={loading || selectedMetrics.length === 0}
        className={`w-full py-2.5 px-4 rounded-lg font-medium transition-colors ${
          loading || selectedMetrics.length === 0
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
        }`}
      >
        {loading ? '내보내는 중...' : `${selectedFormat.toUpperCase()} 내보내기`}
      </button>
    </div>
  );
}
