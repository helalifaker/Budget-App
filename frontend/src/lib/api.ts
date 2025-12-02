/**
 * API Client
 *
 * Axios-based API client with authentication and error handling.
 */

import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { supabase } from './supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Create API client instance
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

/**
 * Request interceptor - add authentication token
 */
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor - handle errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401) {
      // Attempt to refresh session
      const {
        data: { session },
      } = await supabase.auth.refreshSession()

      if (session) {
        // Retry original request with new token
        const originalRequest = error.config
        if (originalRequest) {
          originalRequest.headers.Authorization = `Bearer ${session.access_token}`
          return apiClient(originalRequest)
        }
      } else {
        // Redirect to login
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
