import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route as DashboardRoute } from '@/routes/dashboard'

// Mock dependencies
const mockNavigate = vi.fn()
let mockDashboardData: any = null
let mockActivitiesData: any = null
let mockAlertsData: any = null

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
  PageContainer: ({ title, description, children }: any) => (
    <div data-testid="page-container">
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/BudgetVersionSelector', () => ({
  BudgetVersionSelector: ({ value, onChange, showCreateButton }: any) => (
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
      {showCreateButton && <button data-testid="create-button">Create</button>}
    </div>
  ),
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({ title, value, icon, subtitle }: any) => (
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value">{value}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
    </div>
  ),
}))

vi.mock('@/components/ActivityFeed', () => ({
  ActivityFeed: ({ activities }: any) => (
    <div data-testid="activity-feed">
      {activities?.map((activity: any, index: number) => (
        <div key={index} data-testid="activity-item">
          {activity.description}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('@/components/charts/EnrollmentChart', () => ({
  EnrollmentChart: ({ data }: any) => (
    <div data-testid="enrollment-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/components/charts/RevenueChart', () => ({
  RevenueChart: ({ data }: any) => (
    <div data-testid="revenue-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/components/charts/CostChart', () => ({
  CostChart: ({ data }: any) => (
    <div data-testid="cost-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/hooks/api/useAnalysis', () => ({
  useDashboardSummary: (versionId: string) => ({
    data: versionId ? mockDashboardData : null,
    isLoading: false,
  }),
  useRecentActivity: (limit: number) => ({
    data: mockActivitiesData,
  }),
  useSystemAlerts: (versionId: string) => ({
    data: versionId ? mockAlertsData : null,
  }),
}))

// Mock Recharts
vi.mock('recharts', () => ({
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => null,
  Cell: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Legend: () => null,
  Tooltip: () => null,
}))

describe('Dashboard Route', () => {
  const DashboardPage = DashboardRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockDashboardData = {
      total_students: 1250,
      total_classes: 52,
      total_teachers_fte: 75.5,
      total_revenue_sar: 42500000,
      total_costs_sar: 39100000,
      net_result_sar: 3400000,
      operating_margin_pct: 8.0,
    }
    mockActivitiesData = [
      {
        id: '1',
        description: 'Budget version created',
        timestamp: '2025-01-15T10:00:00Z',
      },
      {
        id: '2',
        description: 'Enrollment data updated',
        timestamp: '2025-01-15T09:30:00Z',
      },
    ]
    mockAlertsData = [
      {
        id: '1',
        severity: 'WARNING',
        message: 'Class size exceeds target for Grade 6',
      },
    ]
  })

  describe('Page structure', () => {
    it('renders within MainLayout', () => {
      render(<DashboardPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('renders within PageContainer with correct title', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Overview of budget planning and key metrics')).toBeInTheDocument()
    })
  })

  describe('Budget version selector', () => {
    it('renders budget version selector', () => {
      render(<DashboardPage />)

      expect(screen.getByTestId('budget-version-selector')).toBeInTheDocument()
    })

    it('shows create button', () => {
      render(<DashboardPage />)

      expect(screen.getByTestId('create-button')).toBeInTheDocument()
    })

    it('allows selecting a version', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      expect(select).toHaveValue('v1')
    })
  })

  describe('Summary cards', () => {
    it('shows loading state when no version selected', () => {
      render(<DashboardPage />)

      // Summary cards should not be visible without a version
      expect(screen.queryByTestId('summary-card-total-students')).not.toBeInTheDocument()
    })

    it('displays summary cards when version selected', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-students')).toBeInTheDocument()
      })
    })

    it('displays total students card', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const card = screen.getByTestId('summary-card-total-students')
        expect(card).toHaveTextContent('Total Students')
        expect(card).toHaveTextContent('1,250')
        expect(card).toHaveTextContent('Enrolled')
      })
    })

    it('displays total classes card', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const card = screen.getByTestId('summary-card-total-classes')
        expect(card).toHaveTextContent('Total Classes')
        expect(card).toHaveTextContent('52')
        expect(card).toHaveTextContent('Active')
      })
    })

    it('displays total teachers card', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const card = screen.getByTestId('summary-card-total-teachers')
        expect(card).toHaveTextContent('Total Teachers')
        expect(card).toHaveTextContent('75.5')
        expect(card).toHaveTextContent('FTE')
      })
    })

    it('displays total revenue card with formatted currency', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const card = screen.getByTestId('summary-card-total-revenue')
        expect(card).toHaveTextContent('Total Revenue')
        // Currency formatting varies, so just check it contains SAR
        expect(card).toHaveTextContent(/SAR|42/)
      })
    })
  })

  describe('Charts', () => {
    it('displays enrollment chart when version selected', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('enrollment-chart')).toBeInTheDocument()
      })
    })

    it('displays revenue chart when version selected', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
      })
    })

    it('displays cost chart when version selected', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('cost-chart')).toBeInTheDocument()
      })
    })

    it('displays nationality pie chart', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
      })
    })
  })

  describe('Activity feed', () => {
    it('displays recent activity', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('activity-feed')).toBeInTheDocument()
      })
    })

    it('shows activity items', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        const activities = screen.getAllByTestId('activity-item')
        expect(activities).toHaveLength(2)
        expect(activities[0]).toHaveTextContent('Budget version created')
        expect(activities[1]).toHaveTextContent('Enrollment data updated')
      })
    })
  })

  describe('Real-world use cases', () => {
    it('displays full dashboard for finance director', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      // Select a budget version
      const select = screen.getByTestId('version-select')
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        // Verify all summary cards appear
        expect(screen.getByTestId('summary-card-total-students')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-total-classes')).toBeInTheDocument()
        expect(screen.getByTestId('summary-card-total-teachers')).toBeInTheDocument()

        // Verify charts appear
        expect(screen.getByTestId('enrollment-chart')).toBeInTheDocument()
        expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
        expect(screen.getByTestId('cost-chart')).toBeInTheDocument()

        // Verify activity feed
        expect(screen.getByTestId('activity-feed')).toBeInTheDocument()
      })
    })

    it('handles empty state when no data available', () => {
      mockDashboardData = null

      render(<DashboardPage />)

      // Should show initial state without summary cards
      expect(screen.queryByTestId('summary-card-total-students')).not.toBeInTheDocument()
    })

    it('allows switching between budget versions', async () => {
      const user = userEvent.setup()

      render(<DashboardPage />)

      const select = screen.getByTestId('version-select')

      // Select first version
      await user.selectOptions(select, 'v1')

      await waitFor(() => {
        expect(screen.getByTestId('summary-card-total-students')).toBeInTheDocument()
      })

      // Switch to second version
      await user.selectOptions(select, 'v2')

      expect(select).toHaveValue('v2')
    })
  })

  describe('Route configuration', () => {
    it('requires authentication', () => {
      expect(DashboardRoute.beforeLoad).toBeDefined()
    })

    it('has correct path', () => {
      expect(DashboardRoute.path).toBe('/dashboard')
    })
  })
})
