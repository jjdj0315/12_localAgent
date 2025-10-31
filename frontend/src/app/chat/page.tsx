'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { chatAPI, conversationsAPI } from '@/lib/api'
import ConversationList, { ConversationListHandle } from '@/components/chat/ConversationList'
import DocumentSelector from '@/components/chat/DocumentSelector'
import FilterWarningModal from '@/components/safety/FilterWarningModal'
import PIIMaskingNotice from '@/components/safety/PIIMaskingNotice'
import ReActDisplay from '@/components/react/ReActDisplay'
import MultiAgentDisplay from '@/components/agents/MultiAgentDisplay'
import type { Message as APIMessage } from '@/types/conversation'

interface ReActStep {
  iteration: number
  thought: string
  action?: string
  action_input?: Record<string, any>
  observation?: string
  timestamp: string
}

interface AgentContribution {
  agent_name: string
  display_name: string
  contribution: string
  execution_time_ms: number
  success: boolean
}

interface MultiAgentInfo {
  workflow_type: string
  agent_contributions: AgentContribution[]
  total_execution_time_ms: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  react_steps?: ReActStep[]
  tools_used?: string[]
  multi_agent_info?: MultiAgentInfo
}

interface FilterWarning {
  message: string
  categories: string[]
  canRetry: boolean
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

  // Safety Filter states
  const [filterWarning, setFilterWarning] = useState<FilterWarning | null>(null)
  const [showFilterModal, setShowFilterModal] = useState(false)
  const [piiMasked, setPiiMasked] = useState(false)
  const [bypassFilter, setBypassFilter] = useState(false)

  // ReAct Agent state
  const [useReActAgent, setUseReActAgent] = useState(false)

  // Multi-Agent state
  const [useMultiAgent, setUseMultiAgent] = useState(false)

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

    // Reset PII notice and bypass flag
    setPiiMasked(false)
    const currentBypassFlag = bypassFilter
    setBypassFilter(false)

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

