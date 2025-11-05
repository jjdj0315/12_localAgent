/**
 * ReAct Display Component
 *
 * Displays ReAct agent execution steps with Thought/Action/Observation pattern.
 * Per FR-064: Show with emoji prefixes 🤔/⚙️/👁️
 */

'use client';

import React from 'react';

interface ReActStep {
  iteration: number;
  thought: string;
  action?: string;
  action_input?: Record<string, any>;
  observation?: string;
  timestamp: string;
}

interface ReActDisplayProps {
  steps: ReActStep[];
  toolsUsed: string[];
  onClose?: () => void;
}

export default function ReActDisplay({ steps, toolsUsed, onClose }: ReActDisplayProps) {
  if (!steps || steps.length === 0) {
    return null;
  }

  return (
    <div className="mb-4 bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-purple-900 flex items-center">
            <span className="mr-2">🤖</span>
            ReAct Agent 실행 과정
          </h3>
          <p className="text-sm text-purple-600 mt-1">
            {steps.length}단계 실행 · 사용된 도구: {toolsUsed.join(', ') || '없음'}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-purple-600 hover:text-purple-800"
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

      {/* Steps */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={index} className="bg-white rounded-lg p-4 shadow-sm border border-purple-100">
            {/* Step Header */}
            <div className="flex items-center mb-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-semibold mr-2">
                {step.iteration}
              </span>
              <span className="text-xs text-gray-500">
                {new Date(step.timestamp).toLocaleTimeString('ko-KR')}
              </span>
            </div>

            {/* Thought */}
            <div className="mb-3">
              <div className="flex items-start">
                <span className="text-xl mr-2">🤔</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-700 mb-1">Thought:</p>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{step.thought}</p>
                </div>
              </div>
            </div>

            {/* Action */}
            {step.action && (
              <div className="mb-3">
                <div className="flex items-start">
                  <span className="text-xl mr-2">⚙️</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700 mb-1">Action:</p>
                    <div className="bg-blue-50 rounded px-3 py-2">
                      <p className="text-sm font-mono text-blue-900">{step.action}</p>
                      {step.action_input && Object.keys(step.action_input).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-blue-700 cursor-pointer hover:text-blue-900">
                            파라미터 보기
                          </summary>
                          <pre className="text-xs text-blue-800 mt-2 overflow-x-auto">
                            {JSON.stringify(step.action_input, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Observation */}
            {step.observation && (
              <div>
                <div className="flex items-start">
                  <span className="text-xl mr-2">👁️</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700 mb-1">Observation:</p>
                    <div className="bg-green-50 rounded px-3 py-2">
                      <p className="text-sm text-green-900 whitespace-pre-wrap">
                        {step.observation}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-purple-200">
        <p className="text-xs text-purple-600">
          💡 ReAct (Reasoning and Acting) 패턴: AI가 단계별로 사고하고 도구를 활용하여 문제를 해결합니다.
        </p>
      </div>
    </div>
  );
}
