import { redirect } from '@tanstack/react-router'
import { supabase } from './supabase'

// E2E Test Mode: Check if running in Playwright test environment
const isE2ETestMode = import.meta.env.VITE_E2E_TEST_MODE === 'true'

// Storage key for E2E mock session (matches AuthProvider)
const E2E_SESSION_KEY = 'efir_e2e_mock_session'

/**
 * Auth guard function for protected routes
 * Checks if user is authenticated and redirects to login if not
 *
 * In E2E test mode, checks localStorage for mock session instead of Supabase
 *
 * Usage in route files:
 * ```ts
 * export const Route = createFileRoute('/protected-route')({
 *   beforeLoad: requireAuth,
 *   component: ProtectedComponent,
 * })
 * ```
 */
export async function requireAuth() {
  // E2E Test Mode: Check localStorage for mock session
  if (isE2ETestMode) {
    const mockSession = localStorage.getItem(E2E_SESSION_KEY)
    if (!mockSession) {
      throw redirect({
        to: '/login',
      })
    }
    return { session: JSON.parse(mockSession) }
  }

  // Real Supabase authentication
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw redirect({
      to: '/login',
    })
  }

  return { session }
}

/**
 * Auth guard with redirect tracking
 * Saves the current path so user can be redirected back after login
 */
export async function requireAuthWithRedirect(pathname: string) {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw redirect({
      to: '/login',
      search: {
        redirect: pathname,
      },
    })
  }

  return { session }
}
