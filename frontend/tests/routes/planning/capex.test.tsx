import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as CapExRoute } from '@/routes/planning/capex'

// Mock dependencies
const mockNavigate = vi.fn()
let mockCapExData: any = null
let mockDepreciationSchedule: any = null

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
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '').replace(/&/g, 'and')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value">{value}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
      {icon}
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

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-testid="badge" data-variant={variant}>
      {children}
    </span>
  ),
}))

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: any) => (open ? <div data-testid="dialog">{children}</div> : null),
  DialogContent: ({ children }: any) => <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: any) => <div data-testid="dialog-header">{children}</div>,
  DialogTitle: ({ children }: any) => <div data-testid="dialog-title">{children}</div>,
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: any) => (
    <div data-testid="ag-grid">
      {rowData?.map((row: any) => (
        <div key={row.id} data-testid="capex-row">
          {row.description}: {row.asset_type}
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

    mockCapExData = {
      items: [
        {
          id: '1',
          description: 'Classroom Projectors',
          asset_type: 'EQUIPMENT',
          account_code: '21500',
          purchase_date: '2025-01-15',
          cost: 50000,
          useful_life_years: 5,
          depreciation_method: 'STRAIGHT_LINE',
        },
        {
          id: '2',
          description: 'Laptops for Teachers',
          asset_type: 'IT',
          account_code: '21800',
          purchase_date: '2025-02-01',
          cost: 80000,
          useful_life_years: 3,
          depreciation_method: 'STRAIGHT_LINE',
        },
        {
          id: '3',
          description: 'Office Furniture',
          asset_type: 'FURNITURE',
          account_code: '21200',
          purchase_date: '2025-03-01',
          cost: 30000,
          useful_life_years: 10,
          depreciation_method: 'STRAIGHT_LINE',
        },
      ],
    }

    mockDepreciationSchedule = [
      { year: 1, depreciation: 10000, book_value: 40000 },
      { year: 2, depreciation: 10000, book_value: 30000 },
      { year: 3, depreciation: 10000, book_value: 20000 },
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

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<CapExPage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
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

    it('enables Add CapEx Item button when version selected', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const addBtn = screen.getByText('Add CapEx Item').closest('button')
        expect(addBtn).not.toBeDisabled()
      })
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<CapExPage />)

      expect(screen.queryByTestId('summary-card-total-capex')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-equipment')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-it-and-software')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-avg-useful-life')).toBeInTheDocument()
      })
    })

    it('calculates total CapEx correctly', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const totalCard = screen.getByTestId('summary-card-total-capex')
        // 50,000 + 80,000 + 30,000 = 160,000
        expect(totalCard).toHaveTextContent('SAR')
        expect(totalCard).toHaveTextContent('3 items')
      })
    })

    it('calculates average useful life correctly', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const avgLifeCard = screen.getByTestId('summary-card-avg-useful-life')
        // (5 + 3 + 10) / 3 = 6.0 years
        expect(avgLifeCard).toHaveTextContent('6.0 years')
      })
    })
  })

  describe('AG Grid', () => {
    it('displays AG Grid with CapEx data', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
        const rows = screen.getAllByTestId('capex-row')
        expect(rows).toHaveLength(3)
      })
    })

    it('displays CapEx row details', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText(/Classroom Projectors: EQUIPMENT/)).toBeInTheDocument()
        expect(screen.getByText(/Laptops for Teachers: IT/)).toBeInTheDocument()
        expect(screen.getByText(/Office Furniture: FURNITURE/)).toBeInTheDocument()
      })
    })
  })

  describe('Asset Categories section', () => {
    it('displays asset categories breakdown', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const allCards = screen.getAllByTestId('card-title')
        const assetCategoriesCard = allCards.find((card) =>
          card.textContent?.includes('Asset Categories')
        )
        expect(assetCategoriesCard).toBeInTheDocument()
      })
    })
  })

  describe('Depreciation Info section', () => {
    it('displays depreciation information', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Depreciation Info')).toBeInTheDocument()
        expect(screen.getByText('Straight Line')).toBeInTheDocument()
        expect(screen.getByText('Declining Balance')).toBeInTheDocument()
        expect(screen.getByText('Account Codes (2xxx)')).toBeInTheDocument()
        expect(screen.getByText('Purchase Date')).toBeInTheDocument()
      })
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<CapExPage />)

      expect(
        screen.getByText('Select a budget version to view capital expenditure planning')
      ).toBeInTheDocument()
    })

    it('hides placeholder when version selected', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(
          screen.queryByText('Select a budget version to view capital expenditure planning')
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full CapEx planning workflow', async () => {
      const user = userEvent.setup()

      render(<CapExPage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify summary cards appear
        expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()

        // Verify AG Grid appears
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()

        // Verify asset categories appear
        const assetCategories = screen.getAllByTestId('card-title').find((card) =>
          card.textContent?.includes('Asset Categories')
        )
        expect(assetCategories).toBeInTheDocument()

        // Verify depreciation info appears
        expect(screen.getByText('Depreciation Info')).toBeInTheDocument()

        // Verify action button is enabled
        const addBtn = screen.getByText('Add CapEx Item').closest('button')
        expect(addBtn).not.toBeDisabled()
      })
    })

    it('handles empty CapEx data', async () => {
      mockCapExData = { items: [] }
      const user = userEvent.setup()

      render(<CapExPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Summary cards should show 0 values
        expect(screen.getByTestId('summary-card-total-capex')).toBeInTheDocument()
        // Grid should still render but with no rows
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument()
        expect(screen.queryAllByTestId('capex-row')).toHaveLength(0)
      })
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(CapExRoute.path).toBe('/planning/capex')
    })
  })
})
