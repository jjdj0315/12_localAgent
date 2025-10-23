/**
 * Conversation and message types for the frontend
 */

export interface Conversation {
  id: string
  user_id: string
  title: string
  tags: string[]
  created_at: string
  updated_at: string
  message_count: number
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  char_count: number
  created_at: string
}

export interface ConversationWithMessages extends Omit<Conversation, 'message_count'> {
  messages: Message[]
}

export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  page_size: number
  has_next: boolean
}

export interface ConversationCreateRequest {
  title?: string
  tags?: string[]
}

export interface ConversationUpdateRequest {
  title?: string
  tags?: string[]
}
