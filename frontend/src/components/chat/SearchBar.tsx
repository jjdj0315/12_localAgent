'use client'

/**
 * SearchBar Component
 * Provides search and tag filtering functionality for conversations
 */

import { useState, useEffect } from 'react'

interface SearchBarProps {
  onSearch: (searchTerm: string) => void
  onTagFilter: (tag: string | undefined) => void
  selectedTag?: string
}

export default function SearchBar({
  onSearch,
  onTagFilter,
  selectedTag,
}: SearchBarProps) {
  const [searchInput, setSearchInput] = useState('')

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(searchInput)
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [searchInput, onSearch])

  const handleClearTag = () => {
    onTagFilter(undefined)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {/* Search Input */}
      <div className="flex items-center space-x-3">
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="제목이나 태그로 검색..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Clear Search */}
        {searchInput && (
          <button
            onClick={() => setSearchInput('')}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg
              className="w-5 h-5"
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
        )}
      </div>

      {/* Active Tag Filter */}
      {selectedTag && (
        <div className="mt-3 flex items-center space-x-2">
          <span className="text-sm text-gray-600">필터:</span>
          <div className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
            <span>{selectedTag}</span>
            <button
              onClick={handleClearTag}
              className="ml-1 hover:text-blue-900"
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
        </div>
      )}

      {/* Help Text */}
      <p className="mt-2 text-xs text-gray-500">
        제목, 태그, 메시지 내용을 기반으로 검색합니다
      </p>
    </div>
  )
}
