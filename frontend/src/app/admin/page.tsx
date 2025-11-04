'use client'

/**
 * Admin Dashboard Home Page
 * Overview of system statistics and quick actions with metrics history
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { UsageStats } from '@/types/admin'
import MetricsGraph from '@/components/admin/MetricsGraph'
import MetricsComparison from '@/components/admin/MetricsComparison'
import MetricsTimeRange from '@/components/admin/MetricsTimeRange'
import MetricsGranularityToggle from '@/components/admin/MetricsGranularityToggle'
import MetricsExport from '@/components/admin/MetricsExport'
import {
  getMetricsTimeSeries,
  getCurrentMetrics,
  getCollectionStatus,
} from '@/lib/metricsApi'
import {
  downsampleMetrics,
  getPresetDateRange,
  formatMetricValue,
  getMetricDisplayName,
  COMPARISON_PRESETS,
  getComparisonDateRanges,
} from '@/lib/chartUtils'
import type { MetricType, MetricGranularity, MetricSnapshot } from '@/types/metrics'

const METRIC_TYPES: MetricType[] = [
  'active_users',
  'storage_bytes',
  'active_sessions',
  'conversation_count',
  'document_count',
  'tag_count',
]

export default function AdminDashboard() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(true)

  // Metrics state
  const [metricsViewMode, setMetricsViewMode] = useState<'normal' | 'comparison'>('normal')
  const [selectedDays, setSelectedDays] = useState(7)
  const [granularity, setGranularity] = useState<MetricGranularity>('hourly')
  const [comparisonPreset, setComparisonPreset] = useState<'week' | 'month'>('week')
  const [metricsData, setMetricsData] = useState<Record<MetricType, MetricSnapshot[]>>({
    active_users: [],
    storage_bytes: [],
    active_sessions: [],
    conversation_count: [],
    document_count: [],
    tag_count: [],
  })
  const [currentValues, setCurrentValues] = useState<Record<string, number | null>>({})
  const [collectionStatus, setCollectionStatus] = useState<{
    status: 'healthy' | 'degraded'
    last_collection_at: string | null
    next_collection_at: string
    failure_count_24h: number
  } | null>(null)
  const [metricsLoading, setMetricsLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user && user.is_admin) {
      loadStats()
      loadMetrics()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  useEffect(() => {
    if (user && user.is_admin) {
      loadMetrics()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDays, granularity, user])

  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      setMetricsLoading(true)
      const { start, end } = getPresetDateRange(selectedDays)

      // Fetch time series for all metrics in parallel
      const promises = METRIC_TYPES.map(async (metricType) => {
        try {
          const data = await getMetricsTimeSeries(metricType, granularity, start, end)
          const downsampled = downsampleMetrics(data, 1000)
          return { metricType, data: downsampled }
        } catch (err) {
          console.error(`Failed to fetch ${metricType}:`, err)
          return { metricType, data: [] }
        }
      })

      const results = await Promise.all(promises)

      const newMetricsData: Record<MetricType, MetricSnapshot[]> = {
        active_users: [],
        storage_bytes: [],
        active_sessions: [],
        conversation_count: [],
        document_count: [],
        tag_count: [],
      }

      results.forEach(({ metricType, data }) => {
        newMetricsData[metricType] = data
      })

      setMetricsData(newMetricsData)

      // Fetch current values
      const currentData = await getCurrentMetrics()
      const currentValuesMap: Record<string, number | null> = {}
      currentData.metrics.forEach((m) => {
        currentValuesMap[m.metric_type] = m.value
      })
      setCurrentValues(currentValuesMap)

      // Fetch collection status
      const status = await getCollectionStatus()
      setCollectionStatus(status)
    } catch (err) {
      console.error('Failed to fetch metrics:', err)
    } finally {
      setMetricsLoading(false)
    }
  }

  if (authLoading || !user || !user.is_admin) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">관리자 대시보드</h1>
            <p className="text-sm text-gray-500">시스템 통계 및 사용자 관리</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user.username} (관리자)</span>
            <button
              onClick={() => router.push('/chat')}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              채팅으로 이동
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Quick Actions */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">빠른 작업</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <button
                onClick={() => router.push('/admin/users')}
                className="rounded-lg border-2 border-gray-200 bg-white p-6 text-left transition-all hover:border-blue-500 hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-blue-100 p-3">
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
                        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">사용자 관리</h3>
                    <p className="text-sm text-gray-500">사용자 생성, 삭제, 비밀번호 재설정</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => router.push('/admin/health')}
                className="rounded-lg border-2 border-gray-200 bg-white p-6 text-left transition-all hover:border-purple-500 hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-purple-100 p-3">
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
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">시스템 상태 및 관리</h3>
                    <p className="text-sm text-gray-500">CPU, 메모리, 디스크, GPU, 스토리지</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => router.push('/admin/advanced-features')}
                className="rounded-lg border-2 border-gray-200 bg-white p-6 text-left transition-all hover:border-indigo-500 hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-indigo-100 p-3">
                    <svg
                      className="h-6 w-6 text-indigo-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">고급 기능</h3>
                    <p className="text-sm text-gray-500">감사 로그, 템플릿, 에이전트 설정</p>
                  </div>
                </div>
              </button>
            </div>
          </section>

          {/* Statistics Overview */}
          {loading ? (
            <div className="rounded-lg bg-white p-8 text-center shadow-sm">
              <div className="text-gray-500">통계 로딩 중...</div>
            </div>
          ) : stats ? (
            <section>
              <h2 className="mb-4 text-lg font-semibold text-gray-900">시스템 통계</h2>
              <div className="grid gap-4 md:grid-cols-3">
                {/* Active Users */}
                <div className="rounded-lg bg-white p-6 shadow-sm">
                  <h3 className="mb-2 text-sm font-medium text-gray-500">활성 사용자</h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{stats.active_users_today}</p>
                      <p className="text-xs text-gray-500">오늘</p>
                    </div>
                    <div className="flex gap-4 text-sm">
                      <div>
                        <p className="font-semibold text-gray-700">{stats.active_users_week}</p>
                        <p className="text-xs text-gray-500">이번 주</p>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700">{stats.active_users_month}</p>
                        <p className="text-xs text-gray-500">이번 달</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Total Queries */}
                <div className="rounded-lg bg-white p-6 shadow-sm">
                  <h3 className="mb-2 text-sm font-medium text-gray-500">처리된 쿼리</h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_queries_today}</p>
                      <p className="text-xs text-gray-500">오늘</p>
                    </div>
                    <div className="flex gap-4 text-sm">
                      <div>
                        <p className="font-semibold text-gray-700">{stats.total_queries_week}</p>
                        <p className="text-xs text-gray-500">이번 주</p>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700">{stats.total_queries_month}</p>
                        <p className="text-xs text-gray-500">이번 달</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Average Response Time */}
                <div className="rounded-lg bg-white p-6 shadow-sm">
                  <h3 className="mb-2 text-sm font-medium text-gray-500">평균 응답 시간</h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-2xl font-bold text-gray-900">
                        {stats.avg_response_time_today.toFixed(0)}ms
                      </p>
                      <p className="text-xs text-gray-500">오늘</p>
                    </div>
                    <div className="flex gap-4 text-sm">
                      <div>
                        <p className="font-semibold text-gray-700">
                          {stats.avg_response_time_week.toFixed(0)}ms
                        </p>
                        <p className="text-xs text-gray-500">이번 주</p>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700">
                          {stats.avg_response_time_month.toFixed(0)}ms
                        </p>
                        <p className="text-xs text-gray-500">이번 달</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          {/* Metrics History Section */}
          <section>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">시스템 메트릭 히스토리</h2>

              {/* Controls */}
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-4">
                {/* View Mode Toggle */}
                <div className="mb-4 flex items-center gap-4 pb-4 border-b border-gray-200">
                  <span className="text-sm font-medium text-gray-700">보기 모드:</span>
                  <div className="inline-flex rounded-lg border border-gray-300 bg-gray-50 p-1">
                    <button
                      onClick={() => setMetricsViewMode('normal')}
                      className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                        metricsViewMode === 'normal'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      일반
                    </button>
                    <button
                      onClick={() => setMetricsViewMode('comparison')}
                      className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                        metricsViewMode === 'comparison'
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
                  {metricsViewMode === 'normal' ? (
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

              {/* Collection Status Widget */}
              {collectionStatus && (
                <div
                  className={`mb-4 p-4 rounded-lg border ${
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
            </div>

            {metricsLoading ? (
              <div className="rounded-lg bg-white p-8 text-center shadow-sm">
                <div className="text-gray-500">메트릭 데이터 로딩 중...</div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  {METRIC_TYPES.map((metricType) => {
                    const currentValue = currentValues[metricType]
                    const data = metricsData[metricType]

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
                          {metricsViewMode === 'normal' && (
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
                        {metricsViewMode === 'normal' ? (
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
                    )
                  })}
                </div>

                {/* Export Section */}
                {metricsViewMode === 'normal' && (
                  <div className="mt-6">
                    <MetricsExport
                      granularity={granularity}
                      startTime={getPresetDateRange(selectedDays).start}
                      endTime={getPresetDateRange(selectedDays).end}
                    />
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
