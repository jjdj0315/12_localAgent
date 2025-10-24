'use client'

/**
 * DeleteConfirmModal Component
 * Confirmation dialog for deleting conversations
 */

interface DeleteConfirmModalProps {
  conversationTitle: string
  onConfirm: () => void
  onCancel: () => void
}

export default function DeleteConfirmModal({
  conversationTitle,
  onConfirm,
  onCancel,
}: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        {/* Icon */}
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <svg
            className="w-6 h-6 text-red-600"
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
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
          대화 삭제 확인
        </h3>

        {/* Message */}
        <p className="text-gray-600 text-center mb-6">
          "<strong>{conversationTitle}</strong>" 대화를 정말 삭제하시겠습니까?
          <br />
          <span className="text-sm text-gray-500">
            이 작업은 되돌릴 수 없으며, 모든 메시지가 영구적으로 삭제됩니다.
          </span>
        </p>

        {/* Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  )
}
