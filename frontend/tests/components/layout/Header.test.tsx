import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/layout/Header'

// Mock dependencies
const mockSignOut = vi.fn()
const mockNavigate = vi.fn()
let mockUser: any = null

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    signOut: mockSignOut,
  }),
}))

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}))

// Use vi.hoisted() to properly hoist mock toast
const { mockToast } = vi.hoisted(() => ({
  mockToast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}))

vi.mock('sonner', () => ({
  toast: mockToast,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, variant, size, ...props }: any) => (
    <button onClick={onClick} data-variant={variant} data-size={size} {...props}>
      {children}
    </button>
  ),
}))

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUser = { email: 'test@efir.sa' }
  })

  it('renders header element', () => {
    render(<Header />)

    const header = document.querySelector('header')
    expect(header).toBeInTheDocument()
  })

  describe('Title and branding', () => {
    it('renders application title', () => {
      render(<Header />)

      expect(screen.getByText('Budget Planning Application')).toBeInTheDocument()
    })

    it('title has correct styling', () => {
      render(<Header />)

      const title = screen.getByText('Budget Planning Application')
      expect(title.className).toMatch(/text-lg/)
      expect(title.className).toMatch(/font-semibold/)
      expect(title.className).toMatch(/text-gray-900/)
    })
  })

  describe('User information', () => {
    it('displays user email when logged in', () => {
      mockUser = { email: 'admin@efir.sa' }

      render(<Header />)

      expect(screen.getByText('admin@efir.sa')).toBeInTheDocument()
    })

    it('displays User icon', () => {
      render(<Header />)

      const icons = document.querySelectorAll('svg.lucide-user')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('user info has correct styling', () => {
      render(<Header />)

      const email = screen.getByText('test@efir.sa')
      const container = email.parentElement

      expect(container?.className).toMatch(/flex/)
      expect(container?.className).toMatch(/items-center/)
      expect(container?.className).toMatch(/text-sm/)
      expect(container?.className).toMatch(/text-gray-600/)
    })
  })

  describe('Sign Out button', () => {
    it('renders sign out button', () => {
      render(<Header />)

      expect(screen.getByText('Sign Out')).toBeInTheDocument()
    })

    it('sign out button has LogOut icon', () => {
      render(<Header />)

      const icons = document.querySelectorAll('svg.lucide-log-out')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('button has outline variant and sm size', () => {
      render(<Header />)

      const button = screen.getByText('Sign Out').closest('button')
      expect(button).toHaveAttribute('data-variant', 'outline')
      expect(button).toHaveAttribute('data-size', 'sm')
    })
  })

  describe('Sign out functionality', () => {
    it('calls signOut when button clicked', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockSignOut).toHaveBeenCalledTimes(1)
    })

    it('shows success toast on successful sign out', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockToast.success).toHaveBeenCalledWith('Signed out successfully', {
        description: 'You have been logged out',
      })
    })

    it('navigates to login page on successful sign out', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/login' })
    })

    it('shows error toast on sign out failure', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Network error' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockToast.error).toHaveBeenCalledWith('Sign out failed', {
        description: 'Network error',
      })
    })

    it('does not navigate on sign out failure', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Network error' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('Styling and layout', () => {
    it('header has correct styling', () => {
      const { container } = render(<Header />)

      const header = container.querySelector('header')
      expect(header?.className).toMatch(/bg-white/)
      expect(header?.className).toMatch(/border-b/)
      expect(header?.className).toMatch(/border-gray-200/)
      expect(header?.className).toMatch(/h-16/)
    })

    it('header uses flexbox for layout', () => {
      const { container } = render(<Header />)

      const header = container.querySelector('header')
      expect(header?.className).toMatch(/flex/)
      expect(header?.className).toMatch(/items-center/)
      expect(header?.className).toMatch(/justify-between/)
      expect(header?.className).toMatch(/px-6/)
    })

    it('left section has title', () => {
      render(<Header />)

      const title = screen.getByText('Budget Planning Application')
      const leftSection = title.parentElement

      expect(leftSection?.className).toMatch(/flex/)
      expect(leftSection?.className).toMatch(/items-center/)
      expect(leftSection?.className).toMatch(/space-x-4/)
    })

    it('right section has user info and sign out', () => {
      render(<Header />)

      const signOut = screen.getByText('Sign Out')
      const rightSection = signOut.parentElement

      expect(rightSection?.className).toMatch(/flex/)
      expect(rightSection?.className).toMatch(/items-center/)
      expect(rightSection?.className).toMatch(/space-x-4/)
    })
  })

  describe('Different user scenarios', () => {
    it('renders with finance director user', () => {
      mockUser = { email: 'finance.director@efir.sa', role: 'FINANCE_DIRECTOR' }

      render(<Header />)

      expect(screen.getByText('finance.director@efir.sa')).toBeInTheDocument()
    })

    it('renders with HR user', () => {
      mockUser = { email: 'hr@efir.sa', role: 'HR' }

      render(<Header />)

      expect(screen.getByText('hr@efir.sa')).toBeInTheDocument()
    })

    it('renders with academic user', () => {
      mockUser = { email: 'academic@efir.sa', role: 'ACADEMIC' }

      render(<Header />)

      expect(screen.getByText('academic@efir.sa')).toBeInTheDocument()
    })

    it('renders with viewer user', () => {
      mockUser = { email: 'viewer@efir.sa', role: 'VIEWER' }

      render(<Header />)

      expect(screen.getByText('viewer@efir.sa')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('handles sign out from enrollment planning page', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      expect(screen.getByText('Budget Planning Application')).toBeInTheDocument()

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockSignOut).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith({ to: '/login' })
    })

    it('handles sign out from DHG workforce page', async () => {
      mockUser = { email: 'teacher@efir.sa' }
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      expect(screen.getByText('teacher@efir.sa')).toBeInTheDocument()

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockToast.success).toHaveBeenCalledWith('Signed out successfully', {
        description: 'You have been logged out',
      })
    })

    it('handles network error during sign out', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Failed to connect to server' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockToast.error).toHaveBeenCalledWith('Sign out failed', {
        description: 'Failed to connect to server',
      })
      expect(mockNavigate).not.toHaveBeenCalled()
    })

    it('handles sign out session timeout', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Session expired' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockToast.error).toHaveBeenCalledWith('Sign out failed', {
        description: 'Session expired',
      })
    })
  })

  describe('Button interaction', () => {
    it('button is clickable', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      expect(button).toBeEnabled()

      await user.click(button)
      expect(mockSignOut).toHaveBeenCalled()
    })

    it('can be activated with Enter key', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      button.focus()
      await user.keyboard('{Enter}')

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('can be activated with Space key', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByText('Sign Out')
      button.focus()
      await user.keyboard(' ')

      expect(mockSignOut).toHaveBeenCalled()
    })
  })

  describe('Icon styling', () => {
    it('User icon has correct size classes', () => {
      render(<Header />)

      const userIcon = document.querySelector('svg.lucide-user')
      expect(userIcon?.getAttribute('class')).toMatch(/w-4/)
      expect(userIcon?.getAttribute('class')).toMatch(/h-4/)
    })

    it('LogOut icon has correct size and margin', () => {
      render(<Header />)

      const logOutIcon = document.querySelector('svg.lucide-log-out')
      expect(logOutIcon?.getAttribute('class')).toMatch(/w-4/)
      expect(logOutIcon?.getAttribute('class')).toMatch(/h-4/)
      expect(logOutIcon?.getAttribute('class')).toMatch(/mr-2/)
    })
  })
})
