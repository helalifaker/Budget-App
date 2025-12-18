/**
 * TaskDescription Unit Tests
 *
 * Tests for the contextual task description component (Phase 2 UI Redesign).
 *
 * Test coverage:
 * - Rendering with correct structure
 * - Auto-detection from route
 * - Override with prop
 * - Fallback for unknown routes
 * - Parent path matching
 * - Module root matching
 * - Text truncation
 * - TAB_DESCRIPTIONS constant coverage
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TaskDescription, TAB_DESCRIPTIONS } from '@/components/layout/TaskDescription'

// Mock TanStack Router
let mockPathname = '/enrollment/planning'
vi.mock('@tanstack/react-router', () => ({
  useLocation: () => ({ pathname: mockPathname }),
}))

// Mock typography
vi.mock('@/styles/typography', () => ({
  getTypographyClasses: () => 'text-description text-text-tertiary',
}))

describe('TaskDescription', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPathname = '/enrollment/planning'
  })

  describe('Rendering', () => {
    it('renders a paragraph element', () => {
      render(<TaskDescription />)

      const paragraph = screen.getByRole('paragraph')
      expect(paragraph).toBeInTheDocument()
    })

    it('applies custom className when provided', () => {
      render(<TaskDescription className="custom-class" />)

      const container = screen.getByRole('paragraph').parentElement
      expect(container).toHaveClass('custom-class')
    })

    it('has correct height from CSS variable', () => {
      render(<TaskDescription />)

      const container = screen.getByRole('paragraph').parentElement
      expect(container?.className).toMatch(/h-\[var\(--description-line-height\)\]/)
    })

    it('has truncation class for long text', () => {
      render(<TaskDescription />)

      const paragraph = screen.getByRole('paragraph')
      expect(paragraph.className).toMatch(/truncate/)
    })

    it('has max-width for readability', () => {
      render(<TaskDescription />)

      const paragraph = screen.getByRole('paragraph')
      expect(paragraph.className).toMatch(/max-w-3xl/)
    })
  })

  describe('Auto-Detection from Route', () => {
    it('displays enrollment planning description', () => {
      mockPathname = '/students/planning'
      render(<TaskDescription />)

      expect(
        screen.getByText('Enter enrollment projections by grade level for the budget year.')
      ).toBeInTheDocument()
    })

    it('displays class structure description', () => {
      mockPathname = '/students/class-structure'
      render(<TaskDescription />)

      expect(
        screen.getByText('Configure classes per level based on enrollment numbers.')
      ).toBeInTheDocument()
    })

    it('displays workforce employees description', () => {
      mockPathname = '/teachers/employees'
      render(<TaskDescription />)

      expect(
        screen.getByText('View and manage staff roster, contracts, and employment details.')
      ).toBeInTheDocument()
    })

    it('displays finance revenue description', () => {
      mockPathname = '/finance/revenue'
      render(<TaskDescription />)

      expect(
        screen.getByText('Plan tuition fees, registration fees, and other revenue streams.')
      ).toBeInTheDocument()
    })

    it('displays analysis KPIs description', () => {
      mockPathname = '/insights/kpis'
      render(<TaskDescription />)

      expect(
        screen.getByText('Monitor key performance indicators across all budget areas.')
      ).toBeInTheDocument()
    })

    it('displays configuration versions description', () => {
      mockPathname = '/settings/versions'
      render(<TaskDescription />)

      expect(
        screen.getByText('Manage versions and fiscal year configurations.')
      ).toBeInTheDocument()
    })

    it('displays command center description', () => {
      mockPathname = '/command-center'
      render(<TaskDescription />)

      expect(
        screen.getByText(
          'Your budget planning hub. Quick access to all modules and recent activity.'
        )
      ).toBeInTheDocument()
    })

    it('displays root path description', () => {
      mockPathname = '/'
      render(<TaskDescription />)

      expect(
        screen.getByText('Welcome to EFIR Budget Planning. Select a module to begin.')
      ).toBeInTheDocument()
    })
  })

  describe('Override with Prop', () => {
    it('uses provided description over auto-detected', () => {
      mockPathname = '/enrollment/planning'
      render(<TaskDescription description="Custom description for this page" />)

      expect(screen.getByText('Custom description for this page')).toBeInTheDocument()
      expect(
        screen.queryByText('Enter enrollment projections by grade level for the budget year.')
      ).not.toBeInTheDocument()
    })

    it('allows empty string override', () => {
      render(<TaskDescription description="" />)

      const paragraph = screen.getByRole('paragraph')
      expect(paragraph).toHaveTextContent('')
    })
  })

  describe('Path Matching Fallbacks', () => {
    it('falls back to immediate parent path for unknown child routes', () => {
      // Path: /students/planning/edit → immediate parent is /students/planning → found!
      // Note: The implementation only checks ONE parent level, not recursively
      mockPathname = '/students/planning/edit'
      render(<TaskDescription />)

      // Should match /students/planning (the immediate parent)
      expect(
        screen.getByText('Enter enrollment projections by grade level for the budget year.')
      ).toBeInTheDocument()
    })

    it('falls back to module root for unknown module paths', () => {
      mockPathname = '/students/unknown-page'
      render(<TaskDescription />)

      // Should match /students
      expect(
        screen.getByText('Manage student enrollment projections and class structure.')
      ).toBeInTheDocument()
    })

    it('uses default fallback for completely unknown paths', () => {
      mockPathname = '/unknown-module/unknown-page'
      render(<TaskDescription />)

      expect(screen.getByText('Configure and manage your budget data.')).toBeInTheDocument()
    })

    it('handles trailing slash correctly', () => {
      mockPathname = '/students/planning/'
      render(<TaskDescription />)

      expect(
        screen.getByText('Enter enrollment projections by grade level for the budget year.')
      ).toBeInTheDocument()
    })
  })

  describe('TAB_DESCRIPTIONS Coverage', () => {
    it('has descriptions for all main modules', () => {
      const moduleRoutes = [
        '/students',
        '/teachers',
        '/finance',
        '/insights',
        '/strategic',
        '/settings',
      ]

      moduleRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
        expect(TAB_DESCRIPTIONS[route].length).toBeGreaterThan(0)
      })
    })

    it('has descriptions for enrollment subpages', () => {
      const enrollmentRoutes = [
        '/students/planning',
        '/students/class-structure',
        '/students/validation',
        '/students/settings',
      ]

      enrollmentRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
      })
    })

    it('has descriptions for workforce subpages', () => {
      const workforceRoutes = [
        '/teachers/employees',
        '/teachers/salaries',
        '/teachers/dhg',
        '/teachers/dhg/planning',
        '/teachers/dhg/requirements',
        '/teachers/dhg/gap-analysis',
        '/teachers/settings',
      ]

      workforceRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
      })
    })

    it('has descriptions for finance subpages', () => {
      const financeRoutes = [
        '/finance/revenue',
        '/finance/costs',
        '/finance/capex',
        '/finance/consolidation',
        '/finance/statements',
        '/finance/settings',
      ]

      financeRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
      })
    })

    it('has descriptions for analysis subpages', () => {
      const analysisRoutes = ['/insights/kpis', '/insights/dashboards', '/insights/variance']

      analysisRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
      })
    })

    it('has descriptions for configuration subpages', () => {
      const configRoutes = [
        '/settings/versions',
        '/settings/class-sizes',
        '/settings/subject-hours',
        '/settings/teacher-costs',
        '/settings/fees',
        '/settings/uploads',
        '/settings/system',
      ]

      configRoutes.forEach((route) => {
        expect(TAB_DESCRIPTIONS[route]).toBeDefined()
      })
    })

    it('has description for legacy admin route', () => {
      expect(TAB_DESCRIPTIONS['/admin/historical-import']).toBeDefined()
    })

    it('has descriptions for special pages', () => {
      expect(TAB_DESCRIPTIONS['/']).toBeDefined()
      expect(TAB_DESCRIPTIONS['/command-center']).toBeDefined()
      expect(TAB_DESCRIPTIONS['/dashboard']).toBeDefined()
    })
  })

  describe('Settings Routes', () => {
    it('displays enrollment settings description', () => {
      mockPathname = '/students/settings'
      render(<TaskDescription />)

      expect(
        screen.getByText('Configure class size parameters and enrollment rules.')
      ).toBeInTheDocument()
    })

    it('displays workforce settings description', () => {
      mockPathname = '/teachers/settings'
      render(<TaskDescription />)

      expect(
        screen.getByText('Configure subject hours and teacher cost parameters.')
      ).toBeInTheDocument()
    })

    it('displays finance settings description', () => {
      mockPathname = '/finance/settings'
      render(<TaskDescription />)

      expect(
        screen.getByText('Configure fee structures and financial parameters.')
      ).toBeInTheDocument()
    })
  })

  describe('DHG Nested Routes', () => {
    it('displays DHG planning description', () => {
      mockPathname = '/teachers/dhg/planning'
      render(<TaskDescription />)

      expect(
        screen.getByText('Plan teaching hours by subject and level (DHG).')
      ).toBeInTheDocument()
    })

    it('displays DHG requirements description', () => {
      mockPathname = '/teachers/dhg/requirements'
      render(<TaskDescription />)

      expect(screen.getByText('Calculate FTE requirements based on DHG hours.')).toBeInTheDocument()
    })

    it('displays DHG gap analysis description', () => {
      mockPathname = '/teachers/dhg/gap-analysis'
      render(<TaskDescription />)

      expect(
        screen.getByText('Compare available staff against requirements (TRMD).')
      ).toBeInTheDocument()
    })
  })
})
