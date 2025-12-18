/**
 * Enrollment Module Dashboard
 *
 * Overview page for the Enrollment module showing:
 * - Planning workflow progress (Projections → Class Structure → Validation)
 * - Key metrics (Students, Classes, Average size, Growth)
 * - Attention items (Capacity issues, imbalanced classes)
 * - Quick actions (Update projections, Form classes)
 */

import { createFileRoute } from '@tanstack/react-router'
import { LayoutGrid, TrendingUp, FileText, Settings } from 'lucide-react'
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

export const Route = createFileRoute('/_authenticated/enrollment/')({
  component: EnrollmentDashboard,
})

/**
 * Mock data - In production, this would come from API endpoints
 */

const workflowSteps: WorkflowStep[] = [
  {
    id: 'projections',
    title: 'Projections',
    metric: '1,245',
    status: 'complete',
    icon: TrendingUp,
  },
  {
    id: 'class-structure',
    title: 'Classes',
    metric: '48',
    status: 'in-progress',
    icon: LayoutGrid,
  },
  {
    id: 'validation',
    title: 'Validation',
    status: 'pending',
  },
]

const metrics: Metric[] = [
  {
    id: 'total-students',
    label: 'Total Students',
    value: '1,245',
    trend: 'up',
    trendValue: '+3.2% vs LY',
    secondaryLabel: 'Target',
    secondaryValue: '1,280',
  },
  {
    id: 'total-classes',
    label: 'Total Classes',
    value: 48,
    secondaryLabel: 'Sections',
    secondaryValue: '96',
  },
  {
    id: 'avg-class-size',
    label: 'Avg Class Size',
    value: '25.9',
    trend: 'neutral',
    trendValue: 'Target: 26',
    progress: 99,
  },
  {
    id: 'growth-rate',
    label: 'Growth Rate',
    value: '+3.2%',
    trend: 'up',
    trendValue: 'vs LY',
    color: 'success',
  },
]

const attentionItems: AttentionItem[] = [
  {
    id: 'over-capacity',
    title: '2 classes over max capacity',
    description: 'CE2-A and CM1-B exceed 28 students',
    severity: 'warning',
    link: '/students/class-structure',
  },
  {
    id: 'under-min',
    title: '1 class under minimum',
    description: 'Terminale S has only 12 students (min: 15)',
    severity: 'info',
    link: '/students/class-structure',
  },
]

const quickActions: QuickAction[] = [
  {
    id: 'update-projections',
    label: 'Update Projections',
    icon: TrendingUp,
    variant: 'primary',
    link: '/students/planning',
  },
  {
    id: 'form-classes',
    label: 'Form Classes',
    icon: LayoutGrid,
    variant: 'secondary',
    link: '/students/class-structure',
  },
  {
    id: 'settings',
    label: 'Class Settings',
    icon: Settings,
    variant: 'outline',
    link: '/settings/class-sizes',
  },
  {
    id: 'export',
    label: 'Export',
    icon: FileText,
    variant: 'outline',
  },
]

/**
 * EnrollmentDashboard renders module content only.
 * Navigation (SmartHeader + ModuleDock) is provided by _authenticated.tsx layout.
 * NO CockpitLayout wrapper here to avoid double navigation.
 */
function EnrollmentDashboard() {
  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <ModuleDashboard
        workflowProgress={
          <PlanningWorkflowProgress steps={workflowSteps} title="Enrollment Planning Progress" />
        }
        metricsPanel={<MetricsPanel metrics={metrics} title="Key Metrics" columns={2} />}
        attentionPanel={
          <AttentionPanel
            items={attentionItems}
            title="Needs Attention"
            emptyMessage="All classes are within capacity limits"
          />
        }
        quickActions={<QuickActionsBar actions={quickActions} title="Quick Actions" />}
      />
    </div>
  )
}
