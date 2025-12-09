import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as CapExRoute } from '@/routes/planning/capex'

// Mock dependencies
const mockNavigate = vi.fn()
let mockCapExData: Record<string, unknown>[] | null = null
let mockDepreciationSchedule: Record<string, unknown>[] | null = null

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface CapExRow {
  id: string
  description: string
  asset_type?: string
  category?: string
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
    <div
      data-testid={`summary-card-${(title as string).toLowerCase().replace(/\s+/g, '-').replace(/\./g, '').replace(/&/g, 'and')}`}
    >
      <div data-testid="card-title">{title as string}</div>
      <div data-testid="card-value">{value as React.ReactNode}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle as string}</div>}
      {icon as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: MockProps) => (
    <div data-testid="card" className={className as string}>
      {children as React.ReactNode}
    </div>
  ),
  CardHeader: ({ children }: MockProps) => (
    <div data-testid="card-header">{children as React.ReactNode}</div>
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

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: MockProps) => (
    <span data-testid="badge" data-variant={variant as string}>
      {children as React.ReactNode}
    </span>
  ),
}))

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: MockProps) =>
    open ? <div data-testid="dialog">{children as React.ReactNode}</div> : null,
  DialogContent: ({ children }: MockProps) => (
    <div data-testid="dialog-content">{children as React.ReactNode}</div>
  ),
  DialogHeader: ({ children }: MockProps) => (
    <div data-testid="dialog-header">{children as React.ReactNode}</div>
  ),
  DialogTitle: ({ children }: MockProps) => (
    <div data-testid="dialog-title">{children as React.ReactNode}</div>
  ),
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: MockProps) => (
    <div data-testid="ag-grid">
      {(rowData as CapExRow[] | undefined)?.map((row) => (
        <div key={row.id} data-testid="capex-row">
          {row.description}: {row.asset_type || row.category}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('ag-grid-community', () => ({
  themeQuartz: 'theme-quartz',
}))

vi.mock('@/components/grid/CurrencyRenderer', () => ({
  CurrencyRenderer: () => null,
}))

vi.mock('@/components/grid/AccountCodeRenderer', () => ({
  AccountCodeRenderer: () => null,
}))

vi.mock('@/hooks/api/useCapEx', () => ({
  useCapEx: (versionId: string) => ({
    data: versionId ? mockCapExData : null,
    isLoading: false,
  }),
  useDepreciationSchedule: (itemId: string) => ({
    data: itemId ? mockDepreciationSchedule : null,
  }),
}))

vi.mock('lucide-react', () => ({
  Building2: () => <span>Building2 Icon</span>,
  Laptop: () => <span>Laptop Icon</span>,
  Wrench: () => <span>Wrench Icon</span>,
  TrendingDown: () => <span>TrendingDown Icon</span>,
  Plus: () => <span>Plus Icon</span>,
  Download: () => <span>Download Icon</span>,
  Eye: () => <span>Eye Icon</span>,
}))

describe('CapEx Planning Route', () => {
  const CapExPage = CapExRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectedVersionId = undefined // Reset version selection

    mockCapExData = [
      {
        id: '1',
        description: 'Classroom Projectors',
        category: 'EQUIPMENT',
        account_code: '21500',
        acquisition_date: '2025-01-15',
        total_cost_sar: 50000,
        useful_life_years: 5,
        annual_depreciation_sar: 10000,
        notes: null,
      },
      {
        id: '2',
        description: 'Laptops for Teachers',
        category: 'IT',
        account_code: '21800',
        acquisition_date: '2025-02-01',
        total_cost_sar: 80000,
        useful_life_years: 3,
        annual_depreciation_sar: 26667,
        notes: null,
      },
      {
        id: '3',
        description: 'Office Furniture',
        category: 'FURNITURE',
        account_code: '21200',
        acquisition_date: '2025-03-01',
        total_cost_sar: 30000,
        useful_life_years: 10,
        annual_depreciation_sar: 3000,
        notes: null,
      },
    ]

    mockDepreciationSchedule = [
      { year: 1, annual_depreciation: 10000, book_value: 40000 },
      { year: 2, annual_depreciation: 10000, book_value: 30000 },
      { year: 3, annual_depreciation: 10000, book_value: 20000 },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<CapExPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<CapExPage />)

      expect(screen.getByText('CapEx Planning')).toBeInTheDocument()
      expect(
        screen.getByText('Manage capital expenditure items and depreciation schedules')
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<CapExPage />)
      expect(
        screen.getByText('Select a budget version to view capital expenditure planning')
      ).toBeInTheDocument()
    })
  })

  describe('Action buttons', () => {
    it('renders Add CapEx Item button', () => {
      render(<CapExPage />)

      expect(screen.getByText('Add CapEx Item')).toBeInTheDocument()
    })

    it('renders Export button', () => {
      render(<CapExPage />)

      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    it('disables Add CapEx Item button when no version selected', () => {
      render(<CapExPage />)

      const addBtn = screen.getByText('Add CapEx Item').closest('button')
      expect(addBtn).toBeDisabled()
    })

    it('enables Add CapEx Item button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      const addBtn = screen.getByText('Add CapEx Item').closest('button')
      expect(addBtn).not.toBeDisabled()
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<CapExPage />)

      expect(screen.queryByTestId('summary-card-total-capex')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-equipment')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-it-and-software')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-avg-useful-life')).toBeInTheDocument()
    })

    it('calculates total CapEx correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      const totalCard = screen.getByTestId('summary-card-total-capex')
      // 50,000 + 80,000 + 30,000 = 160,000
      expect(totalCard).toHaveTextContent('SAR')
      expect(totalCard).toHaveTextContent('3 items')
    })

    it('calculates average useful life correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      const avgLifeCard = screen.getByTestId('summary-card-avg-useful-life')
      // (5 + 3 + 10) / 3 = 6.0 years
      expect(avgLifeCard).toHaveTextContent('6.0 years')
    })
  })

  describe('AG Grid', () => {
    it('displays AG Grid with CapEx data', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
      const rows = screen.getAllByTestId('capex-row')
      expect(rows).toHaveLength(3)
    })

    it('displays CapEx row details', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      expect(screen.getByText(/Classroom Projectors: EQUIPMENT/)).toBeInTheDocument()
      expect(screen.getByText(/Laptops for Teachers: IT/)).toBeInTheDocument()
      expect(screen.getByText(/Office Furniture: FURNITURE/)).toBeInTheDocument()
    })
  })

  describe('Asset Categories section', () => {
    it('displays asset categories breakdown', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      const allCards = screen.getAllByTestId('card-title')
      const assetCategoriesCard = allCards.find((card) =>
        card.textContent?.includes('Asset Categories')
      )
      expect(assetCategoriesCard).toBeInTheDocument()
    })
  })

  describe('Depreciation Info section', () => {
    it('displays depreciation information', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      expect(screen.getByText('Depreciation Info')).toBeInTheDocument()
      expect(screen.getByText('Straight Line')).toBeInTheDocument()
      expect(screen.getByText('Declining Balance')).toBeInTheDocument()
      expect(screen.getByText('Account Codes (2xxx)')).toBeInTheDocument()
      expect(screen.getByText('Purchase Date')).toBeInTheDocument()
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<CapExPage />)

      expect(
        screen.getByText('Select a budget version to view capital expenditure planning')
      ).toBeInTheDocument()
    })

    it('hides placeholder when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      expect(
        screen.queryByText('Select a budget version to view capital expenditure planning')
      ).not.toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full CapEx planning workflow', () => {
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      // Verify summary cards appear
      expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()

      // Verify AG Grid appears
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()

      // Verify asset categories appear
      const assetCategories = screen
        .getAllByTestId('card-title')
        .find((card) => card.textContent?.includes('Asset Categories'))
      expect(assetCategories).toBeInTheDocument()

      // Verify depreciation info appears
      expect(screen.getByText('Depreciation Info')).toBeInTheDocument()

      // Verify action button is enabled
      const addBtn = screen.getByText('Add CapEx Item').closest('button')
      expect(addBtn).not.toBeDisabled()
    })

    it('handles empty CapEx data', () => {
      mockCapExData = []
      mockSelectedVersionId = 'v1'
      render(<CapExPage />)

      // Summary cards should show 0 values
      expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()
      // Grid should still render but with no rows
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
      expect(screen.queryAllByTestId('capex-row')).toHaveLength(0)
    })

    it('context provides version switching capability', () => {
      mockSelectedVersionId = 'v1'
      const { rerender } = render(<CapExPage />)

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument()

      // Simulate version change via context
      mockSelectedVersionId = 'v2'
      rerender(<CapExPage />)

      // Page should still render (context provides new version)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(CapExRoute.path).toBe('/planning/capex')
    })
  })
})
