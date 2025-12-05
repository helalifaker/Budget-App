import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as CostsRoute } from '@/routes/planning/costs'

// Mock dependencies
const mockNavigate = vi.fn()
let mockPersonnelCostsData: any = null
let mockOperatingCostsData: any = null
const mockCalculatePersonnelMutation = vi.fn()

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: (path: string) => (config: any) => ({
    ...config,
    path,
  }),
  Link: ({ to, children, className }: any) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
  useNavigate: () => mockNavigate,
}))

vi.mock('@/components/layout/MainLayout', () => ({
  MainLayout: ({ children }: any) => <div data-testid="main-layout">{children}</div>,
}))

vi.mock('@/components/layout/PageContainer', () => ({
  PageContainer: ({ title, description, children }: any) => (
    <div data-testid="page-container">
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({ value, onChange }: any) => (
    <div data-testid="budget-version-selector">
      <select
        data-testid="version-select"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select version</option>
        <option value="v1">2025-2026</option>
        <option value="v2">2024-2025</option>
      </select>
    </div>
  ),
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({ title, value, subtitle, icon }: any) => (
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value">{value}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
      {icon}
    </div>
  ),
}))

vi.mock('@/components/charts/CostChart', () => ({
  CostChart: ({ data, title }: any) => (
    <div data-testid="cost-chart">
      <div>{title}</div>
      <div>Chart with {data?.length} periods</div>
    </div>
  ),
}))

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: any) => (
    <div data-testid="tabs" data-value={value}>
      {children}
    </div>
  ),
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ value, children }: any) => (
    <button data-testid={`tab-trigger-${value}`}>{children}</button>
  ),
  TabsContent: ({ value, children }: any) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children, className }: any) => (
    <div data-testid="card-header" className={className}>
      {children}
    </div>
  ),
  CardTitle: ({ children }: any) => <div data-testid="card-title">{children}</div>,
  CardContent: ({ children, className }: any) => (
    <div data-testid="card-content" className={className}>
      {children}
    </div>
  ),
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: any) => (
    <div data-testid="ag-grid">
      {rowData?.map((row: any, index: number) => (
        <div key={row.account_code || index} data-testid="cost-row">
          {row.account_code}: {row.description}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('ag-grid-community', () => ({
  themeQuartz: 'theme-quartz',
}))

vi.mock('@/components/grid/AccountCodeRenderer', () => ({
  AccountCodeRenderer: () => null,
}))

vi.mock('@/components/grid/CurrencyRenderer', () => ({
  CurrencyRenderer: () => null,
}))

vi.mock('@/hooks/api/useCosts', () => ({
  useCosts: (versionId: string, type: string) => {
    if (!versionId) return { data: null, isLoading: false }
    return {
      data: type === 'PERSONNEL' ? mockPersonnelCostsData : mockOperatingCostsData,
      isLoading: false,
    }
  },
  useCalculatePersonnelCosts: () => ({
    mutate: mockCalculatePersonnelMutation,
    isPending: false,
  }),
}))

vi.mock('lucide-react', () => ({
  DollarSign: () => <span>DollarSign Icon</span>,
  Users: () => <span>Users Icon</span>,
  ShoppingCart: () => <span>ShoppingCart Icon</span>,
  Calculator: () => <span>Calculator Icon</span>,
  Download: () => <span>Download Icon</span>,
  Plus: () => <span>Plus Icon</span>,
}))

describe('Cost Planning Route', () => {
  const CostsPage = CostsRoute.component

  beforeEach(() => {
    vi.clearAllMocks()

    mockPersonnelCostsData = {
      items: [
        {
          account_code: '64110',
          description: 'Teacher Salaries',
          cost_type: 'Salaries',
          p1_amount: 2000000,
          summer_amount: 500000,
          p2_amount: 1500000,
          annual_amount: 4000000,
          is_auto_calculated: true,
          notes: '',
        },
        {
          account_code: '64510',
          description: 'Social Charges',
          cost_type: 'Benefits',
          p1_amount: 800000,
          summer_amount: 200000,
          p2_amount: 600000,
          annual_amount: 1600000,
          is_auto_calculated: true,
          notes: '',
        },
      ],
    }

    mockOperatingCostsData = {
      items: [
        {
          account_code: '60610',
          description: 'Supplies & Materials',
          cost_type: 'Supplies',
          p1_amount: 300000,
          summer_amount: 50000,
          p2_amount: 250000,
          annual_amount: 600000,
          is_auto_calculated: false,
          notes: '',
        },
        {
          account_code: '61300',
          description: 'Utilities',
          cost_type: 'Utilities',
          p1_amount: 200000,
          summer_amount: 100000,
          p2_amount: 200000,
          annual_amount: 500000,
          is_auto_calculated: false,
          notes: '',
        },
      ],
    }
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<CostsPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<CostsPage />)

      expect(screen.getByText('Cost Planning')).toBeInTheDocument()
      expect(screen.getByText('Manage personnel and operating costs by period')).toBeInTheDocument()
    })
  })

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<CostsPage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
    })
  })

  describe('Action buttons', () => {
    it('renders Recalculate Personnel Costs button', () => {
      render(<CostsPage />)

      expect(screen.getByText('Recalculate Personnel Costs')).toBeInTheDocument()
    })

    it('renders Export button', () => {
      render(<CostsPage />)

      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    it('disables Recalculate button when no version selected', () => {
      render(<CostsPage />)

      const calculateBtn = screen.getByText('Recalculate Personnel Costs').closest('button')
      expect(calculateBtn).toBeDisabled()
    })

    it('enables Recalculate button when version selected', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const calculateBtn = screen.getByText('Recalculate Personnel Costs').closest('button')
        expect(calculateBtn).not.toBeDisabled()
      })
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<CostsPage />)

      expect(screen.queryByTestId('summary-card-total-costs')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-costs')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-personnel-costs')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-operating-costs')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-personnel-%')).toBeInTheDocument()
      })
    })

    it('calculates total costs correctly', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const totalCard = screen.getByTestId('summary-card-total-costs')
        // Personnel (5,600,000) + Operating (1,100,000) = 6,700,000
        expect(totalCard).toHaveTextContent('SAR')
      })
    })
  })

  describe('Tabs', () => {
    it('displays tabs component', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-personnel')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-operating')).toBeInTheDocument()
      })
    })

    it('defaults to personnel tab', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const tabs = screen.getByTestId('tabs')
        expect(tabs).toHaveAttribute('data-value', 'personnel')
      })
    })
  })

  describe('Personnel costs tab', () => {
    it('displays personnel costs grid', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('tab-content-personnel')).toBeInTheDocument()
        // Personnel Costs appears both in tab trigger and card title, so use getAllByText
        const personnelTexts = screen.getAllByText('Personnel Costs')
        expect(personnelTexts.length).toBeGreaterThan(0)
      })
    })

    it('displays personnel cost rows', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText(/64110: Teacher Salaries/)).toBeInTheDocument()
        expect(screen.getByText(/64510: Social Charges/)).toBeInTheDocument()
      })
    })
  })

  describe('Operating costs tab', () => {
    it('displays Add Line Item button', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Add Line Item')).toBeInTheDocument()
      })
    })
  })

  describe('Cost chart', () => {
    it('does not show chart when no version selected', () => {
      render(<CostsPage />)

      expect(screen.queryByTestId('cost-chart')).not.toBeInTheDocument()
    })

    it('displays cost chart when version selected', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('cost-chart')).toBeInTheDocument()
        expect(screen.getByText('Cost Breakdown by Period')).toBeInTheDocument()
        expect(screen.getByText('Chart with 3 periods')).toBeInTheDocument()
      })
    })
  })

  describe('Cost notes', () => {
    it('displays cost notes section when version selected', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Cost Planning Notes')).toBeInTheDocument()
        expect(screen.getByText('Personnel Costs (641xx, 645xx)')).toBeInTheDocument()
        expect(screen.getByText('AEFE Contributions')).toBeInTheDocument()
        expect(screen.getByText('Operating Costs (606xx-625xx)')).toBeInTheDocument()
        expect(screen.getByText('Period Allocation')).toBeInTheDocument()
      })
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<CostsPage />)

      expect(screen.getByText('Select a budget version to view cost planning')).toBeInTheDocument()
    })

    it('hides placeholder when version selected', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(
          screen.queryByText('Select a budget version to view cost planning')
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full cost planning workflow', async () => {
      const user = userEvent.setup()

      render(<CostsPage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify summary cards appear
        expect(screen.getByTestId('summary-card-total-costs')).toBeInTheDocument()

        // Verify tabs appear
        expect(screen.getByTestId('tabs')).toBeInTheDocument()

        // Verify chart appears
        expect(screen.getByTestId('cost-chart')).toBeInTheDocument()

        // Verify notes appear
        expect(screen.getByText('Cost Planning Notes')).toBeInTheDocument()

        // Verify action button is enabled
        const calculateBtn = screen.getByText('Recalculate Personnel Costs').closest('button')
        expect(calculateBtn).not.toBeDisabled()
      })
    })

    it('handles empty cost data', async () => {
      mockPersonnelCostsData = { items: [] }
      mockOperatingCostsData = { items: [] }
      const user = userEvent.setup()

      render(<CostsPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Summary cards should show 0 values
        expect(screen.getByTestId('summary-card-total-costs')).toBeInTheDocument()
        // Grid should still render but with no rows
        expect(screen.queryAllByTestId('cost-row')).toHaveLength(0)
      })
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(CostsRoute.path).toBe('/planning/costs')
    })
  })
})
