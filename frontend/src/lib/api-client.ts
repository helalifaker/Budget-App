import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import { Session } from '@supabase/supabase-js'
import { supabase } from './supabase'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// E2E Test Mode: Check if running in Playwright test environment
const isE2ETestMode = import.meta.env.VITE_E2E_TEST_MODE === 'true'

// Storage key for E2E mock session (must match AuthProvider.tsx)
const E2E_SESSION_KEY = 'efir_e2e_mock_session'

// Cache session in memory to avoid async getSession() calls in interceptor
let cachedSession: Session | null = null
let hasLoggedAuthSuccess = false

/**
 * Get E2E mock session from localStorage if in E2E mode.
 * Returns null if not in E2E mode or no mock session exists.
 */
function getE2EMockSession(): Session | null {
  if (!isE2ETestMode) return null

  try {
    const storedSession = localStorage.getItem(E2E_SESSION_KEY)
    if (storedSession) {
      const mockSession = JSON.parse(storedSession) as Session
      if (import.meta.env.DEV) {
        console.log(`[api-client] 🧪 E2E mock session found for: ${mockSession.user?.email}`)
      }
      return mockSession
    }
  } catch (e) {
    console.error('[api-client] 🧪 Failed to parse E2E mock session:', e)
  }
  return null
}

// Initialize session cache
if (isE2ETestMode) {
  // E2E Mode: Use mock session from localStorage
  cachedSession = getE2EMockSession()
  if (cachedSession && import.meta.env.DEV) {
    console.log(`[api-client] 🧪 E2E session cache initialized for: ${cachedSession.user?.email}`)
  } else if (import.meta.env.DEV) {
    console.log('[api-client] 🧪 E2E mode active but no mock session found yet')
  }

  // In E2E mode, poll localStorage for session changes (since we don't use real Supabase auth)
  // This handles cases where the session is set after api-client initializes
  setInterval(() => {
    const mockSession = getE2EMockSession()
    if (mockSession?.access_token !== cachedSession?.access_token) {
      cachedSession = mockSession
      hasLoggedAuthSuccess = false
      if (import.meta.env.DEV && mockSession) {
        console.log(`[api-client] 🧪 E2E session cache updated: ${mockSession.user?.email}`)
      }
    }
  }, 500) // Check every 500ms
} else {
  // Normal Mode: Use real Supabase session
  supabase.auth.getSession().then(({ data: { session }, error }) => {
    if (error) {
      console.warn('[api-client] Error initializing session cache:', error)
    }
    cachedSession = session
    if (session && import.meta.env.DEV) {
      console.log(`[api-client] ✅ Session cache initialized for user: ${session.user.email}`)
    }
  })

  // Subscribe to auth state changes to keep cache updated
  supabase.auth.onAuthStateChange((event, session) => {
    const previousSession = cachedSession
    cachedSession = session

    if (import.meta.env.DEV) {
      if (event === 'SIGNED_IN' && session) {
        console.log(`[api-client] ✅ Session cache updated (SIGNED_IN): ${session.user.email}`)
      } else if (event === 'SIGNED_OUT') {
        console.log('[api-client] 🚪 Session cache cleared (SIGNED_OUT)')
      } else if (event === 'TOKEN_REFRESHED' && session) {
        console.log('[api-client] 🔄 Session cache updated (TOKEN_REFRESHED)')
      } else if (event === 'USER_UPDATED' && session) {
        console.log('[api-client] 👤 Session cache updated (USER_UPDATED)')
      }
    }

    // Reset success log flag when session changes
    if (previousSession?.access_token !== session?.access_token) {
      hasLoggedAuthSuccess = false
    }
  })
}

// Request interceptor to add auth token (now synchronous using cached session)
apiClient.interceptors.request.use(
  (config) => {
    if (cachedSession?.access_token) {
      config.headers.Authorization = `Bearer ${cachedSession.access_token}`

      // E2E mode: Send role and user info in custom headers
      // Backend reads these headers to set correct role (instead of hardcoding "planner")
      if (isE2ETestMode && cachedSession.user) {
        const userRole =
          cachedSession.user.app_metadata?.role ||
          cachedSession.user.user_metadata?.role ||
          'planner'
        config.headers['X-E2E-User-Role'] = userRole
        config.headers['X-E2E-User-Email'] = cachedSession.user.email || ''
        config.headers['X-E2E-User-Id'] = cachedSession.user.id || ''

        // Debug: Log E2E headers only once per session (only in dev)
        if (import.meta.env.DEV && !hasLoggedAuthSuccess) {
          console.log(
            `[api-client] 🧪 E2E headers attached: role=${userRole}, email=${cachedSession.user.email}`
          )
          hasLoggedAuthSuccess = true
        }
      } else if (import.meta.env.DEV && !hasLoggedAuthSuccess) {
        // Normal mode: Just log auth token attachment
        console.log(
          `[api-client] ✅ Adding auth token to request for user: ${cachedSession.user.email}`
        )
        hasLoggedAuthSuccess = true
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
      // In E2E mode, 401 likely means backend needs SKIP_AUTH_FOR_TESTS=true
      if (isE2ETestMode) {
        console.warn(
          '[api-client] 🧪 E2E Mode: Received 401. ' +
            'Ensure backend has SKIP_AUTH_FOR_TESTS=true or E2E_TEST_MODE=true configured.'
        )
        // Don't redirect in E2E mode - let the error propagate for debugging
        return Promise.reject(error)
      }

      // Check if we have a valid cached session
      if (!cachedSession) {
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
