/**
 * Authenticated Layout Route
 *
 * This layout route wraps all authenticated pages with the Executive Cockpit layout.
 * The CockpitLayout replaces the traditional MainLayout:
 * - SmartHeader (48px) instead of full header
 * - ModuleDock (horizontal tabs) instead of sidebar
 * - More content space for AG Grid and data-heavy pages
 *
 * TanStack Router convention: files starting with `_` are layout routes
 */

import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { CockpitLayout } from '@/components/layout/CockpitLayout'
// import { MainLayout } from '@/components/layout/MainLayout' // Legacy layout

/**
 * Feature flag to toggle between layouts during transition
 * Set to false to use the legacy MainLayout
 */
const USE_COCKPIT_LAYOUT = true

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
  // Use Executive Cockpit layout (new) or legacy MainLayout
  if (USE_COCKPIT_LAYOUT) {
    return (
      <CockpitLayout>
        <Outlet />
      </CockpitLayout>
    )
  }

  // Legacy layout (kept for reference)
  // return (
  //   <MainLayout>
  //     <Outlet />
  //   </MainLayout>
  // )

  // Default to CockpitLayout
  return (
    <CockpitLayout>
      <Outlet />
    </CockpitLayout>
  )
}
