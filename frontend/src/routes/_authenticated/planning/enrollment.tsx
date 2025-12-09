/**
 * Legacy route - redirects to /enrollment/planning
 * @deprecated Use /enrollment/planning instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'

export const Route = createFileRoute('/_authenticated/planning/enrollment')({
  beforeLoad: async () => {
    await requireAuth()
    throw redirect({ to: '/enrollment/planning' })
  },
})
