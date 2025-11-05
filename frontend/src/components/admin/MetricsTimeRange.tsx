'use client';

/**
 * MetricsTimeRange component - Time range selector with presets (FR-017)
 */

import React from 'react';
import { TIME_RANGE_PRESETS, getPresetDateRange } from '@/lib/chartUtils';

interface MetricsTimeRangeProps {
  selectedDays: number;
  onRangeChange: (days: number) => void;
}

export default function MetricsTimeRange({
  selectedDays,
  onRangeChange,
}: MetricsTimeRangeProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium text-gray-700">기간:</span>
      <div className="flex gap-2">
        {TIME_RANGE_PRESETS.map((preset) => (
          <button
            key={preset.days}
            onClick={() => onRangeChange(preset.days)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedDays === preset.days
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
