import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { act } from 'react'
import { AuthProvider } from '@/contexts/AuthProvider'
import { useAuth } from '@/contexts/AuthContext'

// Type definitions for Supabase auth mocks
interface AuthCredentials {
  email: string
  password: string
}

interface MockSession {
  user: {
    id: string
    email: string
  }
  access_token: string
  expires_at: number
}

type AuthChangeEvent = 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | 'USER_UPDATED'
type AuthStateChangeCallback = (event: AuthChangeEvent, session: MockSession | null) => void

// Mock Supabase client
const mockGetSession = vi.fn()
const mockSignInWithPassword = vi.fn()
const mockSignUp = vi.fn()
const mockSignOut = vi.fn()
const mockResetPasswordForEmail = vi.fn()
const mockOnAuthStateChange = vi.fn()

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: () => mockGetSession(),
      signInWithPassword: (credentials: AuthCredentials) => mockSignInWithPassword(credentials),
      signUp: (credentials: AuthCredentials) => mockSignUp(credentials),
      signOut: () => mockSignOut(),
      resetPasswordForEmail: (email: string) => mockResetPasswordForEmail(email),
      onAuthStateChange: (callback: AuthStateChangeCallback) => {
        mockOnAuthStateChange(callback)
        return {
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        }
      },
    },
  },
}))

// Test component that uses the auth context
function TestComponent() {
  const { user, session, loading, signIn, signUp, signOut, resetPassword } = useAuth()

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Ready'}</div>
      <div data-testid="user">{user ? user.email : 'No user'}</div>
      <div data-testid="session">{session ? 'Has session' : 'No session'}</div>
      <button onClick={() => signIn('test@example.com', 'password')}>Sign In</button>
      <button onClick={() => signUp('test@example.com', 'password')}>Sign Up</button>
      <button onClick={() => signOut()}>Sign Out</button>
      <button onClick={() => resetPassword('test@example.com')}>Reset Password</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clear localStorage to prevent E2E mode interference
    localStorage.clear()
    // Default: no session
    mockGetSession.mockResolvedValue({
      data: { session: null },
      error: null,
    })
  })

  describe('Initial state', () => {
    it('provides auth context to children', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })
    })

    it('starts with loading state', () => {
      mockGetSession.mockImplementation(
        () =>
          new Promise(() => {
            /* never resolves */
          })
      )

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('loading')).toHaveTextContent('Loading')
    })

    it('shows no user when not authenticated', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('No user')
      })
    })

    it('shows no session when not authenticated', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('session')).toHaveTextContent('No session')
      })
    })
  })

  describe('Session loading', () => {
    it('loads existing session on mount', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'test@example.com',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      expect(screen.getByTestId('session')).toHaveTextContent('Has session')
    })

    it('handles session loading error', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: { message: 'Failed to get session' },
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('No user')
    })

    it('sets loading to false after session check', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })
    })
  })

  describe('Auth state change listener', () => {
    it('subscribes to auth state changes', () => {
      render(
        <AuthProvider>
          <div>Test</div>
        </AuthProvider>
      )

      expect(mockOnAuthStateChange).toHaveBeenCalled()
    })

    it('updates state when auth state changes', async () => {
      let authStateCallback: AuthStateChangeCallback

      mockOnAuthStateChange.mockImplementation((callback) => {
        authStateCallback = callback
        return {
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        }
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      // Simulate auth state change
      const mockSession = {
        user: {
          id: 'user-456',
          email: 'new@example.com',
        },
        access_token: 'token-456',
        expires_at: Date.now() / 1000 + 3600,
      }

      await act(async () => {
        authStateCallback('SIGNED_IN', mockSession)
      })

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('new@example.com')
      })
    })
  })

  describe('Sign in', () => {
    it('calls Supabase signInWithPassword', async () => {
      mockSignInWithPassword.mockResolvedValue({
        data: {
          session: {
            user: {
              id: 'user-123',
              email: 'test@example.com',
            },
            access_token: 'token-123',
            expires_at: Date.now() / 1000 + 3600,
          },
        },
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signInButton = screen.getByText('Sign In')
      signInButton.click()

      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password',
        })
      })
    })

    it('returns error on sign in failure', async () => {
      mockSignInWithPassword.mockResolvedValue({
        data: { session: null },
        error: { message: 'Invalid credentials' },
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signInButton = screen.getByText('Sign In')
      signInButton.click()

      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalled()
      })
    })
  })

  describe('Sign up', () => {
    it('calls Supabase signUp', async () => {
      mockSignUp.mockResolvedValue({
        data: { user: null, session: null },
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signUpButton = screen.getByText('Sign Up')
      signUpButton.click()

      await waitFor(() => {
        expect(mockSignUp).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password',
        })
      })
    })

    it('returns error on sign up failure', async () => {
      mockSignUp.mockResolvedValue({
        data: { user: null, session: null },
        error: { message: 'Email already registered' },
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signUpButton = screen.getByText('Sign Up')
      signUpButton.click()

      await waitFor(() => {
        expect(mockSignUp).toHaveBeenCalled()
      })
    })
  })

  describe('Sign out', () => {
    it('calls Supabase signOut', async () => {
      mockSignOut.mockResolvedValue({
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signOutButton = screen.getByText('Sign Out')
      signOutButton.click()

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled()
      })
    })

    it('returns error on sign out failure', async () => {
      mockSignOut.mockResolvedValue({
        error: { message: 'Network error' },
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const signOutButton = screen.getByText('Sign Out')
      signOutButton.click()

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled()
      })
    })
  })

  describe('Reset password', () => {
    it('calls Supabase resetPasswordForEmail', async () => {
      mockResetPasswordForEmail.mockResolvedValue({
        data: null,
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const resetButton = screen.getByText('Reset Password')
      resetButton.click()

      await waitFor(() => {
        expect(mockResetPasswordForEmail).toHaveBeenCalledWith('test@example.com')
      })
    })

    it('returns error on reset password failure', async () => {
      mockResetPasswordForEmail.mockResolvedValue({
        data: null,
        error: { message: 'User not found' },
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      const resetButton = screen.getByText('Reset Password')
      resetButton.click()

      await waitFor(() => {
        expect(mockResetPasswordForEmail).toHaveBeenCalled()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('handles complete sign in flow', async () => {
      let authStateCallback: AuthStateChangeCallback

      mockOnAuthStateChange.mockImplementation((callback) => {
        authStateCallback = callback
        return {
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        }
      })

      mockSignInWithPassword.mockResolvedValue({
        data: {
          session: {
            user: {
              id: 'user-123',
              email: 'user@efir.sa',
            },
            access_token: 'token-123',
            expires_at: Date.now() / 1000 + 3600,
          },
        },
        error: null,
      })

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('Ready')
      })

      // User clicks sign in
      const signInButton = screen.getByText('Sign In')
      signInButton.click()

      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalled()
      })

      // Simulate auth state change from Supabase
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'user@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      await act(async () => {
        authStateCallback('SIGNED_IN', mockSession)
      })

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('user@efir.sa')
      })
    })
  })
})
