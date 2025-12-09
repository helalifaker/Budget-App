import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as DHGRoute } from '@/routes/planning/dhg'

// Mock dependencies
const mockNavigate = vi.fn()
let mockSubjectHoursData: Record<string, unknown>[] | null = null
let mockTeacherFTEData: Record<string, unknown>[] | null = null
let mockTRMDGapsData: Record<string, unknown>[] | null = null
let mockHSAPlanningData: Record<string, unknown>[] | null = null
const mockCalculateMutation = vi.fn()

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

// Type definitions for mock props
type MockProps = Record<string, unknown>
interface DHGRow {
  id?: string
  subject_name?: string
  teacher_name?: string
  hours_per_week?: number
  hsa_hours?: number
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
  SummaryCard: ({ title, value, subtitle, icon, valueClassName }: MockProps) => (
    <div data-testid={`summary-card-${(title as string).toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title as string}</div>
      <div data-testid="card-value" className={valueClassName as string}>
        {value as React.ReactNode}
      </div>
      {subtitle && <div data-testid="card-subtitle">{subtitle as string}</div>}
      {icon as React.ReactNode}
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

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: MockProps) => (
    <span data-testid="badge" data-variant={variant as string}>
      {children as React.ReactNode}
    </span>
  ),
}))

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: MockProps) => (
    <div data-testid="ag-grid">
      {(rowData as DHGRow[] | undefined)?.map((row, index) => (
        <div key={row.id || index} data-testid="dhg-row">
          {row.subject_name || row.teacher_name}: {row.hours_per_week || row.hsa_hours}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('ag-grid-community', () => ({
  themeQuartz: 'theme-quartz',
}))

vi.mock('@/hooks/api/useDHG', () => ({
  useSubjectHours: (versionId: string) => ({
    data: versionId ? mockSubjectHoursData : null,
    isLoading: false,
  }),
  useTeacherRequirements: (versionId: string) => ({
    data: versionId ? mockTeacherFTEData : null,
    isLoading: false,
  }),
  useTRMDGapAnalysis: (versionId: string) => ({
    data: versionId ? mockTRMDGapsData : null,
    isLoading: false,
  }),
  useHSAPlanning: (versionId: string) => ({
    data: versionId ? mockHSAPlanningData : null,
    isLoading: false,
  }),
  useCalculateTeacherRequirements: () => ({
    mutate: mockCalculateMutation,
    isPending: false,
  }),
}))

vi.mock('lucide-react', () => ({
  Users: () => <span>Users Icon</span>,
  Clock: () => <span>Clock Icon</span>,
  AlertTriangle: () => <span>AlertTriangle Icon</span>,
  TrendingUp: () => <span>TrendingUp Icon</span>,
  Calculator: () => <span>Calculator Icon</span>,
  Save: () => <span>Save Icon</span>,
}))

describe('DHG Workforce Planning Route', () => {
  const DHGPage = DHGRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectedVersionId = undefined // Reset version selection

    mockSubjectHoursData = [
      {
        id: '1',
        subject_name: 'Mathématiques',
        level_name: '6ème',
        hours_per_week: 4.5,
        is_split: false,
        number_of_classes: 6,
      },
      {
        id: '2',
        subject_name: 'Français',
        level_name: '5ème',
        hours_per_week: 5,
        is_split: true,
        number_of_classes: 5,
      },
      {
        id: '3',
        subject_name: 'Histoire-Géographie',
        level_name: '4ème',
        hours_per_week: 3,
        is_split: false,
        number_of_classes: 4,
      },
    ]

    mockTeacherFTEData = [
      {
        id: '1',
        budget_version_id: 'v1',
        subject_id: 'math',
        cycle_id: 'college',
        required_hours: 96,
        standard_hours: 18,
        fte_required: 5.33,
        notes: null,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: '2',
        budget_version_id: 'v1',
        subject_id: 'french',
        cycle_id: 'college',
        required_hours: 84,
        standard_hours: 18,
        fte_required: 4.67,
        notes: null,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: '3',
        budget_version_id: 'v1',
        subject_id: 'science',
        cycle_id: 'lycee',
        required_hours: 72,
        standard_hours: 18,
        fte_required: 4.0,
        notes: null,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockTRMDGapsData = {
      version_id: 'v1',
      analysis_date: '2024-01-01',
      gaps: [
        {
          subject_id: 'math',
          cycle_id: 'college',
          required_fte: 5.33,
          aefe_allocated: 4,
          local_allocated: 1,
          total_allocated: 5,
          deficit: 0.33,
          hsa_needed: 6,
        },
        {
          subject_id: 'french',
          cycle_id: 'college',
          required_fte: 4.67,
          aefe_allocated: 3,
          local_allocated: 2,
          total_allocated: 5,
          deficit: -0.33,
          hsa_needed: 0,
        },
      ],
      total_deficit: 0,
      total_hsa_needed: 6,
    }

    mockHSAPlanningData = [
      {
        teacher_name: 'Jean Dupont',
        subject_name: 'Mathématiques',
        hsa_hours: 3,
        notes: 'Experienced teacher',
      },
      {
        teacher_name: 'Marie Martin',
        subject_name: 'Français',
        hsa_hours: 2,
        notes: null,
      },
      {
        teacher_name: 'Pierre Bernard',
        subject_name: 'Sciences',
        hsa_hours: 5,
        notes: 'Exceeds maximum',
      },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<DHGPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<DHGPage />)

      expect(screen.getByText('DHG Workforce Planning')).toBeInTheDocument()
      expect(
        screen.getByText('Teacher hours and FTE planning using DHG methodology')
      ).toBeInTheDocument()
    })
  })

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders placeholder when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<DHGPage />)
      expect(
        screen.getByText('Select a budget version to view DHG workforce planning')
      ).toBeInTheDocument()
    })
  })

  describe('Action buttons', () => {
    it('renders Recalculate FTE button', () => {
      render(<DHGPage />)

      expect(screen.getByText('Recalculate FTE')).toBeInTheDocument()
    })

    it('disables Recalculate button when no version selected', () => {
      render(<DHGPage />)

      const calculateBtn = screen.getByText('Recalculate FTE').closest('button')
      expect(calculateBtn).toBeDisabled()
    })

    it('enables Recalculate button when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const calculateBtn = screen.getByText('Recalculate FTE').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<DHGPage />)

      expect(screen.queryByTestId('summary-card-total-fte-required')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByTestId('summary-card-total-fte-required')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-hsa-hours')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-deficit-hours')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-subjects-analyzed')).toBeInTheDocument()
    })

    it('calculates total FTE correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const fteCard = screen.getByTestId('summary-card-total-fte-required')
      expect(fteCard).toHaveTextContent('14.00')
      expect(fteCard).toHaveTextContent('Full-time equivalents')
    })

    it('calculates HSA hours correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const hsaCard = screen.getByTestId('summary-card-hsa-hours')
      expect(hsaCard).toHaveTextContent('6.0')
      expect(hsaCard).toHaveTextContent('Overtime hours')
    })

    it('calculates deficit hours correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const deficitCard = screen.getByTestId('summary-card-deficit-hours')
      expect(deficitCard).toHaveTextContent('0.0')
      expect(deficitCard).toHaveTextContent('Hours to fill')
    })

    it('counts subjects analyzed correctly', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const subjectsCard = screen.getByTestId('summary-card-subjects-analyzed')
      // mockTRMDGapsData has 2 gaps in the array
      expect(subjectsCard).toHaveTextContent('2')
      expect(subjectsCard).toHaveTextContent('In TRMD gap analysis')
    })
  })

  describe('Tabs', () => {
    it('displays tabs component', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-hours')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-fte')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-trmd')).toBeInTheDocument()
      expect(screen.getByTestId('tab-trigger-hsa')).toBeInTheDocument()
    })

    it('defaults to hours tab', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const tabs = screen.getByTestId('tabs')
      expect(tabs).toHaveAttribute('data-value', 'hours')
    })
  })

  describe('Subject Hours tab', () => {
    it('displays subject hours grid', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByTestId('tab-content-hours')).toBeInTheDocument()
      expect(screen.getByText('Subject Hours Matrix')).toBeInTheDocument()
    })

    it('displays subject hours rows', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByText(/Mathématiques: 4.5/)).toBeInTheDocument()
      expect(screen.getByText(/Français: 5/)).toBeInTheDocument()
      expect(screen.getByText(/Histoire-Géographie: 3/)).toBeInTheDocument()
    })
  })

  describe('Teacher FTE tab', () => {
    it('displays Teacher FTE card title', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByText('Teacher FTE Requirements')).toBeInTheDocument()
    })

    it('displays FTE badges', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const badges = screen.getAllByTestId('badge')
      expect(badges.length).toBeGreaterThan(0)
    })
  })

  describe('TRMD Gap Analysis tab', () => {
    it('displays TRMD card title', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      const trmdTexts = screen.getAllByText('TRMD Gap Analysis')
      expect(trmdTexts.length).toBeGreaterThan(0)
    })
  })

  describe('HSA Planning tab', () => {
    it('displays HSA card title', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByText('HSA Overtime Planning')).toBeInTheDocument()
    })

    it('displays Add HSA Assignment button', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(screen.getByText('Add HSA Assignment')).toBeInTheDocument()
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<DHGPage />)

      expect(
        screen.getByText('Select a budget version to view DHG workforce planning')
      ).toBeInTheDocument()
    })

    it('hides placeholder when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      expect(
        screen.queryByText('Select a budget version to view DHG workforce planning')
      ).not.toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays full DHG planning workflow', () => {
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      // Verify summary cards appear
      expect(screen.getByTestId('summary-card-total-fte-required')).toBeInTheDocument()
      expect(screen.getByTestId('summary-card-hsa-hours')).toBeInTheDocument()

      // Verify tabs appear
      expect(screen.getByTestId('tabs')).toBeInTheDocument()

      // Verify Subject Hours content appears
      expect(screen.getByText('Subject Hours Matrix')).toBeInTheDocument()

      // Verify action button is enabled
      const calculateBtn = screen.getByText('Recalculate FTE').closest('button')
      expect(calculateBtn).not.toBeDisabled()
    })

    it('handles empty DHG data', () => {
      mockSubjectHoursData = []
      mockTeacherFTEData = []
      mockTRMDGapsData = {
        version_id: 'v1',
        analysis_date: '2024-01-01',
        gaps: [],
        total_deficit: 0,
        total_hsa_needed: 0,
      }
      mockHSAPlanningData = []
      mockSelectedVersionId = 'v1'
      render(<DHGPage />)

      // Summary cards should show 0 values
      expect(screen.getByTestId('summary-card-total-fte-required')).toHaveTextContent('0.00')
      expect(screen.getByTestId('summary-card-hsa-hours')).toHaveTextContent('0.0')
      expect(screen.getByTestId('summary-card-subjects-analyzed')).toHaveTextContent('0')
    })

    it('context provides version switching capability', () => {
      mockSelectedVersionId = 'v1'
      const { rerender } = render(<DHGPage />)

      expect(screen.getByTestId('tabs')).toBeInTheDocument()

      // Simulate version change via context
      mockSelectedVersionId = 'v2'
      rerender(<DHGPage />)

      // Page should still render (context provides new version)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(DHGRoute.path).toBe('/planning/dhg')
    })
  })
})
