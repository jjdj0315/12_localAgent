'use client'

/**
 * Admin Dashboard Home Page
 * Overview of system statistics and quick actions
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { UsageStats } from '@/types/admin'

export default function AdminDashboard() {
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
            <div className="grid gap-4 md:grid-cols-2">
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
                onClick={() => router.push('/admin/stats')}
                className="rounded-lg border-2 border-gray-200 bg-white p-6 text-left transition-all hover:border-green-500 hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-green-100 p-3">
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
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">사용 통계</h3>
                    <p className="text-sm text-gray-500">활성 사용자, 쿼리 수, 응답 시간</p>
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
                    <h3 className="font-semibold text-gray-900">시스템 상태</h3>
                    <p className="text-sm text-gray-500">CPU, 메모리, 디스크, GPU 사용량</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => router.push('/admin/storage')}
                className="rounded-lg border-2 border-gray-200 bg-white p-6 text-left transition-all hover:border-orange-500 hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-orange-100 p-3">
                    <svg
                      className="h-6 w-6 text-orange-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">스토리지 관리</h3>
                    <p className="text-sm text-gray-500">사용자별 용량 및 전체 스토리지</p>
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
        </div>
      </main>
    </div>
  )
}
