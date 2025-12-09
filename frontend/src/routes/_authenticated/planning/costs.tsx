/**
 * Legacy route - redirects to /finance/costs
 * @deprecated Use /finance/costs instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/planning/costs')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/costs' })
  },
})
