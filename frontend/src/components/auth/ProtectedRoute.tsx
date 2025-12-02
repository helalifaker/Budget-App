import { ReactNode } from 'react'
import { Navigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: string
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading, session } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary" />
      </div>
    )
  }

  if (!user || !session) {
    return <Navigate to="/login" />
  }

  if (requiredRole && session) {
    const userRole = session.user.user_metadata?.role
    if (userRole !== requiredRole && userRole !== 'admin') {
      return <Navigate to="/login" />
    }
  }

  return <>{children}</>
}
