/**
 * Tool Management Component
 *
 * Admin interface for managing ReAct tools.
 * Features:
 * - Enable/disable tools
 * - View tool list with statistics
 * - Update tool settings
 */

'use client';

import React, { useState, useEffect } from 'react';

interface Tool {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  is_active: boolean;
  usage_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
}

export default function ToolManagement() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const response = await fetch('/api/v1/admin/tools/list', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setTools(data.tools);
      }
    } catch (error) {
      console.error('Failed to load tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = async (toolId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/v1/admin/tools/${toolId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ is_active: isActive })
      });

      if (response.ok) {
        loadTools();
      }
    } catch (error) {
      console.error('Failed to toggle tool:', error);
    }
  };

  if (loading) {
    return <div className="p-4">로딩 중...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900">ReAct 도구 관리</h2>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                도구명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                카테고리
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                사용 횟수
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                성공률
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                평균 시간
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                상태
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tools.map((tool) => (
              <tr key={tool.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">{tool.display_name}</div>
                  <div className="text-sm text-gray-500">{tool.name}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{tool.category}</td>
                <td className="px-6 py-4 text-sm text-right text-gray-900">
                  {tool.usage_count}
                </td>
                <td className="px-6 py-4 text-sm text-right text-gray-900">
                  {tool.success_rate.toFixed(1)}%
                </td>
                <td className="px-6 py-4 text-sm text-right text-gray-900">
                  {tool.avg_execution_time_ms}ms
                </td>
                <td className="px-6 py-4 text-center">
                  <button
                    onClick={() => toggleTool(tool.id, !tool.is_active)}
                    className={`px-3 py-1 text-xs rounded-full ${
                      tool.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {tool.is_active ? '활성' : '비활성'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
