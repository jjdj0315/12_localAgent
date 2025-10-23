/**
 * Admin types for user management and system monitoring
 */

export interface User {
  id: string
  username: string
  is_admin: boolean
  created_at: string
  last_login_at: string | null
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
}

export interface PasswordResetResponse {
  username: string
  temporary_password: string
  message: string
}

export interface UsageStats {
  active_users_today: number
  active_users_week: number
  active_users_month: number
  total_queries_today: number
  total_queries_week: number
  total_queries_month: number
  avg_response_time_today: number
  avg_response_time_week: number
  avg_response_time_month: number
}

export interface SystemHealth {
  server_uptime_seconds: number
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
  available_storage_gb: number
  total_storage_gb: number
  llm_service_status: string
  database_status: string
  gpu_usage_percent: number | null
  gpu_memory_usage_percent: number | null
}

export interface StorageUsage {
  user_id: string
  username: string
  total_storage_bytes: number
  document_count: number
  conversation_count: number
}

export interface StorageStats {
  total_storage_used_bytes: number
  total_storage_available_bytes: number
  usage_percent: number
  user_storage: StorageUsage[]
  warning_threshold_exceeded: boolean
  critical_threshold_exceeded: boolean
}
