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
