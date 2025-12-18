/**
 * Consolidation Readiness Checklist Page
 *
 * Provides a comprehensive checklist view of all planning steps with validation
 * status, key metrics, and readiness indicators before budget finalization.
 *
 * Features:
 * - Step-by-step completion status for all 6 planning modules
 * - Key metrics summary (total students, FTE, revenue, costs)
 * - KPI indicators (operating margin, personnel ratio, capacity)
 * - Navigation links to incomplete steps
 * - Finalize budget action when ready
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { usePlanningProgress } from '@/hooks/api/usePlanningProgress'
import { useConsolidationSummary, useSubmitForApproval } from '@/hooks/api/useConsolidation'
import { useVersion } from '@/contexts/VersionContext'
import { STEP_METADATA, type StepProgress } from '@/types/planning-progress'
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Lock,
  Circle,
  Users,
  Calculator,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Building2,
  Grid3x3,
  ArrowRight,
  FileCheck,
  ChevronRight,
  Info,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/_authenticated/consolidation/checklist')({
  component: ChecklistPage,
})

// Icon mapping for step icons
const STEP_ICONS: Record<string, React.ReactNode> = {
  Users: <Users className="w-5 h-5" />,
  Grid3x3: <Grid3x3 className="w-5 h-5" />,
  Calculator: <Calculator className="w-5 h-5" />,
  DollarSign: <DollarSign className="w-5 h-5" />,
  TrendingDown: <TrendingDown className="w-5 h-5" />,
  Building2: <Building2 className="w-5 h-5" />,
}

// Status icon mapping
function getStatusIcon(status: StepProgress['status']) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-6 h-6 text-success-600" />
    case 'in_progress':
      return <AlertTriangle className="w-6 h-6 text-warning-600" />
    case 'error':
      return <AlertCircle className="w-6 h-6 text-error-600" />
    case 'blocked':
      return <Lock className="w-6 h-6 text-text-tertiary" />
    case 'not_started':
    default:
      return <Circle className="w-6 h-6 text-sand-400" />
  }
}

// Status badge variant mapping
function getStatusBadgeVariant(
  status: StepProgress['status']
): 'success' | 'warning' | 'destructive' | 'secondary' | 'default' {
  switch (status) {
    case 'completed':
      return 'success'
    case 'in_progress':
      return 'warning'
    case 'error':
      return 'destructive'
    case 'blocked':
      return 'secondary'
    case 'not_started':
    default:
      return 'default'
  }
}

// Status text mapping
function getStatusText(status: StepProgress['status']): string {
  switch (status) {
    case 'completed':
      return 'Complete'
    case 'in_progress':
      return 'In Progress'
    case 'error':
      return 'Error'
    case 'blocked':
      return 'Blocked'
    case 'not_started':
    default:
      return 'Not Started'
  }
}

// Format compact number for display
function formatCompact(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(0)}K`
  }
  return value.toString()
}

function ChecklistPage() {
  const { selectedVersionId } = useVersion()

  const { data: progress, isLoading: progressLoading } = usePlanningProgress(selectedVersionId)
  const { data: summary, isLoading: summaryLoading } = useConsolidationSummary(selectedVersionId)
  const submitMutation = useSubmitForApproval()

  const isLoading = progressLoading || summaryLoading

  // Calculate readiness
  const isReady = progress?.completed_steps === progress?.total_steps
  const completionPercentage = progress?.overall_progress ?? 0
  const completedSteps = progress?.completed_steps ?? 0
  const totalSteps = progress?.total_steps ?? 6

  // Calculate KPIs from summary
  const operatingMargin = summary
    ? ((summary.operating_result / summary.total_revenue) * 100).toFixed(1)
    : '0.0'

  const personnelRatio = summary
    ? (
        ((summary.total_expenses - (summary.total_capex || 0)) / summary.total_revenue) *
        100
      ).toFixed(1)
    : '0.0'

  // KPI targets and status
  const marginTarget = 5 // 5% operating margin target
  const marginStatus = parseFloat(operatingMargin) >= marginTarget ? 'good' : 'warning'

  const personnelTarget = { min: 60, max: 70 } // 60-70% is typical
  const personnelStatus =
    parseFloat(personnelRatio) >= personnelTarget.min &&
    parseFloat(personnelRatio) <= personnelTarget.max
      ? 'good'
      : 'warning'

  const handleFinalize = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }

    if (!isReady) {
      toastMessages.error.custom('Please complete all planning steps before finalizing')
      return
    }

    try {
      await submitMutation.mutateAsync(selectedVersionId)
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <PageContainer
      title="Budget Consolidation Checklist"
      description="Review planning progress and finalize your budget"
    >
      <div className="space-y-6">
        {selectedVersionId ? (
          <>
            {/* Overall Progress Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-primary" />
                      Budget Readiness
                    </CardTitle>
                    <CardDescription>
                      {completedSteps} of {totalSteps} planning steps completed
                    </CardDescription>
                  </div>
                  <Badge variant={isReady ? 'success' : 'warning'} className="text-sm px-3 py-1">
                    {isReady ? 'Ready to Finalize' : 'In Progress'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Progress value={completionPercentage} className="h-3" />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{completionPercentage.toFixed(0)}% Complete</span>
                    <span>{totalSteps - completedSteps} steps remaining</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Planning Steps Checklist */}
            <Card>
              <CardHeader>
                <CardTitle>Planning Steps</CardTitle>
                <CardDescription>Complete all required steps before consolidation</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {isLoading ? (
                    <div className="py-8 text-center text-muted-foreground">
                      Loading checklist...
                    </div>
                  ) : (
                    progress?.steps.map((step) => {
                      const metadata = STEP_METADATA[step.step_id]
                      const icon = STEP_ICONS[metadata?.icon] || <Circle className="w-5 h-5" />

                      return (
                        <div
                          key={step.step_id}
                          className={cn(
                            'flex items-center justify-between p-4 rounded-lg border transition-colors',
                            step.status === 'completed'
                              ? 'bg-success-50 border-success-200'
                              : step.status === 'in_progress'
                                ? 'bg-warning-50 border-warning-200'
                                : step.status === 'blocked' || step.status === 'error'
                                  ? 'bg-error-50 border-error-200'
                                  : 'bg-subtle border-border-light hover:bg-subtle'
                          )}
                        >
                          <div className="flex items-center gap-4">
                            {getStatusIcon(step.status)}
                            <div className="flex items-center gap-3">
                              <div
                                className={cn(
                                  'p-2 rounded-lg',
                                  step.status === 'completed'
                                    ? 'bg-success-100 text-success-700'
                                    : 'bg-white text-text-secondary'
                                )}
                              >
                                {icon}
                              </div>
                              <div>
                                <h4 className="font-medium text-text-primary">
                                  Step {step.step_number}: {metadata?.title}
                                </h4>
                                <p className="text-sm text-text-secondary">
                                  {metadata?.description}
                                </p>
                                {/* Show key metrics if available */}
                                {Object.keys(step.metrics).length > 0 && (
                                  <div className="flex gap-3 mt-1 text-xs text-text-tertiary">
                                    {Object.entries(step.metrics).map(([key, value]) => (
                                      <span key={key}>
                                        {key.replace(/_/g, ' ')}: <strong>{value}</strong>
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <Badge variant={getStatusBadgeVariant(step.status)}>
                              {getStatusText(step.status)}
                            </Badge>
                            {step.status !== 'completed' && metadata?.route && (
                              <Link to={metadata.route}>
                                <Button size="sm" variant="ghost">
                                  <span className="sr-only">Go to {metadata.title}</span>
                                  <ChevronRight className="w-4 h-4" />
                                </Button>
                              </Link>
                            )}
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Financial Summary */}
            {summary && (
              <Card>
                <CardHeader>
                  <CardTitle>Financial Summary</CardTitle>
                  <CardDescription>Key budget metrics at a glance</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-success-50 rounded-lg border border-success-200">
                      <div className="flex items-center gap-2 text-success-700 mb-1">
                        <TrendingUp className="w-4 h-4" />
                        <span className="text-sm font-medium">Total Revenue</span>
                      </div>
                      <div className="text-2xl font-bold text-success-800">
                        {formatCompact(summary.total_revenue)} SAR
                      </div>
                      <div className="text-xs text-success-600">
                        {summary.revenue_count} line items
                      </div>
                    </div>

                    <div className="p-4 bg-error-50 rounded-lg border border-error-200">
                      <div className="flex items-center gap-2 text-error-700 mb-1">
                        <TrendingDown className="w-4 h-4" />
                        <span className="text-sm font-medium">Total Expenses</span>
                      </div>
                      <div className="text-2xl font-bold text-error-800">
                        {formatCompact(summary.total_expenses)} SAR
                      </div>
                      <div className="text-xs text-error-600">
                        {summary.expense_count} line items
                      </div>
                    </div>

                    <div className="p-4 bg-info-50 rounded-lg border border-info-200">
                      <div className="flex items-center gap-2 text-info-700 mb-1">
                        <Building2 className="w-4 h-4" />
                        <span className="text-sm font-medium">CapEx</span>
                      </div>
                      <div className="text-2xl font-bold text-info-800">
                        {formatCompact(summary.total_capex)} SAR
                      </div>
                      <div className="text-xs text-info-600">{summary.capex_count} items</div>
                    </div>

                    <div
                      className={cn(
                        'p-4 rounded-lg border',
                        summary.operating_result >= 0
                          ? 'bg-success-50 border-success-200'
                          : 'bg-error-50 border-error-200'
                      )}
                    >
                      <div
                        className={cn(
                          'flex items-center gap-2 mb-1',
                          summary.operating_result >= 0 ? 'text-success-700' : 'text-error-700'
                        )}
                      >
                        <DollarSign className="w-4 h-4" />
                        <span className="text-sm font-medium">Operating Result</span>
                      </div>
                      <div
                        className={cn(
                          'text-2xl font-bold',
                          summary.operating_result >= 0 ? 'text-success-800' : 'text-error-800'
                        )}
                      >
                        {formatCompact(summary.operating_result)} SAR
                      </div>
                      <div
                        className={cn(
                          'text-xs',
                          summary.operating_result >= 0 ? 'text-success-600' : 'text-error-600'
                        )}
                      >
                        {summary.operating_result >= 0 ? 'Surplus' : 'Deficit'}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* KPI Indicators */}
            {summary && (
              <Card>
                <CardHeader>
                  <CardTitle>Key Performance Indicators</CardTitle>
                  <CardDescription>Budget health metrics against targets</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Operating Margin */}
                    <div
                      className={cn(
                        'p-4 rounded-lg border',
                        marginStatus === 'good'
                          ? 'bg-success-50 border-success-200'
                          : 'bg-warning-50 border-warning-200'
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-text-secondary">
                          Operating Margin
                        </span>
                        {marginStatus === 'good' ? (
                          <CheckCircle2 className="w-5 h-5 text-success-600" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-warning-600" />
                        )}
                      </div>
                      <div className="text-3xl font-bold text-text-primary">{operatingMargin}%</div>
                      <div className="text-xs text-text-tertiary mt-1">
                        Target: {'>'}
                        {marginTarget}%
                      </div>
                    </div>

                    {/* Personnel Ratio */}
                    <div
                      className={cn(
                        'p-4 rounded-lg border',
                        personnelStatus === 'good'
                          ? 'bg-success-50 border-success-200'
                          : 'bg-warning-50 border-warning-200'
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-text-secondary">
                          Personnel Ratio
                        </span>
                        {personnelStatus === 'good' ? (
                          <CheckCircle2 className="w-5 h-5 text-success-600" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-warning-600" />
                        )}
                      </div>
                      <div className="text-3xl font-bold text-text-primary">{personnelRatio}%</div>
                      <div className="text-xs text-text-tertiary mt-1">
                        Typical: {personnelTarget.min}-{personnelTarget.max}%
                      </div>
                    </div>

                    {/* Budget Status */}
                    <div className="p-4 rounded-lg border bg-twilight-50 border-twilight-200">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-text-secondary">
                          Budget Status
                        </span>
                        <Info className="w-5 h-5 text-text-tertiary" />
                      </div>
                      <div className="text-lg font-bold text-text-primary capitalize">
                        {summary.status.toLowerCase().replace('_', ' ')}
                      </div>
                      <div className="text-xs text-text-tertiary mt-1">
                        FY {summary.fiscal_year}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between items-center p-4 bg-subtle rounded-lg border border-border-light">
              <Link to="/enrollment/projections">
                <Button variant="outline">
                  <ArrowRight className="w-4 h-4 mr-2 rotate-180" />
                  Back to Planning
                </Button>
              </Link>
              <div className="flex gap-3">
                <Link to="/consolidation/rollup">
                  <Button variant="outline">View Consolidated Budget</Button>
                </Link>
                <Button onClick={handleFinalize} disabled={!isReady || submitMutation.isPending}>
                  <FileCheck className="w-4 h-4 mr-2" />
                  {submitMutation.isPending ? 'Submitting...' : 'Finalize Budget'}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-text-secondary">
            Please select a version to view the consolidation checklist
          </div>
        )}
      </div>
    </PageContainer>
  )
}
