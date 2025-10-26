'use client'

/**
 * DocumentSelector Component
 * Allows users to select documents to attach to chat queries
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { documentsAPI } from '@/lib/api'

interface DocumentSelectorProps {
  selectedDocuments: string[]
  onSelectionChange: (documentIds: string[]) => void
}

export default function DocumentSelector({
  selectedDocuments,
  onSelectionChange,
}: DocumentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Fetch documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsAPI.list({ limit: 100, offset: 0 }),
  })

  const toggleDocument = (documentId: string) => {
    const newSelection = selectedDocuments.includes(documentId)
      ? selectedDocuments.filter((id) => id !== documentId)
      : [...selectedDocuments, documentId]

    onSelectionChange(newSelection)
  }

  const removeDocument = (documentId: string) => {
    onSelectionChange(selectedDocuments.filter((id) => id !== documentId))
  }

  const clearAll = () => {
    onSelectionChange([])
  }

  // Get selected document details
  const getSelectedDocumentName = (id: string) => {
    const doc = data?.documents.find((d: any) => d.id === id)
    return doc?.filename || '알 수 없는 문서'
  }

  return (
    <div className="space-y-2">
      {/* Selected Documents Display */}
      {selectedDocuments.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center text-sm text-blue-700 font-medium mr-2">
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            참고 문서 ({selectedDocuments.length}):
          </div>

          {selectedDocuments.map((docId) => (
            <div
              key={docId}
              className="flex items-center space-x-1 px-3 py-1 bg-white border border-blue-200 rounded-full text-sm"
            >
              <span className="text-blue-900 truncate max-w-[200px]">
                {getSelectedDocumentName(docId)}
              </span>
              <button
                onClick={() => removeDocument(docId)}
                className="text-blue-600 hover:text-blue-800"
                title="제거"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          ))}

          <button
            onClick={clearAll}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            모두 제거
          </button>
        </div>
      )}

      {/* Document Selection Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
        <span>문서 첨부</span>
      </button>

      {/* Document List Dropdown */}
      {isOpen && (
        <div className="border border-gray-200 rounded-lg bg-white shadow-lg max-h-64 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">
              문서 목록을 불러오는 중...
            </div>
          ) : data?.documents.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p>업로드된 문서가 없습니다</p>
              <a
                href="/documents"
                className="text-blue-600 hover:underline text-sm mt-2 inline-block"
              >
                문서 업로드하기 →
              </a>
            </div>
          ) : (
            <div className="p-2">
              <div className="text-xs text-gray-500 px-3 py-2 font-medium">
                문서를 선택하여 채팅에 첨부하세요
              </div>
              {data?.documents.map((document: any) => (
                <label
                  key={document.id}
                  className="flex items-center space-x-3 px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(document.id)}
                    onChange={() => toggleDocument(document.id)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {document.filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {document.file_type.toUpperCase()} •{' '}
                      {Math.round(document.file_size / 1024)} KB
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
