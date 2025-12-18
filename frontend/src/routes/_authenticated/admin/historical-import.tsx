/**
 * Redirect: /admin/historical-import → /admin/uploads
 * Historical data import has been consolidated with Data Uploads.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/admin/historical-import')({
  beforeLoad: async () => {
    throw redirect({ to: '/admin/uploads' })
  },
})
