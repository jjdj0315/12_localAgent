'use client'

/**
 * DocumentSelector Component
 * Allows users to upload and select documents to attach to chat queries
 */

import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { documentsAPI } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface DocumentSelectorProps {
  conversationId?: string
  selectedDocuments: string[]
  onSelectionChange: (documentIds: string[]) => void
}

export default function DocumentSelector({
  conversationId,
  selectedDocuments,
  onSelectionChange,
}: DocumentSelectorProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [showList, setShowList] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  // Fetch documents
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsAPI.list({ limit: 100, offset: 0 }),
  })

  // File upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ]
    if (!allowedTypes.includes(file.type)) {
      alert('지원하지 않는 파일 형식입니다. PDF, DOCX, TXT 파일만 업로드 가능합니다.')
      return
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('파일 크기는 50MB를 초과할 수 없습니다.')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      if (conversationId) {
        formData.append('conversation_id', conversationId)
      }

      const response = await fetch(`${API_URL}/documents`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '문서 업로드에 실패했습니다.')
      }

      const uploadedDoc = await response.json()

      // Update cache with new document
      queryClient.setQueryData(['documents'], (oldData: any) => {
        if (!oldData) return oldData
        return {
          ...oldData,
          documents: [uploadedDoc, ...oldData.documents],
          total: oldData.total + 1,
        }
      })

      // Auto-select the uploaded document
      onSelectionChange([...selectedDocuments, uploadedDoc.id])

      // Show list after upload
      setShowList(true)

      // Show success message
      alert(`✓ ${file.name} 업로드 완료!`)

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '문서 업로드 중 오류가 발생했습니다.'
      alert(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

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
  const getSelectedDocument = (id: string) => {
    const doc = data?.documents.find((d: any) => d.id === id)
    return doc
  }

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
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

          {selectedDocuments.map((docId) => {
            const doc = getSelectedDocument(docId)
            return (
              <div
                key={docId}
                className="flex items-center space-x-1 px-3 py-1 bg-white border border-blue-200 rounded-lg text-sm"
              >
                <div className="flex flex-col">
                  <span className="text-blue-900 font-medium truncate max-w-[200px]">
                    {doc?.filename || '알 수 없는 문서'}
                  </span>
                  {doc && (
                    <span className="text-xs text-gray-500">
                      {doc.file_type.toUpperCase()} • {formatFileSize(doc.file_size)}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => removeDocument(docId)}
                  className="text-blue-600 hover:text-blue-800 ml-2"
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
            )
          })}

          <button
            onClick={clearAll}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            모두 제거
          </button>
        </div>
      )}

      {/* Upload Button */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileUpload}
          className="hidden"
          disabled={isUploading}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex items-center space-x-2 text-sm px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
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
          <span>{isUploading ? '업로드 중...' : '문서 첨부'}</span>
        </button>

        {data && data.documents.length > 0 && (
          <button
            onClick={() => setShowList(!showList)}
            className="text-sm text-gray-600 hover:text-gray-900 underline"
          >
            {showList ? '목록 숨기기' : `업로드된 문서 보기 (${data.documents.length})`}
          </button>
        )}
      </div>

      {/* Document List */}
      {showList && (
        <div className="border border-gray-200 rounded-lg bg-white shadow-sm">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">
              문서 목록을 불러오는 중...
            </div>
          ) : data?.documents.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p className="text-sm">업로드된 문서가 없습니다</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {data?.documents.map((document: any) => (
                <label
                  key={document.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
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
                        {document.file_type.toUpperCase()} • {formatFileSize(document.file_size)}
                      </p>
                    </div>
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
