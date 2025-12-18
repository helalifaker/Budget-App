/**
 * Configuration Module Dashboard
 *
 * Overview page for the Configuration module showing:
 * - Workflow progress (Versions → Uploads → System)
 * - Key metrics (Active versions, Last import, System status)
 * - Attention items (Pending imports, outdated configurations)
 * - Quick actions (Manage Versions, Import Data, System Settings)
 */

import { createFileRoute } from '@tanstack/react-router'
import { Settings, FileUp, Database, RefreshCw, Upload, Cog } from 'lucide-react'
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

export const Route = createFileRoute('/_authenticated/settings/')({
  component: ConfigurationDashboard,
})

/**
 * Mock data - In production, this would come from API endpoints
 */

const workflowSteps: WorkflowStep[] = [
  {
    id: 'versions',
    title: 'Versions',
    metric: '3',
    status: 'complete',
    icon: Database,
  },
  {
    id: 'uploads',
    title: 'Uploads',
    metric: '12',
    status: 'in-progress',
    icon: FileUp,
  },
  {
    id: 'system',
    title: 'System',
    status: 'complete',
    icon: Cog,
  },
]

const metrics: Metric[] = [
  {
    id: 'active-versions',
    label: 'Active Versions',
    value: '3',
    secondaryLabel: 'Working',
    secondaryValue: '1',
  },
  {
    id: 'total-uploads',
    label: 'Data Uploads',
    value: 12,
    trend: 'up',
    trendValue: '+2 this week',
  },
  {
    id: 'last-import',
    label: 'Last Import',
    value: 'Today',
    secondaryLabel: 'Records',
    secondaryValue: '1,245',
  },
  {
    id: 'system-status',
    label: 'System Status',
    value: 'Active',
    color: 'success',
  },
]

const attentionItems: AttentionItem[] = [
  {
    id: 'pending-import',
    title: 'Historical data import pending',
    description: 'FY2023 actuals ready for import',
    severity: 'info',
    link: '/settings/uploads',
  },
]

const quickActions: QuickAction[] = [
  {
    id: 'manage-versions',
    label: 'Manage Versions',
    icon: Database,
    variant: 'primary',
    link: '/settings/versions',
  },
  {
    id: 'import-data',
    label: 'Import Data',
    icon: Upload,
    variant: 'secondary',
    link: '/settings/uploads',
  },
  {
    id: 'refresh-config',
    label: 'Refresh Config',
    icon: RefreshCw,
    variant: 'outline',
  },
  {
    id: 'system-settings',
    label: 'System Settings',
    icon: Settings,
    variant: 'outline',
    link: '/settings/system',
  },
]

/**
 * ConfigurationDashboard renders module content only.
 * Navigation (ModuleHeader + WorkflowTabs) is provided by ModuleLayout.
 */
function ConfigurationDashboard() {
  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <ModuleDashboard
        title="Configuration"
        description="System settings and data management"
        icon={Settings}
        workflowProgress={
          <PlanningWorkflowProgress steps={workflowSteps} title="Configuration Status" />
        }
        metricsPanel={<MetricsPanel metrics={metrics} title="Overview" columns={2} />}
        attentionPanel={
          <AttentionPanel
            items={attentionItems}
            title="Pending Tasks"
            emptyMessage="All configuration tasks are up to date"
          />
        }
        quickActions={<QuickActionsBar actions={quickActions} title="Quick Actions" />}
      />
    </div>
  )
}
