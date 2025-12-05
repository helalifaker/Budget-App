import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Breadcrumbs } from '@/components/layout/Breadcrumbs'

// Mock TanStack Router hooks
const mockMatches = vi.fn()
vi.mock('@tanstack/react-router', () => ({
  useMatches: () => mockMatches(),
  Link: ({ to, children, className }: any) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}))

describe('Breadcrumbs', () => {
  it('renders breadcrumb navigation', () => {
    mockMatches.mockReturnValue([
      { id: '1', pathname: '/dashboard' },
      { id: '2', pathname: '/planning' },
    ])

    render(<Breadcrumbs />)

    const nav = screen.getByRole('navigation', { name: 'Breadcrumb' })
    expect(nav).toBeInTheDocument()
  })

  describe('Single route', () => {
    it('renders single breadcrumb item', () => {
      mockMatches.mockReturnValue([{ id: '1', pathname: '/dashboard' }])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
    })

    it('renders last item as span (not link)', () => {
      mockMatches.mockReturnValue([{ id: '1', pathname: '/dashboard' }])

      render(<Breadcrumbs />)

      const item = screen.getByText('/dashboard')
      expect(item.tagName).toBe('SPAN')
      expect(item.className).toMatch(/text-gray-700/)
      expect(item.className).toMatch(/font-medium/)
    })
  })

  describe('Multiple routes', () => {
    it('renders multiple breadcrumb items', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
      expect(screen.getByText('/planning')).toBeInTheDocument()
      expect(screen.getByText('/planning/enrollment')).toBeInTheDocument()
    })

    it('renders separators between items', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
      ])

      const { container } = render(<Breadcrumbs />)

      const separators = container.querySelectorAll('span.mx-2')
      // Should have 2 separators for 3 items
      expect(separators).toHaveLength(2)
      expect(separators[0]).toHaveTextContent('/')
    })

    it('first and middle items are links', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
      ])

      render(<Breadcrumbs />)

      const dashboardLink = screen.getByText('/dashboard')
      const planningLink = screen.getByText('/planning')

      expect(dashboardLink.tagName).toBe('A')
      expect(planningLink.tagName).toBe('A')
    })

    it('last item is span (not link)', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
      ])

      render(<Breadcrumbs />)

      const lastItem = screen.getByText('/planning/enrollment')
      expect(lastItem.tagName).toBe('SPAN')
    })
  })

  describe('Styling', () => {
    it('navigation has correct classes', () => {
      mockMatches.mockReturnValue([{ id: '1', pathname: '/dashboard' }])

      render(<Breadcrumbs />)

      const nav = screen.getByRole('navigation')
      expect(nav.className).toMatch(/flex/)
      expect(nav.className).toMatch(/mb-4/)
    })

    it('list has correct classes', () => {
      mockMatches.mockReturnValue([{ id: '1', pathname: '/dashboard' }])

      const { container } = render(<Breadcrumbs />)

      const list = container.querySelector('ol')
      expect(list?.className).toMatch(/inline-flex/)
      expect(list?.className).toMatch(/items-center/)
    })

    it('links have correct styling', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
      ])

      render(<Breadcrumbs />)

      const link = screen.getByText('/dashboard')
      expect(link.className).toMatch(/text-gray-500/)
      expect(link.className).toMatch(/hover:text-gray-700/)
    })

    it('separator has correct styling', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
      ])

      const { container } = render(<Breadcrumbs />)

      const separator = container.querySelector('span.mx-2')
      expect(separator?.className).toMatch(/text-gray-400/)
    })

    it('list items have inline-flex class', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
      ])

      const { container } = render(<Breadcrumbs />)

      const listItems = container.querySelectorAll('li')
      listItems.forEach((item) => {
        expect(item.className).toMatch(/inline-flex/)
        expect(item.className).toMatch(/items-center/)
      })
    })
  })

  describe('Real-world use cases', () => {
    it('renders enrollment planning breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
      expect(screen.getByText('/planning')).toBeInTheDocument()
      expect(screen.getByText('/planning/enrollment')).toBeInTheDocument()
    })

    it('renders DHG workforce breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/dhg' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
      expect(screen.getByText('/planning/dhg')).toBeInTheDocument()
    })

    it('renders budget consolidation breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/consolidation' },
        { id: '3', pathname: '/consolidation/budget' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/consolidation')).toBeInTheDocument()
      expect(screen.getByText('/consolidation/budget')).toBeInTheDocument()
    })

    it('renders financial statements breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/consolidation' },
        { id: '3', pathname: '/consolidation/statements' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/consolidation/statements')).toBeInTheDocument()
    })

    it('renders KPI analysis breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/analysis' },
        { id: '3', pathname: '/analysis/kpis' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/analysis')).toBeInTheDocument()
      expect(screen.getByText('/analysis/kpis')).toBeInTheDocument()
    })

    it('renders configuration page breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/configuration' },
        { id: '3', pathname: '/configuration/versions' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/configuration')).toBeInTheDocument()
      expect(screen.getByText('/configuration/versions')).toBeInTheDocument()
    })

    it('renders strategic planning breadcrumb', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/strategic' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
      expect(screen.getByText('/strategic')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has aria-label for navigation', () => {
      mockMatches.mockReturnValue([{ id: '1', pathname: '/dashboard' }])

      render(<Breadcrumbs />)

      const nav = screen.getByRole('navigation', { name: 'Breadcrumb' })
      expect(nav).toHaveAttribute('aria-label', 'Breadcrumb')
    })

    it('uses ordered list for breadcrumbs', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
      ])

      const { container } = render(<Breadcrumbs />)

      const list = container.querySelector('ol')
      expect(list).toBeInTheDocument()
    })

    it('links are keyboard navigable', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
      ])

      render(<Breadcrumbs />)

      const link = screen.getByText('/dashboard')
      expect(link).toHaveAttribute('href', '/dashboard')
    })
  })

  describe('Empty state', () => {
    it('renders empty navigation when no matches', () => {
      mockMatches.mockReturnValue([])

      const { container } = render(<Breadcrumbs />)

      const listItems = container.querySelectorAll('li')
      expect(listItems).toHaveLength(0)
    })
  })

  describe('Deep nesting', () => {
    it('handles deeply nested routes', () => {
      mockMatches.mockReturnValue([
        { id: '1', pathname: '/dashboard' },
        { id: '2', pathname: '/planning' },
        { id: '3', pathname: '/planning/enrollment' },
        { id: '4', pathname: '/planning/enrollment/detail' },
        { id: '5', pathname: '/planning/enrollment/detail/edit' },
      ])

      render(<Breadcrumbs />)

      expect(screen.getByText('/dashboard')).toBeInTheDocument()
      expect(screen.getByText('/planning')).toBeInTheDocument()
      expect(screen.getByText('/planning/enrollment')).toBeInTheDocument()
      expect(screen.getByText('/planning/enrollment/detail')).toBeInTheDocument()
      expect(screen.getByText('/planning/enrollment/detail/edit')).toBeInTheDocument()

      // Only last item should be a span
      const lastItem = screen.getByText('/planning/enrollment/detail/edit')
      expect(lastItem.tagName).toBe('SPAN')
    })
  })
})
