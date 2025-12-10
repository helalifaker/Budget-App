/**
 * Redirect: /configuration/fees → /finance/settings
 * Fee structure configuration has been moved to the Finance module settings.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/configuration/fees')({
  beforeLoad: async () => {
    throw redirect({ to: '/finance/settings' })
  },
})
