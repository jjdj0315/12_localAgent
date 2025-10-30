/**
 * Agent Management Component
 *
 * Admin interface for managing Multi-Agent system.
 * Features:
 * - Enable/disable agents (FR-076)
 * - Configure routing mode (LLM vs keyword-based)
 * - Edit agent settings
 * - View agent performance
 */

'use client';

import React, { useState, useEffect } from 'react';

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  is_active: boolean;
  priority: number;
  usage_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  lora_adapter_enabled: boolean;
  lora_adapter_path?: string;
}

interface RoutingConfig {
  mode: 'llm' | 'keyword';
  orchestrator_model: string;
}

// Agent icon mapping
const AGENT_ICONS: Record<string, string> = {
  citizen_support: '🙋',
  document_writing: '📝',
  legal_research: '⚖️',
  data_analysis: '📊',
  review: '✅',
};

export default function AgentManagement() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [routingConfig, setRoutingConfig] = useState<RoutingConfig>({
    mode: 'llm',
    orchestrator_model: 'llm',
  });
  const [loading, setLoading] = useState(true);
  const [editingAgent, setEditingAgent] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
    loadRoutingConfig();
  }, []);

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/v1/admin/agents/list', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRoutingConfig = async () => {
    try {
      const response = await fetch('/api/v1/admin/agents/routing-config', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setRoutingConfig(data);
      }
    } catch (error) {
      console.error('Failed to load routing config:', error);
    }
  };

  const toggleAgent = async (agentId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/v1/admin/agents/${agentId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ enabled: isActive }),
      });

      if (response.ok) {
        await loadAgents();
      }
    } catch (error) {
      console.error('Failed to toggle agent:', error);
    }
  };

  const updateRoutingMode = async (mode: 'llm' | 'keyword') => {
    try {
      const response = await fetch('/api/v1/admin/agents/routing-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ routing_mode: mode }),
      });

      if (response.ok) {
        setRoutingConfig({ ...routingConfig, mode });
      }
    } catch (error) {
      console.error('Failed to update routing mode:', error);
    }
  };

  const updateAgentPriority = async (agentId: string, priority: number) => {
    try {
      const response = await fetch(`/api/v1/admin/agents/${agentId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ priority }),
      });

      if (response.ok) {
        await loadAgents();
        setEditingAgent(null);
      }
    } catch (error) {
      console.error('Failed to update priority:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">에이전트 관리</h2>
        <p className="mt-1 text-sm text-gray-600">
          Multi-Agent 시스템의 에이전트를 관리하고 설정을 조정합니다.
        </p>
      </div>

      {/* Routing Configuration */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">라우팅 설정</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              라우팅 모드
            </label>
            <div className="flex space-x-4">
              <button
                onClick={() => updateRoutingMode('llm')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  routingConfig.mode === 'llm'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🤖 LLM 기반 (권장)
              </button>
              <button
                onClick={() => updateRoutingMode('keyword')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  routingConfig.mode === 'keyword'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🔑 키워드 기반 (Fallback)
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              {routingConfig.mode === 'llm'
                ? 'LLM이 사용자 질문을 분석하여 적절한 에이전트를 선택합니다. (FR-070)'
                : '키워드 매칭으로 에이전트를 선택합니다. LLM 장애 시 자동 전환됩니다. (FR-076)'}
            </p>
          </div>
        </div>
      </div>

      {/* Agent List */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">에이전트 목록</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {agents.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              에이전트가 없습니다.
            </div>
          ) : (
            agents.map((agent) => {
              const icon = AGENT_ICONS[agent.category] || '🤖';

              return (
                <div key={agent.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    {/* Agent Info */}
                    <div className="flex-1">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{icon}</span>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">
                            {agent.display_name}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {agent.description}
                          </p>
                        </div>
                      </div>

                      {/* Statistics */}
                      <div className="mt-4 flex items-center space-x-6 text-sm">
                        <div>
                          <span className="text-gray-500">사용 횟수:</span>
                          <span className="ml-2 font-medium text-gray-900">
                            {agent.usage_count}회
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">성공률:</span>
                          <span className="ml-2 font-medium text-gray-900">
                            {agent.success_rate.toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">평균 시간:</span>
                          <span className="ml-2 font-medium text-gray-900">
                            {(agent.avg_execution_time_ms / 1000).toFixed(2)}초
                          </span>
                        </div>
                      </div>

                      {/* Priority */}
                      <div className="mt-3 flex items-center">
                        <span className="text-sm text-gray-500 mr-2">우선순위:</span>
                        {editingAgent === agent.id ? (
                          <div className="flex items-center space-x-2">
                            <input
                              type="number"
                              min="0"
                              max="1000"
                              defaultValue={agent.priority}
                              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                  updateAgentPriority(
                                    agent.id,
                                    parseInt((e.target as HTMLInputElement).value)
                                  );
                                }
                              }}
                            />
                            <button
                              onClick={() => setEditingAgent(null)}
                              className="text-xs text-gray-600 hover:text-gray-800"
                            >
                              취소
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setEditingAgent(agent.id)}
                            className="text-sm font-medium text-blue-600 hover:text-blue-800"
                          >
                            {agent.priority} (수정)
                          </button>
                        )}
                      </div>

                      {/* LoRA Status */}
                      {agent.lora_adapter_enabled && (
                        <div className="mt-2 inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                          ✨ LoRA 어댑터 활성화
                        </div>
                      )}
                    </div>

                    {/* Toggle Switch */}
                    <div className="ml-4">
                      <label className="flex items-center cursor-pointer">
                        <div className="relative">
                          <input
                            type="checkbox"
                            className="sr-only"
                            checked={agent.is_active}
                            onChange={(e) => toggleAgent(agent.id, e.target.checked)}
                          />
                          <div
                            className={`block w-14 h-8 rounded-full transition-colors ${
                              agent.is_active ? 'bg-blue-600' : 'bg-gray-300'
                            }`}
                          ></div>
                          <div
                            className={`absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${
                              agent.is_active ? 'transform translate-x-6' : ''
                            }`}
                          ></div>
                        </div>
                        <div className="ml-3 text-sm font-medium text-gray-700">
                          {agent.is_active ? '활성화' : '비활성화'}
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>우선순위:</strong> 숫자가 클수록 오케스트레이터가 해당 에이전트를 먼저
              선택합니다. 동일한 적합도일 때 우선순위가 높은 에이전트가 사용됩니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
