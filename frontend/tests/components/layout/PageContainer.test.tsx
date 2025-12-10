import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageContainer } from '@/components/layout/PageContainer'

// Mock Breadcrumbs component
vi.mock('@/components/layout/Breadcrumbs', () => ({
  Breadcrumbs: () => <div data-testid="breadcrumbs">Breadcrumbs</div>,
}))

/**
 * PageContainer Tests
 *
 * NOTE: PageContainer was refactored (2024-12-11) to be a simple content wrapper.
 * - Title/description are now shown in ModuleHeader (from ModuleLayout)
 * - Breadcrumbs are deprecated (use TaskDescription instead)
 * - The component only renders children, actions bar, and optional viewport-fit layout
 */
describe('PageContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic rendering', () => {
    it('renders children content', () => {
      render(
        <PageContainer>
          <div data-testid="test-content">Page content</div>
        </PageContainer>
      )

      expect(screen.getByTestId('test-content')).toBeInTheDocument()
      expect(screen.getByText('Page content')).toBeInTheDocument()
    })

    it('accepts deprecated title prop without error', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      )

      // Title is no longer rendered - just verify no error occurs
      expect(screen.getByText('Content')).toBeInTheDocument()
      // Title should NOT appear in the DOM (deprecated)
      expect(screen.queryByText('Test Page')).not.toBeInTheDocument()
    })

    it('accepts deprecated description prop without error', () => {
      render(
        <PageContainer title="DHG" description="Manage teacher allocation">
          <div>Content</div>
        </PageContainer>
      )

      // Description is no longer rendered
      expect(screen.queryByText('Manage teacher allocation')).not.toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('renders action buttons when provided', () => {
      render(
        <PageContainer actions={<button>Create New Version</button>}>
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.getByText('Create New Version')).toBeInTheDocument()
    })

    it('renders multiple actions', () => {
      render(
        <PageContainer
          actions={
            <>
              <button>Export</button>
              <button>Import</button>
              <button>Save</button>
            </>
          }
        >
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.getByText('Export')).toBeInTheDocument()
      expect(screen.getByText('Import')).toBeInTheDocument()
      expect(screen.getByText('Save')).toBeInTheDocument()
    })

    it('does not render actions bar when actions not provided', () => {
      const { container } = render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      )

      // No actions bar with border-b class
      expect(container.querySelector('.border-b')).not.toBeInTheDocument()
    })
  })

  describe('Breadcrumbs (deprecated)', () => {
    it('does not render Breadcrumbs component', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.queryByTestId('breadcrumbs')).not.toBeInTheDocument()
    })

    it('accepts breadcrumbs prop without error', () => {
      render(
        <PageContainer breadcrumbs={[{ label: 'Home', href: '/' }]}>
          <div>Content</div>
        </PageContainer>
      )

      // Should render without errors
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })

  describe('Layout structure', () => {
    it('has correct container sizing classes', () => {
      const { container } = render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      )

      // Main container has centered layout
      const mainDiv = container.firstChild as HTMLElement
      expect(mainDiv.className).toMatch(/mx-auto/)
      expect(mainDiv.className).toMatch(/w-full/)
      expect(mainDiv.className).toMatch(/xl:max-w-\[85%\]/)
      expect(mainDiv.className).toMatch(/2xl:max-w-\[80%\]/)
    })

    it('applies viewportFit class when enabled', () => {
      const { container } = render(
        <PageContainer viewportFit>
          <div>Content</div>
        </PageContainer>
      )

      const mainDiv = container.firstChild as HTMLElement
      expect(mainDiv.className).toMatch(/page-viewport-fit/)
    })

    it('applies custom className', () => {
      const { container } = render(
        <PageContainer className="custom-class">
          <div>Content</div>
        </PageContainer>
      )

      const mainDiv = container.firstChild as HTMLElement
      expect(mainDiv.className).toMatch(/custom-class/)
    })
  })

  describe('Content container', () => {
    it('renders complex children content', () => {
      render(
        <PageContainer>
          <div>
            <h2>Revenue</h2>
            <p>Total: 2,500,000 SAR</p>
            <h2>Costs</h2>
            <p>Total: 2,200,000 SAR</p>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Total: 2,500,000 SAR')).toBeInTheDocument()
      expect(screen.getByText('Costs')).toBeInTheDocument()
      expect(screen.getByText('Total: 2,200,000 SAR')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('renders enrollment planning page with actions', () => {
      render(
        <PageContainer
          actions={
            <>
              <button>Import from Skolengo</button>
              <button>Save Changes</button>
            </>
          }
        >
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
        </PageContainer>
      )

      expect(screen.getByText('Import from Skolengo')).toBeInTheDocument()
      expect(screen.getByText('Save Changes')).toBeInTheDocument()
      expect(screen.getByText('PS')).toBeInTheDocument()
    })

    it('renders DHG workforce page', () => {
      render(
        <PageContainer actions={<button>Calculate FTE</button>}>
          <div>
            <p>Total Hours: 1,250 hours/week</p>
            <p>Required FTE: 69.4 teachers</p>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('Total Hours: 1,250 hours/week')).toBeInTheDocument()
      expect(screen.getByText('Calculate FTE')).toBeInTheDocument()
    })

    it('renders budget consolidation page', () => {
      render(
        <PageContainer
          actions={
            <>
              <button>Export to Excel</button>
              <button>Submit for Approval</button>
            </>
          }
        >
          <div>
            <h3>Summary</h3>
            <p>Total Revenue: 42,500,000 SAR</p>
            <p>Total Costs: 39,100,000 SAR</p>
            <p>Operating Margin: 8.0%</p>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('Export to Excel')).toBeInTheDocument()
      expect(screen.getByText('Total Revenue: 42,500,000 SAR')).toBeInTheDocument()
    })

    it('renders KPI dashboard page', () => {
      render(
        <PageContainer>
          <div className="grid grid-cols-3 gap-4">
            <div>H/E Ratio: 1.52</div>
            <div>E/D Ratio: 23.5</div>
            <div>Operating Margin: 12.5%</div>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('H/E Ratio: 1.52')).toBeInTheDocument()
      expect(screen.getByText('E/D Ratio: 23.5')).toBeInTheDocument()
    })

    it('renders configuration page', () => {
      render(
        <PageContainer>
          <form>
            <label>Fiscal Year</label>
            <select>
              <option>2025-2026</option>
            </select>
          </form>
        </PageContainer>
      )

      expect(screen.getByText('Fiscal Year')).toBeInTheDocument()
    })
  })
})
