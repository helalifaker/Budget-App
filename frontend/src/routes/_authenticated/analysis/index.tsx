/**
 * Analysis Module Dashboard
 *
 * Overview page for the Analysis module showing:
 * - KPI summary cards (H/E, E/D, Cost per Student, etc.)
 * - Attention items (KPIs out of range, variances)
 * - Quick actions (View KPIs, Dashboards, Export)
 *
 * Note: Analysis doesn't have a typical workflow - it's a reporting/analytics module.
 */

import { createFileRoute } from '@tanstack/react-router'
import { BarChart3, TrendingUp, FileText, Gauge } from 'lucide-react'
import {
  ModuleDashboard,
  MetricsPanel,
  AttentionPanel,
  QuickActionsBar,
  type Metric,
  type AttentionItem,
  type QuickAction,
} from '@/components/dashboard'

export const Route = createFileRoute('/_authenticated/analysis/')({
  component: AnalysisDashboard,
})

/**
 * Mock data - In production, this would come from API endpoints
 */

const metrics: Metric[] = [
  {
    id: 'h-e-ratio',
    label: 'H/E Ratio',
    value: '1.42',
    unit: 'hrs/student',
    trend: 'up',
    trendValue: '+0.03',
    secondaryLabel: 'Target',
    secondaryValue: '1.40',
    progress: 98,
  },
  {
    id: 'e-d-ratio',
    label: 'E/D Ratio',
    value: '24.8',
    unit: 'students/class',
    trend: 'neutral',
    trendValue: 'On target',
    secondaryLabel: 'Target',
    secondaryValue: '25.0',
    progress: 99,
    color: 'success',
  },
  {
    id: 'cost-per-student',
    label: 'Cost per Student',
    value: '36,400',
    unit: 'SAR',
    trend: 'up',
    trendValue: '+4.2%',
    secondaryLabel: 'vs LY',
    secondaryValue: '34,900',
  },
  {
    id: 'revenue-per-student',
    label: 'Revenue per Student',
    value: '36,300',
    unit: 'SAR',
    trend: 'up',
    trendValue: '+3.8%',
  },
  {
    id: 'operating-margin',
    label: 'Operating Margin',
    value: '-0.3%',
    trend: 'down',
    trendValue: 'Below target',
    color: 'warning',
    secondaryLabel: 'Target',
    secondaryValue: '2.0%',
  },
  {
    id: 'teacher-ratio',
    label: 'Student/Teacher',
    value: '12.7',
    trend: 'neutral',
    trendValue: 'Stable',
    secondaryLabel: 'Target',
    secondaryValue: '13.0',
    progress: 97,
    color: 'success',
  },
]

const attentionItems: AttentionItem[] = [
  {
    id: 'margin-below',
    title: 'Operating margin below target',
    description: '-0.3% actual vs 2.0% target',
    severity: 'warning',
    link: '/analysis/kpis',
  },
  {
    id: 'cost-increase',
    title: 'Cost per student rising faster than revenue',
    description: '+4.2% cost vs +3.8% revenue growth',
    severity: 'info',
    link: '/analysis/variance',
  },
]

const quickActions: QuickAction[] = [
  {
    id: 'view-kpis',
    label: 'View All KPIs',
    icon: Gauge,
    variant: 'primary',
    link: '/analysis/kpis',
  },
  {
    id: 'dashboards',
    label: 'Dashboards',
    icon: BarChart3,
    variant: 'secondary',
    link: '/analysis/dashboards',
  },
  {
    id: 'variance',
    label: 'Variance Analysis',
    icon: TrendingUp,
    variant: 'outline',
    link: '/analysis/variance',
  },
  {
    id: 'export',
    label: 'Export',
    icon: FileText,
    variant: 'outline',
  },
]

/**
 * AnalysisDashboard renders module content only.
 * Navigation (SmartHeader + ModuleDock) is provided by _authenticated.tsx layout.
 * NO CockpitLayout wrapper here to avoid double navigation.
 */
function AnalysisDashboard() {
  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <ModuleDashboard
        metricsPanel={
          <MetricsPanel metrics={metrics} title="Key Performance Indicators" columns={3} />
        }
        attentionPanel={
          <AttentionPanel
            items={attentionItems}
            title="KPI Alerts"
            emptyMessage="All KPIs within acceptable range"
          />
        }
        quickActions={<QuickActionsBar actions={quickActions} title="Quick Actions" />}
      />
    </div>
  )
}
