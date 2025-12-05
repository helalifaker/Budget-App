import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

describe('Tabs', () => {
  it('renders tabs with triggers and content', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    )

    expect(screen.getByRole('tab', { name: 'Tab 1' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Tab 2' })).toBeInTheDocument()
    expect(screen.getByText('Content 1')).toBeInTheDocument()
  })

  describe('TabsList', () => {
    it('renders list of tabs', () => {
      render(
        <Tabs defaultValue="first">
          <TabsList>
            <TabsTrigger value="first">First</TabsTrigger>
            <TabsTrigger value="second">Second</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const tablist = screen.getByRole('tablist')
      expect(tablist).toBeInTheDocument()
    })

    it('has correct styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList data-testid="tabs-list">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const tablist = screen.getByTestId('tabs-list')
      expect(tablist.className).toMatch(/inline-flex/)
      expect(tablist.className).toMatch(/items-center/)
      expect(tablist.className).toMatch(/justify-center/)
      expect(tablist.className).toMatch(/rounded-md/)
      expect(tablist.className).toMatch(/bg-gray-100/)
    })

    it('applies custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList className="custom-list" data-testid="tabs-list">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const tablist = screen.getByTestId('tabs-list')
      expect(tablist.className).toMatch(/custom-list/)
      expect(tablist.className).toMatch(/inline-flex/) // Still has default classes
    })
  })

  describe('TabsTrigger', () => {
    it('renders trigger button', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Click me</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const trigger = screen.getByRole('tab', { name: 'Click me' })
      expect(trigger).toBeInTheDocument()
    })

    it('active tab has correct styling', () => {
      render(
        <Tabs defaultValue="active">
          <TabsList>
            <TabsTrigger value="active">Active Tab</TabsTrigger>
            <TabsTrigger value="inactive">Inactive Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const activeTab = screen.getByRole('tab', { name: 'Active Tab' })
      expect(activeTab).toHaveAttribute('aria-selected', 'true')
      expect(activeTab).toHaveAttribute('data-state', 'active')
    })

    it('inactive tab has correct styling', () => {
      render(
        <Tabs defaultValue="active">
          <TabsList>
            <TabsTrigger value="active">Active Tab</TabsTrigger>
            <TabsTrigger value="inactive">Inactive Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const inactiveTab = screen.getByRole('tab', { name: 'Inactive Tab' })
      expect(inactiveTab).toHaveAttribute('aria-selected', 'false')
      expect(inactiveTab).toHaveAttribute('data-state', 'inactive')
    })

    it('disabled tab has correct styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" disabled>
              Disabled Tab
            </TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const disabledTab = screen.getByRole('tab', { name: 'Disabled Tab' })
      expect(disabledTab.className).toMatch(/disabled:pointer-events-none/)
      expect(disabledTab.className).toMatch(/disabled:opacity-50/)
    })

    it('applies custom className to trigger', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" className="custom-trigger">
              Tab
            </TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const trigger = screen.getByRole('tab')
      expect(trigger.className).toMatch(/custom-trigger/)
    })
  })

  describe('TabsContent', () => {
    it('shows content for active tab', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">First tab content</TabsContent>
          <TabsContent value="tab2">Second tab content</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('First tab content')).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveAttribute('aria-selected', 'true')
    })

    it('has correct styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" data-testid="content">
            Content
          </TabsContent>
        </Tabs>
      )

      const content = screen.getByTestId('content')
      expect(content.className).toMatch(/mt-2/)
      expect(content.className).toMatch(/ring-offset-white/)
    })

    it('applies custom className to content', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" className="custom-content" data-testid="content">
            Content
          </TabsContent>
        </Tabs>
      )

      const content = screen.getByTestId('content')
      expect(content.className).toMatch(/custom-content/)
    })
  })

  describe('Interactive behavior', () => {
    it('switches to second tab when clicked', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">First content</TabsContent>
          <TabsContent value="tab2">Second content</TabsContent>
        </Tabs>
      )

      const tab2 = screen.getByRole('tab', { name: 'Tab 2' })
      await user.click(tab2)

      expect(screen.getByText('Second content')).toBeInTheDocument()
      expect(tab2).toHaveAttribute('aria-selected', 'true')
    })

    it('switches back to first tab when clicked', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="tab2">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">First content</TabsContent>
          <TabsContent value="tab2">Second content</TabsContent>
        </Tabs>
      )

      const tab1 = screen.getByRole('tab', { name: 'Tab 1' })
      await user.click(tab1)

      expect(screen.getByText('First content')).toBeInTheDocument()
      expect(tab1).toHaveAttribute('aria-selected', 'true')
    })

    it('does not switch when disabled tab is clicked', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2" disabled>
              Tab 2 (Disabled)
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">First content</TabsContent>
          <TabsContent value="tab2">Second content</TabsContent>
        </Tabs>
      )

      const disabledTab = screen.getByRole('tab', { name: 'Tab 2 (Disabled)' })
      await user.click(disabledTab)

      expect(screen.getByText('First content')).toBeInTheDocument()
      const tab1 = screen.getByRole('tab', { name: 'Tab 1' })
      expect(tab1).toHaveAttribute('aria-selected', 'true')
    })
  })

  describe('Keyboard navigation', () => {
    it('navigates with arrow keys', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
            <TabsTrigger value="tab3">Tab 3</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
          <TabsContent value="tab3">Content 3</TabsContent>
        </Tabs>
      )

      const tab1 = screen.getByRole('tab', { name: 'Tab 1' })
      tab1.focus()

      await user.keyboard('{ArrowRight}')
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveFocus()

      await user.keyboard('{ArrowRight}')
      expect(screen.getByRole('tab', { name: 'Tab 3' })).toHaveFocus()

      await user.keyboard('{ArrowLeft}')
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveFocus()
    })

    it('is keyboard accessible via Tab key', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      await user.tab()
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveFocus()
    })
  })

  describe('Real-world use cases', () => {
    it('renders budget planning tabs', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="enrollment">
          <TabsList>
            <TabsTrigger value="enrollment">Enrollment</TabsTrigger>
            <TabsTrigger value="dhg">DHG Workforce</TabsTrigger>
            <TabsTrigger value="revenue">Revenue</TabsTrigger>
          </TabsList>
          <TabsContent value="enrollment">
            <h2>Enrollment Planning</h2>
            <p>Student projections by academic level</p>
          </TabsContent>
          <TabsContent value="dhg">
            <h2>DHG Workforce Planning</h2>
            <p>Teacher allocation and hours</p>
          </TabsContent>
          <TabsContent value="revenue">
            <h2>Revenue Planning</h2>
            <p>Tuition and fee calculations</p>
          </TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Enrollment Planning')).toBeInTheDocument()

      const dhgTab = screen.getByRole('tab', { name: 'DHG Workforce' })
      await user.click(dhgTab)

      expect(screen.getByText('DHG Workforce Planning')).toBeInTheDocument()
      expect(dhgTab).toHaveAttribute('aria-selected', 'true')
    })

    it('renders budget version tabs', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="working">
          <TabsList>
            <TabsTrigger value="working">Working</TabsTrigger>
            <TabsTrigger value="submitted">Submitted</TabsTrigger>
            <TabsTrigger value="approved">Approved</TabsTrigger>
          </TabsList>
          <TabsContent value="working">
            <p>2025-2026 Working Version</p>
          </TabsContent>
          <TabsContent value="submitted">
            <p>2025-2026 Submitted Version</p>
          </TabsContent>
          <TabsContent value="approved">
            <p>2024-2025 Approved Budget</p>
          </TabsContent>
        </Tabs>
      )

      expect(screen.getByText('2025-2026 Working Version')).toBeVisible()

      const approvedTab = screen.getByRole('tab', { name: 'Approved' })
      await user.click(approvedTab)

      expect(screen.getByText('2024-2025 Approved Budget')).toBeVisible()
    })

    it('renders financial statement format tabs', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="pcg">
          <TabsList>
            <TabsTrigger value="pcg">French PCG</TabsTrigger>
            <TabsTrigger value="ifrs">IFRS</TabsTrigger>
          </TabsList>
          <TabsContent value="pcg">
            <h3>Plan Comptable Général</h3>
            <p>64110 - Teaching Salaries AEFE</p>
            <p>70110 - Tuition T1</p>
          </TabsContent>
          <TabsContent value="ifrs">
            <h3>International Financial Reporting Standards</h3>
            <p>Revenue from contracts with customers</p>
          </TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Plan Comptable Général')).toBeVisible()

      const ifrsTab = screen.getByRole('tab', { name: 'IFRS' })
      await user.click(ifrsTab)

      expect(screen.getByText('International Financial Reporting Standards')).toBeVisible()
    })

    it('renders KPI category tabs', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="operational">
          <TabsList>
            <TabsTrigger value="operational">Operational</TabsTrigger>
            <TabsTrigger value="financial">Financial</TabsTrigger>
            <TabsTrigger value="strategic">Strategic</TabsTrigger>
          </TabsList>
          <TabsContent value="operational">
            <p>H/E Ratio: 1.52</p>
            <p>E/D Ratio: 23.5</p>
          </TabsContent>
          <TabsContent value="financial">
            <p>Operating Margin: 12.5%</p>
            <p>Cost per Student: 45,300 SAR</p>
          </TabsContent>
          <TabsContent value="strategic">
            <p>Enrollment Growth: 5.2%</p>
            <p>Market Share: 18%</p>
          </TabsContent>
        </Tabs>
      )

      expect(screen.getByText('H/E Ratio: 1.52')).toBeVisible()

      const financialTab = screen.getByRole('tab', { name: 'Financial' })
      await user.click(financialTab)

      expect(screen.getByText('Operating Margin: 12.5%')).toBeVisible()
    })

    it('renders academic level tabs', async () => {
      const user = userEvent.setup()

      render(
        <Tabs defaultValue="maternelle">
          <TabsList>
            <TabsTrigger value="maternelle">Maternelle</TabsTrigger>
            <TabsTrigger value="elementaire">Élémentaire</TabsTrigger>
            <TabsTrigger value="college">Collège</TabsTrigger>
            <TabsTrigger value="lycee">Lycée</TabsTrigger>
          </TabsList>
          <TabsContent value="maternelle">PS, MS, GS</TabsContent>
          <TabsContent value="elementaire">CP, CE1, CE2, CM1, CM2</TabsContent>
          <TabsContent value="college">6ème, 5ème, 4ème, 3ème</TabsContent>
          <TabsContent value="lycee">2nde, 1ère, Terminale</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('PS, MS, GS')).toBeVisible()

      const collegeTab = screen.getByRole('tab', { name: 'Collège' })
      await user.click(collegeTab)

      expect(screen.getByText('6ème, 5ème, 4ème, 3ème')).toBeVisible()
    })
  })

  describe('Accessibility', () => {
    it('tabs have proper ARIA roles', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const tablist = screen.getByRole('tablist')
      const tabs = screen.getAllByRole('tab')

      expect(tablist).toBeInTheDocument()
      expect(tabs).toHaveLength(2)
    })

    it('active tab has aria-selected=true', () => {
      render(
        <Tabs defaultValue="active">
          <TabsList>
            <TabsTrigger value="active">Active Tab</TabsTrigger>
            <TabsTrigger value="inactive">Inactive Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const activeTab = screen.getByRole('tab', { name: 'Active Tab' })
      expect(activeTab).toHaveAttribute('aria-selected', 'true')
    })

    it('inactive tab has aria-selected=false', () => {
      render(
        <Tabs defaultValue="active">
          <TabsList>
            <TabsTrigger value="active">Active Tab</TabsTrigger>
            <TabsTrigger value="inactive">Inactive Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      )

      const inactiveTab = screen.getByRole('tab', { name: 'Inactive Tab' })
      expect(inactiveTab).toHaveAttribute('aria-selected', 'false')
    })

    it('content has tabpanel role', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const tabpanel = screen.getByRole('tabpanel')
      expect(tabpanel).toBeInTheDocument()
    })
  })

  describe('Controlled state', () => {
    it('can be controlled with value prop', async () => {
      const user = userEvent.setup()
      let currentValue = 'tab1'

      const { rerender } = render(
        <Tabs value={currentValue} onValueChange={(val) => (currentValue = val)}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Content 1')).toBeVisible()

      const tab2 = screen.getByRole('tab', { name: 'Tab 2' })
      await user.click(tab2)

      // Rerender with new value
      rerender(
        <Tabs value="tab2" onValueChange={(val) => (currentValue = val)}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Content 2')).toBeVisible()
    })
  })
})