    // Use non-streaming API when ReAct or Multi-Agent is enabled
    if (useReActAgent || useMultiAgent) {
      try {
        const response = await chatAPI.sendMessage({
          content: currentInput,
          conversation_id: selectedConversationId,
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : undefined,
          bypass_filter: currentBypassFlag,
          use_react_agent: useReActAgent,
          use_multi_agent: useMultiAgent,
        })

        // Update assistant message with response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: response.message.content,
                  react_steps: response.react_steps,
                  tools_used: response.tools_used,
                  multi_agent_info: response.multi_agent_info,
                }
              : msg
          )
        )

        setIsLoading(false)

        // Update conversation ID if this was a new conversation
        if (response.conversation_id && !selectedConversationId) {
          setSelectedConversationId(response.conversation_id)
          conversationsAPI.get(response.conversation_id).then((conv) => {
            setConversationTitle(conv.title)
          })
        }

        // Refresh conversation list
        conversationListRef.current?.refresh()
      } catch (error: any) {
        console.error('ReAct error:', error)

        // Check if this is a content filter error
        if (error.error === 'content_filtered' || error.details?.error === 'content_filtered') {
          // Remove the placeholder assistant message
          setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))

          // Show filter warning modal
          setFilterWarning({
            message: error.message || error.details?.message || '콘텐츠가 필터링되었습니다.',
            categories: error.details?.categories || [],
            canRetry: error.details?.can_retry || false
          })
          setShowFilterModal(true)
          setInput(currentInput) // Restore input for retry
        } else {
          // Regular error
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: '죄송합니다. 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'),
                  }
                : msg
            )
          )
        }
        setIsLoading(false)
      }
    } else {
      // Use streaming API for standard mode
      try {
        await chatAPI.streamMessage(
          {
            content: currentInput,
            conversation_id: selectedConversationId,
            document_ids: selectedDocuments.length > 0 ? selectedDocuments : undefined,
            bypass_filter: currentBypassFlag,
            use_react_agent: false,
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
        // onError: show error message or filter warning
        (error: any) => {
          console.error('Chat error:', error)

          // Check if this is a content filter error
          if (error.error === 'content_filtered') {
            // Remove the placeholder assistant message
            setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))

            // Show filter warning modal
            setFilterWarning({
              message: error.message || '콘텐츠가 필터링되었습니다.',
              categories: error.categories || [],
              canRetry: error.can_retry || false
            })
            setShowFilterModal(true)
            setInput(currentInput) // Restore input for retry
          } else {
            // Regular error
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
          }
          setIsLoading(false)
        }
      )
      } catch (error: any) {
        console.error('Chat error:', error)

      // Check if this is a content filter error
      if (error.error === 'content_filtered') {
        // Remove the placeholder assistant message
        setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))

        // Show filter warning modal
        setFilterWarning({
          message: error.message || '콘텐츠가 필터링되었습니다.',
          categories: error.categories || [],
          canRetry: error.can_retry || false
        })
        setShowFilterModal(true)
        setInput(currentInput) // Restore input for retry
      } else {
        // Regular error
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
      }
      setIsLoading(false)
      }
    }
  }

  // Handle retry with filter bypass
  const handleRetryWithBypass = () => {
    setBypassFilter(true)
    setShowFilterModal(false)
    // Automatically send with bypass flag
    setTimeout(() => handleSend(), 100)
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
              <div key={message.id}>
                {/* Multi-Agent Display for assistant messages with multi-agent info */}
                {message.role === 'assistant' && message.multi_agent_info && (
                  <MultiAgentDisplay
                    workflowType={message.multi_agent_info.workflow_type}
                    agentContributions={message.multi_agent_info.agent_contributions}
                    totalExecutionTimeMs={message.multi_agent_info.total_execution_time_ms}
                  />
                )}

                {/* ReAct Display for assistant messages with ReAct steps */}
                {message.role === 'assistant' && message.react_steps && message.tools_used && (
                  <ReActDisplay
                    steps={message.react_steps}
                    toolsUsed={message.tools_used}
                  />
                )}

                {/* Regular message bubble */}
                <div
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
            {/* PII Masking Notice */}
            {piiMasked && (
              <PIIMaskingNotice
                piiDetails={[
                  { type: 'korean_id', description: '주민등록번호', count: 1 }
                ]}
                onDismiss={() => setPiiMasked(false)}
              />
            )}

            {/* Document Selector */}
            <DocumentSelector
              selectedDocuments={selectedDocuments}
              onSelectionChange={setSelectedDocuments}
            />

            {/* Agent Mode Toggles */}
            <div className="space-y-2">
              {/* ReAct Agent Toggle */}
              <div className="flex items-center justify-between bg-purple-50 border border-purple-200 rounded-lg px-4 py-3">
                <div className="flex items-center">
                  <span className="text-lg mr-2">🔧</span>
                  <div>
                    <div className="text-sm font-medium text-purple-900">ReAct 에이전트 모드</div>
                    <div className="text-xs text-purple-600">
                      AI가 도구를 사용하여 단계별로 문제를 해결합니다
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setUseReActAgent(!useReActAgent);
                    if (!useReActAgent) setUseMultiAgent(false); // Multi-Agent 비활성화
                  }}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useReActAgent ? 'bg-purple-600' : 'bg-gray-300'
                  }`}
                  aria-label="ReAct 에이전트 모드 전환"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useReActAgent ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Multi-Agent Toggle */}
              <div className="flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-3">
                <div className="flex items-center">
                  <span className="text-lg mr-2">🤖</span>
                  <div>
                    <div className="text-sm font-medium text-indigo-900">Multi-Agent 모드</div>
                    <div className="text-xs text-indigo-600">
                      여러 전문 에이전트가 협력하여 복잡한 작업을 처리합니다
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setUseMultiAgent(!useMultiAgent);
                    if (!useMultiAgent) setUseReActAgent(false); // ReAct 비활성화
                  }}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useMultiAgent ? 'bg-indigo-600' : 'bg-gray-300'
                  }`}
                  aria-label="Multi-Agent 모드 전환"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useMultiAgent ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

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

      {/* Filter Warning Modal */}
      {filterWarning && (
        <FilterWarningModal
          isOpen={showFilterModal}
          onClose={() => setShowFilterModal(false)}
          onRetry={filterWarning.canRetry ? handleRetryWithBypass : undefined}
          message={filterWarning.message}
          categories={filterWarning.categories}
          canRetry={filterWarning.canRetry}
        />
      )}
    </div>
  )
}
