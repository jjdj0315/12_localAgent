'use client'

import { useEffect, useState, forwardRef, useImperativeHandle } from 'react'
import { conversationsAPI } from '@/lib/api'
import type { Conversation } from '@/types/conversation'

interface ConversationListProps {
  selectedId?: string
  onSelect: (conversationId: string) => void
  onNew: () => void
}

export interface ConversationListHandle {
  refresh: () => void
}

const ConversationList = forwardRef<ConversationListHandle, ConversationListProps>(
  ({ selectedId, onSelect, onNew }, ref) => {
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [total, setTotal] = useState(0)

    // Load conversations
    const loadConversations = async () => {
      try {
        setLoading(true)
        const response = await conversationsAPI.list({
          page: 1,
          page_size: 50,
          search: search || undefined,
        })
        setConversations(response.conversations)
        setTotal(response.total)
      } catch (error) {
        console.error('Failed to load conversations:', error)
      } finally {
        setLoading(false)
      }
    }

    useEffect(() => {
      loadConversations()
    }, [search])

    // Expose refresh method to parent
    useImperativeHandle(ref, () => ({
      refresh: loadConversations,
    }))

  // Delete conversation
  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('이 대화를 삭제하시겠습니까?')) return

    try {
      await conversationsAPI.delete(id)
      await loadConversations()
      if (selectedId === id) {
        onNew()
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      alert('대화 삭제에 실패했습니다.')
    }
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
    } else if (days < 7) {
      return `${days}일 전`
    } else {
      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
    }
  }

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">대화</h2>
          <button
            onClick={onNew}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
          >
            + 새 대화
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="대화 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-sm text-gray-500">로딩 중...</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            {search ? '검색 결과가 없습니다.' : '저장된 대화가 없습니다.'}
          </div>
        ) : (
          <div className="divide-y">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`group cursor-pointer p-4 transition-colors hover:bg-white ${
                  selectedId === conv.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 overflow-hidden">
                    <div className="mb-1 flex items-center gap-2">
                      <h3 className="truncate text-sm font-medium text-gray-900">
                        {conv.title}
                      </h3>
                      {conv.document_count > 0 && (
                        <svg
                          className="h-4 w-4 flex-shrink-0 text-blue-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                          aria-label={`${conv.document_count}개 문서 첨부`}
                        >
                          <title>{`${conv.document_count}개 문서 첨부`}</title>
                          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                        </svg>
                      )}
                      <span className="text-xs text-gray-400">
                        {conv.message_count}
                      </span>
                    </div>

                    {/* Tags */}
                    {conv.tags.length > 0 && (
                      <div className="mb-1 flex flex-wrap gap-1">
                        {conv.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-600"
                          >
                            {tag}
                          </span>
                        ))}
                        {conv.tags.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{conv.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="text-xs text-gray-500">
                      {formatDate(conv.updated_at)}
                    </div>
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={(e) => handleDelete(conv.id, e)}
                    className="ml-2 opacity-0 transition-opacity group-hover:opacity-100"
                    title="삭제"
                  >
                    <svg
                      className="h-4 w-4 text-gray-400 hover:text-red-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {total > 0 && (
        <div className="border-t bg-white p-3 text-center text-xs text-gray-500">
          총 {total}개의 대화
        </div>
      )}
    </div>
  )
})

ConversationList.displayName = 'ConversationList'

export default ConversationList
