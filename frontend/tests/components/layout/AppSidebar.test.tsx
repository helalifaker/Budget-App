/**
 * AppSidebar Unit Tests
 *
 * Tests for the collapsible sidebar navigation component (Phase 2 UI Redesign).
 *
 * Test coverage:
 * - Rendering with correct ARIA attributes
 * - Module list display
 * - Hover expand/collapse behavior
 * - Module navigation on click
 * - Keyboard navigation (Enter/Space)
 * - Active module highlighting
 * - Subpages display when expanded
 * - Logo navigation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppSidebar } from '@/components/layout/AppSidebar'

// Mock TanStack Router
const mockNavigate = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/enrollment/planning' }),
}))

// Mock ModuleContext
const mockModuleContextValue = {
  activeModule: 'enrollment' as const,
  activeModuleDefinition: {
    id: 'enrollment',
    label: 'Enrollment',
    shortLabel: 'Enrollment',
    basePath: '/enrollment',
    color: 'sage' as const,
    description: 'Student enrollment and class structure',
    subpages: [
      { id: 'planning', label: 'Planning', path: '/enrollment/planning' },
      { id: 'class-structure', label: 'Class Structure', path: '/enrollment/class-structure' },
      { id: 'validation', label: 'Validation', path: '/enrollment/validation' },
    ],
    hasSettings: true,
    icon: vi.fn(() => null),
  },
  isModuleActive: vi.fn((moduleId: string) => moduleId === 'enrollment'),
  getModuleColors: vi.fn(() => ({
    active: 'bg-sage-100 text-sage-700',
    underline: 'bg-sage-500',
    hover: 'hover:bg-sage-50',
    text: 'text-sage-600',
    bg: 'bg-sage-500',
  })),
  isSubpageActive: vi.fn(),
  getModule: vi.fn(),
  modules: {},
  moduleOrder: [],
  allModules: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
  activeSubpage: null,
}

vi.mock('@/contexts/ModuleContext', () => ({
  useModule: () => mockModuleContextValue,
  ALL_MODULES: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
  MODULES: {
    enrollment: {
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
    },
    workforce: {
      id: 'workforce',
      label: 'Workforce',
      shortLabel: 'Workforce',
      basePath: '/workforce',
      color: 'wine',
      description: 'Employee management',
      subpages: [],
      hasSettings: true,
      icon: () => null,
    },
    finance: {
      id: 'finance',
      label: 'Finance',
      shortLabel: 'Finance',
      basePath: '/finance',
      color: 'gold',
      description: 'Financial planning',
      subpages: [],
      hasSettings: true,
      icon: () => null,
    },
    analysis: {
      id: 'analysis',
      label: 'Analysis',
      shortLabel: 'Analysis',
      basePath: '/analysis',
      color: 'slate',
      description: 'KPIs and dashboards',
      subpages: [],
      hasSettings: false,
      icon: () => null,
    },
    strategic: {
      id: 'strategic',
      label: 'Strategic',
      shortLabel: 'Strategic',
      basePath: '/strategic',
      color: 'neutral',
      description: '5-year planning',
      subpages: [],
      hasSettings: false,
      icon: () => null,
    },
    configuration: {
      id: 'configuration',
      label: 'Configuration',
      shortLabel: 'Config',
      basePath: '/configuration',
      color: 'neutral',
      description: 'System settings',
      subpages: [],
      hasSettings: false,
      icon: () => null,
    },
  },
}))

// Mock typography styles
vi.mock('@/styles/typography', () => ({
  LAYOUT: {
    sidebarAnimationDuration: '200ms',
  },
}))

describe('AppSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset location.pathname for tests using it
    Object.defineProperty(window, 'location', {
      value: { pathname: '/enrollment/planning' },
      writable: true,
    })
  })

  describe('Rendering', () => {
    it('renders as a navigation landmark', () => {
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      expect(nav).toBeInTheDocument()
    })

    it('renders with correct ARIA label', () => {
      render(<AppSidebar />)

      expect(screen.getByRole('navigation', { name: /module navigation/i })).toHaveAttribute(
        'aria-label',
        'Module navigation'
      )
    })

    it('renders logo with command center link', () => {
      render(<AppSidebar />)

      const logoButton = screen.getByRole('button', { name: /go to command center/i })
      expect(logoButton).toBeInTheDocument()
    })

    it('renders all module buttons', () => {
      render(<AppSidebar />)

      expect(screen.getByRole('button', { name: /enrollment/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /workforce/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /finance/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /analysis/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /strategic/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /configuration/i })).toBeInTheDocument()
    })

    it('applies custom className when provided', () => {
      render(<AppSidebar className="custom-class" />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      expect(nav).toHaveClass('custom-class')
    })

    it('is hidden on mobile (md:hidden class)', () => {
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      expect(nav.className).toMatch(/hidden/)
      expect(nav.className).toMatch(/md:flex/)
    })
  })

  describe('Module Navigation', () => {
    it('navigates to module base path on click', async () => {
      const user = userEvent.setup()
      render(<AppSidebar />)

      const financeButton = screen.getByRole('button', { name: /finance/i })
      await user.click(financeButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/finance' })
    })

    it('navigates to command center when logo is clicked', async () => {
      const user = userEvent.setup()
      render(<AppSidebar />)

      const logoButton = screen.getByRole('button', { name: /go to command center/i })
      await user.click(logoButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/command-center' })
    })

    it('marks active module with aria-current="page"', () => {
      render(<AppSidebar />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      expect(enrollmentButton).toHaveAttribute('aria-current', 'page')

      const financeButton = screen.getByRole('button', { name: /finance/i })
      expect(financeButton).not.toHaveAttribute('aria-current')
    })
  })

  describe('Keyboard Navigation', () => {
    it('navigates to module on Enter key press', async () => {
      const user = userEvent.setup()
      render(<AppSidebar />)

      const workforceButton = screen.getByRole('button', { name: /workforce/i })
      workforceButton.focus()
      await user.keyboard('{Enter}')

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/workforce' })
    })

    it('navigates to module on Space key press', async () => {
      const user = userEvent.setup()
      render(<AppSidebar />)

      const analysisButton = screen.getByRole('button', { name: /analysis/i })
      analysisButton.focus()
      await user.keyboard(' ')

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/analysis' })
    })

    it('all module buttons are focusable', () => {
      render(<AppSidebar />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button).not.toHaveAttribute('tabindex', '-1')
      })
    })
  })

  describe('Hover Expand/Collapse', () => {
    it('starts in collapsed state', () => {
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      // Collapsed state uses collapsed width CSS variable
      expect(nav.className).toMatch(/w-\[var\(--sidebar-width-collapsed\)\]/)
    })

    it('expands on mouse enter after delay', async () => {
      vi.useFakeTimers()
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      fireEvent.mouseEnter(nav)

      // Run all pending timers wrapped in act() to handle React state updates
      await act(async () => {
        await vi.runAllTimersAsync()
      })

      // Check expanded state
      expect(nav.className).toMatch(/w-\[var\(--sidebar-width-expanded\)\]/)

      vi.useRealTimers()
    })

    it('collapses on mouse leave after delay', async () => {
      vi.useFakeTimers()
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })

      // Expand first
      fireEvent.mouseEnter(nav)
      await act(async () => {
        await vi.runAllTimersAsync()
      })

      // Then collapse (component uses 100ms delay)
      fireEvent.mouseLeave(nav)
      await act(async () => {
        await vi.runAllTimersAsync()
      })

      // Check collapsed state
      expect(nav.className).toMatch(/w-\[var\(--sidebar-width-collapsed\)\]/)

      vi.useRealTimers()
    })
  })

  describe('Active Module Styling', () => {
    it('applies active styles to current module', () => {
      render(<AppSidebar />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      // Active module should have bg-subtle class
      expect(enrollmentButton.className).toMatch(/bg-subtle/)
    })

    it('renders active indicator bar for active module', () => {
      render(<AppSidebar />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      // The active indicator is a child span
      const indicator = enrollmentButton.querySelector('span[aria-hidden="true"]')
      expect(indicator).toBeInTheDocument()
    })
  })

  describe('Footer', () => {
    it('renders hover hint text', () => {
      render(<AppSidebar />)

      expect(screen.getByText('Hover to expand')).toBeInTheDocument()
    })

    it('renders collapse indicator when collapsed', () => {
      render(<AppSidebar />)

      // The collapse indicator is a small bar
      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      const indicator = nav.querySelector('.w-4.h-1.bg-border-medium')
      expect(indicator).toBeInTheDocument()
    })
  })

  describe('Logo', () => {
    it('displays EF logo mark', () => {
      render(<AppSidebar />)

      expect(screen.getByText('EF')).toBeInTheDocument()
    })

    it('displays application name when expanded', async () => {
      vi.useFakeTimers()
      render(<AppSidebar />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      fireEvent.mouseEnter(nav)

      // Run all pending timers wrapped in act()
      await act(async () => {
        await vi.runAllTimersAsync()
      })

      // Check expanded state shows app name
      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()
      expect(screen.getByText('Planning Application')).toBeInTheDocument()

      vi.useRealTimers()
    })
  })

  describe('Accessibility', () => {
    it('has proper list structure for modules', () => {
      render(<AppSidebar />)

      const lists = screen.getAllByRole('list')
      expect(lists.length).toBeGreaterThan(0)
    })

    it('module buttons have aria-label', () => {
      render(<AppSidebar />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment/i })
      expect(enrollmentButton).toHaveAttribute('aria-label', 'Enrollment')
    })

    it('logo button has aria-label', () => {
      render(<AppSidebar />)

      const logoButton = screen.getByRole('button', { name: /go to command center/i })
      expect(logoButton).toHaveAttribute('aria-label', 'Go to Command Center')
    })
  })
})
