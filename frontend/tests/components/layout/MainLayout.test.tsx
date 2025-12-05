import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MainLayout } from '@/components/layout/MainLayout'

// Mock child components
vi.mock('@/components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar">Sidebar Content</div>,
}))

vi.mock('@/components/layout/Header', () => ({
  Header: () => <div data-testid="header">Header Content</div>,
}))

describe('MainLayout', () => {
  it('renders children content', () => {
    render(
      <MainLayout>
        <div>Main content area</div>
      </MainLayout>
    )

    expect(screen.getByText('Main content area')).toBeInTheDocument()
  })

  describe('Layout structure', () => {
    it('renders Sidebar component', () => {
      render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })

    it('renders Header component', () => {
      render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('renders main element for content', () => {
      const { container } = render(
        <MainLayout>
          <div data-testid="test-content">Test content</div>
        </MainLayout>
      )

      const main = container.querySelector('main')
      expect(main).toBeInTheDocument()
      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })
  })

  describe('Styling and layout', () => {
    it('container has full height and flex layout', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const rootDiv = container.firstChild as HTMLElement
      expect(rootDiv.className).toMatch(/flex/)
      expect(rootDiv.className).toMatch(/h-screen/)
      expect(rootDiv.className).toMatch(/bg-gray-50/)
    })

    it('content area has flex column layout', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      // Find the div containing header and main
      const contentArea = screen.getByTestId('header').parentElement
      expect(contentArea?.className).toMatch(/flex-1/)
      expect(contentArea?.className).toMatch(/flex/)
      expect(contentArea?.className).toMatch(/flex-col/)
      expect(contentArea?.className).toMatch(/overflow-hidden/)
    })

    it('main element has correct styling', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const main = container.querySelector('main')
      expect(main?.className).toMatch(/flex-1/)
      expect(main?.className).toMatch(/overflow-y-auto/)
      expect(main?.className).toMatch(/p-6/)
    })
  })

  describe('Children rendering', () => {
    it('renders single child element', () => {
      render(
        <MainLayout>
          <div>Single child</div>
        </MainLayout>
      )

      expect(screen.getByText('Single child')).toBeInTheDocument()
    })

    it('renders multiple child elements', () => {
      render(
        <MainLayout>
          <>
            <h1>Page Title</h1>
            <p>Page description</p>
            <div>Page content</div>
          </>
        </MainLayout>
      )

      expect(screen.getByText('Page Title')).toBeInTheDocument()
      expect(screen.getByText('Page description')).toBeInTheDocument()
      expect(screen.getByText('Page content')).toBeInTheDocument()
    })

    it('renders complex nested children', () => {
      render(
        <MainLayout>
          <div>
            <header>
              <h1>Dashboard</h1>
            </header>
            <section>
              <div>Chart area</div>
            </section>
            <footer>
              <p>Footer</p>
            </footer>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Chart area')).toBeInTheDocument()
      expect(screen.getByText('Footer')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('renders enrollment planning page', () => {
      render(
        <MainLayout>
          <div>
            <h1>Enrollment Planning</h1>
            <table>
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Students</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>PS</td>
                  <td>45</td>
                </tr>
              </tbody>
            </table>
          </div>
        </MainLayout>
      )

      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      expect(screen.getByTestId('header')).toBeInTheDocument()
      expect(screen.getByText('Enrollment Planning')).toBeInTheDocument()
      expect(screen.getByText('PS')).toBeInTheDocument()
    })

    it('renders DHG workforce page', () => {
      render(
        <MainLayout>
          <div>
            <h2>DHG Workforce Planning</h2>
            <p>Total Hours: 1,250 hours/week</p>
            <p>Required FTE: 69.4 teachers</p>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('DHG Workforce Planning')).toBeInTheDocument()
      expect(screen.getByText('Total Hours: 1,250 hours/week')).toBeInTheDocument()
    })

    it('renders budget dashboard', () => {
      render(
        <MainLayout>
          <div>
            <h1>Budget Dashboard</h1>
            <div className="grid grid-cols-3 gap-4">
              <div>Revenue: 42,500,000 SAR</div>
              <div>Costs: 39,100,000 SAR</div>
              <div>Margin: 8.0%</div>
            </div>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('Budget Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Revenue: 42,500,000 SAR')).toBeInTheDocument()
      expect(screen.getByText('Margin: 8.0%')).toBeInTheDocument()
    })

    it('renders KPI analysis page', () => {
      render(
        <MainLayout>
          <div>
            <h1>Key Performance Indicators</h1>
            <div>
              <p>H/E Ratio: 1.52</p>
              <p>E/D Ratio: 23.5</p>
              <p>Operating Margin: 12.5%</p>
            </div>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('Key Performance Indicators')).toBeInTheDocument()
      expect(screen.getByText('H/E Ratio: 1.52')).toBeInTheDocument()
    })

    it('renders financial statements page', () => {
      render(
        <MainLayout>
          <div>
            <h1>Financial Statements</h1>
            <div>
              <h2>French PCG Format</h2>
              <p>64110 - Teaching Salaries AEFE</p>
              <p>70110 - Tuition T1</p>
            </div>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('Financial Statements')).toBeInTheDocument()
      expect(screen.getByText('French PCG Format')).toBeInTheDocument()
    })

    it('renders configuration page', () => {
      render(
        <MainLayout>
          <div>
            <h1>Budget Versions</h1>
            <button>Create New Version</button>
            <table>
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                </tr>
              </thead>
            </table>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('Budget Versions')).toBeInTheDocument()
      expect(screen.getByText('Create New Version')).toBeInTheDocument()
    })

    it('renders strategic planning page', () => {
      render(
        <MainLayout>
          <div>
            <h1>5-Year Strategic Plan</h1>
            <p>Conservative Scenario</p>
            <p>Base Scenario</p>
            <p>Optimistic Scenario</p>
          </div>
        </MainLayout>
      )

      expect(screen.getByText('5-Year Strategic Plan')).toBeInTheDocument()
      expect(screen.getByText('Conservative Scenario')).toBeInTheDocument()
      expect(screen.getByText('Optimistic Scenario')).toBeInTheDocument()
    })
  })

  describe('Scrolling behavior', () => {
    it('main content area is scrollable', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const main = container.querySelector('main')
      expect(main?.className).toMatch(/overflow-y-auto/)
    })

    it('outer container prevents overflow', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const contentArea = screen.getByTestId('header').parentElement
      expect(contentArea?.className).toMatch(/overflow-hidden/)
    })
  })

  describe('Responsive layout', () => {
    it('container uses flexbox for responsive layout', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const rootDiv = container.firstChild as HTMLElement
      expect(rootDiv.className).toMatch(/flex/)
    })

    it('content area flexes to fill available space', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const contentArea = screen.getByTestId('header').parentElement
      expect(contentArea?.className).toMatch(/flex-1/)
    })
  })

  describe('Integration with child components', () => {
    it('Sidebar is first in layout', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const rootDiv = container.firstChild as HTMLElement
      const sidebar = screen.getByTestId('sidebar')

      expect(rootDiv.firstChild).toBe(sidebar)
    })

    it('Header appears before main content', () => {
      const { container } = render(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      )

      const header = screen.getByTestId('header')
      const main = container.querySelector('main')

      expect(header.compareDocumentPosition(main!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
    })
  })
})
