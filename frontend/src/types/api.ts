/**
 * API TypeScript types and interfaces
 *
 * These types are based on the backend Pydantic schemas and provide
 * type safety for API requests and responses.
 */

// Base types
export type UUID = string;

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  user: UserProfile;
}

export interface UserProfile {
  id: UUID;
  username: string;
  is_admin: boolean;
  created_at: string;
  last_login_at: string | null;
}

// Conversation types
export interface ConversationBase {
  title: string;
  tags?: string[];
}

export interface ConversationCreate extends ConversationBase {}

export interface ConversationUpdate {
  title?: string;
  tags?: string[];
}

export interface ConversationResponse extends ConversationBase {
  id: UUID;
  user_id: UUID;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends ConversationResponse {
  messages: MessageResponse[];
}

export interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
  page: number;
  page_size: number;
}

// Message types
export type MessageRole = "user" | "assistant";

export interface MessageBase {
  role: MessageRole;
  content: string;
}

export interface MessageCreate extends MessageBase {
  conversation_id?: UUID;
}

export interface MessageResponse extends MessageBase {
  id: UUID;
  conversation_id: UUID;
  char_count: number;
  created_at: string;
}

export interface MessageListResponse {
  messages: MessageResponse[];
  total: number;
}

// Chat types
export interface ChatRequest {
  message: string;
  conversation_id?: UUID;
  document_ids?: UUID[];
}

export interface ChatResponse {
  conversation_id: UUID;
  message: MessageResponse;
}

// Document types
export interface DocumentBase {
  filename: string;
  file_type: string;
}

export interface DocumentCreate extends DocumentBase {}

export interface DocumentUpdate {
  filename?: string;
}

export interface DocumentResponse extends DocumentBase {
  id: UUID;
  user_id: UUID;
  file_path: string;
  file_size: number;
  uploaded_at: string;
}

export interface DocumentWithText extends DocumentResponse {
  extracted_text?: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
}

// Admin types
export interface UserCreate {
  username: string;
  password: string;
  is_admin?: boolean;
}

export interface UserResponse {
  id: UUID;
  username: string;
  is_admin: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface UserListResponse {
  users: UserResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface PasswordResetResponse {
  username: string;
  temporary_password: string;
  message: string;
}

export interface StatsResponse {
  active_users_today: number;
  active_users_week: number;
  active_users_month: number;
  total_queries_today: number;
  total_queries_week: number;
  total_queries_month: number;
  avg_response_time_today: number;
  avg_response_time_week: number;
  avg_response_time_month: number;
}

export interface SystemHealthResponse {
  server_uptime_seconds: number;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  available_storage_gb: number;
  total_storage_gb: number;
  llm_service_status: "healthy" | "degraded" | "unavailable";
  database_status: "healthy" | "degraded" | "unavailable";
  gpu_usage_percent?: number;
  gpu_memory_usage_percent?: number;
}

export interface StorageUsageResponse {
  user_id: UUID;
  username: string;
  total_storage_bytes: number;
  document_count: number;
  conversation_count: number;
}

export interface StorageStatsResponse {
  total_storage_used_bytes: number;
  total_storage_available_bytes: number;
  usage_percent: number;
  user_storage: StorageUsageResponse[];
  warning_threshold_exceeded: boolean;
  critical_threshold_exceeded: boolean;
}

// Error types
export interface APIError {
  detail: string;
  status_code?: number;
}

// Pagination params
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// Search params
export interface SearchParams extends PaginationParams {
  search?: string;
  tag?: string;
}
