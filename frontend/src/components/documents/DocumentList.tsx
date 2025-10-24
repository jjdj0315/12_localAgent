'use client'

/**
 * DocumentList Component
 * Displays list of uploaded documents
 */

import DocumentCard from './DocumentCard'

interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  uploaded_at: string
}

interface DocumentListProps {
  documents: Document[]
  onDelete: (id: string) => void
}

export default function DocumentList({ documents, onDelete }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
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
        <p className="mt-4 text-gray-500 text-lg">업로드된 문서가 없습니다</p>
        <p className="mt-2 text-gray-400 text-sm">
          위 영역에서 문서를 업로드해보세요
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        업로드된 문서
      </h2>
      {documents.map((document) => (
        <DocumentCard
          key={document.id}
          document={document}
          onDelete={() => onDelete(document.id)}
        />
      ))}
    </div>
  )
}
