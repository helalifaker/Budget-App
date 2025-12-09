/**
 * ModuleDashboard - Base container component for module dashboards
 *
 * Provides the standard layout structure for all module dashboards:
 * - Header with module title and description
 * - Planning workflow progress (optional)
 * - Two-column layout for metrics and attention panels
 * - Quick actions bar at the bottom
 *
 * This is a composition component - pass in the individual dashboard components.
 */

import { type ReactNode } from 'react'
import { type LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageContainer } from '@/components/layout/PageContainer'

interface ModuleDashboardProps {
  /** Module title */
  title: string
  /** Module description */
  description?: string
  /** Module icon */
  icon?: LucideIcon
  /** Module accent color */
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
  title,
  description,
  icon: Icon,
  workflowProgress,
  metricsPanel,
  attentionPanel,
  quickActions,
  children,
  className,
}: ModuleDashboardProps) {
  return (
    <PageContainer title={title} description={description} className={className}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="space-y-4"
      >
        {/* Module header with icon */}
        {Icon && (
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-gold-100 to-gold-200 shadow-sm">
              <Icon className="w-6 h-6 text-gold-700" />
            </div>
            <div>
              <h1 className="text-xl font-display font-semibold text-text-primary">
                {title} Dashboard
              </h1>
              {description && <p className="text-sm text-text-secondary">{description}</p>}
            </div>
          </div>
        )}

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
