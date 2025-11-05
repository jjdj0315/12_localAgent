'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AdvancedFeaturesPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">고급 기능 관리</h1>
            <p className="text-sm text-gray-500">
              감사 로그, ReAct 에이전트, 백업 관리 등
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/admin')}
              className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
            >
              대시보드로 돌아가기
            </button>
          </div>
        </div>
      </header>

      <main className="p-6">
        <div className="mx-auto max-w-7xl">
          <div className="bg-white rounded-lg shadow p-8">
            <div className="space-y-6">
              <div className="border-b pb-4">
                <h2 className="text-xl font-semibold text-gray-900">감사 로그</h2>
                <p className="mt-2 text-sm text-gray-600">
                  필터, 도구, 에이전트 실행 기록을 조회할 수 있습니다.
                </p>
              </div>

              <div className="border-b pb-4">
                <h2 className="text-xl font-semibold text-gray-900">템플릿 관리</h2>
                <p className="mt-2 text-sm text-gray-600">
                  정부 문서용 Jinja2 템플릿을 업로드하고 관리할 수 있습니다.
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>알림:</strong> 고급 기능 컴포넌트를 불러오는 중입니다...
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
