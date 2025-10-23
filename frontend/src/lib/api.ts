/**
 * API client for communicating with backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

/**
 * Make API request with credentials
 */
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Include cookies for session
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: 'An error occurred',
    }))
    throw new APIError(response.status, error.message || 'Request failed', error)
  }

  return response.json()
}

/**
 * Authentication API
 */
export const authAPI = {
  login: async (username: string, password: string) => {
    return fetchAPI('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  logout: async () => {
    return fetchAPI('/auth/logout', { method: 'POST' })
  },

  getCurrentUser: async () => {
    return fetchAPI('/auth/me')
  },
}

/**
 * Chat API
 */
export const chatAPI = {
  sendMessage: async (data: {
    conversation_id?: string
    content: string
    document_ids?: string[]
  }) => {
    return fetchAPI('/chat/send', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  streamMessage: async (
    data: {
      conversation_id?: string
      content: string
      document_ids?: string[]
    },
    onToken: (token: string) => void,
    onDone: (message: any) => void,
    onError: (error: Error) => void
  ) => {
    const url = `${API_URL}/chat/stream`

    try {
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }))
        throw new APIError(response.status, error.message || 'Request failed', error)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.substring(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.substring(6)
            try {
              const data = JSON.parse(dataStr)

              if (currentEvent === 'token' && data.token !== undefined) {
                onToken(data.token)
              } else if (currentEvent === 'done' && data.conversation_id && data.message_id) {
                console.log('Done event received:', data)
                onDone(data)
              } else if (currentEvent === 'error' && data.error) {
                onError(new Error(data.error))
              }

              // Reset current event after processing
              currentEvent = ''
            } catch (e) {
              console.error('JSON parse error:', e, 'Data:', dataStr)
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown error'))
    }
  },
}

/**
 * Conversations API
 */
export const conversationsAPI = {
  list: async (params?: { page?: number; page_size?: number; search?: string; tag?: string }) => {
    const query = new URLSearchParams(
      Object.entries(params || {})
        .filter(([_, v]) => v !== undefined)
        .reduce((acc, [k, v]) => ({ ...acc, [k]: String(v) }), {})
    ).toString()
    return fetchAPI(`/conversations${query ? '?' + query : ''}`)
  },

  create: async (data: { title?: string; tags?: string[] }) => {
    return fetchAPI('/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  get: async (id: string) => {
    return fetchAPI(`/conversations/${id}`)
  },

  update: async (id: string, data: { title?: string; tags?: string[] }) => {
    return fetchAPI(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  delete: async (id: string) => {
    return fetchAPI(`/conversations/${id}`, { method: 'DELETE' })
  },
}

/**
 * Documents API
 */
export const documentsAPI = {
  list: async (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams(params as any).toString()
    return fetchAPI(`/documents?${query}`)
  },

  upload: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_URL}/documents`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new APIError(response.status, error.message, error)
    }

    return response.json()
  },

  delete: async (id: string) => {
    return fetchAPI(`/documents/${id}`, { method: 'DELETE' })
  },
}

/**
 * Admin API
 */
export const adminAPI = {
  listUsers: async (params?: { page?: number; page_size?: number }) => {
    const queryParams: Record<string, string> = {}
    if (params?.page) queryParams.page = params.page.toString()
    if (params?.page_size) queryParams.page_size = params.page_size.toString()
    const query = new URLSearchParams(queryParams).toString()
    return fetchAPI(`/admin/users${query ? `?${query}` : ''}`)
  },

  createUser: async (data: { username: string; password: string; is_admin?: boolean }) => {
    return fetchAPI('/admin/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  deleteUser: async (userId: string) => {
    return fetchAPI(`/admin/users/${userId}`, { method: 'DELETE' })
  },

  resetPassword: async (userId: string) => {
    return fetchAPI(`/admin/users/${userId}/reset-password`, { method: 'POST' })
  },

  getStats: async () => {
    return fetchAPI('/admin/stats')
  },
}
