'use client'

/**
 * System Health Monitoring Panel
 * Real-time system health metrics
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { SystemHealth } from '@/types/admin'

export default function HealthPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user && user.is_admin) {
      loadHealth()
      // Refresh every 30 seconds
      const interval = setInterval(loadHealth, 30000)
      return () => clearInterval(interval)
    }
  }, [user])

  const loadHealth = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getHealth()
      setHealth(data)
    } catch (error) {
      console.error('Failed to load health:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (days > 0) return `${days}일 ${hours}시간`
    if (hours > 0) return `${hours}시간 ${minutes}분`
    return `${minutes}분`
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800'
      case 'unavailable':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'healthy':
        return '정상'
      case 'degraded':
        return '성능 저하'
      case 'unavailable':
        return '사용 불가'
      default:
        return '알 수 없음'
    }
  }

  const getUsageColor = (percent: number): string => {
    if (percent >= 90) return 'bg-red-500'
    if (percent >= 75) return 'bg-yellow-500'
    return 'bg-green-500'
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
        <div>
          <button
            onClick={() => router.push('/admin')}
            className="mb-2 text-sm text-blue-600 hover:underline"
          >
            ← 대시보드로 돌아가기
          </button>
          <h1 className="text-2xl font-bold text-gray-900">시스템 상태</h1>
          <p className="text-sm text-gray-500">실시간 시스템 건강 모니터링</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {loading ? (
            <div className="rounded-lg bg-white p-8 text-center shadow-sm">
              <div className="text-gray-500">시스템 상태 확인 중...</div>
            </div>
          ) : health ? (
            <>
              {/* Server Status */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">서버 상태</h2>
                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <p className="mb-1 text-sm text-gray-500">가동 시간</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatUptime(health.server_uptime_seconds)}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="mb-2 text-sm text-gray-500">LLM 서비스</p>
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getStatusColor(health.llm_service_status)}`}
                      >
                        {getStatusText(health.llm_service_status)}
                      </span>
                    </div>
                    <div>
                      <p className="mb-2 text-sm text-gray-500">데이터베이스</p>
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getStatusColor(health.database_status)}`}
                      >
                        {getStatusText(health.database_status)}
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Resource Usage */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">리소스 사용량</h2>
                <div className="space-y-6">
                  {/* CPU */}
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">CPU 사용률</span>
                      <span className="text-sm font-bold text-gray-900">
                        {health.cpu_usage_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full ${getUsageColor(health.cpu_usage_percent)}`}
                        style={{ width: `${health.cpu_usage_percent}%` }}
                      />
                    </div>
                  </div>

                  {/* Memory */}
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">메모리 사용률</span>
                      <span className="text-sm font-bold text-gray-900">
                        {health.memory_usage_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full ${getUsageColor(health.memory_usage_percent)}`}
                        style={{ width: `${health.memory_usage_percent}%` }}
                      />
                    </div>
                  </div>

                  {/* Disk */}
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">디스크 사용률</span>
                      <span className="text-sm font-bold text-gray-900">
                        {health.disk_usage_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full ${getUsageColor(health.disk_usage_percent)}`}
                        style={{ width: `${health.disk_usage_percent}%` }}
                      />
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      사용 가능: {health.available_storage_gb.toFixed(1)} GB / 전체:{' '}
                      {health.total_storage_gb.toFixed(1)} GB
                    </p>
                  </div>
                </div>
              </section>

              {/* GPU Metrics (if available) */}
              {(health.gpu_usage_percent !== null || health.gpu_memory_usage_percent !== null) && (
                <section className="rounded-lg bg-white p-6 shadow-sm">
                  <h2 className="mb-4 text-xl font-semibold text-gray-900">GPU 상태</h2>
                  <div className="space-y-6">
                    {health.gpu_usage_percent !== null && (
                      <div>
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">GPU 사용률</span>
                          <span className="text-sm font-bold text-gray-900">
                            {health.gpu_usage_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                          <div
                            className={`h-full ${getUsageColor(health.gpu_usage_percent)}`}
                            style={{ width: `${health.gpu_usage_percent}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {health.gpu_memory_usage_percent !== null && (
                      <div>
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">GPU 메모리 사용률</span>
                          <span className="text-sm font-bold text-gray-900">
                            {health.gpu_memory_usage_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                          <div
                            className={`h-full ${getUsageColor(health.gpu_memory_usage_percent)}`}
                            style={{ width: `${health.gpu_memory_usage_percent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {/* Last Updated */}
              <div className="text-center text-sm text-gray-500">
                자동 갱신: 30초마다 • 마지막 업데이트: {new Date().toLocaleTimeString('ko-KR')}
              </div>
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}
