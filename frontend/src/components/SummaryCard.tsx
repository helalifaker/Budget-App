/**
 * Premium Summary Card - EFIR Luxury Warm Theme
 *
 * Board-ready metric cards with:
 * - Module accent border option (3px left border)
 * - Warm shadows, no harsh grays
 * - Cormorant Garamond for values
 * - Lato/Inter for labels
 * - Sage for positive trends, Terracotta for negative
 */

import { ReactNode } from 'react'
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Module accent color type for left border */
export type ModuleAccent = 'gold' | 'sage' | 'terracotta' | 'slate' | 'wine' | 'none'

interface SummaryCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  icon?: ReactNode
  className?: string
  valueClassName?: string
  /** Compact variant for viewport-fit layouts */
  compact?: boolean
  /** Show gold accent bar at top */
  accent?: boolean
  /** Module accent color for left border (3px) */
  moduleAccent?: ModuleAccent
}

const accentColorMap: Record<ModuleAccent, string> = {
  gold: 'from-efir-gold-400 to-efir-gold-600',
  sage: 'from-sage-400 to-sage-600',
  terracotta: 'from-terracotta-400 to-terracotta-600',
  slate: 'from-efir-slate-400 to-efir-slate-600',
  wine: 'from-wine-400 to-wine-600',
  none: '',
}

const trendColors = {
  up: 'text-sage-600 bg-sage-50', // Sage for positive
  down: 'text-terracotta-600 bg-terracotta-50', // Terracotta for negative
  stable: 'text-text-tertiary bg-subtle',
}

const TrendIcon = {
  up: ArrowUpIcon,
  down: ArrowDownIcon,
  stable: MinusIcon,
}

export function SummaryCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  className,
  valueClassName,
  compact = false,
  accent = true,
  moduleAccent = 'none',
}: SummaryCardProps) {
  const showModuleAccent = moduleAccent !== 'none'

  return (
    <div
      className={cn(
        // Base styles
        'relative bg-paper rounded-xl overflow-hidden',
        'border border-[#E8E6E1]',
        'transition-all duration-300 ease-out',
        // Warm shadow
        'shadow-efir-sm',
        // Hover effects
        'hover:shadow-efir-md',
        'hover:border-efir-gold-200/50',
        'hover:-translate-y-0.5',
        // Padding
        compact ? 'p-3' : 'p-4',
        // Left padding for module accent bar
        showModuleAccent && 'pl-2',
        className
      )}
    >
      {/* Gold accent bar at top (optional) */}
      {accent && !showModuleAccent && (
        <div
          className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-efir-gold-400 to-efir-gold-600"
          aria-hidden="true"
        />
      )}

      {/* Module accent bar on left (3px) */}
      {showModuleAccent && (
        <div
          className={cn(
            'absolute top-0 left-0 w-[3px] h-full bg-gradient-to-b rounded-l-xl',
            accentColorMap[moduleAccent]
          )}
          aria-hidden="true"
        />
      )}

      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        {/* Label: Lato font, tertiary color, uppercase */}
        <span className="text-xs font-body font-medium text-text-tertiary uppercase tracking-wider">
          {title}
        </span>
        {icon && <div className="p-1.5 rounded-lg bg-subtle text-efir-gold-600">{icon}</div>}
      </div>

      {/* Value: Cormorant Garamond font */}
      <div
        className={cn(
          'font-display font-bold text-text-primary tracking-tight',
          compact ? 'text-xl' : 'text-2xl',
          // Tabular numbers for alignment
          '[font-variant-numeric:tabular-nums]',
          valueClassName
        )}
      >
        {value}
      </div>

      {/* Subtitle and Trend */}
      {(subtitle || trend) && (
        <div className="flex items-center gap-2 mt-2">
          {trend && (
            <div
              className={cn(
                'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
                'text-xs font-body font-medium',
                trendColors[trend]
              )}
            >
              {(() => {
                const Icon = TrendIcon[trend]
                return <Icon className="w-3 h-3" />
              })()}
              {trendValue && <span>{trendValue}</span>}
            </div>
          )}
          {subtitle && <p className="text-xs font-body text-text-secondary">{subtitle}</p>}
        </div>
      )}
    </div>
  )
}
