/**
 * LoadingIndicator Component
 *
 * Shows loading state during LLM response generation
 */

import React from "react";

export interface LoadingIndicatorProps {
  message?: string;
  visible?: boolean;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = "AI가 응답을 생성하고 있습니다...",
  visible = true,
}) => {
  if (!visible) return null;

  return (
    <div className="flex items-center justify-center gap-3 rounded-lg bg-blue-50 p-4">
      <div className="flex gap-1">
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:-0.3s]"></div>
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:-0.15s]"></div>
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-600"></div>
      </div>
      <span className="text-sm font-medium text-blue-900">{message}</span>
    </div>
  );
};

export interface StreamingIndicatorProps {
  text?: string;
}

export const StreamingIndicator: React.FC<StreamingIndicatorProps> = ({
  text = "",
}) => {
  return (
    <div className="rounded-lg border border-blue-200 bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-xs font-semibold text-gray-700">
          AI 어시스턴트
        </span>
        <div className="flex gap-1">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500"></div>
          <span className="text-xs text-gray-500">입력 중...</span>
        </div>
      </div>
      <div className="whitespace-pre-wrap text-sm text-gray-900">
        {text}
        <span className="animate-pulse">|</span>
      </div>
    </div>
  );
};
