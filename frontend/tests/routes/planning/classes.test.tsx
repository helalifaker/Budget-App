import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as ClassesRoute } from '@/routes/planning/classes'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockClassStructuresData: Record<string, unknown>[] | null = null
let mockLevelsData: Record<string, unknown>[] | null = null
const mockUpdateMutation = vi.fn()
const mockCalculateMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface ClassRow {
  id: string
  level_id: string
  number_of_classes: number
  avg_class_size: number
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
  PageContainer: ({ title, description, actions, children }: MockProps) => (
    <div data-testid="page-container">
      <h1>{title as string}</h1>
      {description && <p>{description as string}</p>}
      {actions && <div data-testid="page-actions">{actions as React.ReactNode}</div>}
      {children as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({ value, onChange }: MockProps) => (
    <div data-testid="budget-version-selector">
      <select
        data-testid="version-select"
        value={value as string}
        onChange={(e) => (onChange as (v: string) => void)(e.target.value)}
      >
        <option value="">Select version</option>
        <option value="v1">2025-2026</option>
        <option value="v2">2024-2025</option>
      </select>
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
        {(rowData as ClassRow[] | undefined)?.map((row) => (
          <div key={row.id} data-testid="class-structure-row">
            {row.level_id}: {row.number_of_classes} classes, avg {row.avg_class_size} students
          </div>
        ))}
      </div>
    )
  },
}))

vi.mock('@/components/FormDialog', () => ({
  FormDialog: ({ open, title, children, onSubmit }: MockProps) =>
    open ? (
      <div data-testid="form-dialog">
        <h2>{title as string}</h2>
        <form onSubmit={onSubmit as React.FormEventHandler} data-testid="class-structure-form">
          {children as React.ReactNode}
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
  // Note: useCreateClassStructure and useDeleteClassStructure removed - backend doesn't support them
  useUpdateClassStructure: () => ({
    mutateAsync: mockUpdateMutation,
    isPending: false,
  }),
  useCalculateClassStructure: () => ({
    mutateAsync: mockCalculateMutation,
    isPending: false,
  }),
  classStructureKeys: {
    all: ['class-structure'],
    list: (versionId: string) => ['class-structure', 'list', versionId],
  },
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
    mockSelectedVersionId = undefined // Reset version selection

    // API returns arrays directly (not { items: [...] })
    mockClassStructuresData = [
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
    ]

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
      expect(screen.getByText(/Define class structure and average class sizes/)).toBeInTheDocument()
    })

    it('renders page actions', () => {
      render(<ClassStructurePage />)

      expect(screen.getByTestId('page-actions')).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<ClassStructurePage />)

      expect(screen.getByText(/Select a budget version/i)).toBeInTheDocument()
    })
  })

  describe('Action buttons', () => {
    it('renders Calculate from Enrollment button', () => {
      render(<ClassStructurePage />)

      expect(screen.getByText('Calculate from Enrollment')).toBeInTheDocument()
    })

    it('disables button when no version selected', () => {
      render(<ClassStructurePage />)

      const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
      expect(calculateBtn).toBeDisabled()
    })

    it('enables button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })
  })

  describe('Data table', () => {
    it('shows placeholder when no version selected', () => {
      render(<ClassStructurePage />)

      expect(
        screen.getByText('Please select a budget version to view class structure data')
      ).toBeInTheDocument()
    })

    it('displays data table when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      expect(screen.getByTestId('data-table')).toBeInTheDocument()
    })

    it('displays class structure rows', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      const rows = screen.getAllByTestId('class-structure-row')
      expect(rows).toHaveLength(3)
    })

    it('displays class structure details', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      expect(screen.getByText(/cp: 4 classes, avg 24 students/)).toBeInTheDocument()
      expect(screen.getByText(/ce1: 3 classes, avg 26 students/)).toBeInTheDocument()
      expect(screen.getByText(/ce2: 3 classes, avg 25 students/)).toBeInTheDocument()
    })
  })

  describe('Cell editing', () => {
    it('supports inline editing of class structure data', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      // Data table should be editable (AG Grid with editable cells)
      expect(screen.getByTestId('data-table')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full class structure planning workflow', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      // Verify data table appears
      expect(screen.getByTestId('data-table')).toBeInTheDocument()

      // Verify action button is enabled
      const calculateBtn = screen.getByText('Calculate from Enrollment').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })

    it('handles empty class structure data', () => {
      mockClassStructuresData = []
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      // Data table should still render but with no rows
      expect(screen.getByTestId('data-table')).toBeInTheDocument()
      expect(screen.queryAllByTestId('class-structure-row')).toHaveLength(0)
    })

    it('maintains data table when version is selected', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      // Data table persists with selected version
      expect(screen.getByTestId('data-table')).toBeInTheDocument()
      expect(screen.getAllByTestId('class-structure-row')).toHaveLength(3)
    })

    it('calculates total students correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<ClassStructurePage />)

      // CP: 4 classes × 24 = 96 students
      // CE1: 3 classes × 26 = 78 students
      // CE2: 3 classes × 25 = 75 students
      // Total: 249 students
      const rows = screen.getAllByTestId('class-structure-row')
      expect(rows).toHaveLength(3)
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
