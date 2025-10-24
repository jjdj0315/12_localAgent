'use client'

/**
 * TagEditor Component
 * Allows users to add, remove, and manage conversation tags
 */

import { useState, KeyboardEvent } from 'react'

interface TagEditorProps {
  tags: string[]
  onChange: (tags: string[]) => void
  maxTags?: number
  maxTagLength?: number
}

export default function TagEditor({
  tags,
  onChange,
  maxTags = 10,
  maxTagLength = 50,
}: TagEditorProps) {
  const [inputValue, setInputValue] = useState('')
  const [error, setError] = useState('')

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag()
    } else if (e.key === 'Backspace' && inputValue === '' && tags.length > 0) {
      // Remove last tag on backspace if input is empty
      removeTag(tags.length - 1)
    }
  }

  const addTag = () => {
    const trimmedTag = inputValue.trim()

    // Validation
    if (!trimmedTag) {
      return
    }

    if (tags.length >= maxTags) {
      setError(`최대 ${maxTags}개의 태그만 추가할 수 있습니다`)
      return
    }

    if (trimmedTag.length > maxTagLength) {
      setError(`태그는 ${maxTagLength}자 이하여야 합니다`)
      return
    }

    if (tags.includes(trimmedTag)) {
      setError('이미 추가된 태그입니다')
      return
    }

    // Add tag
    onChange([...tags, trimmedTag])
    setInputValue('')
    setError('')
  }

  const removeTag = (index: number) => {
    onChange(tags.filter((_, i) => i !== index))
    setError('')
  }

  return (
    <div className="space-y-2">
      {/* Tags Display */}
      <div className="flex flex-wrap gap-2">
        {tags.map((tag, index) => (
          <div
            key={index}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
          >
            <span>{tag}</span>
            <button
              onClick={() => removeTag(index)}
              className="hover:text-blue-900 focus:outline-none"
              title="태그 제거"
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

        {/* Input for new tag */}
        {tags.length < maxTags && (
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addTag}
            placeholder={tags.length === 0 ? '태그 추가 (Enter 또는 ,로 구분)' : '태그 추가...'}
            className="px-3 py-1 border border-gray-300 rounded-full text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none min-w-[150px]"
          />
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      {/* Help Text */}
      <p className="text-xs text-gray-500">
        태그를 입력하고 Enter 또는 쉼표(,)를 눌러 추가하세요 ({tags.length}/{maxTags})
      </p>
    </div>
  )
}
