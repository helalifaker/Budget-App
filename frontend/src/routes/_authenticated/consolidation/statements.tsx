/**
 * Legacy route - redirects to /finance/statements
 * @deprecated Use /finance/statements instead
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/consolidation/statements')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/statements' })
  },
})
