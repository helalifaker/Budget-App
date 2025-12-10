/**
 * Redirect: /configuration/subject-hours → /workforce/settings
 * Subject hours configuration has been moved to the Workforce module settings.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/configuration/subject-hours')({
  beforeLoad: async () => {
    throw redirect({ to: '/workforce/settings' })
  },
})
