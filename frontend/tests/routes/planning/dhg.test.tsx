import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as DHGRoute } from '@/routes/planning/dhg'

// Mock dependencies
const mockNavigate = vi.fn()
let mockSubjectHoursData: any = null
let mockTeacherFTEData: any = null
let mockTRMDGapsData: any = null
let mockHSAPlanningData: any = null
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
  SummaryCard: ({ title, value, subtitle, icon, valueClassName }: any) => (
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value" className={valueClassName}>
        {value}
      </div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
      {icon}
    </div>
  ),
}))

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: any) => (
    <div data-testid="tabs" data-value={value}>
      {children}
    </div>
  ),
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ value, children }: any) => (
    <button data-testid={`tab-trigger-${value}`}>{children}</button>
  ),
  TabsContent: ({ value, children }: any) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children, className }: any) => (
    <div data-testid="card-header" className={className}>
      {children}
    </div>
  ),
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

vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData }: any) => (
    <div data-testid="ag-grid">
      {rowData?.map((row: any, index: number) => (
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
  useTeacherFTE: (versionId: string) => ({
    data: versionId ? mockTeacherFTEData : null,
    isLoading: false,
  }),
  useTRMDGaps: (versionId: string) => ({
    data: versionId ? mockTRMDGapsData : null,
    isLoading: false,
  }),
  useHSAPlanning: (versionId: string) => ({
    data: versionId ? mockHSAPlanningData : null,
    isLoading: false,
  }),
  useCalculateFTE: () => ({
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

    mockSubjectHoursData = {
      items: [
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
      ],
    }

    mockTeacherFTEData = {
      items: [
        {
          id: '1',
          cycle_name: 'Collège',
          subject_name: 'Mathématiques',
          total_hours: 96,
          standard_fte: 5.33,
          adjusted_fte: 6,
          hsa_hours: 12,
        },
        {
          id: '2',
          cycle_name: 'Collège',
          subject_name: 'Français',
          total_hours: 84,
          standard_fte: 4.67,
          adjusted_fte: 5,
          hsa_hours: 6,
        },
        {
          id: '3',
          cycle_name: 'Lycée',
          subject_name: 'Sciences',
          total_hours: 72,
          standard_fte: 4.0,
          adjusted_fte: 4,
          hsa_hours: 0,
        },
      ],
    }

    mockTRMDGapsData = {
      items: [
        {
          id: '1',
          subject_name: 'Mathématiques',
          hours_needed: 96,
          aefe_positions: 4,
          local_positions: 1,
          deficit_hours: 6,
          hsa_required: 6,
        },
        {
          id: '2',
          subject_name: 'Français',
          hours_needed: 84,
          aefe_positions: 3,
          local_positions: 2,
          deficit_hours: -6,
          hsa_required: 0,
        },
      ],
    }

    mockHSAPlanningData = {
      items: [
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
      ],
    }
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

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<DHGPage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
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

    it('enables Recalculate button when version selected', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const calculateBtn = screen.getByText('Recalculate FTE').closest('button')
        expect(calculateBtn).not.toBeDisabled()
      })
    })
  })

  describe('Summary cards', () => {
    it('does not show summary cards when no version selected', () => {
      render(<DHGPage />)

      expect(screen.queryByTestId('summary-card-total-fte-required')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-fte-required')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-hsa-hours')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-deficit-hours')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-hsa-assignments')).toBeInTheDocument()
      })
    })

    it('calculates total FTE correctly', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const fteCard = screen.getByTestId('summary-card-total-fte-required')
        // 6 + 5 + 4 = 15.00
        expect(fteCard).toHaveTextContent('15.00')
        expect(fteCard).toHaveTextContent('Full-time equivalents')
      })
    })

    it('calculates HSA hours correctly', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const hsaCard = screen.getByTestId('summary-card-hsa-hours')
        // 12 + 6 + 0 = 18.0
        expect(hsaCard).toHaveTextContent('18.0')
        expect(hsaCard).toHaveTextContent('Overtime hours')
      })
    })

    it('calculates deficit hours correctly', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const deficitCard = screen.getByTestId('summary-card-deficit-hours')
        // 6 + (-6) = 0.0
        expect(deficitCard).toHaveTextContent('0.0')
        expect(deficitCard).toHaveTextContent('Hours to fill')
      })
    })

    it('counts HSA assignments correctly', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const assignmentsCard = screen.getByTestId('summary-card-hsa-assignments')
        // 3 teachers
        expect(assignmentsCard).toHaveTextContent('3')
        expect(assignmentsCard).toHaveTextContent('Teachers with overtime')
      })
    })
  })

  describe('Tabs', () => {
    it('displays tabs component', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-hours')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-fte')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-trmd')).toBeInTheDocument()
        expect(screen.getByTestId('tab-trigger-hsa')).toBeInTheDocument()
      })
    })

    it('defaults to hours tab', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const tabs = screen.getByTestId('tabs')
        expect(tabs).toHaveAttribute('data-value', 'hours')
      })
    })
  })

  describe('Subject Hours tab', () => {
    it('displays subject hours grid', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('tab-content-hours')).toBeInTheDocument()
        expect(screen.getByText('Subject Hours Matrix')).toBeInTheDocument()
      })
    })

    it('displays subject hours rows', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText(/Mathématiques: 4.5/)).toBeInTheDocument()
        expect(screen.getByText(/Français: 5/)).toBeInTheDocument()
        expect(screen.getByText(/Histoire-Géographie: 3/)).toBeInTheDocument()
      })
    })
  })

  describe('Teacher FTE tab', () => {
    it('displays Teacher FTE card title', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Teacher FTE Requirements')).toBeInTheDocument()
      })
    })

    it('displays FTE badges', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const badges = screen.getAllByTestId('badge')
        expect(badges.length).toBeGreaterThan(0)
      })
    })
  })

  describe('TRMD Gap Analysis tab', () => {
    it('displays TRMD card title', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // TRMD Gap Analysis appears in both tab trigger and card title
        const trmdTexts = screen.getAllByText('TRMD Gap Analysis')
        expect(trmdTexts.length).toBeGreaterThan(0)
      })
    })
  })

  describe('HSA Planning tab', () => {
    it('displays HSA card title', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('HSA Overtime Planning')).toBeInTheDocument()
      })
    })

    it('displays Add HSA Assignment button', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByText('Add HSA Assignment')).toBeInTheDocument()
      })
    })
  })

  describe('Placeholder state', () => {
    it('shows placeholder when no version selected', () => {
      render(<DHGPage />)

      expect(screen.getByText('Select a budget version to view DHG workforce planning')).toBeInTheDocument()
    })

    it('hides placeholder when version selected', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(
          screen.queryByText('Select a budget version to view DHG workforce planning')
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full DHG planning workflow', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      // Select budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
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
    })

    it('handles empty DHG data', async () => {
      mockSubjectHoursData = { items: [] }
      mockTeacherFTEData = { items: [] }
      mockTRMDGapsData = { items: [] }
      mockHSAPlanningData = { items: [] }
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Summary cards should show 0 values
        expect(screen.getByTestId('summary-card-total-fte-required')).toHaveTextContent('0.00')
        expect(screen.getByTestId('summary-card-hsa-hours')).toHaveTextContent('0.0')
        expect(screen.getByTestId('summary-card-hsa-assignments')).toHaveTextContent('0')
      })
    })

    it('allows switching between budget versions', async () => {
      const user = userEvent.setup()

      render(<DHGPage />)

      const select = screen.getByTestId('version-select')

      // Select first version
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toBeInTheDocument()
      })

      // Switch to second version
      await user.selectOptions(select, 'v2')

      expect(select).toHaveValue('v2')
    })
  })

  describe('Route configuration', () => {
    it('has correct path', () => {
      expect(DHGRoute.path).toBe('/planning/dhg')
    })
  })
})
