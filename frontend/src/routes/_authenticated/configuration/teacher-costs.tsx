/**
 * Redirect: /configuration/teacher-costs → /workforce/settings
 * Teacher costs configuration has been moved to the Workforce module settings.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/configuration/teacher-costs')({
  beforeLoad: async () => {
    throw redirect({ to: '/workforce/settings' })
  },
})
