'use client';

/**
 * MetricsComparison component - Compare two time periods (FR-022)
 */

import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import { ko } from 'date-fns/locale';
import type { MetricType, MetricGranularity } from '@/types/metrics';
import { compareMetricPeriods } from '@/lib/metricsApi';
import {
  getMetricDisplayName,
  getMetricColor,
  formatMetricValue,
  formatChartLabel,
} from '@/lib/chartUtils';

interface Period {
  start: Date;
  end: Date;
  label: string;
}

interface MetricsComparisonProps {
  metricType: MetricType;
  granularity: MetricGranularity;
  period1: Period;
  period2: Period;
  height?: number;
}

export default function MetricsComparison({
  metricType,
  granularity,
  period1,
  period2,
  height = 300,
}: MetricsComparisonProps) {
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComparison = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await compareMetricPeriods(
          metricType,
          granularity,
          period1.start,
          period1.end,
          period2.start,
          period2.end,
          period1.label,
          period2.label
        );
        setComparisonData(data);
      } catch (err) {
        console.error('Failed to fetch comparison:', err);
        setError(err instanceof Error ? err.message : '비교 데이터를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [metricType, granularity, period1, period2]);

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
        <p className="text-gray-500">비교 데이터 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">⚠️ {error}</p>
      </div>
    );
  }

  if (!comparisonData) {
    return null;
  }

  const { period1: p1, period2: p2, change_percentage, change_direction } = comparisonData;

  // Prepare chart data with two datasets
  const baseColor = getMetricColor(metricType);
  const period1Color = baseColor;
  const period2Color = '#94A3B8'; // Gray for comparison period

  const chartData = {
    datasets: [
      {
        label: p1.label,
        data: p1.data_points.map((d: any) => ({
          x: new Date(d.timestamp),
          y: d.value,
        })),
        borderColor: period1Color,
        backgroundColor: `${period1Color}30`,
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
      {
        label: p2.label,
        data: p2.data_points.map((d: any) => ({
          x: new Date(d.timestamp),
          y: d.value,
        })),
        borderColor: period2Color,
        backgroundColor: `${period2Color}30`,
        borderWidth: 2,
        borderDash: [5, 5], // Dashed line for comparison period
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        enabled: true,
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        callbacks: {
          title: (tooltipItems) => {
            if (tooltipItems.length === 0) return '';
            const timestamp = tooltipItems[0].parsed.x;
            return formatChartLabel(new Date(timestamp).toISOString(), granularity);
          },
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const formattedValue = formatMetricValue(metricType, value);
            return `${label}: ${formattedValue}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: granularity === 'hourly' ? 'hour' : 'day',
          displayFormats: {
            hour: 'MM/dd HH:mm',
            day: 'MM/dd',
          },
        },
        adapters: {
          date: {
            locale: ko,
          },
        },
        ticks: {
          maxRotation: 45,
          minRotation: 0,
        },
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          callback: function (value) {
            if (metricType === 'storage_bytes') {
              const kb = Number(value) / 1024;
              if (kb >= 1024 * 1024) {
                return `${(kb / (1024 * 1024)).toFixed(1)} GB`;
              } else if (kb >= 1024) {
                return `${(kb / 1024).toFixed(1)} MB`;
              }
              return `${kb.toFixed(0)} KB`;
            }
            return value.toLocaleString('ko-KR');
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
  };

  // Change indicator styling
  const getChangeColor = () => {
    if (change_direction === 'up') return 'text-green-600';
    if (change_direction === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = () => {
    if (change_direction === 'up') return '↑';
    if (change_direction === 'down') return '↓';
    return '→';
  };

  const isSignificant = change_percentage !== null && Math.abs(change_percentage) > 20;

  return (
    <div>
      {/* Summary Card (FR-013) */}
      <div className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
        <div className="grid grid-cols-3 gap-4">
          {/* Period 1 Average */}
          <div>
            <p className="text-sm text-gray-600">{p1.label} 평균</p>
            <p className="text-xl font-bold text-gray-900">
              {p1.average !== null ? formatMetricValue(metricType, p1.average) : '-'}
            </p>
          </div>

          {/* Period 2 Average */}
          <div>
            <p className="text-sm text-gray-600">{p2.label} 평균</p>
            <p className="text-xl font-bold text-gray-900">
              {p2.average !== null ? formatMetricValue(metricType, p2.average) : '-'}
            </p>
          </div>

          {/* Change Percentage */}
          <div className={isSignificant ? 'border-l-4 border-yellow-400 pl-3' : ''}>
            <p className="text-sm text-gray-600">변화율</p>
            <p className={`text-2xl font-bold ${getChangeColor()}`}>
              {change_percentage !== null ? (
                <>
                  {getChangeIcon()} {Math.abs(change_percentage).toFixed(1)}%
                </>
              ) : (
                '-'
              )}
            </p>
            {isSignificant && (
              <p className="text-xs text-yellow-700 mt-1">⚠️ 유의미한 변화 (&gt;20%)</p>
            )}
          </div>
        </div>
      </div>

      {/* Overlaid Chart */}
      <div style={{ height: `${height}px` }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
