/* eslint-disable react-refresh/only-export-components */
/**
 * Status Indicator Component - EFIR Luxury Warm Theme
 *
 * Status with icon and color:
 * - Completed: Sage (#7D9082) with checkmark
 * - In Progress: Gold (#A68B5B) with loader
 * - Error: Terracotta (#C4785D) with X icon
 * - Blocked: Terracotta (#C4785D) with alert icon
 * - Pending: Slate (#64748B) with clock icon
 *
 * Uses Lucide icons only (no emoji)
 */

import * as React from 'react'
import { Check, Loader2, X, AlertCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Status type */
export type StatusType = 'completed' | 'in_progress' | 'error' | 'blocked' | 'pending'

interface StatusIndicatorProps {
  /** The status to display */
  status: StatusType
  /** Optional label text */
  label?: string
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Show pulse animation for in_progress status */
  showPulse?: boolean
  /** Additional CSS classes */
  className?: string
}

/** Status configuration with colors and icons */
const statusConfig: Record<
  StatusType,
  {
    bgColor: string
    textColor: string
    dotColor: string
    icon: React.ElementType
    label: string
  }
> = {
  completed: {
    bgColor: 'bg-sage-50',
    textColor: 'text-sage-700',
    dotColor: 'bg-sage-500',
    icon: Check,
    label: 'Completed',
  },
  in_progress: {
    bgColor: 'bg-efir-gold-50',
    textColor: 'text-efir-gold-700',
    dotColor: 'bg-efir-gold-500',
    icon: Loader2,
    label: 'In Progress',
  },
  error: {
    bgColor: 'bg-terracotta-50',
    textColor: 'text-terracotta-700',
    dotColor: 'bg-terracotta-500',
    icon: X,
    label: 'Error',
  },
  blocked: {
    bgColor: 'bg-terracotta-50',
    textColor: 'text-terracotta-700',
    dotColor: 'bg-terracotta-500',
    icon: AlertCircle,
    label: 'Blocked',
  },
  pending: {
    bgColor: 'bg-efir-slate-50',
    textColor: 'text-efir-slate-700',
    dotColor: 'bg-efir-slate-400',
    icon: Clock,
    label: 'Pending',
  },
}

const sizeStyles = {
  sm: {
    wrapper: 'gap-1',
    dot: 'w-2 h-2',
    icon: 'w-3 h-3',
    text: 'text-xs',
  },
  md: {
    wrapper: 'gap-1.5',
    dot: 'w-2.5 h-2.5',
    icon: 'w-4 h-4',
    text: 'text-sm',
  },
  lg: {
    wrapper: 'gap-2',
    dot: 'w-3 h-3',
    icon: 'w-5 h-5',
    text: 'text-base',
  },
}

export function StatusIndicator({
  status,
  label,
  size = 'md',
  showPulse = true,
  className,
}: StatusIndicatorProps) {
  const config = statusConfig[status]
  const sizeStyle = sizeStyles[size]
  const Icon = config.icon
  const displayLabel = label ?? config.label

  return (
    <div
      className={cn('inline-flex items-center font-body', sizeStyle.wrapper, className)}
      role="status"
      aria-label={displayLabel}
    >
      {/* Status dot/icon */}
      <span className="relative flex-shrink-0">
        {/* Pulse animation ring for in_progress */}
        {showPulse && status === 'in_progress' && (
          <span
            className={cn('absolute inset-0 rounded-full animate-ping opacity-75', config.dotColor)}
            aria-hidden="true"
          />
        )}
        {/* Icon */}
        <span
          className={cn(
            'relative flex items-center justify-center rounded-full',
            config.dotColor,
            sizeStyle.dot
          )}
        >
          <Icon
            className={cn(
              'text-white',
              size === 'sm' ? 'w-1.5 h-1.5' : size === 'md' ? 'w-2 h-2' : 'w-2.5 h-2.5',
              status === 'in_progress' && 'animate-spin'
            )}
          />
        </span>
      </span>

      {/* Label */}
      {displayLabel && (
        <span className={cn('font-medium', config.textColor, sizeStyle.text)}>{displayLabel}</span>
      )}
    </div>
  )
}

/**
 * Simplified dot-only status indicator
 */
interface StatusDotProps {
  status: StatusType
  size?: 'sm' | 'md' | 'lg'
  showPulse?: boolean
  className?: string
}

export function StatusDot({ status, size = 'md', showPulse = true, className }: StatusDotProps) {
  const config = statusConfig[status]
  const sizeStyle = sizeStyles[size]

  return (
    <span className={cn('relative inline-flex', className)} role="status" aria-label={config.label}>
      {/* Pulse animation ring for in_progress */}
      {showPulse && status === 'in_progress' && (
        <span
          className={cn('absolute inset-0 rounded-full animate-ping opacity-75', config.dotColor)}
          aria-hidden="true"
        />
      )}
      {/* Dot */}
      <span className={cn('relative rounded-full', config.dotColor, sizeStyle.dot)} />
    </span>
  )
}

export { statusConfig }
