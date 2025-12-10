/**
 * Workforce Module Dashboard
 *
 * Overview page for the Workforce module showing:
 * - Planning workflow progress (Employees → Salaries → AEFE → DHG)
 * - Key metrics (Staff count, AEFE positions, FTE, Payroll)
 * - Attention items (FTE gaps, unfilled positions)
 * - Quick actions (Add employee, Run DHG, Fill AEFE)
 */

import { createFileRoute } from '@tanstack/react-router'
import { Users, UserPlus, Calculator, FileText, Briefcase, DollarSign } from 'lucide-react'
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

export const Route = createFileRoute('/_authenticated/workforce/')({
  component: WorkforceDashboard,
})

/**
 * Mock data - In production, this would come from API endpoints
 */

const workflowSteps: WorkflowStep[] = [
  {
    id: 'employees',
    title: 'Employees',
    metric: '123',
    status: 'complete',
    icon: Users,
  },
  {
    id: 'salaries',
    title: 'Salaries',
    metric: '4.2M',
    status: 'complete',
    icon: DollarSign,
  },
  {
    id: 'aefe',
    title: 'AEFE',
    metric: '22/28',
    status: 'in-progress',
    icon: Briefcase,
  },
  {
    id: 'dhg',
    title: 'DHG',
    metric: '-2 FTE',
    status: 'warning',
    icon: Calculator,
  },
]

const metrics: Metric[] = [
  {
    id: 'total-staff',
    label: 'Total Staff',
    value: 123,
    trend: 'up',
    trendValue: '+5 vs LY',
    secondaryLabel: 'Teachers',
    secondaryValue: '98',
  },
  {
    id: 'aefe-positions',
    label: 'AEFE Positions',
    value: '22/28',
    progress: 78,
    secondaryLabel: 'Detached',
    secondaryValue: '22/24',
  },
  {
    id: 'total-fte',
    label: 'Total FTE',
    value: '118.5',
    trend: 'down',
    trendValue: '-2.0 gap',
    color: 'warning',
  },
  {
    id: 'annual-payroll',
    label: 'Annual Payroll',
    value: '4.2M',
    unit: 'SAR',
    trend: 'up',
    trendValue: '+8.5%',
  },
]

const attentionItems: AttentionItem[] = [
  {
    id: 'fte-gap',
    title: 'FTE Gap: -2.0',
    description: 'Need 2 additional FTE for secondary subjects',
    severity: 'warning',
    link: '/workforce/dhg/gap-analysis',
  },
  {
    id: 'aefe-unfilled',
    title: '6 AEFE positions unfilled',
    description: 'PRRD budget available for 6 more detached positions',
    severity: 'info',
    link: '/workforce/aefe-positions',
  },
  {
    id: 'eos-update',
    title: 'EOS provisions need update',
    description: '3 employees reached 5-year threshold',
    severity: 'info',
    link: '/workforce/salaries',
  },
]

const quickActions: QuickAction[] = [
  {
    id: 'add-employee',
    label: 'Add Employee',
    icon: UserPlus,
    variant: 'primary',
    link: '/workforce/employees',
  },
  {
    id: 'run-dhg',
    label: 'Run DHG',
    icon: Calculator,
    variant: 'secondary',
    link: '/workforce/dhg/planning',
  },
  {
    id: 'fill-aefe',
    label: 'Fill AEFE',
    icon: Briefcase,
    variant: 'outline',
    link: '/workforce/aefe-positions',
  },
  {
    id: 'export',
    label: 'Export',
    icon: FileText,
    variant: 'outline',
  },
]

/**
 * WorkforceDashboard renders module content only.
 * Navigation (SmartHeader + ModuleDock) is provided by _authenticated.tsx layout.
 * NO CockpitLayout wrapper here to avoid double navigation.
 */
function WorkforceDashboard() {
  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <ModuleDashboard
        workflowProgress={
          <PlanningWorkflowProgress
            steps={workflowSteps}
            title="Workforce Planning Progress"
            progress={75}
          />
        }
        metricsPanel={<MetricsPanel metrics={metrics} title="Key Metrics" columns={2} />}
        attentionPanel={<AttentionPanel items={attentionItems} title="Needs Attention" />}
        quickActions={<QuickActionsBar actions={quickActions} title="Quick Actions" />}
      />
    </div>
  )
}
