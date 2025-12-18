import { createFileRoute, Navigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { Loader2 } from 'lucide-react'
import { colors } from '@/lib/theme.constants'

export const Route = createFileRoute('/')({
  component: IndexRedirect,
})

function IndexRedirect() {
  const { user, loading } = useAuth()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{
          background: `linear-gradient(to bottom right, ${colors.bg.canvas}, ${colors.bg.subtle})`,
        }}
      >
        <div className="text-center">
          <Loader2
            className="w-8 h-8 animate-spin mx-auto mb-4"
            style={{ color: colors.accent.gold.DEFAULT }}
          />
          <p style={{ color: colors.text.secondary }}>Loading...</p>
        </div>
      </div>
    )
  }

  // Redirect based on authentication status
  if (user) {
    return <Navigate to="/command-center" />
  }

  return <Navigate to="/login" />
}
