'use client'

/**
 * Conversation History Page
 * Displays list of user's conversations with search and filtering
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { conversationsAPI } from '@/lib/api'
import { Conversation } from '@/types/conversation'
import ConversationCard from '@/components/chat/ConversationCard'
import SearchBar from '@/components/chat/SearchBar'

export const dynamic = 'force-dynamic'

export default function HistoryPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | undefined>(undefined)

  // Fetch conversations
  const { data, isLoading, error } = useQuery({
    queryKey: ['conversations', page, search, selectedTag],
    queryFn: () => conversationsAPI.list({
      page,
      page_size: 20,
      search: search || undefined,
      tag: selectedTag
    }),
  })

  const handleSearch = (searchTerm: string) => {
    setSearch(searchTerm)
    setPage(1) // Reset to first page
  }

  const handleTagFilter = (tag: string | undefined) => {
    setSelectedTag(tag)
    setPage(1)
  }

  const handleConversationClick = (id: string) => {
    router.push(`/chat?conversation_id=${id}`)
  }

  const handleDeleteConversation = async (id: string) => {
    try {
      await conversationsAPI.delete(id)
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    } catch (err) {
      console.error('Failed to delete conversation:', err)
    }
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">
          대화 목록을 불러오는데 실패했습니다.
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">대화 기록</h1>
          <p className="text-gray-600">
            이전 대화를 검색하고 다시 시작할 수 있습니다
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6">
          <SearchBar
            onSearch={handleSearch}
            onTagFilter={handleTagFilter}
            selectedTag={selectedTag}
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">대화 목록을 불러오는 중...</p>
          </div>
        )}

        {/* Conversation List */}
        {!isLoading && data && (
          <>
            {data.conversations.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500 text-lg">대화 기록이 없습니다</p>
                <button
                  onClick={() => router.push('/chat')}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  새 대화 시작하기
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {data.conversations.map((conversation: Conversation) => (
                  <ConversationCard
                    key={conversation.id}
                    conversation={conversation}
                    onClick={() => handleConversationClick(conversation.id)}
                    onDelete={() => handleDeleteConversation(conversation.id)}
                  />
                ))}
              </div>
            )}

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
              총 {data.total}개의 대화
            </div>
          </>
        )}
      </div>
    </div>
  )
}
