import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as RevenueRoute } from '@/routes/planning/revenue'

// Mock dependencies
const mockNavigate = vi.fn()
let mockRevenueData: any = null
const mockCalculateMutation = vi.fn()

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

vi.mock('@/components/charts/RevenueChart', () => ({
  RevenueChart: ({ data, title }: any) => (
    <div data-testid="revenue-chart">
      <div>{title}</div>
      <div>Chart with {data?.length} categories</div>
    </div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
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
      {rowData?.map((row: any) => (
        <div key={row.id} data-testid="revenue-row">
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

vi.mock('@/hooks/api/useRevenue', () => ({
  useRevenue: (versionId: string) => ({
    data: versionId ? mockRevenueData : null,
    isLoading: false,
  }),
  useCalculateRevenue: () => ({
    mutate: mockCalculateMutation,
    isPending: false,
  }),
}))

vi.mock('lucide-react', () => ({
  DollarSign: () => <span>DollarSign Icon</span>,
  TrendingUp: () => <span>TrendingUp Icon</span>,
  Calculator: () => <span>Calculator Icon</span>,
  Download: () => <span>Download Icon</span>,
}))

describe('Revenue Planning Route', () => {
  const RevenuePage = RevenueRoute.component

  beforeEach(() => {
    vi.clearAllMocks()

    mockRevenueData = {
      items: [
        {
          id: '1',
          account_code: '70110',
          description: 'Tuition - French Nationality',
          category: 'Tuition',
          t1_amount: 1200000,
          t2_amount: 900000,
          t3_amount: 900000,
          annual_amount: 3000000,
          is_auto_calculated: true,
          notes: '',
        },
        {
          id: '2',
          account_code: '70200',
          description: 'Enrollment Fees',
          category: 'Fees',
          t1_amount: 400000,
          t2_amount: 300000,
          t3_amount: 300000,
          annual_amount: 1000000,
          is_auto_calculated: true,
          notes: '',
        },
        {
          id: '3',
          account_code: '75100',
          description: 'Transportation Services',
          category: 'Other',
          t1_amount: 200000,
          t2_amount: 150000,
          t3_amount: 150000,
          annual_amount: 500000,
          is_auto_calculated: false,
          notes: '',
        },
      ],
    }
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<RevenuePage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<RevenuePage />)

      expect(screen.getByText('Revenue Planning')).toBeInTheDocument()
      expect(screen.getByText('Manage revenue projections by category and trimester')).toBeInTheDocument()
    })
  })

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<RevenuePage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
    })
  })

  describe('Action buttons', () => {
    it('renders Recalculate Revenue button', () => {
      render(<RevenuePage />)

      expect(screen.getByText('Recalculate Revenue')).toBeInTheDocument()
    })

    it('renders Export button', () => {
      render(<RevenuePage />)

      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    it('disables Recalculate button when no version selected', () => {
      render(<RevenuePage />)

      const calculateBtn = screen.getByText('Recalculate Revenue').closest('button')
      expect(calculateBtn).toBeDisabled()
    })

    it('enables Recalculate button when version selected', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const calculateBtn = screen.getByText('Recalculate Revenue').closest('button')
        expect(calculateBtn).not.toBeDisabled()
      })
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<RevenuePage />)

      expect(screen.queryByTestId('summary-card-total-revenue')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-revenue')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-tuition-revenue')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-enrollment-fees')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-other-revenue')).toBeInTheDocument()
      })
    })

    it('calculates total revenue correctly', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const totalCard = screen.getByTestId('summary-card-total-revenue')
        // Tuition (3,000,000) + Fees (1,000,000) + Other (500,000) = 4,500,000
        expect(totalCard).toHaveTextContent('SAR')
      })
    })

    it('calculates tuition revenue correctly', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const tuitionCard = screen.getByTestId('summary-card-tuition-revenue')
        // 3,000,000 SAR from account 70110
        expect(tuitionCard).toHaveTextContent('SAR')
      })
    })
  })

  describe('Revenue chart', () => {
    it('does not show chart when no version selected', () => {
      render(<RevenuePage />)

      expect(screen.queryByTestId('revenue-chart')).not.toBeInTheDocument()
    })

    it('displays revenue chart when version selected', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
        expect(screen.getByText('Revenue Breakdown')).toBeInTheDocument()
        expect(screen.getByText('Chart with 3 categories')).toBeInTheDocument()
      })
    })
  })

  describe('Revenue notes', () => {
    it('displays revenue notes section when version selected', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Revenue Notes')).toBeInTheDocument()
        expect(screen.getByText('Tuition (70110-70130)')).toBeInTheDocument()
        expect(screen.getByText('Enrollment Fees (70200-70299)')).toBeInTheDocument()
        expect(screen.getByText('Other Revenue (75xxx-77xxx)')).toBeInTheDocument()
        expect(screen.getByText('Trimester Split')).toBeInTheDocument()
      })
    })
  })

  describe('AG Grid', () => {
    it('displays AG Grid with revenue data', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
        const rows = screen.getAllByTestId('revenue-row')
        expect(rows).toHaveLength(3)
      })
    })

    it('displays revenue row details', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText(/70110: Tuition - French Nationality/)).toBeInTheDocument()
        expect(screen.getByText(/70200: Enrollment Fees/)).toBeInTheDocument()
        expect(screen.getByText(/75100: Transportation Services/)).toBeInTheDocument()
      })
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<RevenuePage />)

      expect(screen.getByText('Select a budget version to view revenue planning')).toBeInTheDocument()
    })

    it('hides placeholder when version selected', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(
          screen.queryByText('Select a budget version to view revenue planning')
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full revenue planning workflow', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify summary cards appear
        expect(screen.getByTestId('summary-card-total-revenue')).toBeInTheDocument()

        // Verify chart appears
        expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()

        // Verify AG Grid appears
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()

        // Verify notes appear
        expect(screen.getByText('Revenue Notes')).toBeInTheDocument()

        // Verify action button is enabled
        const calculateBtn = screen.getByText('Recalculate Revenue').closest('button')
        expect(calculateBtn).not.toBeDisabled()
      })
    })

    it('handles empty revenue data', async () => {
      mockRevenueData = { items: [] }
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Summary cards should show 0 values
        expect(screen.getByTestId('summary-card-total-revenue')).toBeInTheDocument()
        // AG Grid should still render but with no rows
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
        expect(screen.queryAllByTestId('revenue-row')).toHaveLength(0)
      })
    })

    it('allows switching between budget versions', async () => {
      const user = userEvent.setup()

      render(<RevenuePage />)

      const select = screen.getByTestId('version-select')

      // Select first version
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
      })

      // Switch to second version
      await user.selectOptions(select, 'v2')

      expect(select).toHaveValue('v2')
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(RevenueRoute.path).toBe('/planning/revenue')
    })
  })
})
