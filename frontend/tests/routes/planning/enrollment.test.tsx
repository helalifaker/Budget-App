import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as EnrollmentRoute } from '@/routes/planning/enrollment'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockEnrollmentData: {
  totals: { level_id: string; total_students: number }[]
  distributions: { level_id: string; french_pct: number; saudi_pct: number; other_pct: number }[]
  breakdown: {
    level_id: string
    level_code: string
    level_name: string
    cycle_code: string
    french_count: number
    saudi_count: number
    other_count: number
    total_students: number
  }[]
  summary: {
    total_students: number
    by_nationality: Record<string, number>
    by_cycle: Record<string, number>
  } | null
} | null = null
let mockLevelsData:
  | { id: string; code: string; name_fr: string; name_en: string; cycle_id: string }[]
  | null = null
const mockSaveTotalsMutation = vi.fn()
const mockSaveDistributionsMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface LocalTotal {
  level_id: string
  level_code: string
  level_name: string
  cycle_code: string
  total_students: number
  capacity: number
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
        {(rowData as LocalTotal[] | undefined)?.map((row) => (
          <div key={row.level_id} data-testid="enrollment-row">
            {row.level_code}: {row.total_students} students
          </div>
        ))}
      </div>
    )
  },
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: MockProps) => (
    <div data-testid={(props['data-testid'] as string) || 'card'}>
      {children as React.ReactNode}
    </div>
  ),
  CardHeader: ({ children }: MockProps) => (
    <div data-testid="card-header">{children as React.ReactNode}</div>
  ),
  CardTitle: ({ children }: MockProps) => (
    <div data-testid="card-title">{children as React.ReactNode}</div>
  ),
  CardContent: ({ children }: MockProps) => (
    <div data-testid="card-content">{children as React.ReactNode}</div>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled }: MockProps) => (
    <button onClick={onClick as () => void} disabled={disabled as boolean}>
      {children as React.ReactNode}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: MockProps) => (
    <span data-testid="badge">{children as React.ReactNode}</span>
  ),
}))

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: MockProps) => (
    <div data-testid="tabs" data-value={value as string}>
      {typeof children === 'function'
        ? (children as (fn: (val: string) => void) => React.ReactNode)(
            onValueChange as (val: string) => void
          )
        : (children as React.ReactNode)}
    </div>
  ),
  TabsList: ({ children }: MockProps) => (
    <div data-testid="tabs-list" role="tablist">
      {children as React.ReactNode}
    </div>
  ),
  TabsTrigger: ({ children, value }: MockProps) => (
    <button data-testid={`tab-${value}`} role="tab">
      {children as React.ReactNode}
    </button>
  ),
  TabsContent: ({ children, value }: MockProps) => (
    <div data-testid={`tab-content-${value}`} role="tabpanel">
      {children as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/hooks/api/useEnrollment', () => ({
  useEnrollmentWithDistribution: (versionId: string) => ({
    data: versionId ? mockEnrollmentData : null,
    isLoading: false,
    error: null,
  }),
  useBulkUpsertEnrollmentTotals: () => ({
    mutateAsync: mockSaveTotalsMutation,
    isPending: false,
  }),
  useBulkUpsertDistributions: () => ({
    mutateAsync: mockSaveDistributionsMutation,
    isPending: false,
  }),
}))

vi.mock('@/hooks/api/useConfiguration', () => ({
  useLevels: () => ({
    data: mockLevelsData,
  }),
}))

vi.mock('@/lib/toast-messages', () => ({
  toastMessages: {
    warning: { selectVersion: vi.fn() },
    error: { validation: vi.fn() },
    success: { saved: vi.fn() },
  },
}))

vi.mock('lucide-react', () => ({
  Save: () => <span>Save Icon</span>,
  Users: () => <span>Users Icon</span>,
  TrendingUp: () => <span>TrendingUp Icon</span>,
  Globe: () => <span>Globe Icon</span>,
  AlertCircle: () => <span>AlertCircle Icon</span>,
  CheckCircle: () => <span>CheckCircle Icon</span>,
}))

