/**
 * Legacy Route Redirect: /planning/classes → /enrollment/class-structure
 *
 * This route maintains backward compatibility for existing bookmarks and links.
 * The actual content has been migrated to /enrollment/class-structure as part of
 * the module-centric URL restructuring.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'

export const Route = createFileRoute('/_authenticated/planning/classes')({
  beforeLoad: async () => {
    await requireAuth()
    throw redirect({ to: '/enrollment/class-structure' })
  },
})
