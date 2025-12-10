/**
 * Redirect: /admin/historical-import → /configuration/uploads
 * Historical data import has been moved to Configuration > Uploads.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/admin/historical-import')({
  beforeLoad: async () => {
    throw redirect({ to: '/configuration/uploads' })
  },
})