describe('Enrollment Planning Route', () => {
  const EnrollmentPage = EnrollmentRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectedVersionId = undefined // Reset version selection

    // Setup mock levels data
    mockLevelsData = [
      {
        id: 'cp',
        code: 'CP',
        name_fr: 'Cours Préparatoire',
        name_en: 'Preparatory Course',
        cycle_id: 'ELEM',
      },
      {
        id: 'ce1',
        code: 'CE1',
        name_fr: 'Cours Élémentaire 1',
        name_en: 'Elementary Course 1',
        cycle_id: 'ELEM',
      },
      {
        id: 'ce2',
        code: 'CE2',
        name_fr: 'Cours Élémentaire 2',
        name_en: 'Elementary Course 2',
        cycle_id: 'ELEM',
      },
    ]

    // Setup mock enrollment data
    mockEnrollmentData = {
      totals: [
        { level_id: 'cp', total_students: 45 },
        { level_id: 'ce1', total_students: 38 },
        { level_id: 'ce2', total_students: 22 },
      ],
      distributions: [
        { level_id: 'cp', french_pct: 60, saudi_pct: 30, other_pct: 10 },
        { level_id: 'ce1', french_pct: 55, saudi_pct: 35, other_pct: 10 },
        { level_id: 'ce2', french_pct: 50, saudi_pct: 40, other_pct: 10 },
      ],
      breakdown: [
        {
          level_id: 'cp',
          level_code: 'CP',
          level_name: 'Cours Préparatoire',
          cycle_code: 'ELEM',
          french_count: 27,
          saudi_count: 14,
          other_count: 4,
          total_students: 45,
        },
        {
          level_id: 'ce1',
          level_code: 'CE1',
          level_name: 'Cours Élémentaire 1',
          cycle_code: 'ELEM',
          french_count: 21,
          saudi_count: 13,
          other_count: 4,
          total_students: 38,
        },
        {
          level_id: 'ce2',
          level_code: 'CE2',
          level_name: 'Cours Élémentaire 2',
          cycle_code: 'ELEM',
          french_count: 11,
          saudi_count: 9,
          other_count: 2,
          total_students: 22,
        },
      ],
      summary: {
        total_students: 105,
        by_nationality: { French: 59, Saudi: 36, Other: 10 },
        by_cycle: { ELEM: 105 },
      },
    }
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<EnrollmentPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<EnrollmentPage />)

      expect(screen.getByText('Enrollment Planning')).toBeInTheDocument()
      expect(
        screen.getByText('Plan student enrollment by level with nationality distribution')
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<EnrollmentPage />)

      expect(screen.getByText(/Select a budget version/i)).toBeInTheDocument()
    })
  })

  describe('Tab navigation', () => {
    it('renders tab navigation when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByTestId('tabs-list')).toBeInTheDocument()
    })

    it('renders Enrollment by Level tab', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('tab-totals')).toBeInTheDocument()
      expect(screen.getByText('Enrollment by Level')).toBeInTheDocument()
    })

    it('renders Nationality Distribution tab', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('tab-distribution')).toBeInTheDocument()
      expect(screen.getByText('Nationality Distribution')).toBeInTheDocument()
    })

    it('renders Calculated Breakdown tab', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('tab-breakdown')).toBeInTheDocument()
      expect(screen.getByText('Calculated Breakdown')).toBeInTheDocument()
    })
  })

  describe('Summary statistics cards', () => {
    it('does not show statistics when no version selected', () => {
      render(<EnrollmentPage />)

      expect(screen.queryByTestId('total-students-card')).not.toBeInTheDocument()
    })

    it('displays Total Students card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('total-students-card')).toBeInTheDocument()
      expect(screen.getByText('Total Students')).toBeInTheDocument()
    })

    it('displays School Capacity card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByText('School Capacity')).toBeInTheDocument()
    })

    it('displays By Nationality card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByText('By Nationality')).toBeInTheDocument()
    })

    it('displays By Cycle card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      // Use getAllByText since "By Cycle" might appear in multiple places
      const byCycleElements = screen.getAllByText('By Cycle')
      expect(byCycleElements.length).toBeGreaterThan(0)
    })
  })

  describe('Save functionality', () => {
    it('renders Save Totals button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByText('Save Totals')).toBeInTheDocument()
    })

    it('Save Totals button is disabled when no unsaved changes', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      const saveBtn = screen.getByText('Save Totals').closest('button')
      expect(saveBtn).toBeDisabled()
    })
  })

  describe('Data table', () => {
    it('shows placeholder when no version selected', () => {
      render(<EnrollmentPage />)

      expect(
        screen.getByText('Please select a budget version to view enrollment data')
      ).toBeInTheDocument()
    })

    it('displays data table when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      // Check for the totals tab content
      expect(screen.getByTestId('tab-content-totals')).toBeInTheDocument()
    })

    it('displays tab content areas', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      expect(screen.getByTestId('tab-content-totals')).toBeInTheDocument()
      expect(screen.getByTestId('tab-content-distribution')).toBeInTheDocument()
      expect(screen.getByTestId('tab-content-breakdown')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full enrollment planning interface', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      // Verify summary cards appear
      expect(screen.getByTestId('total-students-card')).toBeInTheDocument()
      expect(screen.getByText('School Capacity')).toBeInTheDocument()

      // Verify tabs appear
      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByText('Enrollment by Level')).toBeInTheDocument()
      expect(screen.getByText('Nationality Distribution')).toBeInTheDocument()
      expect(screen.getByText('Calculated Breakdown')).toBeInTheDocument()

      // Verify save button
      expect(screen.getByText('Save Totals')).toBeInTheDocument()
    })

    it('handles no data state (shows cards with zero values)', () => {
      mockEnrollmentData = {
        totals: [],
        distributions: [],
        breakdown: [],
        summary: null,
      }
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      // Cards should still render
      expect(screen.getByTestId('total-students-card')).toBeInTheDocument()
      expect(screen.getByTestId('tabs')).toBeInTheDocument()
    })

    it('maintains interface when version is selected', () => {
      mockSelectedVersionId = 'v1'
      render(<EnrollmentPage />)

      // Interface persists with selected version
      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByTestId('tab-content-totals')).toBeInTheDocument()
    })
  })

  describe('Route configuration', () => {
    it('requires authentication', () => {
      expect(EnrollmentRoute.beforeLoad).toBeDefined()
    })

    it('has correct path', () => {
      expect(EnrollmentRoute.path).toBe('/planning/enrollment')
    })
  })
})
