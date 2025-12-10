/**
 * MobileBottomNav Unit Tests
 *
 * Tests for the mobile bottom navigation bar component (Phase 2 UI Redesign).
 *
 * Test coverage:
 * - Rendering with correct structure
 * - Module icons display
 * - Module navigation on click
 * - Active module highlighting
 * - Accessibility attributes
 * - Mobile-only visibility
 * - Touch-friendly sizing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MobileBottomNav } from '@/components/layout/MobileBottomNav'

// Mock TanStack Router
const mockNavigate = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock ModuleContext
vi.mock('@/contexts/ModuleContext', () => ({
  useModule: () => ({
    isModuleActive: (moduleId: string) => moduleId === 'enrollment',
    getModuleColors: (moduleId: string) => {
      const colors: Record<string, { active: string; text: string }> = {
        enrollment: { active: 'bg-sage-100 text-sage-700', text: 'text-sage-600' },
        workforce: { active: 'bg-wine-100 text-wine-700', text: 'text-wine-600' },
        finance: { active: 'bg-gold-100 text-gold-700', text: 'text-gold-600' },
        analysis: { active: 'bg-slate-100 text-slate-700', text: 'text-slate-600' },
        strategic: { active: 'bg-subtle text-text-primary', text: 'text-text-secondary' },
        configuration: { active: 'bg-subtle text-text-primary', text: 'text-text-secondary' },
      }
      return colors[moduleId] || { active: '', text: '' }
    },
  }),
  ALL_MODULES: ['enrollment', 'workforce', 'finance', 'analysis', 'strategic', 'configuration'],
  MODULES: {
    enrollment: {
      id: 'enrollment',
      label: 'Enrollment',
      shortLabel: 'Enrollment',
      basePath: '/enrollment',
      color: 'sage',
      icon: () => <svg data-testid="icon-enrollment" />,
    },
    workforce: {
      id: 'workforce',
      label: 'Workforce',
      shortLabel: 'Workforce',
      basePath: '/workforce',
      color: 'wine',
      icon: () => <svg data-testid="icon-workforce" />,
    },
    finance: {
      id: 'finance',
      label: 'Finance',
      shortLabel: 'Finance',
      basePath: '/finance',
      color: 'gold',
      icon: () => <svg data-testid="icon-finance" />,
    },
    analysis: {
      id: 'analysis',
      label: 'Analysis',
      shortLabel: 'Analysis',
      basePath: '/analysis',
      color: 'slate',
      icon: () => <svg data-testid="icon-analysis" />,
    },
    strategic: {
      id: 'strategic',
      label: 'Strategic',
      shortLabel: 'Strategic',
      basePath: '/strategic',
      color: 'neutral',
      icon: () => <svg data-testid="icon-strategic" />,
    },
    configuration: {
      id: 'configuration',
      label: 'Configuration',
      shortLabel: 'Config',
      basePath: '/configuration',
      color: 'neutral',
      icon: () => <svg data-testid="icon-configuration" />,
    },
  },
}))

describe('MobileBottomNav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders as a navigation element', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation', { name: /module navigation/i })
      expect(nav).toBeInTheDocument()
    })

    it('renders all module buttons', () => {
      render(<MobileBottomNav />)

      expect(screen.getByRole('button', { name: /enrollment module/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /workforce module/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /finance module/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /analysis module/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /strategic module/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /configuration module/i })).toBeInTheDocument()
    })

    it('renders module icons', () => {
      render(<MobileBottomNav />)

      expect(screen.getByTestId('icon-enrollment')).toBeInTheDocument()
      expect(screen.getByTestId('icon-workforce')).toBeInTheDocument()
      expect(screen.getByTestId('icon-finance')).toBeInTheDocument()
      expect(screen.getByTestId('icon-analysis')).toBeInTheDocument()
      expect(screen.getByTestId('icon-strategic')).toBeInTheDocument()
      expect(screen.getByTestId('icon-configuration')).toBeInTheDocument()
    })

    it('renders module short labels', () => {
      render(<MobileBottomNav />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
      expect(screen.getByText('Workforce')).toBeInTheDocument()
      expect(screen.getByText('Finance')).toBeInTheDocument()
      expect(screen.getByText('Analysis')).toBeInTheDocument()
      expect(screen.getByText('Strategic')).toBeInTheDocument()
      expect(screen.getByText('Config')).toBeInTheDocument()
    })

    it('applies custom className when provided', () => {
      render(<MobileBottomNav className="custom-class" />)

      const nav = screen.getByRole('navigation')
      expect(nav).toHaveClass('custom-class')
    })
  })

  describe('Mobile Visibility', () => {
    it('has md:hidden class for desktop hiding', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/md:hidden/)
    })

    it('is fixed at bottom', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/fixed/)
      expect(nav.className).toMatch(/bottom-0/)
    })

    it('spans full width', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/left-0/)
      expect(nav.className).toMatch(/right-0/)
    })
  })

  describe('Module Navigation', () => {
    it('navigates to module on click', async () => {
      const user = userEvent.setup()
      render(<MobileBottomNav />)

      const financeButton = screen.getByRole('button', { name: /finance module/i })
      await user.click(financeButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/finance' })
    })

    it('navigates to enrollment on click', async () => {
      const user = userEvent.setup()
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      await user.click(enrollmentButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/enrollment' })
    })

    it('navigates to workforce on click', async () => {
      const user = userEvent.setup()
      render(<MobileBottomNav />)

      const workforceButton = screen.getByRole('button', { name: /workforce module/i })
      await user.click(workforceButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/workforce' })
    })

    it('navigates to configuration on click', async () => {
      const user = userEvent.setup()
      render(<MobileBottomNav />)

      const configButton = screen.getByRole('button', { name: /configuration module/i })
      await user.click(configButton)

      expect(mockNavigate).toHaveBeenCalledWith({ to: '/configuration' })
    })
  })

  describe('Active Module Highlighting', () => {
    it('marks active module with aria-current', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      expect(enrollmentButton).toHaveAttribute('aria-current', 'page')

      const financeButton = screen.getByRole('button', { name: /finance module/i })
      expect(financeButton).not.toHaveAttribute('aria-current')
    })

    it('active module icon has colored background', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const iconContainer = enrollmentButton.querySelector('div')
      expect(iconContainer?.className).toMatch(/bg-sage-100/)
    })

    it('active module label has primary text color', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const label = enrollmentButton.querySelector('span')
      expect(label?.className).toMatch(/text-text-primary/)
    })

    it('inactive module label has tertiary text color', () => {
      render(<MobileBottomNav />)

      const financeButton = screen.getByRole('button', { name: /finance module/i })
      const label = financeButton.querySelector('span')
      expect(label?.className).toMatch(/text-text-tertiary/)
    })
  })

  describe('Touch-Friendly Sizing', () => {
    it('buttons have minimum touch target height', () => {
      render(<MobileBottomNav />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button.className).toMatch(/min-h-\[44px\]/)
      })
    })

    it('nav has correct height for touch', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/h-16/)
    })

    it('buttons have active scale effect', () => {
      render(<MobileBottomNav />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button.className).toMatch(/active:scale-95/)
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA label on navigation', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav).toHaveAttribute('aria-label', 'Module navigation')
    })

    it('each button has descriptive aria-label', () => {
      render(<MobileBottomNav />)

      expect(screen.getByRole('button', { name: 'Enrollment module' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Workforce module' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Finance module' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Analysis module' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Strategic module' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Configuration module' })).toBeInTheDocument()
    })

    it('buttons are focusable', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      enrollmentButton.focus()
      expect(document.activeElement).toBe(enrollmentButton)
    })
  })

  describe('Layout', () => {
    it('distributes buttons evenly', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/justify-around/)
    })

    it('buttons flex to fill space', () => {
      render(<MobileBottomNav />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button.className).toMatch(/flex-1/)
      })
    })

    it('buttons have column layout', () => {
      render(<MobileBottomNav />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button.className).toMatch(/flex-col/)
      })
    })
  })

  describe('Styling', () => {
    it('has backdrop blur effect', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/backdrop-blur/)
    })

    it('has top border', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/border-t/)
    })

    it('has high z-index for overlay', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/z-50/)
    })

    it('has safe area padding for notched devices', () => {
      render(<MobileBottomNav />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/pb-\[env\(safe-area-inset-bottom\)\]/)
    })
  })

  describe('Icon Container', () => {
    it('icon container has rounded corners', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const iconContainer = enrollmentButton.querySelector('div')
      expect(iconContainer?.className).toMatch(/rounded-lg/)
    })

    it('icon container has fixed size', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const iconContainer = enrollmentButton.querySelector('div')
      expect(iconContainer?.className).toMatch(/w-8/)
      expect(iconContainer?.className).toMatch(/h-8/)
    })
  })

  describe('Label Styling', () => {
    it('labels have small font size', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const label = enrollmentButton.querySelector('span')
      expect(label?.className).toMatch(/text-\[10px\]/)
    })

    it('labels have medium font weight', () => {
      render(<MobileBottomNav />)

      const enrollmentButton = screen.getByRole('button', { name: /enrollment module/i })
      const label = enrollmentButton.querySelector('span')
      expect(label?.className).toMatch(/font-medium/)
    })
  })
})
