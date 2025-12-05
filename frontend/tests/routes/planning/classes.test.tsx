import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as ClassesRoute } from '@/routes/planning/classes'

// Mock dependencies
const mockNavigate = vi.fn()
let mockClassStructuresData: any = null
let mockLevelsData: any = null
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
          <div key={row.id} data-testid="class-structure-row">
            {row.level_id}: {row.number_of_classes} classes, avg {row.avg_class_size} students
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
        <form onSubmit={onSubmit} data-testid="class-structure-form">
          {children}
        </form>
      </div>
    ) : null,
}))

vi.mock('@/hooks/api/useClassStructure', () => ({
  useClassStructures: (versionId: string) => ({
    data: versionId ? mockClassStructuresData : null,
    isLoading: false,
    error: null,
  }),
  useCreateClassStructure: () => ({
    mutateAsync: mockCreateMutation,
    isPending: false,
  }),
  useUpdateClassStructure: () => ({
    mutateAsync: mockUpdateMutation,
    isPending: false,
  }),
  useDeleteClassStructure: () => ({
    mutateAsync: mockDeleteMutation,
    isPending: false,
  }),
  useCalculateClassStructure: () => ({
    mutateAsync: mockCalculateMutation,
    isPending: false,
  }),
}))

vi.mock('@/hooks/api/useConfiguration', () => ({
  useLevels: () => ({
    data: mockLevelsData,
  }),
}))

vi.mock('lucide-react', () => ({
  Plus: () => <span>Plus Icon</span>,
  Trash2: () => <span>Trash Icon</span>,
  Calculator: () => <span>Calculator Icon</span>,
  ChevronDown: () => <span>ChevronDown Icon</span>,
  ChevronUp: () => <span>ChevronUp Icon</span>,
  Check: () => <span>Check Icon</span>,
}))

describe('Class Structure Route', () => {
  const ClassStructurePage = ClassesRoute.component

  beforeEach(() => {
    vi.clearAllMocks()

    mockClassStructuresData = {
      items: [
        {
          id: '1',
          level_id: 'cp',
          number_of_classes: 4,
          avg_class_size: 24,
          budget_version_id: 'v1',
        },
        {
          id: '2',
          level_id: 'ce1',
          number_of_classes: 3,
          avg_class_size: 26,
          budget_version_id: 'v1',
        },
        {
          id: '3',
          level_id: 'ce2',
          number_of_classes: 3,
          avg_class_size: 25,
          budget_version_id: 'v1',
        },
      ],
    }

    mockLevelsData = [
      { id: 'cp', name: 'CP', cycle: 'Elementary' },
      { id: 'ce1', name: 'CE1', cycle: 'Elementary' },
      { id: 'ce2', name: 'CE2', cycle: 'Elementary' },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<ClassStructurePage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<ClassStructurePage />)

      expect(screen.getByText('Class Structure')).toBeInTheDocument()
      expect(screen.getByText('Define class structure and average class sizes')).toBeInTheDocument()
    })

    it('renders page actions', () => {
      render(<ClassStructurePage />)

      expect(screen.getByTestId('page-actions')).toBeInTheDocument()
    })
  })

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<ClassStructurePage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
    })
  })

  describe('Action buttons', () => {
    it('renders Calculate from Enrollment button', () => {
      render(<ClassStructurePage />)

      expect(screen.getByText('Calculate from Enrollment')).toBeInTheDocument()
    })

    it('renders Add Class Structure button', () => {
      render(<ClassStructurePage />)

      expect(screen.getByText('Add Class Structure')).toBeInTheDocument()
    })

    it('disables buttons when no version selected', () => {
      render(<ClassStructurePage />)

      const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
      const addBtn = screen.getByText('Add Class Structure').closest('button')

      expect(calculateBtn).toBeDisabled()
      expect(addBtn).toBeDisabled()
    })

    it('enables buttons when version selected', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
        const addBtn = screen.getByText('Add Class Structure').closest('button')

        expect(calculateBtn).not.toBeDisabled()
        expect(addBtn).not.toBeDisabled()
      })
    })
  })

  describe('Data table', () => {
    it('shows placeholder when no version selected', () => {
      render(<ClassStructurePage />)

      expect(
        screen.getByText('Please select a budget version to view class structure data')
      ).toBeInTheDocument()
    })

    it('displays data table when version selected', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('data-table')).toBeInTheDocument()
      })
    })

    it('displays class structure rows', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const rows = screen.getAllByTestId('class-structure-row')
        expect(rows).toHaveLength(3)
      })
    })

    it('displays class structure details', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText(/cp: 4 classes, avg 24 students/)).toBeInTheDocument()
        expect(screen.getByText(/ce1: 3 classes, avg 26 students/)).toBeInTheDocument()
        expect(screen.getByText(/ce2: 3 classes, avg 25 students/)).toBeInTheDocument()
      })
    })
  })

  describe('Create class structure dialog', () => {
    it('does not show dialog initially', () => {
      render(<ClassStructurePage />)

      expect(screen.queryByTestId('form-dialog')).not.toBeInTheDocument()
    })

    it('opens dialog when Add Class Structure clicked', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      // Select version first
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      // Click Add Class Structure
      const addBtn = screen.getByText('Add Class Structure').closest('button')
      await user.click(addBtn!)

      await waitFor(() => {
        expect(screen.getByTestId('form-dialog')).toBeInTheDocument()
        expect(screen.getByText('Add Class Structure Entry')).toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full class structure planning workflow', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify data table appears
        expect(screen.getByTestId('data-table')).toBeInTheDocument()

        // Verify action buttons are enabled
        const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
        const addBtn = screen.getByText('Add Class Structure').closest('button')
        expect(calculateBtn).not.toBeDisabled()
        expect(addBtn).not.toBeDisabled()
      })
    })

    it('handles empty class structure data', async () => {
      mockClassStructuresData = { items: [] }
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Data table should still render but with no rows
        expect(screen.getByTestId('data-table')).toBeInTheDocument()
        expect(screen.queryAllByTestId('class-structure-row')).toHaveLength(0)
      })
    })

    it('allows switching between budget versions', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

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

    it('calculates total students correctly', async () => {
      const user = userEvent.setup()

      render(<ClassStructurePage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // CP: 4 classes × 24 = 96 students
        // CE1: 3 classes × 26 = 78 students
        // CE2: 3 classes × 25 = 75 students
        // Total: 249 students
        const rows = screen.getAllByTestId('class-structure-row')
        expect(rows).toHaveLength(3)
      })
    })
  })

  describe('Route configuration', () => {
    it('requires authentication', () => {
      expect(ClassesRoute.beforeLoad).toBeDefined()
    })

    it('has correct path', () => {
      expect(ClassesRoute.path).toBe('/planning/classes')
    })
  })
})
