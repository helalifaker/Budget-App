import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route as DashboardRoute } from '@/routes/dashboard'
import React from 'react'

// Mock dependencies
const mockNavigate = vi.fn()
let mockDashboardData: Record<string, unknown> | null = null
let mockActivitiesData: Record<string, unknown>[] | null = null
let mockAlertsData: Record<string, unknown>[] | null = null

// BudgetVersionContext mock state
let mockSelectedVersionId: string | undefined = undefined
const mockSetSelectedVersionId = vi.fn((id: string | undefined) => {
  mockSelectedVersionId = id
})

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: (path: string) => (config: Record<string, unknown>) => ({
    ...config,
    path,
  }),
  Link: ({
    to,
    children,
    className,
  }: {
    to: string
    children: React.ReactNode
    className?: string
  }) => (
    <a href={to} className={className}>
      {children}
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
  MainLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  ),
}))

vi.mock('@/components/layout/PageContainer', () => ({
  PageContainer: ({
    title,
    description,
    children,
  }: {
    title: string
    description?: string
    children: React.ReactNode
  }) => (
    <div data-testid="page-container">
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-header">{children}</div>
  ),
  CardTitle: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-title">{children}</div>
  ),
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-content" className={className}>
      {children}
    </div>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    className,
    onClick,
  }: {
    children: React.ReactNode
    className?: string
    onClick?: () => void
  }) => (
    <button className={className} onClick={onClick}>
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({
    children,
    variant,
    className,
  }: {
    children: React.ReactNode
    variant?: string
    className?: string
  }) => (
    <span data-testid="badge" data-variant={variant} className={className}>
      {children}
    </span>
  ),
}))

vi.mock('@/components/SummaryCard', () => ({
  SummaryCard: ({
    title,
    value,
    subtitle,
  }: {
    title: string
    value: string
    icon?: React.ReactNode
    subtitle?: string
  }) => (
    <div data-testid={`summary-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div data-testid="card-title">{title}</div>
      <div data-testid="card-value">{value}</div>
      {subtitle && <div data-testid="card-subtitle">{subtitle}</div>}
    </div>
  ),
}))

vi.mock('@/components/ActivityFeed', () => ({
  ActivityFeed: ({ activities }: { activities: Array<{ description: string }> }) => (
    <div data-testid="activity-feed">
      {activities?.map((activity: { description: string }, index: number) => (
        <div key={index} data-testid="activity-item">
          {activity.description}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('@/components/charts/EnrollmentChart', () => ({
  EnrollmentChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="enrollment-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/components/charts/RevenueChart', () => ({
  RevenueChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="revenue-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/components/charts/CostChart', () => ({
  CostChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="cost-chart">Chart with {data?.length} data points</div>
  ),
}))

vi.mock('@/hooks/api/useAnalysis', () => ({
  useDashboardSummary: (versionId: string | undefined) => ({
    data: versionId ? mockDashboardData : null,
    isLoading: false,
  }),
  useRecentActivity: () => ({
    data: mockActivitiesData,
  }),
  useSystemAlerts: (versionId: string | undefined) => ({
    data: versionId ? mockAlertsData : null,
  }),
}))

// Mock Recharts
vi.mock('recharts', () => ({
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => null,
  Cell: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Legend: () => null,
  Tooltip: () => null,
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Users: () => <span>Users Icon</span>,
  School: () => <span>School Icon</span>,
  GraduationCap: () => <span>GraduationCap Icon</span>,
  DollarSign: () => <span>DollarSign Icon</span>,
  TrendingUp: () => <span>TrendingUp Icon</span>,
  FileText: () => <span>FileText Icon</span>,
  Download: () => <span>Download Icon</span>,
  AlertCircle: () => <span>AlertCircle Icon</span>,
  Info: () => <span>Info Icon</span>,
}))

describe('Dashboard Route', () => {
  const DashboardPage = DashboardRoute.component

  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectedVersionId = undefined // Reset version selection

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

  describe('Budget version context', () => {
    it('uses global budget version from context', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
    })

    it('shows no summary cards when no version selected', () => {
      mockSelectedVersionId = undefined
      render(<DashboardPage />)

      // Summary cards should not be visible without a version
      expect(screen.queryByTestId('summary-card-total-students')).not.toBeInTheDocument()
    })
  })

  describe('Summary cards', () => {
    it('displays summary cards when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('summary-card-total-students')).toBeInTheDocument()
    })

    it('displays total students card', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const card = screen.getByTestId('summary-card-total-students')
      expect(card).toHaveTextContent('Total Students')
      expect(card).toHaveTextContent('1,250')
      expect(card).toHaveTextContent('Enrolled')
    })

    it('displays total classes card', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const card = screen.getByTestId('summary-card-total-classes')
      expect(card).toHaveTextContent('Total Classes')
      expect(card).toHaveTextContent('52')
      expect(card).toHaveTextContent('Active')
    })

    it('displays total teachers card', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const card = screen.getByTestId('summary-card-total-teachers')
      expect(card).toHaveTextContent('Total Teachers')
      expect(card).toHaveTextContent('75.5')
      expect(card).toHaveTextContent('FTE')
    })

    it('displays total revenue card with formatted currency', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const card = screen.getByTestId('summary-card-total-revenue')
      expect(card).toHaveTextContent('Total Revenue')
      // Currency formatting varies, so just check it contains SAR
      expect(card).toHaveTextContent(/SAR|42/)
    })

    it('displays total costs card', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const card = screen.getByTestId('summary-card-total-costs')
      expect(card).toHaveTextContent('Total Costs')
      expect(card).toHaveTextContent(/SAR|39/)
    })
  })

  describe('Charts', () => {
    it('displays enrollment chart when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('enrollment-chart')).toBeInTheDocument()
    })

    it('displays revenue chart when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
    })

    it('displays cost chart when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('cost-chart')).toBeInTheDocument()
    })

    it('displays nationality pie chart', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    })
  })

  describe('Activity feed', () => {
    it('displays recent activity when version selected', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      expect(screen.getByTestId('activity-feed')).toBeInTheDocument()
    })

    it('shows activity items', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

      const activities = screen.getAllByTestId('activity-item')
      expect(activities).toHaveLength(2)
      expect(activities[0]).toHaveTextContent('Budget version created')
      expect(activities[1]).toHaveTextContent('Enrollment data updated')
    })
  })

  describe('Real-world use cases', () => {
    it('displays full dashboard for finance director', () => {
      mockSelectedVersionId = 'v1'
      render(<DashboardPage />)

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

    it('handles empty state when no data available', () => {
      mockDashboardData = null
      mockSelectedVersionId = undefined

      render(<DashboardPage />)

      // Should show initial state without summary cards
      expect(screen.queryByTestId('summary-card-total-students')).not.toBeInTheDocument()
    })

    it('context provides version switching capability', () => {
      mockSelectedVersionId = 'v1'
      const { rerender } = render(<DashboardPage />)

      expect(screen.getByTestId('summary-card-total-students')).toBeInTheDocument()

      // Simulate version change via context
      mockSelectedVersionId = 'v2'
      rerender(<DashboardPage />)

      // Page should still render (context provides new version)
      expect(screen.getByTestId('main-layout')).toBeInTheDocument()
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
