/**
 * Filter Warning Modal Component
 *
 * Displays when content is blocked by safety filter.
 * Shows violation categories and provides retry option (if applicable).
 *
 * FR-058: Retry with rule-based bypass, ML filter still applies
 */

import React from 'react';

interface FilterWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRetry?: () => void;
  message: string;
  categories: string[];
  canRetry: boolean;
}

export default function FilterWarningModal({
  isOpen,
  onClose,
  onRetry,
  message,
  categories,
  canRetry
}: FilterWarningModalProps) {
  if (!isOpen) return null;

  // Map category codes to Korean labels
  const categoryLabels: Record<string, string> = {
    violence: '폭력적인 내용',
    sexual: '부적절한 성적 내용',
    dangerous: '위험한 정보',
    hate: '혐오 발언',
    pii: '개인정보',
    toxic: '유해한 콘텐츠'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <svg
              className="w-6 h-6 text-red-600 mr-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900">
              콘텐츠 필터링 알림
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Main message */}
          <p className="text-gray-700 mb-4">{message}</p>

          {/* Categories */}
          {categories.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">감지된 항목:</p>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <span
                    key={category}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 text-red-800"
                  >
                    {categoryLabels[category] || category}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Info box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <svg
                className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="text-sm text-blue-800">
                {canRetry ? (
                  <>
                    <p className="font-medium mb-1">다시 시도할 수 있습니다</p>
                    <p>
                      키워드 필터만 우회하여 다시 시도할 수 있습니다.
                      ML 기반 안전 필터는 여전히 적용됩니다.
                    </p>
                  </>
                ) : (
                  <>
                    <p className="font-medium mb-1">안전한 콘텐츠를 작성해주세요</p>
                    <p>
                      다른 방식으로 질문하거나 내용을 수정하여 다시 시도해주세요.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            닫기
          </button>
          {canRetry && onRetry && (
            <button
              onClick={() => {
                onRetry();
                onClose();
              }}
              className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              다시 시도
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
