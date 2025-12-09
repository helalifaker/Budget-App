import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as ClassSizesRoute } from '@/routes/configuration/class-sizes'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockClassSizeParamsData:
  | {
      id: string
      budget_version_id: string
      level_id: string | null
      cycle_id: string | null
      min_class_size: number
      target_class_size: number
      max_class_size: number
      notes: string | null
    }[]
  | null = null
let mockLevelsData:
  | {
      id: string
      code: string
      name_fr: string
      name_en: string
      cycle_id: string
      sort_order: number
    }[]
  | null = null
let mockCyclesData:
  | {
      id: string
      code: string
      name_fr: string
      name_en: string
      sort_order: number
      requires_atsem: boolean
    }[]
  | null = null
const mockCreateMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface LocalLevelConfig {
  level_id: string
  level_code: string
  level_name: string
  cycle_code: string
  min_class_size: number
  target_class_size: number
  max_class_size: number
  notes: string | null
  isValid: boolean
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

// Mock BudgetVersionContext
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

vi.mock('@/lib/auth-guard', () => ({
  requireAuth: vi.fn(),
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

vi.mock('@/components/DataTableLazy', () => ({
  DataTableLazy: ({ rowData, loading, error }: MockProps) => {
    if (loading) {
      return <div data-testid="data-table-loading">Loading...</div>
    }
    if (error) {
      return <div data-testid="data-table-error">Error loading data</div>
    }
    return (
      <div data-testid="data-table">
        {(rowData as LocalLevelConfig[] | undefined)?.map((row) => (
          <div key={row.level_id} data-testid="class-size-row">
            {row.level_code}: Min={row.min_class_size}, Target={row.target_class_size}, Max=
            {row.max_class_size}
            {!row.isValid && <span data-testid="validation-error">Invalid</span>}
          </div>
        ))}
      </div>
    )
  },
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({ title, value, subtitle }: MockProps) => (
    <div data-testid={`summary-card-${(title as string).toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title as string}</div>
      <div data-testid="card-value">{String(value)}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle as string}</div>}
    </div>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled }: MockProps) => (
    <button
      onClick={onClick as () => void}
      disabled={disabled as boolean}
      data-testid="save-button"
    >
      {children as React.ReactNode}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: MockProps) => (
    <span data-testid="badge">{children as React.ReactNode}</span>
  ),
}))

vi.mock('@/hooks/api/useConfiguration', () => ({
  useClassSizeParams: (versionId: string) => ({
    data: versionId ? mockClassSizeParamsData : null,
    isLoading: false,
    error: null,
  }),
  useLevels: () => ({
    data: mockLevelsData,
    isLoading: false,
  }),
  useCycles: () => ({
    data: mockCyclesData,
  }),
  useCreateClassSizeParam: () => ({
    mutateAsync: mockCreateMutation,
    isPending: false,
  }),
}))

vi.mock('@/lib/toast-messages', () => ({
  toastMessages: {
    warning: { selectVersion: vi.fn() },
    error: { custom: vi.fn(), generic: vi.fn() },
    success: { updated: vi.fn() },
  },
}))

vi.mock('sonner', () => ({
  toast: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('lucide-react', () => ({
  Save: () => <span>Save Icon</span>,
  Settings: () => <span>Settings Icon</span>,
  BarChart3: () => <span>BarChart3 Icon</span>,
  CheckCircle: () => <span>CheckCircle Icon</span>,
  AlertCircle: () => <span>AlertCircle Icon</span>,
}))

describe('Class Sizes Configuration Route', () => {
  const ClassSizesPage = ClassSizesRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectedVersionId = undefined

    // Setup mock cycles data
    mockCyclesData = [
      {
        id: 'mat',
        code: 'MAT',
        name_fr: 'Maternelle',
        name_en: 'Preschool',
        sort_order: 1,
        requires_atsem: true,
      },
      {
        id: 'elem',
        code: 'ELEM',
        name_fr: 'Élémentaire',
        name_en: 'Elementary',
        sort_order: 2,
        requires_atsem: false,
      },
      {
        id: 'coll',
        code: 'COLL',
        name_fr: 'Collège',
        name_en: 'Middle School',
        sort_order: 3,
        requires_atsem: false,
      },
    ]

    // Setup mock levels data
    mockLevelsData = [
      {
        id: 'ps',
        code: 'PS',
        name_fr: 'Petite Section',
        name_en: 'Petite Section',
        cycle_id: 'mat',
        sort_order: 1,
      },
      {
        id: 'ms',
        code: 'MS',
        name_fr: 'Moyenne Section',
        name_en: 'Moyenne Section',
        cycle_id: 'mat',
        sort_order: 2,
      },
      {
        id: 'gs',
        code: 'GS',
        name_fr: 'Grande Section',
        name_en: 'Grande Section',
        cycle_id: 'mat',
        sort_order: 3,
      },
      {
        id: 'cp',
        code: 'CP',
        name_fr: 'Cours Préparatoire',
        name_en: 'CP',
        cycle_id: 'elem',
        sort_order: 4,
      },
      {
        id: 'ce1',
        code: 'CE1',
        name_fr: 'Cours Élémentaire 1',
        name_en: 'CE1',
        cycle_id: 'elem',
        sort_order: 5,
      },
    ]

    // Setup mock class size params data (some levels have explicit config)
    mockClassSizeParamsData = [
      {
        id: '1',
        budget_version_id: 'v1',
        level_id: 'ps',
        cycle_id: null,
        min_class_size: 12,
        target_class_size: 20,
        max_class_size: 25,
        notes: 'Small class',
      },
      {
        id: '2',
        budget_version_id: 'v1',
        level_id: 'cp',
        cycle_id: null,
        min_class_size: 18,
        target_class_size: 26,
        max_class_size: 30,
        notes: null,
      },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<ClassSizesPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<ClassSizesPage />)

      expect(screen.getByText('Class Size Parameters')).toBeInTheDocument()
      expect(
        screen.getByText(
          'Configure minimum, target, and maximum class sizes for each academic level'
        )
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<ClassSizesPage />)

      expect(screen.getByText(/Please select a budget version/i)).toBeInTheDocument()
    })
  })

  describe('Summary statistics cards', () => {
    it('does not show statistics when no version selected', () => {
      render(<ClassSizesPage />)

      expect(screen.queryByTestId('summary-card-levels-configured')).not.toBeInTheDocument()
    })

    it('displays Levels Configured card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('summary-card-levels-configured')).toBeInTheDocument()
      expect(screen.getByText('Levels Configured')).toBeInTheDocument()
    })

    it('displays Average Target Size card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('summary-card-average-target-size')).toBeInTheDocument()
      expect(screen.getByText('Average Target Size')).toBeInTheDocument()
    })

    it('displays Size Range card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('summary-card-size-range')).toBeInTheDocument()
      expect(screen.getByText('Size Range')).toBeInTheDocument()
    })

    it('displays Configuration Status card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('summary-card-configuration-status')).toBeInTheDocument()
      expect(screen.getByText('Configuration Status')).toBeInTheDocument()
    })
  })

  describe('Save functionality', () => {
    it('renders Save Changes button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByText('Save Changes')).toBeInTheDocument()
    })

    it('Save Changes button is disabled when no unsaved changes', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      const saveBtn = screen.getByTestId('save-button')
      expect(saveBtn).toBeDisabled()
    })
  })

  describe('Data table', () => {
    it('shows placeholder when no version selected', () => {
      render(<ClassSizesPage />)

      expect(screen.getByText(/Please select a budget version/i)).toBeInTheDocument()
    })

    it('displays data table when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByTestId('data-table')).toBeInTheDocument()
    })

    it('displays all levels as rows (pre-populated)', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      // Should show 5 rows (one for each level)
      const rows = screen.getAllByTestId('class-size-row')
      expect(rows).toHaveLength(5)
    })

    it('displays level codes in rows', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByText(/PS:/)).toBeInTheDocument()
      expect(screen.getByText(/MS:/)).toBeInTheDocument()
      expect(screen.getByText(/GS:/)).toBeInTheDocument()
      expect(screen.getByText(/CP:/)).toBeInTheDocument()
      expect(screen.getByText(/CE1:/)).toBeInTheDocument()
    })
  })

  describe('Default values', () => {
    it('uses existing config values when available', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      // PS has explicit config: min=12, target=20, max=25
      expect(screen.getByText(/PS:.*Min=12.*Target=20.*Max=25/)).toBeInTheDocument()
    })

    it('uses default values for levels without config', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      // MS has no explicit config, should use defaults: min=15, target=25, max=30
      expect(screen.getByText(/MS:.*Min=15.*Target=25.*Max=30/)).toBeInTheDocument()
    })
  })

  describe('Instructions', () => {
    it('displays inline editing instructions when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      expect(screen.getByText(/Edit cells directly/i)).toBeInTheDocument()
      expect(screen.getByText(/Validation: Min/i)).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full class sizes interface', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      // Verify summary cards appear
      expect(screen.getByTestId('summary-card-levels-configured')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-average-target-size')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-size-range')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-configuration-status')).toBeInTheDocument()

      // Verify save button
      expect(screen.getByText('Save Changes')).toBeInTheDocument()

      // Verify data table
      expect(screen.getByTestId('data-table')).toBeInTheDocument()
    })

    it('handles empty class size params (all use defaults)', () => {
      mockClassSizeParamsData = []
      mockSelectedVersionId = 'v1'
      render(<ClassSizesPage />)

      // Cards should still render
      expect(screen.getByTestId('summary-card-levels-configured')).toBeInTheDocument()

      // All rows should have default values
      const rows = screen.getAllByTestId('class-size-row')
      expect(rows).toHaveLength(5)
    })
  })

  describe('Route configuration', () => {
    it('requires authentication', () => {
      expect(ClassSizesRoute.beforeLoad).toBeDefined()
    })

    it('has correct path', () => {
      expect(ClassSizesRoute.path).toBe('/configuration/class-sizes')
    })
  })
})
