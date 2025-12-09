/**
 * Legacy route - redirects to /finance/capex
 * @deprecated Use /finance/capex instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/planning/capex')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/capex' })
  },
})
