/**
 * Authenticated Layout Route
 *
 * This layout route wraps all authenticated pages with the ModuleLayout.
 * The ModuleLayout (Phase 2 UI Redesign) provides:
 * - AppSidebar (64px collapsed, 240px expanded)
 * - ModuleHeader (48px) with search, version selector, user avatar
 * - WorkflowTabs (40px) with automatic settings tab detection
 * - TaskDescription (32px) contextual help
 * - Total Chrome: 120px
 *
 * TanStack Router convention: files starting with `_` are layout routes
 */

import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { ModuleLayout } from '@/components/layout/ModuleLayout'

export const Route = createFileRoute('/_authenticated')({
  // Optional: Add authentication check here
  beforeLoad: async ({ location }) => {
    // Check if user is authenticated
    // For now, we'll allow all access - add auth check when ready
    const isAuthenticated = true // Replace with actual auth check

    if (!isAuthenticated) {
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      })
    }
  },
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  return (
    <ModuleLayout>
      <Outlet />
    </ModuleLayout>
  )
}
