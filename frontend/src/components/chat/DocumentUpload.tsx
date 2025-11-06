'use client'

import { useState, useRef } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface UploadedDocument {
  id: string
  filename: string
  file_size: number
  file_type: string
  uploaded_at: string
}

interface DocumentUploadProps {
  conversationId?: string
  onUploadSuccess?: (document: UploadedDocument) => void
  onUploadError?: (error: string) => void
}

export default function DocumentUpload({
  conversationId,
  onUploadSuccess,
  onUploadError,
}: DocumentUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if (!allowedTypes.includes(file.type)) {
      const error = '지원하지 않는 파일 형식입니다. PDF, DOCX, TXT 파일만 업로드 가능합니다.'
      onUploadError?.(error)
      alert(error)
      return
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      const error = '파일 크기는 50MB를 초과할 수 없습니다.'
      onUploadError?.(error)
      alert(error)
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

      const document: UploadedDocument = await response.json()
      setUploadedDocs((prev) => [...prev, document])
      onUploadSuccess?.(document)

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '문서 업로드 중 오류가 발생했습니다.'
      onUploadError?.(errorMessage)
      alert(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getFileIcon = (fileType: string): string => {
    switch (fileType) {
      case 'pdf':
        return '📄'
      case 'docx':
        return '📝'
      case 'txt':
        return '📃'
      default:
        return '📎'
    }
  }

  return (
    <div className="space-y-2">
      {/* Upload Button */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
          disabled={isUploading}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
            />
          </svg>
          {isUploading ? '업로드 중...' : '파일 첨부'}
        </button>
        <span className="text-xs text-gray-500">PDF, DOCX, TXT (최대 50MB)</span>
      </div>

      {/* Uploaded Documents List */}
      {uploadedDocs.length > 0 && (
        <div className="space-y-1">
          {uploadedDocs.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm"
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{getFileIcon(doc.file_type)}</span>
                <div>
                  <div className="font-medium text-gray-900">{doc.filename}</div>
                  <div className="text-xs text-gray-500">
                    {formatFileSize(doc.file_size)}
                  </div>
                </div>
              </div>
              <div className="text-xs text-green-600">✓ 업로드 완료</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
