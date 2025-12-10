/**
 * ModuleHeader Unit Tests
 *
 * Tests for the module title bar component (Phase 2 UI Redesign).
 *
 * Test coverage:
 * - Rendering with correct ARIA attributes
 * - Module title display
 * - Command palette trigger
 * - User info display
 * - Sign out functionality
 * - Mobile hamburger menu
 * - Search button (mobile/desktop)
 * - Version selector visibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ModuleHeader } from '@/components/layout/ModuleHeader'

// Mock TanStack Router
const mockNavigate = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/enrollment/planning' }),
}))

// Mock ModuleContext - include useModule for MobileDrawer dependency
vi.mock('@/contexts/ModuleContext', () => {
  const mockModuleDefinition = {
    id: 'enrollment',
    label: 'Enrollment',
    shortLabel: 'Enrollment',
    basePath: '/enrollment',
    color: 'sage',
    description: 'Student enrollment and class structure',
    subpages: [{ id: 'planning', label: 'Planning', path: '/enrollment/planning' }],
    hasSettings: true,
    icon: () => null,
  }

  return {
    useActiveModule: () => ({
      activeModule: 'enrollment',
      definition: mockModuleDefinition,
      activeSubpage: null,
    }),
    useModule: () => ({
      activeModule: 'enrollment',
      activeModuleDefinition: mockModuleDefinition,
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
    MODULE_COLORS: {
      sage: {
        active: 'bg-sage-100 text-sage-700',
        underline: 'bg-sage-500',
        hover: 'hover:bg-sage-50',
        text: 'text-sage-600',
        bg: 'bg-sage-500',
      },
      gold: {
        active: 'bg-gold-100 text-gold-700',
        underline: 'bg-gold-500',
        hover: 'hover:bg-gold-50',
        text: 'text-gold-600',
        bg: 'bg-gold-500',
      },
      wine: {
        active: 'bg-wine-100 text-wine-700',
        underline: 'bg-wine-500',
        hover: 'hover:bg-wine-50',
        text: 'text-wine-600',
        bg: 'bg-wine-500',
      },
      slate: {
        active: 'bg-slate-100 text-slate-700',
        underline: 'bg-slate-500',
        hover: 'hover:bg-slate-50',
        text: 'text-slate-600',
        bg: 'bg-slate-500',
      },
      neutral: {
        active: 'bg-subtle text-text-primary',
        underline: 'bg-text-tertiary',
        hover: 'hover:bg-subtle',
        text: 'text-text-secondary',
        bg: 'bg-text-tertiary',
      },
    },
    ALL_MODULES: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
    MODULES: {
      enrollment: {
        id: 'enrollment',
        label: 'Enrollment',
        shortLabel: 'Enrollment',
        basePath: '/enrollment',
        color: 'sage',
        subpages: [{ id: 'planning', label: 'Planning', path: '/enrollment/planning' }],
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

// Mock AccessibilityToggle
vi.mock('@/components/accessibility', () => ({
  AccessibilityToggle: () => <button data-testid="accessibility-toggle">Accessibility</button>,
}))

// Mock MobileDrawer - use full path for vi.mock
vi.mock('@/components/layout/MobileDrawer', () => ({
  MobileDrawer: ({ isOpen }: { isOpen: boolean }) => (
    <div data-testid="mobile-drawer" data-open={isOpen}>
      Mobile Drawer
    </div>
  ),
}))

// Mock Button component
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: React.ComponentProps<'button'>) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}))

// Mock typography
vi.mock('@/styles/typography', () => ({
  getTypographyClasses: () => 'text-module-title font-semibold',
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('ModuleHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSignOut.mockResolvedValue({ error: null })
  })

  describe('Rendering', () => {
    it('renders as a header landmark', () => {
      render(<ModuleHeader />)

      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('renders with correct ARIA label', () => {
      render(<ModuleHeader />)

      const header = screen.getByRole('banner')
      expect(header).toHaveAttribute('aria-label', 'Module header')
    })

    it('renders module title', () => {
      render(<ModuleHeader />)

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Enrollment')
    })

    it('applies custom className when provided', () => {
      render(<ModuleHeader className="custom-class" />)

      const header = screen.getByRole('banner')
      expect(header).toHaveClass('custom-class')
    })
  })

  describe('Module Title', () => {
    it('displays the active module label', () => {
      render(<ModuleHeader />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
    })

    it('displays module title from definition', () => {
      // The component uses definition?.label with 'Dashboard' as fallback
      // Since we mock 'enrollment' module, it should show 'Enrollment'
      // Testing the fallback would require a separate test file with different mock
      render(<ModuleHeader />)

      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('Enrollment')
    })
  })

  describe('Command Palette Trigger', () => {
    it('renders search button on desktop', () => {
      render(<ModuleHeader />)

      const searchButton = screen.getByRole('button', { name: /open command palette/i })
      expect(searchButton).toBeInTheDocument()
    })

    it('renders search button on mobile', () => {
      render(<ModuleHeader />)

      const searchButton = screen.getByRole('button', { name: /open search/i })
      expect(searchButton).toBeInTheDocument()
    })

    it('dispatches Cmd+K keyboard event on click', async () => {
      const user = userEvent.setup()
      const dispatchEventSpy = vi.spyOn(document, 'dispatchEvent')

      render(<ModuleHeader />)

      const searchButton = screen.getByRole('button', { name: /open command palette/i })
      await user.click(searchButton)

      expect(dispatchEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          key: 'k',
          metaKey: true,
        })
      )

      dispatchEventSpy.mockRestore()
    })

    it('shows keyboard shortcut hint (Cmd+K)', () => {
      render(<ModuleHeader />)

      expect(screen.getByText('K')).toBeInTheDocument()
    })
  })

  describe('Version Selector', () => {
    it('renders version selector', () => {
      render(<ModuleHeader />)

      expect(screen.getByTestId('version-selector')).toBeInTheDocument()
    })
  })

  describe('User Info', () => {
    it('displays user email username', () => {
      render(<ModuleHeader />)

      expect(screen.getByText('admin')).toBeInTheDocument()
    })
  })

  describe('Sign Out', () => {
    it('renders sign out button', () => {
      render(<ModuleHeader />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).toBeInTheDocument()
    })

    it('calls signOut on click', async () => {
      const user = userEvent.setup()
      render(<ModuleHeader />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('navigates to login after successful sign out', async () => {
      const user = userEvent.setup()
      mockSignOut.mockResolvedValue({ error: null })

      render(<ModuleHeader />)

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

      render(<ModuleHeader />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Sign out failed', {
          description: 'Network error',
        })
      })
    })
  })

  describe('Mobile Logo', () => {
    it('renders mobile logo button', () => {
      render(<ModuleHeader />)

      const logoButton = screen.getByRole('button', { name: /go to command center/i })
      expect(logoButton).toBeInTheDocument()
    })

    it('navigates to command center on mobile logo click', async () => {
      const user = userEvent.setup()
      render(<ModuleHeader />)

      const logoButton = screen.getByRole('button', { name: /go to command center/i })
      await user.click(logoButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/command-center' })
    })

    it('displays EF logo text', () => {
      render(<ModuleHeader />)

      expect(screen.getByText('EF')).toBeInTheDocument()
    })
  })

  describe('Mobile Hamburger Menu', () => {
    it('renders hamburger menu button', () => {
      render(<ModuleHeader />)

      const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
      expect(menuButton).toBeInTheDocument()
    })

    it('has correct ARIA attributes for hamburger menu', () => {
      render(<ModuleHeader />)

      const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
      expect(menuButton).toHaveAttribute('aria-expanded', 'false')
      expect(menuButton).toHaveAttribute('aria-controls', 'mobile-drawer')
    })

    it('opens mobile drawer on click', async () => {
      const user = userEvent.setup()
      render(<ModuleHeader />)

      const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
      await user.click(menuButton)

      const drawer = screen.getByTestId('mobile-drawer')
      expect(drawer).toHaveAttribute('data-open', 'true')
    })
  })

  describe('Accessibility', () => {
    it('accessibility toggle is present', () => {
      render(<ModuleHeader />)

      expect(screen.getByTestId('accessibility-toggle')).toBeInTheDocument()
    })

    it('has proper heading hierarchy', () => {
      render(<ModuleHeader />)

      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toBeInTheDocument()
    })

    it('separators are hidden from screen readers', () => {
      render(<ModuleHeader />)

      // Separators should have aria-hidden="true"
      const separators = document.querySelectorAll('[aria-hidden="true"]')
      expect(separators.length).toBeGreaterThan(0)
    })
  })

  describe('Layout Structure', () => {
    it('has correct height from CSS variable', () => {
      render(<ModuleHeader />)

      const header = screen.getByRole('banner')
      expect(header.className).toMatch(/h-\[var\(--header-line-height\)\]/)
    })

    it('is sticky at top', () => {
      render(<ModuleHeader />)

      const header = screen.getByRole('banner')
      expect(header.className).toMatch(/sticky/)
      expect(header.className).toMatch(/top-0/)
    })
  })
})
