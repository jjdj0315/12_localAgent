"use client";

import React, { useState, useEffect } from 'react';

interface User {
  id: string;
  username: string;
  email?: string;
  is_active: boolean;
  is_locked: boolean;
  locked_until?: string;
  last_login?: string;
  created_at: string;
  failed_login_attempts?: number;
}

interface UserManagementProps {
  apiBaseUrl?: string;
}

export default function UserManagement({ apiBaseUrl = '/api/v1' }: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unlockingUserId, setUnlockingUserId] = useState<string | null>(null);

  // Fetch users from API
  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiBaseUrl}/admin/users`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '사용자 목록을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Unlock user account (FR-031)
  const unlockAccount = async (userId: string, username: string) => {
    if (!confirm(`${username} 계정의 잠금을 해제하시겠습니까?`)) {
      return;
    }

    try {
      setUnlockingUserId(userId);

      const response = await fetch(`${apiBaseUrl}/admin/users/${userId}/lockout`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      // Success - refresh user list
      alert(`${username} 계정의 잠금이 해제되었습니다.`);
      await fetchUsers();
    } catch (err) {
      alert(`잠금 해제 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
    } finally {
      setUnlockingUserId(null);
    }
  };

  // Load users on mount
  useEffect(() => {
    fetchUsers();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">사용자 목록 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">⚠️ {error}</p>
        <button
          onClick={fetchUsers}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">사용자 관리</h2>
        <button
          onClick={fetchUsers}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          새로고침
        </button>
      </div>

      {users.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600">등록된 사용자가 없습니다.</p>
        </div>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  사용자명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  잠금 상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  마지막 로그인
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className={user.is_locked ? 'bg-red-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.username}
                        </div>
                        {user.email && (
                          <div className="text-sm text-gray-500">{user.email}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {user.is_active ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.is_locked ? (
                      <div className="flex items-center">
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800 flex items-center">
                          🔒 잠김
                        </span>
                        {user.locked_until && (
                          <span className="ml-2 text-xs text-gray-500">
                            ({new Date(user.locked_until).toLocaleString('ko-KR')})
                          </span>
                        )}
                        {user.failed_login_attempts !== undefined && user.failed_login_attempts > 0 && (
                          <span className="ml-2 text-xs text-red-600">
                            ({user.failed_login_attempts}회 실패)
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                        정상
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleString('ko-KR')
                      : '로그인 기록 없음'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {user.is_locked && (
                      <button
                        onClick={() => unlockAccount(user.id, user.username)}
                        disabled={unlockingUserId === user.id}
                        className={`px-3 py-1 rounded text-white ${
                          unlockingUserId === user.id
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-orange-600 hover:bg-orange-700'
                        }`}
                      >
                        {unlockingUserId === user.id ? '처리 중...' : '잠금 해제'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* User Statistics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-600 font-medium">전체 사용자</div>
          <div className="text-2xl font-bold text-blue-900">{users.length}</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">활성 사용자</div>
          <div className="text-2xl font-bold text-green-900">
            {users.filter((u) => u.is_active).length}
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium">잠긴 계정</div>
          <div className="text-2xl font-bold text-red-900">
            {users.filter((u) => u.is_locked).length}
          </div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600 font-medium">비활성 사용자</div>
          <div className="text-2xl font-bold text-gray-900">
            {users.filter((u) => !u.is_active).length}
          </div>
        </div>
      </div>

      {/* FR-031 Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>계정 잠금 정책 (FR-031):</strong> 5회 연속 로그인 실패 시 30분간 계정이 자동으로 잠깁니다.
          잠긴 계정은 관리자가 수동으로 해제하거나 30분 경과 후 자동 해제됩니다.
        </p>
      </div>
    </div>
  );
}
