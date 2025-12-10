/**
 * Redirect: /configuration/class-sizes → /enrollment/settings
 * Class size configuration has been moved to the Enrollment module settings.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/configuration/class-sizes')({
  beforeLoad: async () => {
    throw redirect({ to: '/enrollment/settings' })
  },
})
