/**
 * Workflow Progress Component
 *
 * Shows current agent and workflow execution stage in real-time.
 * Per FR-072: Sequential workflow visibility
 */

'use client';

import React, { useEffect, useState } from 'react';

interface WorkflowStep {
  agent_name: string;
  display_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
}

interface WorkflowProgressProps {
  workflowType: string; // "single", "sequential", "parallel"
  steps: WorkflowStep[];
  currentStepIndex?: number;
}

// Agent icon mapping
const AGENT_ICONS: Record<string, string> = {
  citizen_support: '🙋',
  document_writing: '📝',
  legal_research: '⚖️',
  data_analysis: '📊',
  review: '✅',
};

// Status colors
const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  pending: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' },
  running: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-400' },
  completed: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-400' },
  failed: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-400' },
};

export default function WorkflowProgress({
  workflowType,
  steps,
  currentStepIndex,
}: WorkflowProgressProps) {
  const [elapsedTime, setElapsedTime] = useState(0);

  // Calculate elapsed time for running step
  useEffect(() => {
    const runningStep = steps.find((s) => s.status === 'running');
    if (!runningStep || !runningStep.started_at) {
      setElapsedTime(0);
      return;
    }

    const interval = setInterval(() => {
      const startTime = new Date(runningStep.started_at!).getTime();
      const now = Date.now();
      setElapsedTime(Math.floor((now - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [steps]);

  if (!steps || steps.length === 0) {
    return null;
  }

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const progressPercentage = (completedCount / steps.length) * 100;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">⚙️</span>
            워크플로 진행 상황
          </h4>
          <p className="text-xs text-gray-600 mt-1">
            {workflowType === 'sequential' && '순차 실행'}
            {workflowType === 'parallel' && '병렬 실행'}
            {workflowType === 'single' && '단일 실행'}
            {' · '}
            {completedCount} / {steps.length} 완료
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium text-gray-700">
            {Math.round(progressPercentage)}%
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, index) => {
          const icon = AGENT_ICONS[step.agent_name] || '🤖';
          const colors = STATUS_COLORS[step.status] || STATUS_COLORS.pending;
          const isCurrentStep = currentStepIndex !== undefined && currentStepIndex === index;

          return (
            <div
              key={index}
              className={`flex items-center p-3 rounded-lg border ${colors.bg} ${colors.border} ${
                isCurrentStep ? 'ring-2 ring-blue-400' : ''
              }`}
            >
              {/* Step Number/Icon */}
              <div className="flex-shrink-0 mr-3">
                {step.status === 'completed' ? (
                  <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                ) : step.status === 'failed' ? (
                  <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                ) : step.status === 'running' ? (
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-sm font-semibold">
                    {index + 1}
                  </div>
                )}
              </div>

              {/* Step Info */}
              <div className="flex-1">
                <div className="flex items-center">
                  <span className="text-lg mr-2">{icon}</span>
                  <h5 className={`text-sm font-medium ${colors.text}`}>
                    {step.display_name}
                  </h5>
                </div>
                <div className="flex items-center mt-1">
                  <p className={`text-xs ${colors.text}`}>
                    {step.status === 'pending' && '대기 중'}
                    {step.status === 'running' && `실행 중 (${elapsedTime}초 경과)`}
                    {step.status === 'completed' && '완료'}
                    {step.status === 'failed' && '실패'}
                  </p>
                </div>
              </div>

              {/* Connector (for sequential) */}
              {workflowType === 'sequential' && index < steps.length - 1 && (
                <div className="flex-shrink-0 ml-2">
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Hint */}
      {workflowType === 'sequential' && (
        <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
          <p className="text-xs text-blue-700">
            💡 순차 워크플로: 각 단계가 이전 단계의 결과를 활용하여 실행됩니다.
          </p>
        </div>
      )}
      {workflowType === 'parallel' && (
        <div className="mt-3 p-2 bg-purple-50 rounded border border-purple-200">
          <p className="text-xs text-purple-700">
            💡 병렬 워크플로: 여러 에이전트가 동시에 독립적으로 실행됩니다.
          </p>
        </div>
      )}
    </div>
  );
}
