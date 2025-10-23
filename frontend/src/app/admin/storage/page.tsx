'use client'

/**
 * Storage Usage Page
 * Per-user storage breakdown and total capacity monitoring
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { StorageStats } from '@/types/admin'

export default function StoragePage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [storage, setStorage] = useState<StorageStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user && user.is_admin) {
      loadStorage()
    }
  }, [user])

  const loadStorage = async () => {
    try {
      setLoading(true)
      const data = await adminAPI.getStorage()
      setStorage(data)
    } catch (error) {
      console.error('Failed to load storage:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
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
          <h1 className="text-2xl font-bold text-gray-900">스토리지 사용량</h1>
          <p className="text-sm text-gray-500">사용자별 스토리지 분석 및 용량 관리</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {loading ? (
            <div className="rounded-lg bg-white p-8 text-center shadow-sm">
              <div className="text-gray-500">스토리지 정보 로딩 중...</div>
            </div>
          ) : storage ? (
            <>
              {/* Total Storage Overview */}
              <section className="rounded-lg bg-white p-6 shadow-sm">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">전체 스토리지</h2>

                {/* Warning/Critical Alerts */}
                {storage.critical_threshold_exceeded && (
                  <div className="mb-4 rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <svg
                        className="h-5 w-5 text-red-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">
                          ⚠️ 위험: 스토리지 공간 부족
                        </h3>
                        <p className="mt-1 text-sm text-red-700">
                          스토리지 사용량이 95%를 초과했습니다. 즉시 조치가 필요합니다.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {storage.warning_threshold_exceeded && !storage.critical_threshold_exceeded && (
                  <div className="mb-4 rounded-md bg-yellow-50 p-4">
                    <div className="flex">
                      <svg
                        className="h-5 w-5 text-yellow-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-yellow-800">
                          경고: 스토리지 공간 부족
                        </h3>
                        <p className="mt-1 text-sm text-yellow-700">
                          스토리지 사용량이 80%를 초과했습니다. 공간 확보를 권장합니다.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Storage Bar */}
                <div className="mb-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">전체 사용량</span>
                    <span className="text-sm font-bold text-gray-900">
                      {storage.usage_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className={`h-full ${
                        storage.critical_threshold_exceeded
                          ? 'bg-red-500'
                          : storage.warning_threshold_exceeded
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${storage.usage_percent}%` }}
                    />
                  </div>
                  <div className="mt-2 flex justify-between text-sm text-gray-500">
                    <span>사용: {formatBytes(storage.total_storage_used_bytes)}</span>
                    <span>여유: {formatBytes(storage.total_storage_available_bytes)}</span>
                  </div>
                </div>
              </section>

              {/* Per-User Storage */}
              <section className="rounded-lg bg-white shadow-sm">
                <div className="border-b px-6 py-4">
                  <h2 className="text-lg font-semibold text-gray-900">사용자별 스토리지</h2>
                </div>

                {storage.user_storage.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    스토리지 사용 내역이 없습니다.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                            사용자명
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                            문서 수
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                            대화 수
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                            사용량
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 bg-white">
                        {storage.user_storage
                          .sort((a, b) => b.total_storage_bytes - a.total_storage_bytes)
                          .map((userStorage) => (
                            <tr key={userStorage.user_id} className="hover:bg-gray-50">
                              <td className="whitespace-nowrap px-6 py-4">
                                <div className="font-medium text-gray-900">
                                  {userStorage.username}
                                </div>
                                <div className="text-xs text-gray-500">{userStorage.user_id}</div>
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                                {userStorage.document_count}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                                {userStorage.conversation_count}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-right">
                                <div className="text-sm font-medium text-gray-900">
                                  {formatBytes(userStorage.total_storage_bytes)}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {storage.total_storage_used_bytes > 0
                                    ? (
                                        (userStorage.total_storage_bytes /
                                          storage.total_storage_used_bytes) *
                                        100
                                      ).toFixed(1)
                                    : 0}
                                  %
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}
