'use client'

import { useState, useEffect } from 'react'

interface ProgressEvent {
  node: 'classify' | 'direct' | 'reasoning' | 'specialized' | 'finalize'
  status: 'started' | 'completed' | 'error'
  details: Record<string, any>
  timestamp: number
}

interface OrchestratorProgressPanelProps {
  progressEvents: ProgressEvent[]
  isOpen: boolean
}

const NODE_LABELS: Record<string, string> = {
  classify: '경로 분류',
  direct: '직접 응답',
  reasoning: '의도 명확화',
  specialized: '전문 에이전트',
  finalize: '최종 처리'
}

const NODE_EMOJIS: Record<string, string> = {
  classify: '🔍',
  direct: '⚡',
  reasoning: '🤔',
  specialized: '👥',
  finalize: '✅'
}

export default function OrchestratorProgressPanel({ progressEvents, isOpen }: OrchestratorProgressPanelProps) {
  if (!isOpen || progressEvents.length === 0) {
    return null
  }

  // Group events by node
  const nodeStates: Record<string, { status: string; details: any }> = {}
  progressEvents.forEach(event => {
    nodeStates[event.node] = {
      status: event.status,
      details: event.details
    }
  })

  // Determine current executing node
  const currentNode = progressEvents[progressEvents.length - 1]?.node

  return (
    <div className="mt-2 mb-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-gray-700">실행 과정</h4>
        <span className="text-xs text-gray-500">{progressEvents.length}개 이벤트</span>
      </div>

      {/* Node flow visualization */}
      <div className="flex items-center justify-between mb-3">
        {['classify', 'direct', 'reasoning', 'specialized', 'finalize'].map((node, index) => {
          const state = nodeStates[node]
          const isActive = currentNode === node && state?.status === 'started'
          const isCompleted = state?.status === 'completed'
          const isError = state?.status === 'error'

          return (
            <div key={node} className="flex items-center">
              <div
                className={`
                  flex flex-col items-center justify-center w-16 h-16 rounded-lg transition-all
                  ${isActive ? 'bg-blue-100 border-2 border-blue-500 animate-pulse' : ''}
                  ${isCompleted ? 'bg-green-100 border-2 border-green-500' : ''}
                  ${isError ? 'bg-red-100 border-2 border-red-500' : ''}
                  ${!state ? 'bg-gray-100 border border-gray-300 opacity-50' : ''}
                `}
              >
                <div className="text-2xl">{NODE_EMOJIS[node]}</div>
                <div className="text-xs mt-1 font-medium text-center">
                  {NODE_LABELS[node]}
                </div>
              </div>

              {/* Arrow between nodes */}
              {index < 4 && (
                <div className="mx-1 text-gray-400">→</div>
              )}
            </div>
          )
        })}
      </div>

      {/* Details section */}
      <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
        {progressEvents.slice().reverse().map((event, index) => (
          <div
            key={index}
            className={`
              text-xs px-2 py-1 rounded
              ${event.status === 'started' ? 'bg-blue-50 text-blue-700' : ''}
              ${event.status === 'completed' ? 'bg-green-50 text-green-700' : ''}
              ${event.status === 'error' ? 'bg-red-50 text-red-700' : ''}
            `}
          >
            <span className="font-medium">{NODE_EMOJIS[event.node]} {NODE_LABELS[event.node]}</span>
            {': '}
            <span>
              {event.status === 'started' && '시작'}
              {event.status === 'completed' && '완료'}
              {event.status === 'error' && '오류'}
            </span>
            {event.details.route && ` (${event.details.route})`}
            {event.details.time_ms && ` - ${event.details.time_ms}ms`}
            {event.details.agents && ` - ${event.details.agents.join(', ')}`}
          </div>
        ))}
      </div>
    </div>
  )
}
