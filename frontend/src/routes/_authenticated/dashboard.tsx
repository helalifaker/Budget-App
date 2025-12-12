import { createFileRoute, Link } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { SummaryCard } from '@/components/SummaryCard'
import { EnrollmentChart } from '@/components/charts/EnrollmentChart'
import { RevenueChart } from '@/components/charts/RevenueChart'
import { CostChart } from '@/components/charts/CostChart'
import { ActivityFeed } from '@/components/ActivityFeed'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useDashboardSummary, useRecentActivity, useSystemAlerts } from '@/hooks/api/useAnalysis'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import {
  Users,
  School,
  GraduationCap,
  DollarSign,
  TrendingUp,
  FileText,
  Download,
  AlertCircle,
  Info,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

export const Route = createFileRoute('/_authenticated/dashboard')({
  beforeLoad: requireAuth,
  component: DashboardPage,
})

function DashboardPage() {
  const { selectedVersionId } = useBudgetVersion()

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary(selectedVersionId)
  const { data: activities } = useRecentActivity(10)
  const { data: alerts } = useSystemAlerts(selectedVersionId)

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value)
  }

  // Mock data for charts (to be replaced with real data from API)
  const enrollmentData = [
    { level: 'Maternelle', students: 120, capacity: 150 },
    { level: 'Élémentaire', students: 300, capacity: 350 },
    { level: 'Collège', students: 250, capacity: 280 },
    { level: 'Lycée', students: 180, capacity: 200 },
  ]

  // Premium color palette for charts - using theme CSS variables
  const nationalityData = [
    { category: 'French', amount: 450, color: 'var(--color-gold)' },
    { category: 'Saudi', amount: 280, color: 'var(--color-sage)' },
    { category: 'Other', amount: 120, color: 'var(--color-slate)' },
  ]

  const costData = [
    {
      period: 'Current',
      personnel: summary?.total_costs_sar ? summary.total_costs_sar * 0.7 : 0,
      operating: summary?.total_costs_sar ? summary.total_costs_sar * 0.3 : 0,
    },
  ]

  const revenueData = [
    {
      category: 'Tuition',
      amount: summary?.total_revenue_sar ? summary.total_revenue_sar * 0.85 : 0,
      color: 'var(--color-sage)',
    },
    {
      category: 'DAI',
      amount: summary?.total_revenue_sar ? summary.total_revenue_sar * 0.1 : 0,
      color: 'var(--color-gold)',
    },
    {
      category: 'Other',
      amount: summary?.total_revenue_sar ? summary.total_revenue_sar * 0.05 : 0,
      color: 'var(--color-slate)',
    },
  ]

  const alertColors = {
    INFO: 'bg-info-50 text-info-800 border-info-200',
    WARNING: 'bg-warning-50 text-warning-800 border-warning-200',
    ERROR: 'bg-error-50 text-error-800 border-error-200',
  }

  const alertIcons = {
    INFO: <Info className="w-4 h-4" />,
    WARNING: <AlertCircle className="w-4 h-4" />,
    ERROR: <AlertCircle className="w-4 h-4" />,
  }

  return (
    <PageContainer
      title="Command Center"
      description="Executive overview of budget planning and key metrics"
      compactHeader
    >
      <div className="space-y-5">
        {import.meta.env.DEV && (
          <div className="flex justify-end">
            <Button
              onClick={() => {
                throw new Error('Test Sentry error from dashboard')
              }}
              variant="outline"
              size="sm"
            >
              Test Sentry Error
            </Button>
          </div>
        )}

        {selectedVersionId && (
          <>
            {/* Summary Cards - Premium Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {summaryLoading ? (
                <div className="col-span-5 text-center py-8 text-text-secondary">
                  Loading summary...
                </div>
              ) : summary ? (
                <>
                  <SummaryCard
                    title="Total Students"
                    value={summary.total_students?.toLocaleString() || '0'}
                    icon={<Users className="w-4 h-4" />}
                    subtitle="Enrolled"
                    compact
                  />
                  <SummaryCard
                    title="Total Classes"
                    value={summary.total_classes?.toLocaleString() || '0'}
                    icon={<School className="w-4 h-4" />}
                    subtitle="Active"
                    compact
                  />
                  <SummaryCard
                    title="Total Teachers"
                    value={summary.total_teachers_fte?.toLocaleString() || '0'}
                    icon={<GraduationCap className="w-4 h-4" />}
                    subtitle="FTE"
                    compact
                  />
                  <SummaryCard
                    title="Total Revenue"
                    value={formatCurrency(summary.total_revenue_sar)}
                    icon={<DollarSign className="w-4 h-4" />}
                    valueClassName="text-success-600"
                    trend="up"
                    compact
                  />
                  <SummaryCard
                    title="Total Costs"
                    value={formatCurrency(summary.total_costs_sar)}
                    icon={<DollarSign className="w-4 h-4" />}
                    valueClassName="text-error-600"
                    compact
                  />
                </>
              ) : null}
            </div>

            {/* System Alerts */}
            {alerts && alerts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>System Alerts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border ${alertColors[alert.type]}`}
                      >
                        {alertIcons[alert.type]}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{alert.message}</p>
                          <p className="text-xs mt-1 opacity-75">
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <EnrollmentChart
                data={enrollmentData}
                title="Enrollment by Level"
                showCapacity={true}
              />

              <Card>
                <CardHeader>
                  <CardTitle>Enrollment by Nationality</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={nationalityData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }: { name?: string; percent?: number }) =>
                          `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                        }
                        outerRadius={80}
                        fill="var(--color-gold)"
                        dataKey="amount"
                      >
                        {nationalityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <CostChart data={costData} title="Cost Breakdown" />
              <RevenueChart data={revenueData} title="Revenue Breakdown" />
            </div>

            {/* Recent Activity & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                {activities && <ActivityFeed activities={activities} />}
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Link to="/configuration/versions">
                    <Button variant="outline" className="w-full justify-start">
                      <FileText className="w-4 h-4 mr-2" />
                      Create New Version
                    </Button>
                  </Link>
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    View Reports
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Download className="w-4 h-4 mr-2" />
                    Export Data
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    View KPIs
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Budget Health - Premium Card */}
            {summary && (
              <Card accent elevated>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-gold-600" />
                    Budget Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Net Income */}
                    <div className="p-4 rounded-xl bg-subtle/50">
                      <div className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        Net Income
                      </div>
                      <div
                        className={`text-2xl font-bold font-mono ${summary.net_result_sar >= 0 ? 'text-success-600' : 'text-error-600'}`}
                      >
                        {formatCurrency(summary.net_result_sar)}
                      </div>
                    </div>

                    {/* Operating Margin */}
                    <div className="p-4 rounded-xl bg-subtle/50">
                      <div className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        Operating Margin
                      </div>
                      <div className="text-2xl font-bold font-mono text-text-primary">
                        {summary.operating_margin_pct.toFixed(1)}%
                      </div>
                      <Badge
                        variant={summary.operating_margin_pct >= 5 ? 'default' : 'destructive'}
                        className="mt-2"
                      >
                        {summary.operating_margin_pct >= 5 ? 'Healthy' : 'Below Target'}
                      </Badge>
                    </div>

                    {/* Cost per Student */}
                    <div className="p-4 rounded-xl bg-subtle/50">
                      <div className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        Cost per Student
                      </div>
                      <div className="text-2xl font-bold font-mono text-text-primary">
                        {formatCurrency(
                          summary.total_students > 0
                            ? summary.total_costs_sar / summary.total_students
                            : 0
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </PageContainer>
  )
}
