/**
 * MetricsPanel - Key metrics grid display for module dashboards
 *
 * Displays a grid of metric cards with:
 * - Label and value
 * - Optional trend indicator (up/down/neutral)
 * - Optional secondary value (comparison, unit, etc.)
 * - Optional progress bar
 *
 * Used in module dashboards to show KPIs at a glance.
 */

import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'

export type MetricTrend = 'up' | 'down' | 'neutral'

export interface Metric {
  id: string
  label: string
  value: string | number
  unit?: string
  trend?: MetricTrend
  trendValue?: string
  secondaryLabel?: string
  secondaryValue?: string
  progress?: number // 0-100 for optional progress bar
  icon?: LucideIcon
  color?: 'default' | 'success' | 'warning' | 'error' | 'info'
}

interface MetricsPanelProps {
  metrics: Metric[]
  title?: string
  columns?: 2 | 3 | 4
  className?: string
}

/**
 * Get trend icon and color
 */
function getTrendInfo(trend: MetricTrend) {
  switch (trend) {
    case 'up':
      return { icon: TrendingUp, color: 'text-success-600' }
    case 'down':
      return { icon: TrendingDown, color: 'text-error-600' }
    default:
      return { icon: Minus, color: 'text-text-tertiary' }
  }
}

/**
 * Get metric color styles
 */
function getMetricColorStyles(color: Metric['color']) {
  switch (color) {
    case 'success':
      return { bg: 'bg-success-50', border: 'border-success-200', text: 'text-success-700' }
    case 'warning':
      return { bg: 'bg-warning-50', border: 'border-warning-200', text: 'text-warning-700' }
    case 'error':
      return { bg: 'bg-error-50', border: 'border-error-200', text: 'text-error-700' }
    case 'info':
      return { bg: 'bg-info-50', border: 'border-info-200', text: 'text-info-700' }
    default:
      return { bg: 'bg-subtle/50', border: 'border-border-light', text: 'text-text-primary' }
  }
}

/**
 * Individual metric card
 */
function MetricCard({ metric }: { metric: Metric }) {
  const colorStyles = getMetricColorStyles(metric.color)
  const TrendIcon = metric.trend ? getTrendInfo(metric.trend).icon : null
  const trendColor = metric.trend ? getTrendInfo(metric.trend).color : ''
  const MetricIcon = metric.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'rounded-xl p-3 border transition-all duration-200',
        'hover:shadow-sm',
        colorStyles.bg,
        colorStyles.border
      )}
    >
      {/* Header with label and icon */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-text-secondary font-medium">{metric.label}</span>
        {MetricIcon && <MetricIcon className="w-4 h-4 text-text-muted" />}
      </div>

      {/* Main value with trend */}
      <div className="flex items-baseline gap-1.5">
        <span className={cn('text-2xl font-bold font-mono', colorStyles.text)}>{metric.value}</span>
        {metric.unit && <span className="text-xs text-text-tertiary">{metric.unit}</span>}
      </div>

      {/* Trend indicator */}
      {metric.trend && metric.trendValue && (
        <div className={cn('flex items-center gap-1 mt-1', trendColor)}>
          {TrendIcon && <TrendIcon className="w-3 h-3" />}
          <span className="text-xs font-medium">{metric.trendValue}</span>
        </div>
      )}

      {/* Secondary value */}
      {metric.secondaryLabel && metric.secondaryValue && (
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-light/50">
          <span className="text-xs text-text-tertiary">{metric.secondaryLabel}</span>
          <span className="text-xs font-medium text-text-primary">{metric.secondaryValue}</span>
        </div>
      )}

      {/* Optional progress bar */}
      {metric.progress !== undefined && (
        <div className="mt-2">
          <div className="h-1.5 bg-subtle rounded-full overflow-hidden">
            <motion.div
              className={cn(
                'h-full rounded-full',
                metric.progress >= 100
                  ? 'bg-success-500'
                  : metric.progress >= 75
                    ? 'bg-gold-500'
                    : metric.progress >= 50
                      ? 'bg-slate-400'
                      : 'bg-error-400'
              )}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(metric.progress, 100)}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

export function MetricsPanel({
  metrics,
  title = 'Key Metrics',
  columns = 2,
  className,
}: MetricsPanelProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-2 md:grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-4',
  }

  return (
    <div className={cn('bg-white rounded-xl border border-border-light p-4', className)}>
      {/* Header */}
      {title && <h3 className="text-sm font-semibold text-text-primary mb-3">{title}</h3>}

      {/* Metrics grid */}
      <div className={cn('grid gap-3', gridCols[columns])}>
        {metrics.map((metric) => (
          <MetricCard key={metric.id} metric={metric} />
        ))}
      </div>
    </div>
  )
}
