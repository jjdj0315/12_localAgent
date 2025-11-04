/**
 * MetricsCollectionStatus component - Collection health status indicator
 *
 * Displays real-time collection status with color-coded indicator (FR-106):
 * - Green: Healthy (last collection <5min, <3 failures/24h)
 * - Yellow: Degraded (3-10 failures OR 5-60min ago)
 * - Red: Critical (>10 failures OR >1hr ago)
 *
 * Feature 002: Admin Metrics History Dashboard
 */

import React, { useEffect, useState } from 'react';

interface CollectionStatus {
  last_collection_at: string | null;
  next_collection_at: string;
  recent_failures: Array<{
    metric_type: string;
    attempted_at: string;
    error_message: string;
  }>;
  failure_count_24h: number;
  status: 'healthy' | 'degraded';
}

interface MetricsCollectionStatusProps {
  className?: string;
}

export default function MetricsCollectionStatus({ className = '' }: MetricsCollectionStatusProps) {
  const [status, setStatus] = useState<CollectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/metrics/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('상태 조회 실패');
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '상태 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (): string => {
    if (!status || !status.last_collection_at) {
      return 'bg-gray-400'; // No data yet
    }

    const lastCollection = new Date(status.last_collection_at);
    const now = new Date();
    const minutesAgo = (now.getTime() - lastCollection.getTime()) / (1000 * 60);

    // Red: >10 failures OR >1hr ago
    if (status.failure_count_24h > 10 || minutesAgo > 60) {
      return 'bg-red-500';
    }

    // Yellow: 3-10 failures OR 5-60min ago
    if (
      (status.failure_count_24h >= 3 && status.failure_count_24h <= 10) ||
      (minutesAgo >= 5 && minutesAgo <= 60)
    ) {
      return 'bg-yellow-500';
    }

    // Green: <5min AND <3 failures
    return 'bg-green-500';
  };

  const getStatusText = (): string => {
    if (!status || !status.last_collection_at) {
      return '데이터 수집 대기 중';
    }

    const lastCollection = new Date(status.last_collection_at);
    const now = new Date();
    const minutesAgo = Math.floor((now.getTime() - lastCollection.getTime()) / (1000 * 60));

    if (minutesAgo > 60) {
      return `수집 지연 (${Math.floor(minutesAgo / 60)}시간 전)`;
    } else if (minutesAgo > 5) {
      return `${minutesAgo}분 전 수집`;
    } else {
      return '정상 수집 중';
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="w-3 h-3 rounded-full bg-gray-300 animate-pulse" />
        <span className="text-sm text-gray-500">로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <span className="text-sm text-red-600">{error}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
      <span className="text-sm font-medium">{getStatusText()}</span>

      {status && status.failure_count_24h > 0 && (
        <span className="text-xs text-gray-500">
          (24시간 내 실패: {status.failure_count_24h}회)
        </span>
      )}

      {status && status.recent_failures.length > 0 && (
        <button
          onClick={() => alert(`최근 실패:\n${status.recent_failures.map(f => `${f.metric_type}: ${f.error_message}`).join('\n')}`)}
          className="text-xs text-blue-600 hover:underline ml-2"
        >
          상세 보기
        </button>
      )}
    </div>
  );
}
