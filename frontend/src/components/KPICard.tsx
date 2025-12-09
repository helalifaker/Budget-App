/**
 * Premium KPI Card - EFIR Luxury Warm Theme
 *
 * Executive-ready KPI display with:
 * - Cormorant Garamond serif font for values (text-2xl+)
 * - Lato/Inter for labels (uppercase, smaller)
 * - Sage (#7D9082) for positive change
 * - Terracotta (#C4785D) for negative change
 * - Optional colored indicator bar at bottom
 * - Status-based accent colors
 */

import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Status type for KPI visual styling */
export type KPIStatus = 'good' | 'warning' | 'alert'

interface KPICardProps {
  title: string
  value: number | string
  unit: string
  benchmark?: { min: number; max: number }
  trend?: 'up' | 'down' | 'stable'
  status?: KPIStatus
  previousValue?: number
  /** Compact variant for viewport-fit layouts */
  compact?: boolean
  /** Show colored indicator bar at bottom */
  showIndicator?: boolean
}

const statusStyles: Record<
  KPIStatus,
  {
    border: string
    bg: string
    accent: string
    badge: string
    indicator: string
  }
> = {
  good: {
    border: 'border-sage-200',
    bg: 'bg-sage-50/50',
    accent: 'from-sage-400 to-sage-500',
    badge: 'bg-sage-100 text-sage-700',
    indicator: 'bg-sage-500',
  },
  warning: {
    border: 'border-terracotta-200',
    bg: 'bg-terracotta-50/50',
    accent: 'from-terracotta-400 to-terracotta-500',
    badge: 'bg-terracotta-100 text-terracotta-700',
    indicator: 'bg-terracotta-500',
  },
  alert: {
    border: 'border-terracotta-300',
    bg: 'bg-terracotta-50/50',
    accent: 'from-terracotta-500 to-terracotta-600',
    badge: 'bg-terracotta-100 text-terracotta-800',
    indicator: 'bg-terracotta-600',
  },
}

const trendConfig = {
  up: { icon: ArrowUpIcon, color: 'text-sage-600' }, // Sage for positive
  down: { icon: ArrowDownIcon, color: 'text-terracotta-600' }, // Terracotta for negative
  stable: { icon: MinusIcon, color: 'text-text-tertiary' },
}

export function KPICard({
  title,
  value,
  unit,
  benchmark,
  trend,
  status = 'good',
  previousValue,
  compact = false,
  showIndicator = true,
}: KPICardProps) {
  const styles = statusStyles[status]

  return (
    <div
      className={cn(
        // Base styles
        'relative bg-paper rounded-xl overflow-hidden',
        'border',
        styles.border,
        'transition-all duration-300 ease-out',
        // Shadow
        'shadow-efir-sm',
        // Hover effects
        'hover:shadow-efir-md',
        'hover:-translate-y-0.5',
        // Padding
        compact ? 'p-3' : 'p-4'
      )}
    >
      {/* Status accent bar at top */}
      <div
        className={cn('absolute top-0 left-0 right-0 h-1', 'bg-gradient-to-r', styles.accent)}
        aria-hidden="true"
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        {/* Label: Lato font, tertiary color, uppercase, smaller */}
        <span className="text-xs font-body font-medium text-text-tertiary uppercase tracking-wider">
          {title}
        </span>
        <span
          className={cn(
            'px-2 py-0.5 rounded-full text-xs font-body font-medium uppercase',
            styles.badge
          )}
        >
          {status}
        </span>
      </div>

      {/* Value: Cormorant Garamond font, text-2xl or larger */}
      <div className="flex items-baseline gap-2">
        <span
          className={cn(
            'font-display font-bold text-text-primary tracking-tight',
            '[font-variant-numeric:tabular-nums]',
            compact ? 'text-2xl' : 'text-3xl'
          )}
        >
          {typeof value === 'number' ? value.toFixed(2) : value}
        </span>
        <span className="text-sm font-body text-text-secondary">{unit}</span>
      </div>

      {/* Benchmark */}
      {benchmark && (
        <div className="mt-2 text-xs font-body text-text-secondary">
          <span className="font-medium">Benchmark:</span> {benchmark.min.toFixed(2)} -{' '}
          {benchmark.max.toFixed(2)} {unit}
        </div>
      )}

      {/* Trend indicator */}
      {trend && previousValue !== undefined && (
        <div className="mt-2">
          {(() => {
            const TrendIcon = trendConfig[trend].icon
            const diff = typeof value === 'number' ? value - previousValue : 0
            return (
              <div
                className={cn(
                  'inline-flex items-center gap-1 text-sm font-body font-medium',
                  trendConfig[trend].color
                )}
              >
                <TrendIcon className="w-4 h-4" />
                <span>
                  {trend === 'up' ? '+' : trend === 'down' ? '' : ''}
                  {Math.abs(diff).toFixed(2)} vs previous
                </span>
              </div>
            )
          })()}
        </div>
      )}

      {/* Optional colored indicator bar at bottom */}
      {showIndicator && (
        <div
          className={cn('absolute bottom-0 left-0 right-0 h-[3px]', styles.indicator)}
          aria-hidden="true"
        />
      )}
    </div>
  )
}
