/**
 * Safety Filter Management Component
 *
 * Admin interface for managing safety filter rules.
 * Features:
 * - View all filter rules by category
 * - Create, edit, delete rules
 * - Enable/disable rules
 * - Bulk operations by category
 */

'use client';

import React, { useState, useEffect } from 'react';

interface FilterRule {
  id: string;
  name: string;
  description: string;
  category: string;
  keywords: string[];
  regex_patterns: string[];
  is_active: boolean;
  is_system_rule: boolean;
  priority: number;
  match_count: number;
  created_at: string;
}

const CATEGORIES = [
  { value: 'violence', label: '폭력성', color: 'red' },
  { value: 'sexual', label: '성적 내용', color: 'pink' },
  { value: 'dangerous', label: '위험 정보', color: 'orange' },
  { value: 'hate', label: '혐오 발언', color: 'purple' },
  { value: 'pii', label: '개인정보', color: 'blue' }
];

export default function SafetyFilterManagement() {
  const [rules, setRules] = useState<FilterRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRule, setEditingRule] = useState<FilterRule | null>(null);

  // Load rules
  useEffect(() => {
    loadRules();
  }, [selectedCategory]);

  const loadRules = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }

      const response = await fetch(`/api/v1/admin/safety-filter/rules?${params}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setRules(data);
      }
    } catch (error) {
      console.error('Failed to load rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRule = async (ruleId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/v1/admin/safety-filter/rules/${ruleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ is_active: isActive })
      });

      if (response.ok) {
        loadRules();
      }
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('이 규칙을 삭제하시겠습니까?')) return;

    try {
      const response = await fetch(`/api/v1/admin/safety-filter/rules/${ruleId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        loadRules();
      }
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const handleBulkToggle = async (category: string, isActive: boolean) => {
    if (!confirm(`${category} 카테고리의 모든 규칙을 ${isActive ? '활성화' : '비활성화'}하시겠습니까?`)) return;

    try {
      const response = await fetch(
        `/api/v1/admin/safety-filter/rules/bulk-toggle?category=${category}&is_active=${isActive}`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );

      if (response.ok) {
        loadRules();
      }
    } catch (error) {
      console.error('Failed to bulk toggle:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">안전 필터 관리</h2>
          <p className="text-gray-600 mt-1">
            콘텐츠 필터링 규칙을 관리합니다
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + 새 규칙 추가
        </button>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory('all')}
          className={`px-4 py-2 rounded-lg whitespace-nowrap ${
            selectedCategory === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          전체 ({rules.length})
        </button>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            onClick={() => setSelectedCategory(cat.value)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap ${
              selectedCategory === cat.value
                ? `bg-${cat.color}-600 text-white`
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Bulk Actions */}
      {selectedCategory !== 'all' && (
        <div className="flex gap-2 p-4 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-600 mr-2">일괄 작업:</span>
          <button
            onClick={() => handleBulkToggle(selectedCategory, true)}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            전체 활성화
          </button>
          <button
            onClick={() => handleBulkToggle(selectedCategory, false)}
            className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            전체 비활성화
          </button>
        </div>
      )}

      {/* Rules Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                규칙명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                카테고리
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                키워드
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                우선순위
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                매칭 수
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                상태
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                작업
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">
                    {rule.name}
                    {rule.is_system_rule && (
                      <span className="ml-2 text-xs text-blue-600">(시스템)</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">{rule.description}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full bg-${
                    CATEGORIES.find(c => c.value === rule.category)?.color || 'gray'
                  }-100 text-${
                    CATEGORIES.find(c => c.value === rule.category)?.color || 'gray'
                  }-800`}>
                    {CATEGORIES.find(c => c.value === rule.category)?.label || rule.category}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900">
                    {rule.keywords.slice(0, 3).join(', ')}
                    {rule.keywords.length > 3 && ` +${rule.keywords.length - 3}`}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rule.priority}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rule.match_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleToggleRule(rule.id, !rule.is_active)}
                    className={`px-3 py-1 text-xs rounded-full ${
                      rule.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {rule.is_active ? '활성' : '비활성'}
                  </button>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => setEditingRule(rule)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    수정
                  </button>
                  {!rule.is_system_rule && (
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      삭제
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {rules.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            규칙이 없습니다
          </div>
        )}
      </div>
    </div>
  );
}
