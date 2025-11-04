/**
 * PII Masking Notice Component
 *
 * Displays when personally identifiable information (PII) is detected and masked.
 * Shows "개인정보가 자동으로 마스킹되었습니다." per FR-052
 */

import React from 'react';

interface PIIDetail {
  type: string;
  description: string;
  count: number;
}

interface PIIMaskingNoticeProps {
  piiDetails: PIIDetail[];
  onDismiss?: () => void;
}

export default function PIIMaskingNotice({
  piiDetails,
  onDismiss
}: PIIMaskingNoticeProps) {
  if (!piiDetails || piiDetails.length === 0) return null;

  // Map PII types to icons
  const getIcon = (type: string) => {
    switch (type) {
      case 'korean_id':
        return '🆔';
      case 'phone':
        return '📞';
      case 'email':
        return '📧';
      default:
        return '🔒';
    }
  };

  return (
    <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
      <div className="flex items-start">
        {/* Icon */}
        <div className="flex-shrink-0">
          <svg
            className="w-5 h-5 text-amber-600 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="ml-3 flex-1">
          <h4 className="text-sm font-medium text-amber-800 mb-2">
            개인정보가 자동으로 마스킹되었습니다
          </h4>

          <p className="text-sm text-amber-700 mb-3">
            보안을 위해 다음 개인정보가 자동으로 숨김 처리되었습니다:
          </p>

          {/* PII Details */}
          <div className="space-y-2">
            {piiDetails.map((detail, index) => (
              <div
                key={index}
                className="flex items-center text-sm text-amber-700"
              >
                <span className="mr-2">{getIcon(detail.type)}</span>
                <span>
                  <strong>{detail.description}</strong> ({detail.count}개 감지됨)
                </span>
              </div>
            ))}
          </div>

          {/* Examples */}
          <div className="mt-3 pt-3 border-t border-amber-200">
            <p className="text-xs text-amber-600">
              예시: 주민등록번호 → 123456-*******,
              전화번호 → 010-****-****,
              이메일 → u***@domain.com
            </p>
          </div>
        </div>

        {/* Dismiss button (optional) */}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 ml-3 text-amber-600 hover:text-amber-800"
            aria-label="닫기"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
