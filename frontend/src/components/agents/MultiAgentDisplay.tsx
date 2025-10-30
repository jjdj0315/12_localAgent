/**
 * Multi-Agent Display Component
 *
 * Shows agent attribution and contributions in multi-agent responses.
 * Per FR-074: Clear agent attribution with labels and icons
 */

'use client';

import React from 'react';

interface AgentContribution {
  agent_name: string;
  display_name: string;
  contribution: string;
  execution_time_ms: number;
  success: boolean;
}

interface MultiAgentDisplayProps {
  workflowType: string; // "single", "sequential", "parallel"
  agentContributions: AgentContribution[];
  totalExecutionTimeMs: number;
  onClose?: () => void;
}

// Agent icon mapping per FR-074
const AGENT_ICONS: Record<string, string> = {
  citizen_support: '🙋',
  document_writing: '📝',
  legal_research: '⚖️',
  data_analysis: '📊',
  review: '✅',
};

// Agent color mapping
const AGENT_COLORS: Record<string, string> = {
  citizen_support: 'from-blue-50 to-blue-100 border-blue-200',
  document_writing: 'from-green-50 to-green-100 border-green-200',
  legal_research: 'from-purple-50 to-purple-100 border-purple-200',
  data_analysis: 'from-orange-50 to-orange-100 border-orange-200',
  review: 'from-pink-50 to-pink-100 border-pink-200',
};

// Workflow type labels
const WORKFLOW_LABELS: Record<string, string> = {
  single: '단일 에이전트',
  sequential: '순차 워크플로',
  parallel: '병렬 워크플로',
};

export default function MultiAgentDisplay({
  workflowType,
  agentContributions,
  totalExecutionTimeMs,
  onClose,
}: MultiAgentDisplayProps) {
  if (!agentContributions || agentContributions.length === 0) {
    return null;
  }

  return (
    <div className="mb-6 bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-indigo-900 flex items-center">
            <span className="mr-2">🤖</span>
            Multi-Agent 실행 결과
          </h3>
          <p className="text-sm text-indigo-600 mt-1">
            {WORKFLOW_LABELS[workflowType] || workflowType} · {agentContributions.length}개 에이전트 사용 · 총 실행시간: {(totalExecutionTimeMs / 1000).toFixed(2)}초
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-indigo-600 hover:text-indigo-800 transition-colors"
            aria-label="닫기"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Agent Contributions */}
      <div className="space-y-3">
        {agentContributions.map((agent, index) => {
          const icon = AGENT_ICONS[agent.agent_name] || '🤖';
          const colorClass = AGENT_COLORS[agent.agent_name] || 'from-gray-50 to-gray-100 border-gray-200';

          return (
            <div
              key={index}
              className={`bg-gradient-to-r ${colorClass} border rounded-lg p-4 shadow-sm`}
            >
              {/* Agent Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">{icon}</span>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">
                      {agent.display_name}
                    </h4>
                    <p className="text-xs text-gray-600">
                      {workflowType === 'sequential' && `단계 ${index + 1}`}
                      {workflowType === 'parallel' && '병렬 실행'}
                      {workflowType === 'single' && '단일 실행'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center">
                    {agent.success ? (
                      <span className="text-green-600 text-xs font-medium">✓ 성공</span>
                    ) : (
                      <span className="text-red-600 text-xs font-medium">✗ 실패</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {(agent.execution_time_ms / 1000).toFixed(2)}초
                  </p>
                </div>
              </div>

              {/* Agent Response */}
              {agent.contribution && (
                <div className="bg-white rounded px-3 py-2 border border-gray-200">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {agent.contribution}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-indigo-200">
        <div className="flex items-start">
          <span className="text-lg mr-2">💡</span>
          <div className="flex-1">
            <p className="text-xs text-indigo-700 font-medium mb-1">
              Multi-Agent 시스템이란?
            </p>
            <p className="text-xs text-indigo-600">
              {workflowType === 'sequential' &&
                '각 에이전트가 순차적으로 실행되며, 이전 에이전트의 출력을 다음 에이전트가 활용합니다.'}
              {workflowType === 'parallel' &&
                '여러 에이전트가 독립적으로 병렬 실행되어 빠른 응답을 제공합니다.'}
              {workflowType === 'single' &&
                '가장 적합한 단일 에이전트가 질문에 응답합니다.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
