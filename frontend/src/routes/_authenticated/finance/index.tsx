/**
 * Finance Module Dashboard
 *
 * Overview page for the Finance module showing:
 * - Planning workflow progress (Revenue → Personnel → Operating → CapEx → Consolidation)
 * - Key metrics (Revenue, Costs, Net Result, Variance)
 * - Attention items (Budget overruns, shortfalls)
 * - Quick actions (Review budget, Consolidate, Statements)
 */

import { createFileRoute } from '@tanstack/react-router'
import {
  TrendingUp,
  Users,
  Building,
  HardDrive,
  FileSpreadsheet,
  FileText,
  Calculator,
} from 'lucide-react'
import {
  ModuleDashboard,
  PlanningWorkflowProgress,
  MetricsPanel,
  AttentionPanel,
  QuickActionsBar,
  type WorkflowStep,
  type Metric,
  type AttentionItem,
  type QuickAction,
} from '@/components/dashboard'

export const Route = createFileRoute('/_authenticated/finance/')({
  component: FinanceDashboard,
})

/**
 * Mock data - In production, this would come from API endpoints
 */

const workflowSteps: WorkflowStep[] = [
  {
    id: 'revenue',
    title: 'Revenue',
    metric: '45.2M',
    status: 'complete',
    icon: TrendingUp,
  },
  {
    id: 'personnel',
    title: 'Personnel',
    metric: '32.1M',
    status: 'complete',
    icon: Users,
  },
  {
    id: 'operating',
    title: 'Operating',
    metric: '8.5M',
    status: 'in-progress',
    icon: Building,
  },
  {
    id: 'capex',
    title: 'CapEx',
    metric: '2.8M',
    status: 'pending',
    icon: HardDrive,
  },
  {
    id: 'consolidation',
    title: 'Consolidate',
    status: 'pending',
    icon: FileSpreadsheet,
  },
]

const metrics: Metric[] = [
  {
    id: 'total-revenue',
    label: 'Total Revenue',
    value: '45.2M',
    unit: 'SAR',
    trend: 'up',
    trendValue: '+5.3%',
    color: 'success',
  },
  {
    id: 'total-costs',
    label: 'Total Costs',
    value: '45.3M',
    unit: 'SAR',
    trend: 'up',
    trendValue: '+6.1%',
    color: 'warning',
  },
  {
    id: 'net-result',
    label: 'Net Result',
    value: '-120K',
    unit: 'SAR',
    trend: 'down',
    trendValue: 'Deficit',
    color: 'error',
  },
  {
    id: 'variance',
    label: 'vs Budget',
    value: '-2.5%',
    trend: 'down',
    trendValue: 'Under plan',
    secondaryLabel: 'Abs',
    secondaryValue: '-1.2M SAR',
  },
]

const attentionItems: AttentionItem[] = [
  {
    id: 'deficit',
    title: 'Budget shows deficit of 120K SAR',
    description: 'Operating costs exceed budget by 3.2%',
    severity: 'critical',
    link: '/finance/consolidation',
  },
  {
    id: 'revenue-shortfall',
    title: 'Revenue shortfall in Q3',
    description: 'Projected enrollment lower than expected',
    severity: 'warning',
    link: '/finance/revenue',
  },
  {
    id: 'capex-pending',
    title: 'CapEx planning incomplete',
    description: 'IT infrastructure and equipment not finalized',
    severity: 'info',
    link: '/finance/capex',
  },
]

const quickActions: QuickAction[] = [
  {
    id: 'review-budget',
    label: 'Review Budget',
    icon: FileSpreadsheet,
    variant: 'primary',
    link: '/finance/consolidation',
  },
  {
    id: 'consolidate',
    label: 'Consolidate',
    icon: Calculator,
    variant: 'secondary',
    link: '/finance/consolidation',
  },
  {
    id: 'statements',
    label: 'Statements',
    icon: FileText,
    variant: 'outline',
    link: '/finance/statements',
  },
  {
    id: 'export',
    label: 'Export',
    icon: FileText,
    variant: 'outline',
  },
]

/**
 * FinanceDashboard renders module content only.
 * Navigation (ModuleHeader + WorkflowTabs) is provided by ModuleLayout.
 * Title/description shown in ModuleHeader, not here.
 */
function FinanceDashboard() {
  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <ModuleDashboard
        workflowProgress={
          <PlanningWorkflowProgress
            steps={workflowSteps}
            title="Financial Planning Progress"
            progress={60}
          />
        }
        metricsPanel={<MetricsPanel metrics={metrics} title="Key Metrics" columns={2} />}
        attentionPanel={<AttentionPanel items={attentionItems} title="Needs Attention" />}
        quickActions={<QuickActionsBar actions={quickActions} title="Quick Actions" />}
      />
    </div>
  )
}
