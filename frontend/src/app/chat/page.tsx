'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { chatAPI, conversationsAPI } from '@/lib/api'
import ConversationList, { ConversationListHandle } from '@/components/chat/ConversationList'
import DocumentSelector from '@/components/chat/DocumentSelector'
import type { Message as APIMessage } from '@/types/conversation'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function ChatPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedConversationId, setSelectedConversationId] = useState<string>()
  const [conversationTitle, setConversationTitle] = useState<string>('새 대화')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const conversationListRef = useRef<ConversationListHandle>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load conversation when selected
  const loadConversation = async (conversationId: string) => {
    try {
      const conv = await conversationsAPI.get(conversationId)
      setSelectedConversationId(conversationId)
      setConversationTitle(conv.title)

      // Convert API messages to UI messages
      const uiMessages: Message[] = conv.messages.map((msg: APIMessage) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
      }))
      setMessages(uiMessages)
    } catch (error) {
      console.error('Failed to load conversation:', error)
      alert('대화를 불러오는데 실패했습니다.')
    }
  }

  // Start new conversation
  const handleNewConversation = () => {
    setSelectedConversationId(undefined)
    setConversationTitle('새 대화')
    setMessages([])
    setInput('')
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessageId = `user-${Date.now()}-${Math.random()}`
    const userMessage: Message = {
      id: userMessageId,
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    console.log('Creating user message:', userMessageId, input)
    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)

    // Small delay to ensure different timestamp
    await new Promise(resolve => setTimeout(resolve, 10))

    // Create a placeholder message for streaming
    const assistantMessageId = `assistant-${Date.now()}-${Math.random()}`
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }

    console.log('Creating assistant message placeholder:', assistantMessageId)
    setMessages((prev) => [...prev, assistantMessage])

    try {
      await chatAPI.streamMessage(
        {
          content: currentInput,
          conversation_id: selectedConversationId,
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : undefined,
        },
        // onToken: append to assistant message
        (token: string) => {
          console.log('Token received for', assistantMessageId, ':', token)
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id === assistantMessageId) {
                console.log('Updating assistant message, current content:', msg.content.length, 'chars')
                return { ...msg, content: msg.content + token }
              }
              return msg
            })
          )
        },
        // onDone: update conversation info
        (messageData: any) => {
          console.log('Stream completed, message data:', messageData)
          setIsLoading(false)

          // Update conversation ID if this was a new conversation
          if (messageData.conversation_id && !selectedConversationId) {
            setSelectedConversationId(messageData.conversation_id)
            // Load the conversation to get the auto-generated title
            conversationsAPI.get(messageData.conversation_id).then((conv) => {
              setConversationTitle(conv.title)
            })
          }

          // Always refresh conversation list to update timestamps and message counts
          conversationListRef.current?.refresh()
        },
        // onError: show error message
        (error: Error) => {
          console.error('Chat error:', error)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: '죄송합니다. 오류가 발생했습니다: ' + error.message,
                  }
                : msg
            )
          )
          setIsLoading(false)
        }
      )
    } catch (error: any) {
      console.error('Chat error:', error)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: '죄송합니다. 오류가 발생했습니다: ' + error.message,
              }
            : msg
        )
      )
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-80' : 'w-0'
        } flex-shrink-0 border-r bg-white transition-all duration-300`}
      >
        {sidebarOpen && (
          <ConversationList
            ref={conversationListRef}
            selectedId={selectedConversationId}
            onSelect={loadConversation}
            onNew={handleNewConversation}
          />
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="border-b bg-white px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-md p-2 hover:bg-gray-100"
                title={sidebarOpen ? '사이드바 숨기기' : '사이드바 표시'}
              >
                <svg
                  className="h-5 w-5 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{conversationTitle}</h1>
                <p className="text-sm text-gray-500">AI 업무 지원 시스템</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user.username}</span>
              <button
                onClick={logout}
                className="rounded-md bg-gray-200 px-4 py-2 text-sm text-gray-700 hover:bg-gray-300"
              >
                로그아웃
              </button>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">안녕하세요! 무엇을 도와드릴까요?</p>
                <p className="mt-2 text-sm">궁금한 내용을 입력해주세요.</p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p
                    className={`mt-1 text-xs ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString('ko-KR')}
                  </p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 animation-delay-200"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 animation-delay-400"></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t bg-white p-6 shadow-lg">
          <div className="mx-auto max-w-3xl space-y-4">
            {/* Document Selector */}
            <DocumentSelector
              selectedDocuments={selectedDocuments}
              onSelectionChange={setSelectedDocuments}
            />

            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="메시지를 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
                className="flex-1 resize-none rounded-lg border border-gray-300 p-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:bg-gray-400"
              >
                전송
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
