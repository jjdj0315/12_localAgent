'use client';

/**
 * MetricsGranularityToggle component - Toggle between hourly and daily views
 */

import React from 'react';
import type { MetricGranularity } from '@/types/metrics';

interface MetricsGranularityToggleProps {
  granularity: MetricGranularity;
  onGranularityChange: (granularity: MetricGranularity) => void;
}

export default function MetricsGranularityToggle({
  granularity,
  onGranularityChange,
}: MetricsGranularityToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium text-gray-700">세분성:</span>
      <div className="inline-flex rounded-lg border border-gray-300 bg-white p-1">
        <button
          onClick={() => onGranularityChange('hourly')}
          className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
            granularity === 'hourly'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          시간별
        </button>
        <button
          onClick={() => onGranularityChange('daily')}
          className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
            granularity === 'daily'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          일별
        </button>
      </div>
    </div>
  );
}
