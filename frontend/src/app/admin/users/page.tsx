'use client'

/**
 * User Management Page
 * Create, list, delete users and reset passwords
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { adminAPI } from '@/lib/api'
import type { User, UserListResponse, PasswordResetResponse } from '@/types/admin'

export default function UserManagementPage() {
  const { user: currentUser, loading: authLoading } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetResult, setResetResult] = useState<PasswordResetResponse | null>(null)

  // Form state
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isAdmin, setIsAdmin] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    if (!authLoading && (!currentUser || !currentUser.is_admin)) {
      router.push('/login')
    }
  }, [currentUser, authLoading, router])

  useEffect(() => {
    if (currentUser && currentUser.is_admin) {
      loadUsers()
    }
  }, [currentUser])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const data: UserListResponse = await adminAPI.listUsers({ page: 1, page_size: 50 })
      setUsers(data.users)
      setTotal(data.total)
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')

    if (username.length < 3) {
      setFormError('사용자명은 최소 3자 이상이어야 합니다.')
      return
    }

    if (password.length < 8) {
      setFormError('비밀번호는 최소 8자 이상이어야 합니다.')
      return
    }

    try {
      await adminAPI.createUser({
        username,
        password,
        is_admin: isAdmin,
      })

      // Reset form
      setUsername('')
      setPassword('')
      setIsAdmin(false)
      setShowCreateForm(false)
      setFormError('')

      // Reload users
      await loadUsers()
    } catch (error: any) {
      setFormError(error.message || '사용자 생성에 실패했습니다.')
    }
  }

  const handleDeleteUser = async (userId: string, userName: string) => {
    if (!confirm(`'${userName}' 사용자를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
      return
    }

    try {
      await adminAPI.deleteUser(userId)
      await loadUsers()
    } catch (error: any) {
      alert('사용자 삭제에 실패했습니다: ' + error.message)
    }
  }

  const handleResetPassword = async (userId: string) => {
    try {
      const result: PasswordResetResponse = await adminAPI.resetPassword(userId)
      setResetResult(result)
      setShowResetModal(true)
    } catch (error: any) {
      alert('비밀번호 재설정에 실패했습니다: ' + error.message)
    }
  }

  if (authLoading || !currentUser || !currentUser.is_admin) {
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
            <button
              onClick={() => router.push('/admin')}
              className="mb-2 text-sm text-blue-600 hover:underline"
            >
              ← 대시보드로 돌아가기
            </button>
            <h1 className="text-2xl font-bold text-gray-900">사용자 관리</h1>
            <p className="text-sm text-gray-500">총 {total}명의 사용자</p>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            {showCreateForm ? '취소' : '+ 사용자 생성'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Create User Form */}
          {showCreateForm && (
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">새 사용자 생성</h2>
              <form onSubmit={handleCreateUser} className="space-y-4">
                {formError && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">{formError}</div>
                )}

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    사용자명 *
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="최소 3자"
                    required
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    초기 비밀번호 *
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="최소 8자"
                    required
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isAdmin"
                    checked={isAdmin}
                    onChange={(e) => setIsAdmin(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="isAdmin" className="ml-2 text-sm text-gray-700">
                    관리자 권한 부여
                  </label>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
                  >
                    생성
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateForm(false)
                      setFormError('')
                      setUsername('')
                      setPassword('')
                      setIsAdmin(false)
                    }}
                    className="rounded-md bg-gray-200 px-4 py-2 text-sm text-gray-700 hover:bg-gray-300"
                  >
                    취소
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* User List */}
          <div className="rounded-lg bg-white shadow-sm">
            <div className="border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">사용자 목록</h2>
            </div>

            {loading ? (
              <div className="p-8 text-center text-gray-500">로딩 중...</div>
            ) : users.length === 0 ? (
              <div className="p-8 text-center text-gray-500">사용자가 없습니다.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        사용자명
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        권한
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        생성일
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        마지막 로그인
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                        작업
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-6 py-4">
                          <div className="font-medium text-gray-900">{user.username}</div>
                          <div className="text-xs text-gray-500">{user.id}</div>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          {user.is_admin ? (
                            <span className="inline-flex rounded-full bg-purple-100 px-2 py-1 text-xs font-semibold text-purple-800">
                              관리자
                            </span>
                          ) : (
                            <span className="inline-flex rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-800">
                              일반 사용자
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {new Date(user.created_at).toLocaleDateString('ko-KR')}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {user.last_login_at
                            ? new Date(user.last_login_at).toLocaleDateString('ko-KR')
                            : '없음'}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                          <button
                            onClick={() => handleResetPassword(user.id)}
                            className="mr-3 text-blue-600 hover:text-blue-900"
                          >
                            비밀번호 재설정
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            className="text-red-600 hover:text-red-900"
                            disabled={user.id === currentUser.id}
                          >
                            삭제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Password Reset Modal */}
      {showResetModal && resetResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="mx-4 max-w-md rounded-lg bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-center rounded-full bg-green-100 p-3 w-12 h-12 mx-auto">
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
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>

            <h3 className="mb-2 text-center text-lg font-semibold text-gray-900">
              비밀번호 재설정 완료
            </h3>

            <p className="mb-4 text-center text-sm text-gray-600">{resetResult.message}</p>

            <div className="mb-4 rounded-md bg-yellow-50 p-4">
              <p className="mb-2 text-sm font-medium text-yellow-800">임시 비밀번호:</p>
              <div className="flex items-center justify-between rounded bg-white px-3 py-2">
                <code className="text-sm font-mono text-gray-900">
                  {resetResult.temporary_password}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(resetResult.temporary_password)
                    alert('클립보드에 복사되었습니다.')
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  복사
                </button>
              </div>
              <p className="mt-2 text-xs text-yellow-700">
                ⚠️ 이 비밀번호를 사용자에게 전달하세요. 창을 닫으면 다시 확인할 수 없습니다.
              </p>
            </div>

            <button
              onClick={() => {
                setShowResetModal(false)
                setResetResult(null)
              }}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
