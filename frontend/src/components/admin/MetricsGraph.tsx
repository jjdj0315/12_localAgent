'use client';

/**
 * MetricsGraph component - Line chart for metric visualization (FR-017)
 */

import React from 'react';
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
  Filler,
  ChartOptions,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { ko } from 'date-fns/locale';
import type { MetricSnapshot, MetricType, MetricGranularity } from '@/types/metrics';
import {
  formatMetricValue,
  getMetricDisplayName,
  getMetricColor,
  formatChartLabel,
} from '@/lib/chartUtils';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MetricsGraphProps {
  metricType: MetricType;
  granularity: MetricGranularity;
  data: MetricSnapshot[];
  height?: number;
  showLegend?: boolean;
}

export default function MetricsGraph({
  metricType,
  granularity,
  data,
  height = 300,
  showLegend = true,
}: MetricsGraphProps) {
  // Prepare chart data
  const chartData = {
    labels: data.map((d) => d.timestamp),
    datasets: [
      {
        label: getMetricDisplayName(metricType),
        data: data.map((d) => d.value),
        borderColor: getMetricColor(metricType),
        backgroundColor: `${getMetricColor(metricType)}20`,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        spanGaps: false, // Show gaps as dotted lines (FR-009)
        segment: {
          borderDash: (ctx: any) => {
            // Dotted line for missing data gaps
            if (ctx.p0.skip || ctx.p1.skip) {
              return [5, 5];
            }
            return [];
          },
        },
      },
    ],
  };

  // Chart options
  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        position: 'top' as const,
      },
      tooltip: {
        enabled: true,
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: getMetricColor(metricType),
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          // Korean formatted title (FR-008)
          title: (tooltipItems) => {
            if (tooltipItems.length === 0) return '';
            const timestamp = tooltipItems[0].label;
            return formatChartLabel(timestamp, granularity);
          },
          // Korean formatted value (FR-008)
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const formattedValue = formatMetricValue(metricType, value);
            return `${label}: ${formattedValue}`;
          },
          // Show "데이터 수집 실패" for gaps (FR-009)
          footer: (tooltipItems) => {
            if (tooltipItems.length === 0) return '';
            const dataIndex = tooltipItems[0].dataIndex;
            if (dataIndex > 0) {
              const prev = data[dataIndex - 1];
              const curr = data[dataIndex];
              const prevTime = new Date(prev.timestamp).getTime();
              const currTime = new Date(curr.timestamp).getTime();
              const expectedGap = granularity === 'hourly' ? 3600000 : 86400000;

              if (currTime - prevTime > expectedGap * 1.5) {
                return '⚠️ 이 기간 동안 데이터 수집 실패';
              }
            }
            return '';
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
            // Format y-axis labels based on metric type
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
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
  };

  // Empty state (FR-021)
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300"
        style={{ height: `${height}px` }}
      >
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium">데이터 수집 중입니다</p>
          <p className="text-sm mt-2">첫 데이터는 다음 정시에 표시됩니다</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: `${height}px` }}>
      <Line data={chartData} options={options} />
    </div>
  );
}
