/**
 * Agent Statistics Component
 *
 * Displays performance metrics for Multi-Agent system.
 * Features:
 * - Usage counts per agent (FR-076)
 * - Success/error rates
 * - Average execution times
 * - Workflow type distribution
 */

'use client';

import React, { useState, useEffect } from 'react';

interface AgentStat {
  agent_id: string;
  agent_name: string;
  display_name: string;
  category: string;
  is_active: boolean;
  usage_count: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  last_used_at?: string;
}

interface WorkflowStat {
  workflow_type: string;
  count: number;
  avg_execution_time_ms: number;
  success_rate: number;
}

interface StatisticsResponse {
  agent_statistics: AgentStat[];
  workflow_statistics: WorkflowStat[];
  total_executions: number;
  overall_success_rate: number;
  time_period_days: number;
}

// Agent icon mapping
const AGENT_ICONS: Record<string, string> = {
  citizen_support: '🙋',
  document_writing: '📝',
  legal_research: '⚖️',
  data_analysis: '📊',
  review: '✅',
};

// Workflow type labels
const WORKFLOW_LABELS: Record<string, string> = {
  single: '단일',
  sequential: '순차',
  parallel: '병렬',
};

export default function AgentStatistics() {
  const [statistics, setStatistics] = useState<StatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [timePeriod, setTimePeriod] = useState(7); // days

  useEffect(() => {
    loadStatistics();
  }, [timePeriod]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/admin/agents/stats?days=${timePeriod}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="text-center p-8 text-gray-500">
        통계를 불러올 수 없습니다.
      </div>
    );
  }

  // Sort agents by usage count
  const sortedAgents = [...statistics.agent_statistics].sort(
    (a, b) => b.usage_count - a.usage_count
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">에이전트 통계</h2>
          <p className="mt-1 text-sm text-gray-600">
            Multi-Agent 시스템 성능 메트릭 및 사용 현황
          </p>
        </div>

        {/* Time Period Selector */}
        <select
          value={timePeriod}
          onChange={(e) => setTimePeriod(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={1}>최근 1일</option>
          <option value={7}>최근 7일</option>
          <option value={30}>최근 30일</option>
          <option value={90}>최근 90일</option>
        </select>
      </div>

      {/* Overall Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-100 rounded-lg p-3">
              <svg
                className="h-6 w-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 실행 횟수</p>
              <p className="text-2xl font-bold text-gray-900">
                {statistics.total_executions.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-100 rounded-lg p-3">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">전체 성공률</p>
              <p className="text-2xl font-bold text-gray-900">
                {statistics.overall_success_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-purple-100 rounded-lg p-3">
              <svg
                className="h-6 w-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">활성 에이전트</p>
              <p className="text-2xl font-bold text-gray-900">
                {statistics.agent_statistics.filter((a) => a.is_active).length} /{' '}
                {statistics.agent_statistics.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Performance Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">에이전트별 성능</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  에이전트
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  사용 횟수
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  성공률
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  평균 시간
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  마지막 사용
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedAgents.map((agent) => {
                const icon = AGENT_ICONS[agent.category] || '🤖';

                return (
                  <tr key={agent.agent_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{icon}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {agent.display_name}
                          </div>
                          <div className="text-xs text-gray-500">{agent.agent_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          agent.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {agent.is_active ? '활성화' : '비활성화'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {agent.usage_count.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className={`h-2 rounded-full ${
                              agent.success_rate >= 90
                                ? 'bg-green-500'
                                : agent.success_rate >= 70
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${agent.success_rate}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-900">
                          {agent.success_rate.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {(agent.avg_execution_time_ms / 1000).toFixed(2)}초
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      {agent.last_used_at
                        ? new Date(agent.last_used_at).toLocaleDateString('ko-KR')
                        : '미사용'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Workflow Statistics */}
      {statistics.workflow_statistics && statistics.workflow_statistics.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">워크플로 타입별 통계</h3>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {statistics.workflow_statistics.map((workflow) => (
                <div
                  key={workflow.workflow_type}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-gray-900">
                      {WORKFLOW_LABELS[workflow.workflow_type] || workflow.workflow_type}
                    </h4>
                    <span className="text-xs text-gray-500">{workflow.count}회</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">성공률:</span>
                      <span className="font-medium text-gray-900">
                        {workflow.success_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">평균 시간:</span>
                      <span className="font-medium text-gray-900">
                        {(workflow.avg_execution_time_ms / 1000).toFixed(2)}초
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
