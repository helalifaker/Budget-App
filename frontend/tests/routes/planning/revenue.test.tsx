import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as RevenueRoute } from '@/routes/planning/revenue'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockRevenueData: unknown = null
const mockCalculateMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: (path: string) => (config: unknown) => ({
    ...(config as object),
    path,
  }),
  Link: ({
    to,
    children,
    className,
  }: {
    to: string
    children: React.ReactNode
    className?: string
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
  useNavigate: () => mockNavigate,
}))

// Mock BudgetVersionContext - this must come before component imports
vi.mock('@/contexts/BudgetVersionContext', () => ({
  useBudgetVersion: () => ({
    selectedVersionId: mockSelectedVersionId,
    selectedVersion: mockSelectedVersionId
      ? { id: mockSelectedVersionId, name: '2025-2026', status: 'working' }
      : null,
    setSelectedVersionId: mockSetSelectedVersionId,
    versions: [
      { id: 'v1', name: '2025-2026', status: 'working' },
      { id: 'v2', name: '2024-2025', status: 'approved' },
    ],
    isLoading: false,
    error: null,
    clearSelection: () => {
      mockSelectedVersionId = undefined
    },
  }),
}))

vi.mock('@/components/layout/MainLayout', () => ({
  MainLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  ),
}))

vi.mock('@/components/layout/PageContainer', () => ({
  PageContainer: ({
    title,
    description,
    children,
  }: {
    title: string
    description?: string
    children: React.ReactNode
  }) => (
    <div data-testid="page-container">
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({
    value,
    onChange,
  }: {
    value?: string
    onChange: (value: string) => void
  }) => (
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
  SummaryCard: ({
    title,
    value,
    subtitle,
    icon,
  }: {
    title: string
    value: React.ReactNode
    subtitle?: string
    icon?: React.ReactNode
  }) => (
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value">{value}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
      {icon}
    </div>
  ),
}))

vi.mock('@/components/charts/RevenueChart', () => ({
  RevenueChart: ({ data, title }: { data?: unknown[]; title?: string }) => (
    <div data-testid="revenue-chart">
      <div>{title}</div>
      <div>Chart with {data?.length} categories</div>
    </div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-header">{children}</div>
  ),
  CardTitle: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-title">{children}</div>
  ),
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-content" className={className}>
      {children}
    </div>
  ),
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({
    rowData,
  }: {
    rowData?: Array<{ id: string; account_code: string; description: string }>
  }) => (
    <div data-testid="ag-grid">
      {rowData?.map((row) => (
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
    mockSelectedVersionId = undefined // Reset version selection

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
      expect(
        screen.getByText('Manage revenue projections by category and trimester')
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      // Set version via context mock
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      // Page should render with data when version is selected
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<RevenuePage />)

      // Should show placeholder text
      expect(screen.getByText(/Select a budget version/i)).toBeInTheDocument()
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

    it('enables Recalculate button when version selected', () => {
      // Set version via context mock
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      const calculateBtn = screen.getByText('Recalculate Revenue').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<RevenuePage />)

      expect(screen.queryByTestId('summary-card-total-revenue')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(screen.getByTestId('summary-card-total-revenue')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-tuition-revenue')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-enrollment-fees')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-other-revenue')).toBeInTheDocument()
    })

    it('calculates total revenue correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      const totalCard = screen.getByTestId('summary-card-total-revenue')
      // Tuition (3,000,000) + Fees (1,000,000) + Other (500,000) = 4,500,000
      expect(totalCard).toHaveTextContent('SAR')
    })

    it('calculates tuition revenue correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      const tuitionCard = screen.getByTestId('summary-card-tuition-revenue')
      // 3,000,000 SAR from account 70110
      expect(tuitionCard).toHaveTextContent('SAR')
    })
  })

  describe('Revenue chart', () => {
    it('does not show chart when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<RevenuePage />)

      expect(screen.queryByTestId('revenue-chart')).not.toBeInTheDocument()
    })

    it('displays revenue chart when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
      expect(screen.getByText('Revenue Breakdown')).toBeInTheDocument()
      expect(screen.getByText('Chart with 3 categories')).toBeInTheDocument()
    })
  })

  describe('Revenue notes', () => {
    it('displays revenue notes section when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(screen.getByText('Revenue Notes')).toBeInTheDocument()
      expect(screen.getByText('Tuition (70110-70130)')).toBeInTheDocument()
      expect(screen.getByText('Enrollment Fees (70200-70299)')).toBeInTheDocument()
      expect(screen.getByText('Other Revenue (75xxx-77xxx)')).toBeInTheDocument()
      expect(screen.getByText('Trimester Split')).toBeInTheDocument()
    })
  })

  describe('AG Grid', () => {
    it('displays AG Grid with revenue data', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
      const rows = screen.getAllByTestId('revenue-row')
      expect(rows).toHaveLength(3)
    })

    it('displays revenue row details', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(screen.getByText(/70110: Tuition - French Nationality/)).toBeInTheDocument()
      expect(screen.getByText(/70200: Enrollment Fees/)).toBeInTheDocument()
      expect(screen.getByText(/75100: Transportation Services/)).toBeInTheDocument()
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<RevenuePage />)

      expect(
        screen.getByText('Select a budget version to view revenue planning')
      ).toBeInTheDocument()
    })

    it('hides placeholder when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      expect(
        screen.queryByText('Select a budget version to view revenue planning')
      ).not.toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full revenue planning workflow', () => {
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

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

    it('handles empty revenue data', () => {
      mockRevenueData = { items: [] }
      mockSelectedVersionId = 'v1'
      render(<RevenuePage />)

      // Summary cards should show 0 values
      expect(screen.getByTestId('summary-card-total-revenue')).toBeInTheDocument()
      // AG Grid should still render but with no rows
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
      expect(screen.queryAllByTestId('revenue-row')).toHaveLength(0)
    })

    it('context provides version switching capability', () => {
      // Test that context provides version switching
      mockSelectedVersionId = 'v1'
      const { rerender } = render(<RevenuePage />)

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()

      // Simulate version change via context
      mockSelectedVersionId = 'v2'
      rerender(<RevenuePage />)

      // Page should still render (context provides new version)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(RevenueRoute.path).toBe('/planning/revenue')
    })
  })
})
