'use client'

/**
 * Documents Page
 * Allows users to upload and manage documents for LLM analysis
 */

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { documentsAPI } from '@/lib/api'
import FileUploader from '@/components/documents/FileUploader'
import DocumentList from '@/components/documents/DocumentList'

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)

  // Fetch documents
  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', page],
    queryFn: () => documentsAPI.list({ page, page_size: 20 }),
  })

  const handleUploadSuccess = () => {
    // Invalidate and refetch
    queryClient.invalidateQueries({ queryKey: ['documents'] })
  }

  const handleDelete = async (id: string) => {
    try {
      await documentsAPI.delete(id)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    } catch (err) {
      console.error('Failed to delete document:', err)
    }
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">
          문서 목록을 불러오는데 실패했습니다.
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">문서 관리</h1>
          <p className="text-gray-600">
            PDF, DOCX, TXT 파일을 업로드하여 LLM과 대화할 수 있습니다
          </p>
        </div>

        {/* File Uploader */}
        <div className="mb-8">
          <FileUploader onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">문서 목록을 불러오는 중...</p>
          </div>
        )}

        {/* Document List */}
        {!isLoading && data && (
          <>
            <DocumentList
              documents={data.documents}
              onDelete={handleDelete}
            />

            {/* Pagination */}
            {data.total > 20 && (
              <div className="mt-8 flex justify-center items-center space-x-4">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  이전
                </button>
                <span className="text-gray-700">
                  페이지 {page} / {Math.ceil(data.total / 20)}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.has_next}
                  className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  다음
                </button>
              </div>
            )}

            {/* Stats */}
            <div className="mt-6 text-center text-gray-600">
              총 {data.total}개의 문서
            </div>
          </>
        )}
      </div>
    </div>
  )
}
