import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/layout/Header'

// Mock dependencies
const mockSignOut = vi.fn()
const mockNavigate = vi.fn()
let mockUser: { email?: string; role?: string } | null = null

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
  Button: ({
    children,
    onClick,
    variant,
    size,
    ...props
  }: {
    children: React.ReactNode
    onClick?: () => void
    variant?: string
    size?: string
    [key: string]: unknown
  }) => (
    <button onClick={onClick} data-variant={variant} data-size={size} {...props}>
      {children}
    </button>
  ),
}))

// Mock GlobalVersionSelector
vi.mock('@/components/GlobalVersionSelector', () => ({
  GlobalVersionSelector: () => <div data-testid="global-version-selector">Version Selector</div>,
}))

// Mock AccessibilityToggle
vi.mock('@/components/accessibility', () => ({
  AccessibilityToggle: () => <div data-testid="accessibility-toggle">Accessibility</div>,
}))

// Mock lucide-react icons - must spread props to pass data-testid from component
vi.mock('lucide-react', () => ({
  LogOut: ({ className, ...props }: { className?: string; [key: string]: unknown }) => (
    <svg data-testid="logout-icon" className={className} {...props}>
      LogOut
    </svg>
  ),
  User: ({ className, ...props }: { className?: string; [key: string]: unknown }) => (
    <svg className={className} {...props}>
      User
    </svg>
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

      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()
    })

    it('title has correct styling', () => {
      render(<Header />)

      const title = screen.getByText('EFIR Budget')
      expect(title.className).toMatch(/text-base/)
      expect(title.className).toMatch(/font-semibold/)
      expect(title.className).toMatch(/text-text-primary/)
    })
  })

  describe('Global Version Selector', () => {
    it('renders GlobalVersionSelector in the center', () => {
      render(<Header />)

      expect(screen.getByTestId('global-version-selector')).toBeInTheDocument()
    })
  })

  describe('Accessibility Toggle', () => {
    it('renders AccessibilityToggle', () => {
      render(<Header />)

      expect(screen.getByTestId('accessibility-toggle')).toBeInTheDocument()
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

      expect(screen.getByTestId('user-avatar')).toBeInTheDocument()
    })

    it('user info has correct test ids', () => {
      render(<Header />)

      expect(screen.getByTestId('user-info')).toBeInTheDocument()
      expect(screen.getByTestId('user-email')).toBeInTheDocument()
      expect(screen.getByTestId('user-avatar')).toBeInTheDocument()
    })

    it('user info has correct styling', () => {
      render(<Header />)

      const userInfo = screen.getByTestId('user-info')

      expect(userInfo.className).toMatch(/flex/)
      expect(userInfo.className).toMatch(/items-center/)
      expect(userInfo.className).toMatch(/gap-2/)
      expect(userInfo.className).toMatch(/rounded-lg/)
    })
  })

  describe('Sign Out button', () => {
    it('renders sign out button', () => {
      render(<Header />)

      expect(screen.getByText('Sign Out')).toBeInTheDocument()
    })

    it('sign out button has LogOut icon', () => {
      render(<Header />)

      expect(screen.getByTestId('logout-icon')).toBeInTheDocument()
    })

    it('button has ghost variant and sm size', () => {
      render(<Header />)

      const button = screen.getByTestId('logout-button')
      expect(button).toHaveAttribute('data-variant', 'ghost')
      expect(button).toHaveAttribute('data-size', 'sm')
    })
  })

  describe('Sign out functionality', () => {
    it('calls signOut when button clicked', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockSignOut).toHaveBeenCalledTimes(1)
    })

    it('shows success toast on successful sign out', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockToast.success).toHaveBeenCalledWith('Signed out successfully', {
        description: 'You have been logged out',
      })
    })

    it('navigates to login page on successful sign out', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/login' })
    })

    it('shows error toast on sign out failure', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Network error' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockToast.error).toHaveBeenCalledWith('Sign out failed', {
        description: 'Network error',
      })
    })

    it('does not navigate on sign out failure', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Network error' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('Styling and layout', () => {
    it('header has correct styling', () => {
      const { container } = render(<Header />)

      const header = container.querySelector('header')
      // Sahara Luxe Theme: Glass morphism effect
      expect(header?.className).toMatch(/bg-white/)
      expect(header?.className).toMatch(/backdrop-blur-md/)
      expect(header?.className).toMatch(/border-b/)
      expect(header?.className).toMatch(/border-border-light/)
      expect(header?.className).toMatch(/h-14/)
    })

    it('header uses flexbox for layout', () => {
      const { container } = render(<Header />)

      const header = container.querySelector('header')
      expect(header?.className).toMatch(/flex/)
      expect(header?.className).toMatch(/items-center/)
      expect(header?.className).toMatch(/justify-between/)
      expect(header?.className).toMatch(/px-5/)
    })

    it('header has aria attributes for accessibility', () => {
      const { container } = render(<Header />)

      const header = container.querySelector('header')
      expect(header).toHaveAttribute('role', 'banner')
      expect(header).toHaveAttribute('aria-label', 'Application header')
    })

    it('user menu section has correct structure', () => {
      render(<Header />)

      const userMenu = screen.getByTestId('user-menu')
      expect(userMenu.className).toMatch(/flex/)
      expect(userMenu.className).toMatch(/items-center/)
      expect(userMenu.className).toMatch(/gap-3/)
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

      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()

      const button = screen.getByTestId('logout-button')
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

      const button = screen.getByTestId('logout-button')
      await user.click(button)

      expect(mockToast.success).toHaveBeenCalledWith('Signed out successfully', {
        description: 'You have been logged out',
      })
    })

    it('handles network error during sign out', async () => {
      mockSignOut.mockResolvedValue({ error: { message: 'Failed to connect to server' } })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
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

      const button = screen.getByTestId('logout-button')
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

      const button = screen.getByTestId('logout-button')
      expect(button).toBeEnabled()

      await user.click(button)
      expect(mockSignOut).toHaveBeenCalled()
    })

    it('can be activated with Enter key', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      button.focus()
      await user.keyboard('{Enter}')

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('can be activated with Space key', async () => {
      mockSignOut.mockResolvedValue({ error: null })
      const user = userEvent.setup()

      render(<Header />)

      const button = screen.getByTestId('logout-button')
      button.focus()
      await user.keyboard(' ')

      expect(mockSignOut).toHaveBeenCalled()
    })
  })

  describe('Icon styling', () => {
    it('User icon has correct size classes', () => {
      render(<Header />)

      const userIcon = screen.getByTestId('user-avatar')
      // Compact icon size for Sahara Luxe header
      expect(userIcon.getAttribute('class')).toMatch(/w-3\.5/)
      expect(userIcon.getAttribute('class')).toMatch(/h-3\.5/)
    })

    it('LogOut icon has correct size', () => {
      render(<Header />)

      const logOutIcon = screen.getByTestId('logout-icon')
      expect(logOutIcon.getAttribute('class')).toMatch(/w-4/)
      expect(logOutIcon.getAttribute('class')).toMatch(/h-4/)
    })
  })
})
