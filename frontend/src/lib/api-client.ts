import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import { supabase } from './supabase'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession()

    if (error) {
      console.warn('[api-client] Error getting session:', error)
    }

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
      // Debug: Log token attachment (only in dev)
      if (import.meta.env.DEV) {
        console.log(
          `[api-client] ✅ Adding Authorization header, token length: ${session.access_token.length}, ` +
            `user: ${session.user.email}`
        )
      }
    } else {
      // Debug: Warn if no session when making API call
      if (import.meta.env.DEV) {
        console.warn(
          `[api-client] ⚠️ No session found for request to ${config.url}. ` +
            'This may cause 401 errors.'
        )
      }
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Check if we have a valid Supabase session
      const {
        data: { session },
      } = await supabase.auth.getSession()

      if (!session) {
        // No session - user is truly unauthenticated, redirect to login
        await supabase.auth.signOut()
        window.location.href = '/login'
      } else {
        // Session exists but backend returned 401
        // This likely means backend JWT verification failed (e.g., SUPABASE_JWT_SECRET not configured)
        // Don't sign out - let the error propagate so user can see the issue
        console.warn(
          '[api-client] Received 401 but Supabase session exists. ' +
            'This may indicate backend JWT configuration issue. ' +
            'Check backend logs and ensure SUPABASE_JWT_SECRET is configured.'
        )
      }
    }
    return Promise.reject(error)
  }
)

export { apiClient }

// Generic API request function
export async function apiRequest<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<T>(config)
  return response.data
}
