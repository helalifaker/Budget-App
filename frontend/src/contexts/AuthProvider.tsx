import React, { useEffect, useState } from 'react'
import { Session, User, AuthError } from '@supabase/supabase-js'

import { supabase } from '@/lib/supabase'

import { AuthContext, type AuthContextType } from './AuthContext'

// E2E Test Mode: Check if running in Playwright test environment
const isE2ETestMode = import.meta.env.VITE_E2E_TEST_MODE === 'true'

// Storage key for E2E mock session (must match auth-guard.ts)
const E2E_SESSION_KEY = 'efir_e2e_mock_session'

// Test users for E2E testing (matches tests/e2e/fixtures/test-data.ts)
const TEST_USERS: Record<string, { id: string; email: string; role: string }> = {
  'admin@efir.local': { id: 'test-admin-id', email: 'admin@efir.local', role: 'Admin' },
  'manager@efir.local': { id: 'test-manager-id', email: 'manager@efir.local', role: 'Finance Director' },
  'user@efir.local': { id: 'test-user-id', email: 'user@efir.local', role: 'Viewer' },
  'hr@efir.local': { id: 'test-hr-id', email: 'hr@efir.local', role: 'HR' },
  'academic@efir.local': { id: 'test-academic-id', email: 'academic@efir.local', role: 'Academic' },
  // Additional test users for auth.spec.ts
  'test@efir.local': { id: 'test-default-id', email: 'test@efir.local', role: 'Finance Director' },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // E2E Test Mode: Restore mock session from localStorage if exists
    if (isE2ETestMode) {
      console.log('[AuthProvider] 🧪 E2E Test Mode enabled - Supabase auth bypassed')
      const storedSession = localStorage.getItem(E2E_SESSION_KEY)
      if (storedSession) {
        try {
          const mockSession = JSON.parse(storedSession) as Session
          console.log('[AuthProvider] 🧪 Restored mock session from localStorage:', mockSession.user?.email)
          setSession(mockSession)
          setUser(mockSession.user)
        } catch (e) {
          console.error('[AuthProvider] 🧪 Failed to parse stored mock session:', e)
        }
      }
      setLoading(false)
      return
    }

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
    // E2E Test Mode: Create mock session for test users
    if (isE2ETestMode) {
      const testUser = TEST_USERS[email]
      if (testUser && password === 'password123') {
        console.log('[AuthProvider] 🧪 E2E Test Mode - Mock sign-in for:', email)

        // Create mock user object matching Supabase User type
        const mockUser = {
          id: testUser.id,
          email: testUser.email,
          app_metadata: { role: testUser.role },
          user_metadata: { role: testUser.role, full_name: `Test ${testUser.role}` },
          aud: 'authenticated',
          created_at: new Date().toISOString(),
        } as User

        // Create mock session
        const mockSession = {
          access_token: `test-token-${testUser.id}`,
          refresh_token: `test-refresh-${testUser.id}`,
          expires_in: 3600,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
          token_type: 'bearer',
          user: mockUser,
        } as Session

        // Store mock session in localStorage for auth guard to find
        localStorage.setItem(E2E_SESSION_KEY, JSON.stringify(mockSession))

        setUser(mockUser)
        setSession(mockSession)

        return { error: null }
      } else {
        console.error('[AuthProvider] 🧪 E2E Test Mode - Invalid test credentials:', email)
        const testError = new Error('Invalid test credentials') as AuthError
        testError.name = 'AuthError'
        return { error: testError }
      }
    }

    // Real Supabase authentication
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
    // E2E Test Mode: Clear mock session from localStorage
    if (isE2ETestMode) {
      localStorage.removeItem(E2E_SESSION_KEY)
      setUser(null)
      setSession(null)
      return { error: null }
    }

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
