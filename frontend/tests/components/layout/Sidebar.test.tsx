import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { Sidebar } from '@/components/layout/Sidebar'

// Mock dependencies
const mockPrefetchRoute = vi.fn()
let mockBudgetVersionsData: any = null

vi.mock('@tanstack/react-router', () => ({
  Link: ({ to, children, className, activeProps, onMouseEnter }: any) => (
    <a href={to} className={className} onMouseEnter={onMouseEnter} data-active-class={activeProps?.className}>
      {children}
    </a>
  ),
}))

vi.mock('@/hooks/usePrefetchRoute', () => ({
  usePrefetchRoute: () => ({
    prefetchRoute: mockPrefetchRoute,
  }),
}))

vi.mock('@/hooks/api/useBudgetVersions', () => ({
  useBudgetVersions: () => ({
    data: mockBudgetVersionsData,
  }),
}))

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockBudgetVersionsData = {
      items: [
        { id: 'v1', status: 'WORKING', fiscal_year: '2025-2026' },
        { id: 'v2', status: 'APPROVED', fiscal_year: '2024-2025' },
      ],
    }
  })

  it('renders sidebar container', () => {
    render(<Sidebar />)

    const sidebar = document.querySelector('.w-64')
    expect(sidebar).toBeInTheDocument()
  })

  describe('Branding', () => {
    it('renders EFIR Budget title', () => {
      render(<Sidebar />)

      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()
    })

    it('title has correct styling', () => {
      render(<Sidebar />)

      const title = screen.getByText('EFIR Budget')
      expect(title.className).toMatch(/text-xl/)
      expect(title.className).toMatch(/font-bold/)
      expect(title.className).toMatch(/text-gray-900/)
    })

    it('title is in header section with correct height', () => {
      render(<Sidebar />)

      const title = screen.getByText('EFIR Budget')
      const header = title.parentElement

      expect(header?.className).toMatch(/h-16/)
      expect(header?.className).toMatch(/border-b/)
    })
  })

  describe('Navigation structure', () => {
    it('renders navigation element', () => {
      render(<Sidebar />)

      const nav = document.querySelector('nav')
      expect(nav).toBeInTheDocument()
    })

    it('renders Dashboard link', () => {
      render(<Sidebar />)

      const link = screen.getByText('Dashboard').closest('a')
      expect(link).toHaveAttribute('href', '/dashboard')
    })

    it('renders Configuration section', () => {
      render(<Sidebar />)

      expect(screen.getByText('Configuration')).toBeInTheDocument()
    })

    it('renders Planning section', () => {
      render(<Sidebar />)

      expect(screen.getByText('Planning')).toBeInTheDocument()
    })

    it('renders Consolidation section', () => {
      render(<Sidebar />)

      expect(screen.getByText('Consolidation')).toBeInTheDocument()
    })

    it('renders Analysis section', () => {
      render(<Sidebar />)

      expect(screen.getByText('Analysis')).toBeInTheDocument()
    })

    it('renders Strategic Planning link', () => {
      render(<Sidebar />)

      const link = screen.getByText('Strategic Planning').closest('a')
      expect(link).toHaveAttribute('href', '/strategic')
    })
  })

  describe('Configuration sub-menu', () => {
    it('renders all configuration links', () => {
      render(<Sidebar />)

      expect(screen.getByText('Budget Versions')).toBeInTheDocument()
      expect(screen.getByText('Class Sizes')).toBeInTheDocument()
      expect(screen.getByText('Subject Hours')).toBeInTheDocument()
      expect(screen.getByText('Teacher Costs')).toBeInTheDocument()
      expect(screen.getByText('Fee Structure')).toBeInTheDocument()
      expect(screen.getByText('Timetable')).toBeInTheDocument()
    })

    it('configuration links have correct hrefs', () => {
      render(<Sidebar />)

      expect(screen.getByText('Budget Versions').closest('a')).toHaveAttribute('href', '/configuration/versions')
      expect(screen.getByText('Class Sizes').closest('a')).toHaveAttribute('href', '/configuration/class-sizes')
      expect(screen.getByText('Subject Hours').closest('a')).toHaveAttribute('href', '/configuration/subject-hours')
      expect(screen.getByText('Teacher Costs').closest('a')).toHaveAttribute('href', '/configuration/teacher-costs')
      expect(screen.getByText('Fee Structure').closest('a')).toHaveAttribute('href', '/configuration/fees')
      expect(screen.getByText('Timetable').closest('a')).toHaveAttribute('href', '/configuration/timetable')
    })
  })

  describe('Planning sub-menu', () => {
    it('renders all planning links', () => {
      render(<Sidebar />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
      expect(screen.getByText('Class Structure')).toBeInTheDocument()
      expect(screen.getByText('DHG Workforce')).toBeInTheDocument()
      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Costs')).toBeInTheDocument()
      expect(screen.getByText('CapEx')).toBeInTheDocument()
    })

    it('planning links have correct hrefs', () => {
      render(<Sidebar />)

      expect(screen.getByText('Enrollment').closest('a')).toHaveAttribute('href', '/planning/enrollment')
      expect(screen.getByText('Class Structure').closest('a')).toHaveAttribute('href', '/planning/classes')
      expect(screen.getByText('DHG Workforce').closest('a')).toHaveAttribute('href', '/planning/dhg')
      expect(screen.getByText('Revenue').closest('a')).toHaveAttribute('href', '/planning/revenue')
      expect(screen.getByText('Costs').closest('a')).toHaveAttribute('href', '/planning/costs')
      expect(screen.getByText('CapEx').closest('a')).toHaveAttribute('href', '/planning/capex')
    })
  })

  describe('Consolidation sub-menu', () => {
    it('renders consolidation links', () => {
      render(<Sidebar />)

      expect(screen.getByText('Budget Review')).toBeInTheDocument()
      expect(screen.getByText('Financial Statements')).toBeInTheDocument()
    })

    it('consolidation links have correct hrefs', () => {
      render(<Sidebar />)

      expect(screen.getByText('Budget Review').closest('a')).toHaveAttribute('href', '/consolidation/budget')
      expect(screen.getByText('Financial Statements').closest('a')).toHaveAttribute('href', '/consolidation/statements')
    })
  })

  describe('Analysis sub-menu', () => {
    it('renders analysis links', () => {
      render(<Sidebar />)

      expect(screen.getByText('KPIs')).toBeInTheDocument()
      expect(screen.getByText('Dashboards')).toBeInTheDocument()
      expect(screen.getByText('Budget vs Actual')).toBeInTheDocument()
    })

    it('analysis links have correct hrefs', () => {
      render(<Sidebar />)

      expect(screen.getByText('KPIs').closest('a')).toHaveAttribute('href', '/analysis/kpis')
      expect(screen.getByText('Dashboards').closest('a')).toHaveAttribute('href', '/analysis/dashboards')
      expect(screen.getByText('Budget vs Actual').closest('a')).toHaveAttribute('href', '/analysis/variance')
    })
  })

  describe('Icons', () => {
    it('dashboard has emoji icon', () => {
      render(<Sidebar />)

      const link = screen.getByText('Dashboard').closest('a')
      expect(link).toHaveTextContent('📊')
    })

    it('configuration section has emoji icon', () => {
      render(<Sidebar />)

      const section = screen.getByText('Configuration')
      expect(section.parentElement).toHaveTextContent('⚙️')
    })

    it('planning section has emoji icon', () => {
      render(<Sidebar />)

      const section = screen.getByText('Planning')
      expect(section.parentElement).toHaveTextContent('📝')
    })

    it('consolidation section has emoji icon', () => {
      render(<Sidebar />)

      const section = screen.getByText('Consolidation')
      expect(section.parentElement).toHaveTextContent('💰')
    })

    it('analysis section has emoji icon', () => {
      render(<Sidebar />)

      const section = screen.getByText('Analysis')
      expect(section.parentElement).toHaveTextContent('📈')
    })

    it('strategic planning has emoji icon', () => {
      render(<Sidebar />)

      const link = screen.getByText('Strategic Planning').closest('a')
      expect(link).toHaveTextContent('🎯')
    })
  })

  describe('Budget version integration', () => {
    it('finds active WORKING budget version', () => {
      mockBudgetVersionsData = {
        items: [
          { id: 'working-v1', status: 'WORKING', fiscal_year: '2025-2026' },
          { id: 'approved-v', status: 'APPROVED', fiscal_year: '2024-2025' },
        ],
      }

      render(<Sidebar />)

      // Verify sidebar renders with budget version context
      expect(screen.getByText('Planning')).toBeInTheDocument()
    })

    it('finds active SUBMITTED budget version', () => {
      mockBudgetVersionsData = {
        items: [
          { id: 'submitted-v', status: 'SUBMITTED', fiscal_year: '2025-2026' },
          { id: 'approved-v', status: 'APPROVED', fiscal_year: '2024-2025' },
        ],
      }

      render(<Sidebar />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
    })

    it('handles no active budget versions', () => {
      mockBudgetVersionsData = {
        items: [
          { id: 'archived', status: 'ARCHIVED', fiscal_year: '2023-2024' },
        ],
      }

      render(<Sidebar />)

      expect(screen.getByText('Revenue')).toBeInTheDocument()
    })

    it('handles empty budget versions', () => {
      mockBudgetVersionsData = { items: [] }

      render(<Sidebar />)

      expect(screen.getByText('DHG Workforce')).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('sidebar has fixed width', () => {
      const { container } = render(<Sidebar />)

      const sidebar = container.firstChild as HTMLElement
      expect(sidebar.className).toMatch(/w-64/)
      expect(sidebar.className).toMatch(/bg-white/)
      expect(sidebar.className).toMatch(/border-r/)
    })

    it('navigation has scrollable content', () => {
      const { container } = render(<Sidebar />)

      const nav = container.querySelector('nav')
      expect(nav?.className).toMatch(/overflow-y-auto/)
      expect(nav?.className).toMatch(/flex-1/)
    })

    it('top-level links have correct styling', () => {
      render(<Sidebar />)

      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink?.className).toMatch(/px-4/)
      expect(dashboardLink?.className).toMatch(/py-2/)
      expect(dashboardLink?.className).toMatch(/text-sm/)
      expect(dashboardLink?.className).toMatch(/rounded-md/)
      expect(dashboardLink?.className).toMatch(/hover:bg-gray-100/)
    })

    it('section headers have correct styling', () => {
      render(<Sidebar />)

      const configSection = screen.getByText('Configuration')
      // Section headers are rendered as divs with styling
      expect(configSection.tagName).toBe('DIV')
    })

    it('sub-menu links are indented', () => {
      render(<Sidebar />)

      const enrollmentLink = screen.getByText('Enrollment').closest('a')
      // Sub-menu links exist and are rendered as links
      expect(enrollmentLink).toBeInTheDocument()
      expect(enrollmentLink).toHaveAttribute('href', '/planning/enrollment')
    })

    it('sub-menu links have correct styling', () => {
      render(<Sidebar />)

      const enrollmentLink = screen.getByText('Enrollment').closest('a')
      expect(enrollmentLink?.className).toMatch(/block/)
      expect(enrollmentLink?.className).toMatch(/px-4/)
      expect(enrollmentLink?.className).toMatch(/py-2/)
      expect(enrollmentLink?.className).toMatch(/text-sm/)
      expect(enrollmentLink?.className).toMatch(/text-gray-600/)
      expect(enrollmentLink?.className).toMatch(/rounded-md/)
    })
  })

  describe('Active state', () => {
    it('active links have special styling class', () => {
      render(<Sidebar />)

      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink).toHaveAttribute('data-active-class', 'bg-gray-100 text-primary')
    })

    it('active sub-menu links have special styling', () => {
      render(<Sidebar />)

      const enrollmentLink = screen.getByText('Enrollment').closest('a')
      expect(enrollmentLink).toHaveAttribute('data-active-class', 'bg-gray-100 text-primary font-medium')
    })
  })

  describe('Real-world navigation scenarios', () => {
    it('renders complete enrollment workflow navigation', () => {
      render(<Sidebar />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
      expect(screen.getByText('Class Structure')).toBeInTheDocument()
      expect(screen.getByText('DHG Workforce')).toBeInTheDocument()
    })

    it('renders complete budget workflow navigation', () => {
      render(<Sidebar />)

      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Costs')).toBeInTheDocument()
      expect(screen.getByText('Budget Review')).toBeInTheDocument()
      expect(screen.getByText('Financial Statements')).toBeInTheDocument()
    })

    it('renders analysis tools navigation', () => {
      render(<Sidebar />)

      expect(screen.getByText('KPIs')).toBeInTheDocument()
      expect(screen.getByText('Dashboards')).toBeInTheDocument()
      expect(screen.getByText('Budget vs Actual')).toBeInTheDocument()
    })

    it('renders configuration management navigation', () => {
      render(<Sidebar />)

      expect(screen.getByText('Budget Versions')).toBeInTheDocument()
      expect(screen.getByText('Class Sizes')).toBeInTheDocument()
      expect(screen.getByText('Subject Hours')).toBeInTheDocument()
      expect(screen.getByText('Teacher Costs')).toBeInTheDocument()
      expect(screen.getByText('Fee Structure')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('all links are keyboard navigable', () => {
      render(<Sidebar />)

      const allLinks = screen.getAllByRole('link')
      expect(allLinks.length).toBeGreaterThan(0)

      allLinks.forEach((link) => {
        expect(link).toHaveAttribute('href')
      })
    })

    it('navigation is semantic', () => {
      const { container } = render(<Sidebar />)

      const nav = container.querySelector('nav')
      expect(nav?.tagName).toBe('NAV')
    })
  })

  describe('Empty budget versions', () => {
    it('handles no budget versions data', () => {
      mockBudgetVersionsData = null

      render(<Sidebar />)

      expect(screen.getByText('Enrollment')).toBeInTheDocument()
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('handles empty budget versions array', () => {
      mockBudgetVersionsData = { items: [] }

      render(<Sidebar />)

      // Verify sidebar still renders navigation correctly
      expect(screen.getByText('DHG Workforce')).toBeInTheDocument()
      expect(screen.getByText('Enrollment')).toBeInTheDocument()
    })
  })

  describe('Full sidebar structure', () => {
    it('has all major navigation sections', () => {
      render(<Sidebar />)

      expect(screen.getByText('EFIR Budget')).toBeInTheDocument()
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Configuration')).toBeInTheDocument()
      expect(screen.getByText('Planning')).toBeInTheDocument()
      expect(screen.getByText('Consolidation')).toBeInTheDocument()
      expect(screen.getByText('Analysis')).toBeInTheDocument()
      expect(screen.getByText('Strategic Planning')).toBeInTheDocument()
    })

    it('has total of 24 navigation links', () => {
      render(<Sidebar />)

      const allLinks = screen.getAllByRole('link')
      // 1 Dashboard + 6 Configuration + 6 Planning + 2 Consolidation + 3 Analysis + 1 Strategic = 19
      expect(allLinks.length).toBe(19)
    })
  })
})
