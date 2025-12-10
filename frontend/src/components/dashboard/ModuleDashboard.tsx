/**
 * ModuleDashboard - Base container component for module dashboards
 *
 * Provides the standard layout structure for all module dashboards:
 * - Planning workflow progress (optional)
 * - Two-column layout for metrics and attention panels
 * - Quick actions bar at the bottom
 *
 * UI Redesign: Removed duplicate header - ModuleHeader now handles titles
 *
 * This is a composition component - pass in the individual dashboard components.
 */

import { type ReactNode } from 'react'
import { type LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageContainer } from '@/components/layout/PageContainer'

interface ModuleDashboardProps {
  /** @deprecated Title now shown in ModuleHeader */
  title?: string
  /** @deprecated Description now shown in TaskDescription */
  description?: string
  /** @deprecated Icon now shown in ModuleHeader */
  icon?: LucideIcon
  /** @deprecated No longer used */
  color?: string
  /** Workflow progress component */
  workflowProgress?: ReactNode
  /** Left column content (usually MetricsPanel) */
  metricsPanel?: ReactNode
  /** Right column content (usually AttentionPanel) */
  attentionPanel?: ReactNode
  /** Bottom quick actions bar */
  quickActions?: ReactNode
  /** Additional children to render */
  children?: ReactNode
  /** Additional classes */
  className?: string
}

export function ModuleDashboard({
  workflowProgress,
  metricsPanel,
  attentionPanel,
  quickActions,
  children,
  className,
}: ModuleDashboardProps) {
  return (
    <PageContainer className={className}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="space-y-4"
      >
        {/* Planning workflow progress */}
        {workflowProgress && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            {workflowProgress}
          </motion.div>
        )}

        {/* Two-column layout for metrics and attention */}
        {(metricsPanel || attentionPanel) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {metricsPanel && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                {metricsPanel}
              </motion.div>
            )}
            {attentionPanel && (
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                {attentionPanel}
              </motion.div>
            )}
          </div>
        )}

        {/* Additional children */}
        {children && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            {children}
          </motion.div>
        )}

        {/* Quick actions bar */}
        {quickActions && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.5 }}
          >
            {quickActions}
          </motion.div>
        )}
      </motion.div>
    </PageContainer>
  )
}
