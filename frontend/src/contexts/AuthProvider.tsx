import React, { useEffect, useState } from 'react'
import { Session, User } from '@supabase/supabase-js'

import { supabase } from '@/lib/supabase'

import { AuthContext, type AuthContextType } from './AuthContext'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Initial session check
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        console.error('[AuthProvider] Error getting session:', error)
      }
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)

      // Debug: Log session status
      if (session) {
        console.log('[AuthProvider] ✅ Session found on init:', {
          userId: session.user.id,
          email: session.user.email,
          expiresAt: new Date(session.expires_at! * 1000).toISOString(),
        })
      } else {
        console.log('[AuthProvider] ⚠️ No session on init')
      }
    })

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('[AuthProvider] Auth state changed:', event, {
        hasSession: !!session,
        userId: session?.user?.id,
      })

      // Use session directly from the event (more reliable than calling getSession again)
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      console.error('[AuthProvider] Sign-in error:', error)
      return { error }
    }

    // Verify session exists after sign-in
    if (data.session) {
      console.log('[AuthProvider] ✅ Sign-in successful, session:', {
        userId: data.session.user.id,
        email: data.session.user.email,
        expiresAt: new Date(data.session.expires_at! * 1000).toISOString(),
      })
      // Session will be updated via onAuthStateChange
    } else {
      console.warn('[AuthProvider] ⚠️ Sign-in succeeded but no session returned')
    }

    return { error }
  }

  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    })
    return { error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    return { error }
  }

  const value: AuthContextType = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    resetPassword,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
