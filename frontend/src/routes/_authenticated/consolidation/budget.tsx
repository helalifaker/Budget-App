/**
 * Legacy route - redirects to /finance/consolidation
 * @deprecated Use /finance/consolidation instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/consolidation/budget')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/consolidation' })
  },
})
