import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { Route as SubjectHoursRoute } from '@/routes/configuration/subject-hours'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// API mock data
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
let mockMatrixResponse: {
  cycle_code: string
  levels: { id: string; code: string; name_en: string; name_fr: string; sort_order: number }[]
  subjects: {
    id: string
    code: string
    name_fr: string
    name_en: string
    category: string
    is_applicable: boolean
    hours: Record<
      string,
      { hours_per_week: number | null; is_split: boolean; notes: string | null }
    >
  }[]
} | null = null
let mockTemplatesData:
  | { code: string; name: string; description: string; cycle_codes: string[] }[]
  | null = null

const mockBatchSaveMutation = vi.fn()
const mockApplyTemplateMutation = vi.fn()
const mockCreateSubjectMutation = vi.fn()

// Type definitions for mock props
type MockProps = Record<string, unknown>

interface SubjectHoursMatrixRow {
  id: string
  subjectId: string
  subjectCode: string
  subjectName: string
  category: 'core' | 'elective' | 'specialty' | 'local'
  isApplicable: boolean
  hours: Record<string, number | null>
  splitFlags: Record<string, boolean>
  notes: string
  isDirty: boolean
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

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: MockProps) => (
    <div data-testid="tabs" data-value={value as string}>
      {typeof onValueChange === 'function' && (
        <input
          type="hidden"
          data-testid="tab-change-trigger"
          onChange={(e) => (onValueChange as (v: string) => void)(e.target.value)}
        />
      )}
      {children as React.ReactNode}
    </div>
  ),
  TabsList: ({ children }: MockProps) => (
    <div data-testid="tabs-list">{children as React.ReactNode}</div>
  ),
  TabsTrigger: ({ value, children, disabled }: MockProps) => (
    <button
      data-testid={`tab-trigger-${value as string}`}
      disabled={disabled as boolean}
      data-value={value as string}
    >
      {children as React.ReactNode}
    </button>
  ),
  TabsContent: ({ value, children }: MockProps) => (
    <div data-testid={`tab-content-${value as string}`}>{children as React.ReactNode}</div>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant }: MockProps) => (
    <button
      onClick={onClick as () => void}
      disabled={disabled as boolean}
      data-testid={`button-${variant || 'default'}`}
      data-variant={variant as string}
    >
      {children as React.ReactNode}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: MockProps) => (
    <span data-testid="badge" data-variant={variant as string}>
      {children as React.ReactNode}
    </span>
  ),
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({ title, value, subtitle, icon, trend }: MockProps) => (
    <div data-testid={`summary-card-${(title as string).toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title as string}</div>
      <div data-testid="card-value">{String(value)}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle as string}</div>}
      {trend && <div data-testid="card-trend">{trend as string}</div>}
      {icon as React.ReactNode}
    </div>
  ),
}))

vi.mock('@/components/configuration/SubjectHoursMatrix', () => ({
  SubjectHoursMatrix: ({ levels, rowData, onDataChange, isLoading, error }: MockProps) => {
    if (isLoading) {
      return <div data-testid="matrix-loading">Loading matrix...</div>
    }
    if (error) {
      return <div data-testid="matrix-error">Error loading matrix</div>
    }
    return (
      <div data-testid="subject-hours-matrix">
        <div data-testid="matrix-levels">
          {(levels as { id: string; code: string }[])?.map((l) => (
            <span key={l.id}>{l.code}</span>
          ))}
        </div>
        <div data-testid="matrix-rows">
          {(rowData as SubjectHoursMatrixRow[])?.map((row) => (
            <div key={row.id} data-testid="matrix-row" data-dirty={row.isDirty}>
              <span>
                {row.subjectCode}: {row.subjectName}
              </span>
              {Object.entries(row.hours).map(([levelId, hours]) => (
                <input
                  key={levelId}
                  data-testid={`hours-${row.id}-${levelId}`}
                  type="number"
                  defaultValue={hours ?? ''}
                  onChange={(e) => {
                    const newRows = (rowData as SubjectHoursMatrixRow[]).map((r) =>
                      r.id === row.id
                        ? {
                            ...r,
                            hours: { ...r.hours, [levelId]: parseFloat(e.target.value) || null },
                            isDirty: true,
                          }
                        : r
                    )
                    ;(onDataChange as (rows: SubjectHoursMatrixRow[]) => void)(newRows)
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    )
  },
}))

vi.mock('@/components/configuration/TemplateSelector', () => ({
  TemplateSelector: ({
    templates,
    currentCycleCode,
    onApplyTemplate,
    isApplying,
    disabled,
  }: MockProps) => (
    <div data-testid="template-selector">
      <select
        data-testid="template-select"
        disabled={(disabled || isApplying) as boolean}
        onChange={(e) =>
          (onApplyTemplate as (code: string, overwrite: boolean) => void)(e.target.value, false)
        }
      >
        <option value="">Select template</option>
        {(templates as { code: string; name: string; cycle_codes: string[] }[])
          ?.filter((t) => t.cycle_codes.includes(currentCycleCode as string))
          .map((t) => (
            <option key={t.code} value={t.code}>
              {t.name}
            </option>
          ))}
      </select>
      {isApplying && <span data-testid="template-applying">Applying...</span>}
    </div>
  ),
}))

vi.mock('@/components/configuration/AddSubjectDialog', () => ({
  AddSubjectDialog: ({ onAddSubject, isAdding }: MockProps) => (
    <div data-testid="add-subject-dialog">
      <button
        data-testid="add-subject-button"
        disabled={isAdding as boolean}
        onClick={() =>
          (
            onAddSubject as (data: {
              code: string
              name_fr: string
              name_en: string
              category: string
              applicable_cycles: string[]
            }) => void
          )({
            code: 'TEST',
            name_fr: 'Test',
            name_en: 'Test',
            category: 'elective',
            applicable_cycles: ['COLL'],
          })
        }
      >
        Add Subject
      </button>
    </div>
  ),
}))

vi.mock('@/hooks/api/useConfiguration', () => ({
  useLevels: () => ({
    data: mockLevelsData,
    isLoading: false,
  }),
  useCycles: () => ({
    data: mockCyclesData,
    isLoading: false,
  }),
  useSubjectHoursMatrix: () => ({
    data: mockMatrixResponse,
    isLoading: false,
    error: null,
  }),
  useBatchSaveSubjectHours: () => ({
    mutateAsync: mockBatchSaveMutation,
    isPending: false,
  }),
  useCurriculumTemplates: () => ({
    data: mockTemplatesData,
    isLoading: false,
  }),
  useApplyTemplate: () => ({
    mutateAsync: mockApplyTemplateMutation,
    isPending: false,
  }),
  useCreateSubject: () => ({
    mutateAsync: mockCreateSubjectMutation,
    isPending: false,
  }),
}))

vi.mock('@/lib/toast-messages', () => ({
  toastMessages: {
    warning: {
      unsavedChanges: vi.fn(),
      selectVersion: vi.fn(),
    },
    error: {
      custom: vi.fn(),
      generic: vi.fn(),
    },
    success: {
      created: vi.fn(),
      updated: vi.fn(),
    },
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
  AlertCircle: () => <span>AlertCircle Icon</span>,
  CheckCircle: () => <span>CheckCircle Icon</span>,
}))

describe('Subject Hours Configuration Route', () => {
  const SubjectHoursPage = SubjectHoursRoute.component

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
      {
        id: 'lyc',
        code: 'LYC',
        name_fr: 'Lycée',
        name_en: 'High School',
        sort_order: 4,
        requires_atsem: false,
      },
    ]

    // Setup mock levels data
    mockLevelsData = [
      {
        id: '6eme',
        code: '6ème',
        name_fr: 'Sixième',
        name_en: '6th Grade',
        cycle_id: 'coll',
        sort_order: 1,
      },
      {
        id: '5eme',
        code: '5ème',
        name_fr: 'Cinquième',
        name_en: '5th Grade',
        cycle_id: 'coll',
        sort_order: 2,
      },
      {
        id: '4eme',
        code: '4ème',
        name_fr: 'Quatrième',
        name_en: '4th Grade',
        cycle_id: 'coll',
        sort_order: 3,
      },
      {
        id: '3eme',
        code: '3ème',
        name_fr: 'Troisième',
        name_en: '3rd Grade',
        cycle_id: 'coll',
        sort_order: 4,
      },
      {
        id: '2nde',
        code: '2nde',
        name_fr: 'Seconde',
        name_en: '10th Grade',
        cycle_id: 'lyc',
        sort_order: 5,
      },
      {
        id: '1ere',
        code: '1ère',
        name_fr: 'Première',
        name_en: '11th Grade',
        cycle_id: 'lyc',
        sort_order: 6,
      },
      {
        id: 'term',
        code: 'Term',
        name_fr: 'Terminale',
        name_en: '12th Grade',
        cycle_id: 'lyc',
        sort_order: 7,
      },
    ]

    // Setup mock matrix response
    mockMatrixResponse = {
      cycle_code: 'COLL',
      levels: [
        { id: '6eme', code: '6ème', name_en: '6th Grade', name_fr: 'Sixième', sort_order: 1 },
        { id: '5eme', code: '5ème', name_en: '5th Grade', name_fr: 'Cinquième', sort_order: 2 },
        { id: '4eme', code: '4ème', name_en: '4th Grade', name_fr: 'Quatrième', sort_order: 3 },
        { id: '3eme', code: '3ème', name_en: '3rd Grade', name_fr: 'Troisième', sort_order: 4 },
      ],
      subjects: [
        {
          id: 'math',
          code: 'MATH',
          name_fr: 'Mathématiques',
          name_en: 'Mathematics',
          category: 'core',
          is_applicable: true,
          hours: {
            '6eme': { hours_per_week: 4.5, is_split: false, notes: null },
            '5eme': { hours_per_week: 3.5, is_split: false, notes: null },
            '4eme': { hours_per_week: 3.5, is_split: false, notes: null },
            '3eme': { hours_per_week: 3.5, is_split: false, notes: null },
          },
        },
        {
          id: 'fran',
          code: 'FRAN',
          name_fr: 'Français',
          name_en: 'French',
          category: 'core',
          is_applicable: true,
          hours: {
            '6eme': { hours_per_week: 4.5, is_split: false, notes: null },
            '5eme': { hours_per_week: 4.5, is_split: false, notes: null },
            '4eme': { hours_per_week: 4.5, is_split: false, notes: null },
            '3eme': { hours_per_week: 4.0, is_split: false, notes: null },
          },
        },
        {
          id: 'angl',
          code: 'ANGL',
          name_fr: 'Anglais',
          name_en: 'English',
          category: 'core',
          is_applicable: true,
          hours: {
            '6eme': { hours_per_week: 4.0, is_split: true, notes: 'LV1' },
            '5eme': { hours_per_week: 3.0, is_split: true, notes: 'LV1' },
            '4eme': { hours_per_week: 3.0, is_split: true, notes: 'LV1' },
            '3eme': { hours_per_week: 3.0, is_split: true, notes: 'LV1' },
          },
        },
      ],
    }

    // Setup mock templates
    mockTemplatesData = [
      {
        code: 'AEFE_STANDARD_COLL',
        name: 'AEFE Standard - Collège',
        description: 'Standard AEFE curriculum for middle school',
        cycle_codes: ['COLL'],
      },
      {
        code: 'AEFE_STANDARD_LYC',
        name: 'AEFE Standard - Lycée',
        description: 'Standard AEFE curriculum for high school',
        cycle_codes: ['LYC'],
      },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<SubjectHoursPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<SubjectHoursPage />)

      expect(screen.getByText('Subject Hours Configuration')).toBeInTheDocument()
      expect(
        screen.getByText('Configure weekly teaching hours for each subject by academic level')
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<SubjectHoursPage />)

      expect(screen.getByText(/Please select a budget version/i)).toBeInTheDocument()
    })
  })

  describe('Cycle tabs', () => {
    it('displays cycle tabs when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByTestId('tabs-list')).toBeInTheDocument()
    })

    it('shows Maternelle and Élémentaire tabs as disabled', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const matTab = screen.getByTestId('tab-trigger-MAT')
      const elemTab = screen.getByTestId('tab-trigger-ELEM')

      expect(matTab).toBeDisabled()
      expect(elemTab).toBeDisabled()
    })

    it('shows Collège and Lycée tabs as enabled', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const collTab = screen.getByTestId('tab-trigger-COLL')
      const lycTab = screen.getByTestId('tab-trigger-LYC')

      expect(collTab).not.toBeDisabled()
      expect(lycTab).not.toBeDisabled()
    })

    it('defaults to Collège tab', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const tabs = screen.getByTestId('tabs')
      expect(tabs).toHaveAttribute('data-value', 'COLL')
    })
  })

  describe('Summary statistics cards', () => {
    it('does not show statistics when no version selected', () => {
      render(<SubjectHoursPage />)

      expect(screen.queryByTestId('summary-card-subjects')).not.toBeInTheDocument()
    })

    it('displays Subjects card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')
      expect(within(collTab).getByTestId('summary-card-subjects')).toBeInTheDocument()
    })

    it('displays Total Hours card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')
      expect(within(collTab).getByTestId('summary-card-total-hours')).toBeInTheDocument()
    })

    it('displays Unsaved Changes card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')
      expect(within(collTab).getByTestId('summary-card-unsaved-changes')).toBeInTheDocument()
    })

    it('displays Validation card when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')
      expect(within(collTab).getByTestId('summary-card-validation')).toBeInTheDocument()
    })
  })

  describe('Matrix grid', () => {
    it('renders matrix grid when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')
      expect(within(collTab).getByTestId('subject-hours-matrix')).toBeInTheDocument()
    })

    it('displays level columns from current cycle', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default)
      const collTab = screen.getByTestId('tab-content-COLL')
      const matrixLevels = within(collTab).getByTestId('matrix-levels')
      expect(matrixLevels).toHaveTextContent('6ème')
      expect(matrixLevels).toHaveTextContent('5ème')
      expect(matrixLevels).toHaveTextContent('4ème')
      expect(matrixLevels).toHaveTextContent('3ème')
    })
  })

  describe('Template selector', () => {
    it('renders template selector when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByTestId('template-selector')).toBeInTheDocument()
    })

    it('shows applicable templates for current cycle', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const templateSelect = screen.getByTestId('template-select')
      expect(templateSelect).toBeInTheDocument()
    })
  })

  describe('Add subject dialog', () => {
    it('renders add subject button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByTestId('add-subject-dialog')).toBeInTheDocument()
      expect(screen.getByTestId('add-subject-button')).toBeInTheDocument()
    })

    it('triggers create subject mutation when add button clicked', async () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const addButton = screen.getByTestId('add-subject-button')
      fireEvent.click(addButton)

      await waitFor(() => {
        expect(mockCreateSubjectMutation).toHaveBeenCalledWith({
          code: 'TEST',
          name_fr: 'Test',
          name_en: 'Test',
          category: 'elective',
          applicable_cycles: ['COLL'],
        })
      })
    })
  })

  describe('Save functionality', () => {
    it('renders Save Changes button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByText('Save Changes')).toBeInTheDocument()
    })

    it('Save Changes button is disabled when no unsaved changes', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      const saveBtn = screen.getByText('Save Changes').closest('button')
      expect(saveBtn).toBeDisabled()
    })
  })

  describe('Instructions', () => {
    it('displays inline editing instructions when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      expect(screen.getByText(/Edit cells directly/i)).toBeInTheDocument()
      expect(screen.getByText(/Hours must be between 0 and 12/i)).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full subject hours interface', () => {
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default) to avoid duplicate elements
      const collTab = screen.getByTestId('tab-content-COLL')

      // Verify summary cards appear in the active tab
      expect(within(collTab).getByTestId('summary-card-subjects')).toBeInTheDocument()
      expect(within(collTab).getByTestId('summary-card-total-hours')).toBeInTheDocument()
      expect(within(collTab).getByTestId('summary-card-unsaved-changes')).toBeInTheDocument()
      expect(within(collTab).getByTestId('summary-card-validation')).toBeInTheDocument()

      // Verify tabs appear
      expect(screen.getByTestId('tabs')).toBeInTheDocument()

      // Verify matrix grid appears in the active tab
      expect(within(collTab).getByTestId('subject-hours-matrix')).toBeInTheDocument()

      // Verify action buttons appear (these are outside tabs, so use screen)
      expect(screen.getByTestId('template-selector')).toBeInTheDocument()
      expect(screen.getByTestId('add-subject-dialog')).toBeInTheDocument()
    })

    it('handles empty matrix data', () => {
      mockMatrixResponse = {
        cycle_code: 'COLL',
        levels: [],
        subjects: [],
      }
      mockSelectedVersionId = 'v1'
      render(<SubjectHoursPage />)

      // Scope to active tab (COLL is default)
      const collTab = screen.getByTestId('tab-content-COLL')

      // Summary cards should still render
      expect(within(collTab).getByTestId('summary-card-subjects')).toBeInTheDocument()

      // Matrix should render (but empty)
      expect(within(collTab).getByTestId('subject-hours-matrix')).toBeInTheDocument()
    })

    it('context provides version switching capability', () => {
      mockSelectedVersionId = 'v1'
      const { rerender } = render(<SubjectHoursPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()

      // Simulate version change via context
      mockSelectedVersionId = 'v2'
      rerender(<SubjectHoursPage />)

      // Page should still render (context provides new version)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })
  })

  describe('Route configuration', () => {
    it('requires authentication', () => {
      expect(SubjectHoursRoute.beforeLoad).toBeDefined()
    })

    it('has correct path', () => {
      expect(SubjectHoursRoute.path).toBe('/configuration/subject-hours')
    })
  })
})
