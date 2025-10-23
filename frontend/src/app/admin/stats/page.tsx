'use client'

/**
 * Usage Statistics Dashboard
 * Detailed view of system usage metrics
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { UsageStats } from '@/types/admin'

export default function StatsPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user && user.is_admin) {
      loadStats()
      // Refresh every 30 seconds
      const interval = setInterval(loadStats, 30000)
      return () => clearInterval(interval)
    }
  }, [user])

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
          <h1 className="text-2xl font-bold text-gray-900">사용 통계</h1>
          <p className="text-sm text-gray-500">시스템 사용량 및 성능 지표</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {loading ? (
            <div className="rounded-lg bg-white p-8 text-center shadow-sm">
              <div className="text-gray-500">통계 로딩 중...</div>
            </div>
          ) : stats ? (
            <>
              {/* Active Users */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-full bg-blue-100 p-2">
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
                  <h2 className="text-xl font-semibold text-gray-900">활성 사용자</h2>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">오늘</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.active_users_today}</p>
                    <p className="mt-1 text-xs text-gray-400">활성 사용자</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 주</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.active_users_week}</p>
                    <p className="mt-1 text-xs text-gray-400">활성 사용자</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 달</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.active_users_month}</p>
                    <p className="mt-1 text-xs text-gray-400">활성 사용자</p>
                  </div>
                </div>
              </section>

              {/* Query Volume */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-2">
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
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900">처리된 쿼리</h2>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">오늘</p>
                    <p className="text-3xl font-bold text-green-600">
                      {stats.total_queries_today}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">총 쿼리 수</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 주</p>
                    <p className="text-3xl font-bold text-green-600">
                      {stats.total_queries_week}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">총 쿼리 수</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 달</p>
                    <p className="text-3xl font-bold text-green-600">
                      {stats.total_queries_month}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">총 쿼리 수</p>
                  </div>
                </div>
              </section>

              {/* Response Times */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-full bg-purple-100 p-2">
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
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900">평균 응답 시간</h2>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">오늘</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {stats.avg_response_time_today.toFixed(0)}
                      <span className="text-lg">ms</span>
                    </p>
                    <p className="mt-1 text-xs text-gray-400">평균 응답 시간</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 주</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {stats.avg_response_time_week.toFixed(0)}
                      <span className="text-lg">ms</span>
                    </p>
                    <p className="mt-1 text-xs text-gray-400">평균 응답 시간</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="mb-1 text-sm text-gray-500">이번 달</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {stats.avg_response_time_month.toFixed(0)}
                      <span className="text-lg">ms</span>
                    </p>
                    <p className="mt-1 text-xs text-gray-400">평균 응답 시간</p>
                  </div>
                </div>
              </section>

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
