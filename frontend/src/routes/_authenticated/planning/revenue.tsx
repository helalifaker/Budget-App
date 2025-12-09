/**
 * Legacy route - redirects to /finance/revenue
 * @deprecated Use /finance/revenue instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/planning/revenue')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/revenue' })
  },
})
