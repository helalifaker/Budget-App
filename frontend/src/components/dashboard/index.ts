/**
 * Dashboard Components - Executive Cockpit Module Dashboards
 *
 * Export all dashboard-related components for module dashboards.
 */

// Base dashboard container
export { ModuleDashboard } from './ModuleDashboard'

// Dashboard panels
export {
  PlanningWorkflowProgress,
  type WorkflowStep,
  type WorkflowStepStatus,
} from './PlanningWorkflowProgress'

export { MetricsPanel, type Metric, type MetricTrend } from './MetricsPanel'

export { AttentionPanel, type AttentionItem, type AttentionSeverity } from './AttentionPanel'

export { QuickActionsBar, type QuickAction } from './QuickActionsBar'
