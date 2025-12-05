import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageContainer } from '@/components/layout/PageContainer'

// Mock Breadcrumbs component
vi.mock('@/components/layout/Breadcrumbs', () => ({
  Breadcrumbs: () => <div data-testid="breadcrumbs">Breadcrumbs</div>,
}))

describe('PageContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with title and children', () => {
    render(
      <PageContainer title="Test Page">
        <div>Page content</div>
      </PageContainer>
    )

    expect(screen.getByText('Test Page')).toBeInTheDocument()
    expect(screen.getByText('Page content')).toBeInTheDocument()
  })

  describe('Title and description', () => {
    it('renders title as h1 element', () => {
      render(
        <PageContainer title="Enrollment Planning">
          <div>Content</div>
        </PageContainer>
      )

      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('Enrollment Planning')
    })

    it('renders description when provided', () => {
      render(
        <PageContainer
          title="DHG Workforce"
          description="Manage teacher allocation and hours"
        >
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.getByText('Manage teacher allocation and hours')).toBeInTheDocument()
    })

    it('does not render description when not provided', () => {
      const { container } = render(
        <PageContainer title="Budget Review">
          <div>Content</div>
        </PageContainer>
      )

      const descriptions = container.querySelectorAll('p')
      expect(descriptions).toHaveLength(0)
    })

    it('title has correct styling', () => {
      render(
        <PageContainer title="Test Title">
          <div>Content</div>
        </PageContainer>
      )

      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading.className).toMatch(/text-3xl/)
      expect(heading.className).toMatch(/font-bold/)
      expect(heading.className).toMatch(/text-gray-900/)
    })

    it('description has correct styling', () => {
      render(
        <PageContainer title="Test Title" description="Test description">
          <div>Content</div>
        </PageContainer>
      )

      const description = screen.getByText('Test description')
      expect(description.className).toMatch(/text-sm/)
      expect(description.className).toMatch(/text-gray-600/)
    })
  })

  describe('Actions', () => {
    it('renders action buttons when provided', () => {
      render(
        <PageContainer
          title="Budget Versions"
          actions={<button>Create New Version</button>}
        >
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.getByText('Create New Version')).toBeInTheDocument()
    })

    it('renders multiple actions', () => {
      render(
        <PageContainer
          title="Enrollment"
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

    it('does not render actions div when actions not provided', () => {
      const { container } = render(
        <PageContainer title="Test">
          <div>Content</div>
        </PageContainer>
      )

      // Check that there's no extra div for actions
      const heading = screen.getByRole('heading', { level: 1 })
      const parent = heading.parentElement?.parentElement
      const divs = parent?.querySelectorAll('div')
      // Should only have the div containing heading/description
      expect(divs?.length).toBe(1)
    })
  })

  describe('Breadcrumbs', () => {
    it('renders Breadcrumbs component by default', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.getByTestId('breadcrumbs')).toBeInTheDocument()
    })

    it('does not render Breadcrumbs when breadcrumbs prop provided', () => {
      render(
        <PageContainer title="Test Page" breadcrumbs={[]}>
          <div>Content</div>
        </PageContainer>
      )

      expect(screen.queryByTestId('breadcrumbs')).not.toBeInTheDocument()
    })
  })

  describe('Content container', () => {
    it('renders children in white card container', () => {
      const { container } = render(
        <PageContainer title="Test Page">
          <div data-testid="test-content">Page content here</div>
        </PageContainer>
      )

      const content = screen.getByTestId('test-content')
      const contentContainer = content.parentElement

      expect(contentContainer?.className).toMatch(/bg-white/)
      expect(contentContainer?.className).toMatch(/rounded-lg/)
      expect(contentContainer?.className).toMatch(/shadow/)
    })

    it('renders complex children content', () => {
      render(
        <PageContainer title="Budget Dashboard">
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
    it('renders enrollment planning page', () => {
      render(
        <PageContainer
          title="Enrollment Planning"
          description="Project student enrollment for 2025-2026"
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

      expect(screen.getByText('Enrollment Planning')).toBeInTheDocument()
      expect(screen.getByText('Project student enrollment for 2025-2026')).toBeInTheDocument()
      expect(screen.getByText('Import from Skolengo')).toBeInTheDocument()
      expect(screen.getByText('Save Changes')).toBeInTheDocument()
      expect(screen.getByText('PS')).toBeInTheDocument()
    })

    it('renders DHG workforce page', () => {
      render(
        <PageContainer
          title="DHG Workforce Planning"
          description="Configure teacher allocation and hours"
          actions={<button>Calculate FTE</button>}
        >
          <div>
            <p>Total Hours: 1,250 hours/week</p>
            <p>Required FTE: 69.4 teachers</p>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('DHG Workforce Planning')).toBeInTheDocument()
      expect(screen.getByText('Total Hours: 1,250 hours/week')).toBeInTheDocument()
      expect(screen.getByText('Calculate FTE')).toBeInTheDocument()
    })

    it('renders budget consolidation page', () => {
      render(
        <PageContainer
          title="Budget Consolidation"
          description="Review and approve 2025-2026 budget"
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

      expect(screen.getByText('Budget Consolidation')).toBeInTheDocument()
      expect(screen.getByText('Review and approve 2025-2026 budget')).toBeInTheDocument()
      expect(screen.getByText('Export to Excel')).toBeInTheDocument()
      expect(screen.getByText('Total Revenue: 42,500,000 SAR')).toBeInTheDocument()
    })

    it('renders KPI dashboard page', () => {
      render(
        <PageContainer
          title="Key Performance Indicators"
          description="Monitor EFIR operational and financial metrics"
        >
          <div className="grid grid-cols-3 gap-4">
            <div>H/E Ratio: 1.52</div>
            <div>E/D Ratio: 23.5</div>
            <div>Operating Margin: 12.5%</div>
          </div>
        </PageContainer>
      )

      expect(screen.getByText('Key Performance Indicators')).toBeInTheDocument()
      expect(screen.getByText('H/E Ratio: 1.52')).toBeInTheDocument()
      expect(screen.getByText('E/D Ratio: 23.5')).toBeInTheDocument()
    })

    it('renders configuration page without breadcrumbs', () => {
      render(
        <PageContainer
          title="System Configuration"
          breadcrumbs={[
            { label: 'Home', href: '/dashboard' },
            { label: 'Configuration' },
          ]}
        >
          <form>
            <label>Fiscal Year</label>
            <select>
              <option>2025-2026</option>
            </select>
          </form>
        </PageContainer>
      )

      expect(screen.getByText('System Configuration')).toBeInTheDocument()
      expect(screen.queryByTestId('breadcrumbs')).not.toBeInTheDocument()
      expect(screen.getByText('Fiscal Year')).toBeInTheDocument()
    })
  })

  describe('Layout structure', () => {
    it('has correct container spacing', () => {
      const { container } = render(
        <PageContainer title="Test">
          <div>Content</div>
        </PageContainer>
      )

      // The mb-6 class is on the div containing the flex container
      const heading = screen.getByText('Test')
      const flexContainer = heading.parentElement?.parentElement // div with flex
      const headerSection = flexContainer?.parentElement // div with mb-6
      expect(headerSection?.className).toMatch(/mb-6/)
    })

    it('title and actions are in flex layout', () => {
      render(
        <PageContainer title="Test" actions={<button>Action</button>}>
          <div>Content</div>
        </PageContainer>
      )

      const heading = screen.getByRole('heading', { level: 1 })
      const flexContainer = heading.parentElement?.parentElement

      expect(flexContainer?.className).toMatch(/flex/)
      expect(flexContainer?.className).toMatch(/items-center/)
      expect(flexContainer?.className).toMatch(/justify-between/)
    })
  })
})
