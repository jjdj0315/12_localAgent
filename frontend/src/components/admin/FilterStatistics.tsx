/**
 * Filter Statistics Component
 *
 * Displays safety filter usage statistics and metrics.
 * Shows:
 * - Total events and trends
 * - Events by category
 * - Top triggered rules
 * - Average processing time
 * - Bypass attempt rate
 */

'use client';

import React, { useState, useEffect } from 'react';

interface FilterStats {
  total_events: number;
  events_today: number;
  events_this_week: number;
  by_category: CategoryStat[];
  top_triggered_rules: RuleStat[];
  avg_processing_time_ms: number;
  bypass_attempt_rate: number;
}

interface CategoryStat {
  category: string;
  total_count: number;
  blocked_count: number;
  masked_count: number;
  warned_count: number;
}

interface RuleStat {
  rule_id: string;
  rule_name: string;
  category: string;
  count: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  violence: '폭력성',
  sexual: '성적 내용',
  dangerous: '위험 정보',
  hate: '혐오 발언',
  pii: '개인정보',
  toxic: '유해 콘텐츠'
};

export default function FilterStatistics() {
  const [stats, setStats] = useState<FilterStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(7); // days

  useEffect(() => {
    loadStats();
  }, [timeRange]);

  const loadStats = async () => {
    try {
      const response = await fetch(
        `/api/v1/admin/safety-filter/stats?days=${timeRange}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12 text-gray-500">
        통계를 불러올 수 없습니다
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">필터 통계</h2>
          <p className="text-gray-600 mt-1">
            안전 필터 사용 현황 및 성능 지표
          </p>
        </div>

        {/* Time Range Selector */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value={1}>최근 1일</option>
          <option value={7}>최근 7일</option>
          <option value={30}>최근 30일</option>
          <option value={90}>최근 90일</option>
        </select>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">전체 이벤트</div>
          <div className="text-3xl font-bold text-gray-900">
            {stats.total_events.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-2">
            오늘: {stats.events_today}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">기간 내 이벤트</div>
          <div className="text-3xl font-bold text-blue-600">
            {stats.events_this_week.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-2">
            최근 {timeRange}일
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">평균 처리 시간</div>
          <div className="text-3xl font-bold text-green-600">
            {stats.avg_processing_time_ms.toFixed(0)}ms
          </div>
          <div className="text-xs text-gray-500 mt-2">
            {stats.avg_processing_time_ms < 2000 ? '✓ 목표 달성' : '⚠ 목표 초과'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">우회 시도율</div>
          <div className="text-3xl font-bold text-orange-600">
            {stats.bypass_attempt_rate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 mt-2">
            전체 대비 비율
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          카테고리별 현황
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  카테고리
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  전체
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  차단
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  마스킹
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  경고
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  차단율
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats.by_category.map((cat) => {
                const blockRate = cat.total_count > 0
                  ? (cat.blocked_count / cat.total_count * 100)
                  : 0;

                return (
                  <tr key={cat.category} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {CATEGORY_LABELS[cat.category] || cat.category}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {cat.total_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-red-600">
                      {cat.blocked_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-blue-600">
                      {cat.masked_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-yellow-600">
                      {cat.warned_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {blockRate.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {stats.by_category.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              이벤트가 없습니다
            </div>
          )}
        </div>
      </div>

      {/* Top Triggered Rules */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          가장 많이 작동한 규칙 (Top 10)
        </h3>
        <div className="space-y-3">
          {stats.top_triggered_rules.map((rule, index) => (
            <div
              key={rule.rule_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                  {index + 1}
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-900">
                    {rule.rule_name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {CATEGORY_LABELS[rule.category] || rule.category}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-gray-900">
                  {rule.count.toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">회</div>
              </div>
            </div>
          ))}

          {stats.top_triggered_rules.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              작동한 규칙이 없습니다
            </div>
          )}
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          성능 지표
        </h3>
        <div className="space-y-4">
          {/* Processing Time */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">평균 처리 시간</span>
              <span className="text-sm font-semibold text-gray-900">
                {stats.avg_processing_time_ms.toFixed(0)}ms / 2000ms
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  stats.avg_processing_time_ms < 2000
                    ? 'bg-green-600'
                    : 'bg-red-600'
                }`}
                style={{
                  width: `${Math.min((stats.avg_processing_time_ms / 2000) * 100, 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              목표: 2초 이내 (FR-082, SC-014)
            </p>
          </div>

          {/* Bypass Rate */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">우회 시도율</span>
              <span className="text-sm font-semibold text-gray-900">
                {stats.bypass_attempt_rate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-orange-600"
                style={{ width: `${Math.min(stats.bypass_attempt_rate, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              False positive 발생 시 사용자가 우회 시도
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
