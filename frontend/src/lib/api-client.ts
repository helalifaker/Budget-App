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
    } = await supabase.auth.getSession()

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
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
      await supabase.auth.signOut()
      window.location.href = '/login'
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
