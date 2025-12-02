import { useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

export function useAuthRedirect() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && user) {
      navigate({ to: '/dashboard' })
    }
  }, [user, loading, navigate])
}
