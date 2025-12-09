import { createFileRoute, Navigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { Loader2 } from 'lucide-react'

export const Route = createFileRoute('/')({
  component: IndexRedirect,
})

function IndexRedirect() {
  const { user, loading } = useAuth()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
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
