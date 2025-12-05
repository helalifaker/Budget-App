import { describe, it, expect, vi, beforeEach } from 'vitest'
import { requireAuth, requireAuthWithRedirect } from '@/lib/auth-guard'

// Mock Supabase client
const mockGetSession = vi.fn()

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: () => mockGetSession(),
    },
  },
}))

// Mock TanStack Router redirect
const mockRedirect = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  redirect: (options: any) => {
    mockRedirect(options)
    // Throw to simulate redirect behavior
    throw new Error('REDIRECT')
  },
}))

describe('requireAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('With valid session', () => {
    it('returns session when user is authenticated', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'test@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      const result = await requireAuth()

      expect(result).toEqual({ session: mockSession })
      expect(mockRedirect).not.toHaveBeenCalled()
    })

    it('returns session with admin user', async () => {
      const mockSession = {
        user: {
          id: 'admin-123',
          email: 'admin@efir.sa',
          role: 'ADMIN',
        },
        access_token: 'token-admin',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      const result = await requireAuth()

      expect(result).toEqual({ session: mockSession })
    })

    it('returns session with finance director', async () => {
      const mockSession = {
        user: {
          id: 'finance-123',
          email: 'finance.director@efir.sa',
          role: 'FINANCE_DIRECTOR',
        },
        access_token: 'token-finance',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      const result = await requireAuth()

      expect(result.session.user.email).toBe('finance.director@efir.sa')
    })
  })

  describe('Without valid session', () => {
    it('redirects to login when no session', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
      })
    })

    it('redirects when session is undefined', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: undefined },
        error: null,
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
      })
    })

    it('redirects when getSession returns error', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: { message: 'Session expired' },
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
      })
    })
  })

  describe('Session expiry', () => {
    it('redirects when session is expired', async () => {
      const expiredSession = {
        user: {
          id: 'user-123',
          email: 'test@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 - 3600, // Expired 1 hour ago
      }

      mockGetSession.mockResolvedValue({
        data: { session: null }, // Supabase returns null for expired sessions
        error: null,
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
      })
    })
  })

  describe('Real-world use cases', () => {
    it('protects dashboard route', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
      })
    })

    it('allows access to enrollment planning with valid session', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'hr@efir.sa',
          role: 'HR',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      const result = await requireAuth()

      expect(result.session.user.email).toBe('hr@efir.sa')
    })

    it('protects configuration pages', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuth()).rejects.toThrow('REDIRECT')
    })
  })
})

describe('requireAuthWithRedirect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('With valid session', () => {
    it('returns session when authenticated', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'test@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      const result = await requireAuthWithRedirect('/planning/enrollment')

      expect(result).toEqual({ session: mockSession })
      expect(mockRedirect).not.toHaveBeenCalled()
    })

    it('does not include redirect in successful auth', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'test@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      await requireAuthWithRedirect('/dashboard')

      expect(mockRedirect).not.toHaveBeenCalled()
    })
  })

  describe('Without valid session', () => {
    it('redirects to login with return path', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/planning/enrollment')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/planning/enrollment',
        },
      })
    })

    it('includes dashboard path in redirect', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/dashboard')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/dashboard',
        },
      })
    })

    it('includes configuration path in redirect', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/configuration/versions')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/configuration/versions',
        },
      })
    })

    it('includes DHG workforce path in redirect', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/planning/dhg')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/planning/dhg',
        },
      })
    })
  })

  describe('Real-world redirect scenarios', () => {
    it('saves deep link to enrollment planning', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/planning/enrollment')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/planning/enrollment',
        },
      })
    })

    it('saves deep link to budget consolidation', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/consolidation/budget')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/consolidation/budget',
        },
      })
    })

    it('saves deep link to financial statements', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/consolidation/statements')).rejects.toThrow(
        'REDIRECT'
      )

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/consolidation/statements',
        },
      })
    })

    it('saves deep link to KPI analysis', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/analysis/kpis')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/analysis/kpis',
        },
      })
    })

    it('allows user to return after login', async () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'test@efir.sa',
        },
        access_token: 'token-123',
        expires_at: Date.now() / 1000 + 3600,
      }

      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })

      // User logs in and returns to the saved path
      const result = await requireAuthWithRedirect('/planning/enrollment')

      expect(result.session.user.email).toBe('test@efir.sa')
      expect(mockRedirect).not.toHaveBeenCalled()
    })
  })

  describe('Edge cases', () => {
    it('handles root path redirect', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/',
        },
      })
    })

    it('handles path with query parameters', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(requireAuthWithRedirect('/dashboard?version=v1')).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/dashboard?version=v1',
        },
      })
    })

    it('handles nested paths', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      await expect(
        requireAuthWithRedirect('/planning/enrollment/detail/edit')
      ).rejects.toThrow('REDIRECT')

      expect(mockRedirect).toHaveBeenCalledWith({
        to: '/login',
        search: {
          redirect: '/planning/enrollment/detail/edit',
        },
      })
    })
  })
})
