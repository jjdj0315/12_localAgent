/**
 * Tool Statistics Component
 *
 * Admin interface for viewing ReAct tool usage analytics.
 * Per FR-069: Display per-tool usage, avg time, error rate.
 */

'use client';

import React, { useState, useEffect } from 'react';

interface ToolStat {
  tool_id: string;
  tool_name: string;
  display_name: string;
  category: string;
  is_active: boolean;
  usage_count: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  last_used_at: string | null;
}

interface StatisticsResponse {
  statistics: ToolStat[];
  total_executions: number;
  total_tools: number;
  overall_success_rate: number;
  time_period_days: number;
}

export default function ToolStatistics() {
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [timePeriod, setTimePeriod] = useState<number>(7);
  const [sortBy, setSortBy] = useState<'usage' | 'success_rate' | 'avg_time'>('usage');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadStatistics();
  }, [timePeriod]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/admin/tools/stats/overview?days=${timePeriod}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const sortedStats = stats?.statistics.slice().sort((a, b) => {
    let aVal: number, bVal: number;

    switch (sortBy) {
      case 'usage':
        aVal = a.usage_count;
        bVal = b.usage_count;
        break;
      case 'success_rate':
        aVal = a.success_rate;
        bVal = b.success_rate;
        break;
      case 'avg_time':
        aVal = a.avg_execution_time_ms;
        bVal = b.avg_execution_time_ms;
        break;
      default:
        return 0;
    }

    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const handleSort = (column: 'usage' | 'success_rate' | 'avg_time') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const formatLastUsed = (timestamp: string | null) => {
    if (!timestamp) return '사용 이력 없음';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString('ko-KR');
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600 bg-green-50';
    if (rate >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getPerformanceColor = (ms: number) => {
    if (ms < 1000) return 'text-green-600';
    if (ms < 5000) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return <div className="p-4">통계 로딩 중...</div>;
  }

  if (!stats) {
    return <div className="p-4">통계를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">도구 사용 통계</h2>

        {/* Time Period Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">기간:</span>
          <div className="flex space-x-1">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimePeriod(days)}
                className={`px-3 py-1 text-sm rounded ${
                  timePeriod === days
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {days}일
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">전체 실행 횟수</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {stats.total_executions.toLocaleString()}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">활성 도구</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {stats.statistics.filter((s) => s.is_active).length} / {stats.total_tools}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">전체 성공률</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              stats.overall_success_rate >= 90
                ? 'text-green-600'
                : stats.overall_success_rate >= 70
                ? 'text-yellow-600'
                : 'text-red-600'
            }`}
          >
            {stats.overall_success_rate.toFixed(1)}%
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">평균 실행 시간</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {stats.statistics.length > 0
              ? Math.round(
                  stats.statistics.reduce((sum, s) => sum + s.avg_execution_time_ms, 0) /
                    stats.statistics.length
                )
              : 0}
            ms
          </div>
        </div>
      </div>

      {/* Tool Statistics Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                도구명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                카테고리
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('usage')}
              >
                사용 횟수 {sortBy === 'usage' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('success_rate')}
              >
                성공률 {sortBy === 'success_rate' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('avg_time')}
              >
                평균 시간 {sortBy === 'avg_time' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                마지막 사용
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                상태
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedStats?.map((stat) => (
              <tr key={stat.tool_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">{stat.display_name}</div>
                  <div className="text-sm text-gray-500">{stat.tool_name}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{stat.category}</td>
                <td className="px-6 py-4 text-sm text-right text-gray-900">
                  <div>{stat.usage_count.toLocaleString()}</div>
                  <div className="text-xs text-gray-500">
                    성공 {stat.success_count} / 실패 {stat.error_count}
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSuccessRateColor(
                      stat.success_rate
                    )}`}
                  >
                    {stat.success_rate.toFixed(1)}%
                  </span>
                </td>
                <td className={`px-6 py-4 text-sm text-right font-mono ${getPerformanceColor(stat.avg_execution_time_ms)}`}>
                  {stat.avg_execution_time_ms}ms
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {formatLastUsed(stat.last_used_at)}
                </td>
                <td className="px-6 py-4 text-center">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      stat.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {stat.is_active ? '활성' : '비활성'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {sortedStats?.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            선택한 기간 동안 도구 사용 이력이 없습니다.
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="text-xs text-gray-500">
        <p>• 성공률: 녹색(90% 이상), 노란색(70-90%), 빨간색(70% 미만)</p>
        <p>• 평균 시간: 녹색(1초 미만), 노란색(1-5초), 빨간색(5초 이상)</p>
        <p>• 통계는 최근 {stats.time_period_days}일 기준입니다.</p>
      </div>
    </div>
  );
}
