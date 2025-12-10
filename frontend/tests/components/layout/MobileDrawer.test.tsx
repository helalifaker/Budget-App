/**
 * MobileDrawer Unit Tests
 *
 * Tests for the mobile navigation drawer component (Phase 5 UI Redesign).
 *
 * Test coverage:
 * - Rendering when open/closed
 * - Module navigation
 * - Subpage navigation
 * - Active module highlighting
 * - Sign out functionality
 * - Version selector
 * - User info display
 * - Close on navigation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MobileDrawer } from '@/components/layout/MobileDrawer'

// Mock TanStack Router
const mockNavigate = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock ModuleContext - define inside vi.mock to avoid hoisting issues
vi.mock('@/contexts/ModuleContext', () => {
  const mockActiveModuleDefinition = {
    id: 'enrollment',
    label: 'Enrollment',
    shortLabel: 'Enrollment',
    basePath: '/enrollment',
    color: 'sage',
    description: 'Student enrollment and class structure',
    subpages: [
      { id: 'planning', label: 'Planning', path: '/enrollment/planning' },
      { id: 'class-structure', label: 'Class Structure', path: '/enrollment/class-structure' },
    ],
    hasSettings: true,
    icon: () => null,
  }

  return {
    useModule: () => ({
      activeModule: 'enrollment',
      activeModuleDefinition: mockActiveModuleDefinition,
      isModuleActive: (moduleId: string) => moduleId === 'enrollment',
      getModuleColors: () => ({
        active: 'bg-sage-100 text-sage-700',
        underline: 'bg-sage-500',
        hover: 'hover:bg-sage-50',
        text: 'text-sage-600',
        bg: 'bg-sage-500',
      }),
      isSubpageActive: () => false,
      getModule: () => undefined,
      modules: {},
      moduleOrder: [],
      allModules: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
      activeSubpage: null,
    }),
    ALL_MODULES: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
    MODULES: {
      enrollment: {
        id: 'enrollment',
        label: 'Enrollment',
        shortLabel: 'Enrollment',
        basePath: '/enrollment',
        color: 'sage',
        subpages: [
          { id: 'planning', label: 'Planning', path: '/enrollment/planning' },
          { id: 'class-structure', label: 'Class Structure', path: '/enrollment/class-structure' },
        ],
        hasSettings: true,
        icon: () => null,
      },
      workforce: {
        id: 'workforce',
        label: 'Workforce',
        shortLabel: 'Workforce',
        basePath: '/workforce',
        color: 'wine',
        subpages: [],
        icon: () => null,
      },
      finance: {
        id: 'finance',
        label: 'Finance',
        shortLabel: 'Finance',
        basePath: '/finance',
        color: 'gold',
        subpages: [],
        icon: () => null,
      },
      analysis: {
        id: 'analysis',
        label: 'Analysis',
        shortLabel: 'Analysis',
        basePath: '/analysis',
        color: 'slate',
        subpages: [],
        icon: () => null,
      },
      strategic: {
        id: 'strategic',
        label: 'Strategic',
        shortLabel: 'Strategic',
        basePath: '/strategic',
        color: 'neutral',
        subpages: [],
        icon: () => null,
      },
      configuration: {
        id: 'configuration',
        label: 'Configuration',
        shortLabel: 'Config',
        basePath: '/configuration',
        color: 'neutral',
        subpages: [],
        icon: () => null,
      },
    },
  }
})

// Mock AuthContext
const mockSignOut = vi.fn()
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { email: 'admin@efir.edu.sa' },
    signOut: mockSignOut,
  }),
}))

// Mock GlobalVersionSelector
vi.mock('@/components/GlobalVersionSelector', () => ({
  GlobalVersionSelector: () => <div data-testid="version-selector">Version Selector</div>,
}))

// Mock Sheet component from shadcn
vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({
    children,
    open,
    onOpenChange,
  }: {
    children: React.ReactNode
    open: boolean
    onOpenChange: (open: boolean) => void
  }) => (
    <div data-testid="sheet" data-open={open} onClick={() => onOpenChange(false)}>
      {open && children}
    </div>
  ),
  SheetContent: ({
    children,
    side,
    className,
  }: {
    children: React.ReactNode
    side: string
    className?: string
  }) => (
    <div data-testid="sheet-content" data-side={side} className={className}>
      {children}
    </div>
  ),
  SheetHeader: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="sheet-header" className={className}>
      {children}
    </div>
  ),
  SheetTitle: ({ children }: { children: React.ReactNode; asChild?: boolean }) => (
    <div data-testid="sheet-title">{children}</div>
  ),
  SheetClose: ({ children }: { children: React.ReactNode; asChild?: boolean }) => <>{children}</>,
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('MobileDrawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockSignOut.mockResolvedValue({ error: null })
    // Reset location.pathname
    Object.defineProperty(window, 'location', {
      value: { pathname: '/enrollment/planning' },
      writable: true,
    })
  })

  describe('Rendering', () => {
    it('renders when open', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByTestId('sheet-content')).toBeInTheDocument()
    })

    it('does not render content when closed', () => {
      render(<MobileDrawer {...defaultProps} isOpen={false} />)

      expect(screen.queryByTestId('sheet-content')).not.toBeInTheDocument()
    })

    it('renders on left side', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByTestId('sheet-content')).toHaveAttribute('data-side', 'left')
    })
  })

  describe('Header', () => {
    it('renders logo with EF text', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByText('EF')).toBeInTheDocument()
    })

    it('renders application name', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()
      expect(screen.getByText('Planning Application')).toBeInTheDocument()
    })

    it('navigates to command center when header is clicked', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const headerButton = screen.getByText('EFIR Budget').closest('button')
      if (headerButton) {
        await user.click(headerButton)
      }

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/command-center' })
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Module Navigation', () => {
    it('renders all module buttons', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByRole('button', { name: /enrollment/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /workforce/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /finance/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /analysis/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /strategic/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /configuration/i })).toBeInTheDocument()
    })

    it('navigates to module on click', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const financeButton = screen.getByRole('button', { name: /finance/i })
      await user.click(financeButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/finance' })
    })

    it('closes drawer after module navigation', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const financeButton = screen.getByRole('button', { name: /finance/i })
      await user.click(financeButton)

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('marks active module with aria-current', () => {
      render(<MobileDrawer {...defaultProps} />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      expect(enrollmentButton).toHaveAttribute('aria-current', 'page')

      const financeButton = screen.getByRole('button', { name: /finance/i })
      expect(financeButton).not.toHaveAttribute('aria-current')
    })
  })

  describe('Subpages', () => {
    it('renders subpages for active module', () => {
      render(<MobileDrawer {...defaultProps} />)

      // Use exact text to avoid matching "Planning Application" in header
      expect(screen.getByRole('button', { name: 'Planning' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Class Structure' })).toBeInTheDocument()
    })

    it('navigates to subpage on click', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const classStructureButton = screen.getByRole('button', { name: 'Class Structure' })
      await user.click(classStructureButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/enrollment/class-structure' })
    })

    it('closes drawer after subpage navigation', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      // Use exact text to avoid matching "Planning Application" in header
      const planningButton = screen.getByRole('button', { name: 'Planning' })
      await user.click(planningButton)

      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Footer', () => {
    it('renders version selector', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByTestId('version-selector')).toBeInTheDocument()
    })

    it('displays Budget Version label', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
    })

    it('displays user email username', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    it('renders sign out button', () => {
      render(<MobileDrawer {...defaultProps} />)

      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
    })
  })

  describe('Sign Out', () => {
    it('calls signOut on click', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('closes drawer before sign out', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('navigates to login after successful sign out', async () => {
      const user = userEvent.setup()
      mockSignOut.mockResolvedValue({ error: null })

      render(<MobileDrawer {...defaultProps} />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith({ to: '/login' })
      })
    })

    it('shows error toast on sign out failure', async () => {
      const { toast } = await import('sonner')
      const user = userEvent.setup()
      mockSignOut.mockResolvedValue({ error: { message: 'Network error' } })

      render(<MobileDrawer {...defaultProps} />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Sign out failed', {
          description: 'Network error',
        })
      })
    })
  })

  describe('Sheet Behavior', () => {
    it('calls onClose when sheet closes', async () => {
      const user = userEvent.setup()
      render(<MobileDrawer {...defaultProps} />)

      // Click on the sheet to trigger close (simulated by our mock)
      const sheet = screen.getByTestId('sheet')
      await user.click(sheet)

      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('has proper list structure for modules', () => {
      render(<MobileDrawer {...defaultProps} />)

      const lists = screen.getAllByRole('list')
      expect(lists.length).toBeGreaterThan(0)
    })

    it('module buttons have aria-label', () => {
      render(<MobileDrawer {...defaultProps} />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      expect(enrollmentButton).toHaveAttribute('aria-label', 'Enrollment')
    })

    it('sign out button has aria-label', () => {
      render(<MobileDrawer {...defaultProps} />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).toHaveAttribute('aria-label', 'Sign out')
    })
  })

  describe('Styling', () => {
    it('applies correct width to sheet content', () => {
      render(<MobileDrawer {...defaultProps} />)

      const content = screen.getByTestId('sheet-content')
      expect(content.className).toMatch(/w-\[280px\]/)
    })

    it('active module has active styling', () => {
      render(<MobileDrawer {...defaultProps} />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      expect(enrollmentButton.className).toMatch(/bg-subtle/)
    })
  })
})
