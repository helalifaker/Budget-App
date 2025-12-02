import { redirect } from '@tanstack/react-router'
import { supabase } from './supabase'

/**
 * Auth guard function for protected routes
 * Checks if user is authenticated and redirects to login if not
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
