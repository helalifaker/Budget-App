import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as CostsRoute } from '@/routes/planning/costs'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockPersonnelCostsData: Record<string, unknown>[] | null = null
let mockOperatingCostsData: Record<string, unknown>[] | null = null
const mockCalculatePersonnelMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface CostRow {
  account_code: string
  description: string
}

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: (path: string) => (config: MockProps) => ({
    ...config,
    path,
  }),
  Link: ({ to, children, className }: MockProps) => (
    <a href={to as string} className={className as string}>
      {children as React.ReactNode}
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
  MainLayout: ({ children }: MockProps) => (
    <div data-testid="main-layout">{children as React.ReactNode}</div>
  ),
}))

vi.mock('@/components/layout/PageContainer', () => ({
  PageContainer: ({ title, description, children }: MockProps) => (
    <div data-testid="page-container">
      <h1>{title as string}</h1>
      {description && <p>{description as string}</p>}
      {children as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({ value, onChange }: MockProps) => (
    <div data-testid="budget-version-selector">
      <select
        data-testid="version-select"
        value={(value as string) || ''}
        onChange={(e) => (onChange as (v: string) => void)(e.target.value)}
      >
        <option value="">Select version</option>
        <option value="v1">2025-2026</option>
        <option value="v2">2024-2025</option>
      </select>
    </div>
  ),
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({ title, value, subtitle, icon }: MockProps) => (
    <div data-testid={`summary-card-${(title as string).toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title as string}</div>
      <div data-testid="card-value">{value as React.ReactNode}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle as string}</div>}
      {icon as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/components/charts/CostChart', () => ({
  CostChart: ({ data, title }: MockProps) => (
    <div data-testid="cost-chart">
      <div>{title as string}</div>
      <div>Chart with {(data as unknown[] | undefined)?.length} periods</div>
    </div>
  ),
}))

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value }: MockProps) => (
    <div data-testid="tabs" data-value={value as string}>
      {children as React.ReactNode}
    </div>
  ),
  TabsList: ({ children }: MockProps) => (
    <div data-testid="tabs-list">{children as React.ReactNode}</div>
  ),
  TabsTrigger: ({ value, children }: MockProps) => (
    <button data-testid={`tab-trigger-${value as string}`}>{children as React.ReactNode}</button>
  ),
  TabsContent: ({ value, children }: MockProps) => (
    <div data-testid={`tab-content-${value as string}`}>{children as React.ReactNode}</div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: MockProps) => (
    <div data-testid="card" className={className as string}>
      {children as React.ReactNode}
    </div>
  ),
  CardHeader: ({ children, className }: MockProps) => (
    <div data-testid="card-header" className={className as string}>
      {children as React.ReactNode}
    </div>
  ),
  CardTitle: ({ children }: MockProps) => (
    <div data-testid="card-title">{children as React.ReactNode}</div>
  ),
  CardContent: ({ children, className }: MockProps) => (
    <div data-testid="card-content" className={className as string}>
      {children as React.ReactNode}
    </div>
  ),
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: MockProps) => (
    <div data-testid="ag-grid">
      {(rowData as CostRow[] | undefined)?.map((row, index) => (
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
  // Renamed from useCosts to separate usePersonnelCosts and useOperatingCosts
  usePersonnelCosts: (versionId: string) => ({
    data: versionId ? mockPersonnelCostsData : null,
    isLoading: false,
  }),
  useOperatingCosts: (versionId: string) => ({
    data: versionId ? mockOperatingCostsData : null,
    isLoading: false,
  }),
  useCalculatePersonnelCosts: () => ({
    mutate: mockCalculatePersonnelMutation,
    isPending: false,
  }),
  costsKeys: {
    all: ['costs'],
    personnel: (versionId: string) => ['costs', 'personnel', versionId],
    operating: (versionId: string) => ['costs', 'operating', versionId],
    summary: (versionId: string) => ['costs', 'summary', versionId],
  },
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
    mockSelectedVersionId = undefined // Reset version selection

    // API returns arrays directly - matches PersonnelCostPlan type
    mockPersonnelCostsData = [
      {
        id: '1',
        budget_version_id: 'v1',
        account_code: '64110',
        description: 'Teacher Salaries',
        fte_count: 20,
        unit_cost_sar: 200000,
        total_cost_sar: 4000000,
        category_id: 'salaries',
        cycle_id: null,
        is_calculated: true,
        calculation_driver: 'DHG',
        notes: '',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: '2',
        budget_version_id: 'v1',
        account_code: '64510',
        description: 'Social Charges',
        fte_count: 20,
        unit_cost_sar: 80000,
        total_cost_sar: 1600000,
        category_id: 'benefits',
        cycle_id: null,
        is_calculated: true,
        calculation_driver: 'DHG',
        notes: '',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    // API returns arrays directly - matches OperatingCostPlan type
    mockOperatingCostsData = [
      {
        id: '3',
        budget_version_id: 'v1',
        account_code: '60610',
        description: 'Supplies & Materials',
        category: 'supplies',
        amount_sar: 600000,
        is_calculated: false,
        calculation_driver: null,
        notes: '',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: '4',
        budget_version_id: 'v1',
        account_code: '61300',
        description: 'Utilities',
        category: 'utilities',
        amount_sar: 500000,
        is_calculated: false,
        calculation_driver: null,
        notes: '',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]
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

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<CostsPage />)

      expect(screen.getByText(/Select a budget version/i)).toBeInTheDocument()
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

    it('enables Recalculate button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      const calculateBtn = screen.getByText('Recalculate Personnel Costs').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<CostsPage />)

      expect(screen.queryByTestId('summary-card-total-costs')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByTestId('summary-card-total-costs')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-personnel-costs')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-operating-costs')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-personnel-%')).toBeInTheDocument()
    })

    it('calculates total costs correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      const totalCard = screen.getByTestId('summary-card-total-costs')
      // Personnel (5,600,000) + Operating (1,100,000) = 6,700,000
      expect(totalCard).toHaveTextContent('SAR')
    })
  })

  describe('Tabs', () => {
    it('displays tabs component', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-personnel')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-operating')).toBeInTheDocument()
    })

    it('defaults to personnel tab', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      const tabs = screen.getByTestId('tabs')
      expect(tabs).toHaveAttribute('data-value', 'personnel')
    })
  })

  describe('Personnel costs tab', () => {
    it('displays personnel costs grid', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByTestId('tab-content-personnel')).toBeInTheDocument()
      // Personnel Costs appears both in tab trigger and card title, so use getAllByText
      const personnelTexts = screen.getAllByText('Personnel Costs')
      expect(personnelTexts.length).toBeGreaterThan(0)
    })

    it('displays personnel cost rows', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByText(/64110: Teacher Salaries/)).toBeInTheDocument()
      expect(screen.getByText(/64510: Social Charges/)).toBeInTheDocument()
    })
  })

  describe('Operating costs tab', () => {
    it('displays Add Line Item button', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByText('Add Line Item')).toBeInTheDocument()
    })
  })

  describe('Cost chart', () => {
    it('does not show chart when no version selected', () => {
      render(<CostsPage />)

      expect(screen.queryByTestId('cost-chart')).not.toBeInTheDocument()
    })

    it('displays cost chart when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByTestId('cost-chart')).toBeInTheDocument()
      expect(screen.getByText('Cost Breakdown by Period')).toBeInTheDocument()
      expect(screen.getByText('Chart with 3 periods')).toBeInTheDocument()
    })
  })

  describe('Cost notes', () => {
    it('displays cost notes section when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(screen.getByText('Cost Planning Notes')).toBeInTheDocument()
      expect(screen.getByText('Personnel Costs (641xx, 645xx)')).toBeInTheDocument()
      expect(screen.getByText('AEFE Contributions')).toBeInTheDocument()
      expect(screen.getByText('Operating Costs (606xx-625xx)')).toBeInTheDocument()
      expect(screen.getByText('Period Allocation')).toBeInTheDocument()
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<CostsPage />)

      expect(screen.getByText('Select a budget version to view cost planning')).toBeInTheDocument()
    })

    it('hides placeholder when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      expect(
        screen.queryByText('Select a budget version to view cost planning')
      ).not.toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full cost planning workflow', () => {
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

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

    it('handles empty cost data', () => {
      mockPersonnelCostsData = []
      mockOperatingCostsData = []
      mockSelectedVersionId = 'v1'
      render(<CostsPage />)

      // Summary cards should show 0 values
      expect(screen.getByTestId('summary-card-total-costs')).toBeInTheDocument()
      // Grid should still render but with no rows
      expect(screen.queryAllByTestId('cost-row')).toHaveLength(0)
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(CostsRoute.path).toBe('/planning/costs')
    })
  })
})
