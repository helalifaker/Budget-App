import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as EnrollmentRoute } from '@/routes/planning/enrollment'

// Mock dependencies
const mockNavigate = vi.fn()
let mockEnrollmentsData: any = null
let mockLevelsData: any = null
let mockNationalityTypesData: any = null
const mockCreateMutation = vi.fn()
const mockUpdateMutation = vi.fn()
const mockDeleteMutation = vi.fn()
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

vi.mock('@/lib/auth-guard', () => ({
  requireAuth: vi.fn(),
}))

vi.mock('@/components/layout/MainLayout', () => ({
  MainLayout: ({ children }: any) => <div data-testid="main-layout">{children}</div>,
}))

vi.mock('@/components/layout/PageContainer', () => ({
  PageContainer: ({ title, description, actions, children }: any) => (
    <div data-testid="page-container">
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {actions && <div data-testid="page-actions">{actions}</div>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({ value, onChange }: any) => (
    <div data-testid="budget-version-selector">
      <select
        data-testid="version-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select version</option>
        <option value="v1">2025-2026</option>
        <option value="v2">2024-2025</option>
      </select>
    </div>
  ),
}))

vi.mock('@/components/DataTableLazy', () => ({
  DataTableLazy: ({ rowData, loading, error }: any) => {
    if (loading) {
      return <div data-testid="data-table-loading">Loading...</div>
    }
    if (error) {
      return <div data-testid="data-table-error">Error loading data</div>
    }
    return (
      <div data-testid="data-table">
        {rowData?.map((row: any) => (
          <div key={row.id} data-testid="enrollment-row">
            {row.level_id} - {row.nationality_type_id}: {row.student_count}
          </div>
        ))}
      </div>
    )
  },
}))

vi.mock('@/components/FormDialog', () => ({
  FormDialog: ({ open, title, children, onSubmit }: any) =>
    open ? (
      <div data-testid="form-dialog">
        <h2>{title}</h2>
        <form onSubmit={onSubmit} data-testid="enrollment-form">
          {children}
        </form>
      </div>
    ) : null,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div data-testid="card-title">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
}))

vi.mock('@/hooks/api/useEnrollment', () => ({
  useEnrollments: (versionId: string) => ({
    data: versionId ? mockEnrollmentsData : null,
    isLoading: false,
    error: null,
  }),
  useCreateEnrollment: () => ({
    mutateAsync: mockCreateMutation,
    isPending: false,
  }),
  useUpdateEnrollment: () => ({
    mutateAsync: mockUpdateMutation,
    isPending: false,
  }),
  useDeleteEnrollment: () => ({
    mutateAsync: mockDeleteMutation,
    isPending: false,
  }),
  useCalculateProjections: () => ({
    mutateAsync: mockCalculateMutation,
    isPending: false,
  }),
}))

vi.mock('@/hooks/api/useConfiguration', () => ({
  useLevels: () => ({
    data: mockLevelsData,
  }),
  useNationalityTypes: () => ({
    data: mockNationalityTypesData,
  }),
}))

vi.mock('lucide-react', () => ({
  Plus: () => <span>Plus Icon</span>,
  Trash2: () => <span>Trash Icon</span>,
  Calculator: () => <span>Calculator Icon</span>,
  Users: () => <span>Users Icon</span>,
  TrendingUp: () => <span>TrendingUp Icon</span>,
  Globe: () => <span>Globe Icon</span>,
  ChevronDown: () => <span>ChevronDown Icon</span>,
  ChevronUp: () => <span>ChevronUp Icon</span>,
  Check: () => <span>Check Icon</span>,
}))

describe('Enrollment Planning Route', () => {
  const EnrollmentPage = EnrollmentRoute.component

  beforeEach(() => {
    vi.clearAllMocks()

    mockEnrollmentsData = {
      items: [
        {
          id: '1',
          level_id: 'cp',
          nationality_type_id: 'french',
          student_count: 45,
          budget_version_id: 'v1',
        },
        {
          id: '2',
          level_id: 'ce1',
          nationality_type_id: 'saudi',
          student_count: 38,
          budget_version_id: 'v1',
        },
        {
          id: '3',
          level_id: 'ce2',
          nationality_type_id: 'other',
          student_count: 22,
          budget_version_id: 'v1',
        },
      ],
    }

    mockLevelsData = [
      { id: 'cp', name: 'CP', cycle: 'Elementary' },
      { id: 'ce1', name: 'CE1', cycle: 'Elementary' },
      { id: 'ce2', name: 'CE2', cycle: 'Elementary' },
    ]

    mockNationalityTypesData = [
      { id: 'french', name: 'French' },
      { id: 'saudi', name: 'Saudi' },
      { id: 'other', name: 'Other' },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<EnrollmentPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<EnrollmentPage />)

      expect(screen.getByText('Enrollment Planning')).toBeInTheDocument()
      expect(screen.getByText('Plan student enrollment by level and nationality')).toBeInTheDocument()
    })

    it('renders page actions', () => {
      render(<EnrollmentPage />)

      expect(screen.getByTestId('page-actions')).toBeInTheDocument()
    })
  })

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<EnrollmentPage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
    })
  })

  describe('Action buttons', () => {
    it('renders Calculate Projections button', () => {
      render(<EnrollmentPage />)

      expect(screen.getByText('Calculate Projections')).toBeInTheDocument()
    })

    it('renders Add Enrollment button', () => {
      render(<EnrollmentPage />)

      expect(screen.getByText('Add Enrollment')).toBeInTheDocument()
    })

    it('disables buttons when no version selected', () => {
      render(<EnrollmentPage />)

      const calculateBtn = screen.getByText('Calculate Projections').closest('button')
      const addBtn = screen.getByText('Add Enrollment').closest('button')

      expect(calculateBtn).toBeDisabled()
      expect(addBtn).toBeDisabled()
    })

    it('enables buttons when version selected', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const calculateBtn = screen.getByText('Calculate Projections').closest('button')
        const addBtn = screen.getByText('Add Enrollment').closest('button')

        expect(calculateBtn).not.toBeDisabled()
        expect(addBtn).not.toBeDisabled()
      })
    })
  })

  describe('Summary statistics', () => {
    it('does not show statistics when no version selected', () => {
      render(<EnrollmentPage />)

      expect(screen.queryByTestId('card')).not.toBeInTheDocument()
    })

    it('displays statistics cards when version selected with data', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const cards = screen.getAllByTestId('card')
        expect(cards.length).toBeGreaterThan(0)
      })
    })

    it('calculates total students correctly', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Total Students')).toBeInTheDocument()
        // 45 + 38 + 22 = 105
        expect(screen.getByText('105')).toBeInTheDocument()
      })
    })

    it('displays capacity utilization', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Capacity')).toBeInTheDocument()
        // 105 / 1875 * 100 = 5.6%
        expect(screen.getByText(/5\.6/)).toBeInTheDocument()
      })
    })
  })

  describe('Data table', () => {
    it('shows placeholder when no version selected', () => {
      render(<EnrollmentPage />)

      expect(screen.getByText('Please select a budget version to view enrollment data')).toBeInTheDocument()
    })

    it('displays data table when version selected', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('data-table')).toBeInTheDocument()
      })
    })

    it('displays enrollment rows', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const rows = screen.getAllByTestId('enrollment-row')
        expect(rows).toHaveLength(3)
      })
    })
  })

  describe('Create enrollment dialog', () => {
    it('does not show dialog initially', () => {
      render(<EnrollmentPage />)

      expect(screen.queryByTestId('form-dialog')).not.toBeInTheDocument()
    })

    it('opens dialog when Add Enrollment clicked', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      // Select version first
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      // Click Add Enrollment
      const addBtn = screen.getByText('Add Enrollment').closest('button')
      await user.click(addBtn!)

      await waitFor(() => {
        expect(screen.getByTestId('form-dialog')).toBeInTheDocument()
        expect(screen.getByText('Add Enrollment Entry')).toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full enrollment planning workflow', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify summary statistics appear
        expect(screen.getByText('Total Students')).toBeInTheDocument()
        expect(screen.getByText('105')).toBeInTheDocument()

        // Verify data table appears
        expect(screen.getByTestId('data-table')).toBeInTheDocument()

        // Verify action buttons are enabled
        const calculateBtn = screen.getByText('Calculate Projections').closest('button')
        const addBtn = screen.getByText('Add Enrollment').closest('button')
        expect(calculateBtn).not.toBeDisabled()
        expect(addBtn).not.toBeDisabled()
      })
    })

    it('handles empty enrollment data', async () => {
      mockEnrollmentsData = { items: [] }
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // No statistics cards should appear when rowData is empty
        expect(screen.queryByText('Total Students')).not.toBeInTheDocument()
        // Data table should still render
        expect(screen.getByTestId('data-table')).toBeInTheDocument()
      })
    })

    it('allows switching between budget versions', async () => {
      const user = userEvent.setup()

      render(<EnrollmentPage />)

      const select = screen.getByTestId('version-select')

      // Select first version
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('data-table')).toBeInTheDocument()
      })

      // Switch to second version
      await user.selectOptions(select, 'v2')

      expect(select).toHaveValue('v2')
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
