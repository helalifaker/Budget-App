import { Check, Cloud, CloudOff, Loader2, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DraftStatus } from '@/hooks/useDraft'

interface DraftStatusIndicatorProps {
  /**
   * Current status of the draft system
   */
  status: DraftStatus

  /**
   * When the data was last applied/saved to the server
   */
  lastAppliedAt?: Date | null

  /**
   * Whether there are unapplied changes
   */
  hasUnappliedChanges?: boolean

  /**
   * Show the last applied timestamp
   * @default true
   */
  showTimestamp?: boolean

  /**
   * Additional class names
   */
  className?: string
}

/**
 * DraftStatusIndicator - Shows the current save/draft status
 *
 * Displays in the page header to give users constant feedback about
 * whether their changes are saved as a draft or applied.
 *
 * Status states:
 * - idle: No changes, all synced
 * - saving: Draft is being saved to server
 * - saved: Draft saved successfully
 * - applying: Changes being applied (calculation running)
 * - applied: Changes applied successfully
 * - error: An error occurred
 *
 * @example
 * ```tsx
 * <DraftStatusIndicator
 *   status={status}
 *   lastAppliedAt={lastAppliedAt}
 *   hasUnappliedChanges={hasUnappliedChanges}
 * />
 * ```
 */
export function DraftStatusIndicator({
  status,
  lastAppliedAt,
  hasUnappliedChanges = false,
  showTimestamp = true,
  className,
}: DraftStatusIndicatorProps) {
  const config = getStatusConfig(status, hasUnappliedChanges)

  return (
    <div
      className={cn('flex items-center gap-2 text-xs', 'transition-all duration-200', className)}
      role="status"
      aria-live="polite"
    >
      {/* Status Icon */}
      <div
        className={cn('flex items-center justify-center', 'h-5 w-5 rounded-full', config.iconBg)}
      >
        <config.icon className={cn('h-3 w-3', config.iconColor)} />
      </div>

      {/* Status Text */}
      <div className="flex flex-col">
        <span className={cn('font-medium', config.textColor)}>{config.label}</span>
        {showTimestamp && lastAppliedAt && status !== 'saving' && status !== 'applying' && (
          <span className="text-[10px] text-text-tertiary">
            {formatRelativeTime(lastAppliedAt)}
          </span>
        )}
      </div>
    </div>
  )
}

/**
 * Compact inline version for tight spaces
 */
interface DraftStatusBadgeProps {
  status: DraftStatus
  hasUnappliedChanges?: boolean
  className?: string
}

export function DraftStatusBadge({
  status,
  hasUnappliedChanges = false,
  className,
}: DraftStatusBadgeProps) {
  const config = getStatusConfig(status, hasUnappliedChanges)

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
        config.badgeBg,
        config.textColor,
        className
      )}
      role="status"
    >
      <config.icon className={cn('h-3 w-3', config.iconColor)} />
      <span>{config.shortLabel}</span>
    </div>
  )
}

// Configuration for each status
interface StatusConfig {
  icon: React.ComponentType<{ className?: string }>
  label: string
  shortLabel: string
  iconColor: string
  iconBg: string
  textColor: string
  badgeBg: string
}

function getStatusConfig(status: DraftStatus, hasUnappliedChanges: boolean): StatusConfig {
  // If there are unapplied changes, show that state regardless of status
  if (hasUnappliedChanges && status !== 'applying') {
    return {
      icon: Clock,
      label: 'Pending changes',
      shortLabel: 'Pending',
      iconColor: 'text-warning-600',
      iconBg: 'bg-warning-100',
      textColor: 'text-warning-700',
      badgeBg: 'bg-warning-100',
    }
  }

  switch (status) {
    case 'saving':
      return {
        icon: Loader2,
        label: 'Saving...',
        shortLabel: 'Saving',
        iconColor: 'text-info-600 animate-spin',
        iconBg: 'bg-info-100',
        textColor: 'text-info-700',
        badgeBg: 'bg-info-100',
      }

    case 'saved':
      return {
        icon: Cloud,
        label: 'Draft saved',
        shortLabel: 'Draft',
        iconColor: 'text-info-600',
        iconBg: 'bg-info-100',
        textColor: 'text-info-700',
        badgeBg: 'bg-info-100',
      }

    case 'applying':
      return {
        icon: Loader2,
        label: 'Calculating...',
        shortLabel: 'Calculating',
        iconColor: 'text-gold-600 animate-spin',
        iconBg: 'bg-gold-100',
        textColor: 'text-gold-700',
        badgeBg: 'bg-gold-100',
      }

    case 'applied':
      return {
        icon: Check,
        label: 'Applied',
        shortLabel: 'Applied',
        iconColor: 'text-success-600',
        iconBg: 'bg-success-100',
        textColor: 'text-success-700',
        badgeBg: 'bg-success-100',
      }

    case 'error':
      return {
        icon: CloudOff,
        label: 'Sync error',
        shortLabel: 'Error',
        iconColor: 'text-error-600',
        iconBg: 'bg-error-100',
        textColor: 'text-error-700',
        badgeBg: 'bg-error-100',
      }

    case 'idle':
    default:
      return {
        icon: Check,
        label: 'Up to date',
        shortLabel: 'Synced',
        iconColor: 'text-text-tertiary',
        iconBg: 'bg-subtle',
        textColor: 'text-text-secondary',
        badgeBg: 'bg-subtle',
      }
  }
}

/**
 * Format a date as a relative time string
 */
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)

  if (diffSec < 60) {
    return 'Just now'
  } else if (diffMin < 60) {
    return `${diffMin} min ago`
  } else if (diffHour < 24) {
    return `${diffHour} hr ago`
  } else {
    return date.toLocaleDateString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }
}

/**
 * Animated dot indicator for minimal UI
 */
interface DraftStatusDotProps {
  status: DraftStatus
  hasUnappliedChanges?: boolean
  className?: string
}

export function DraftStatusDot({
  status,
  hasUnappliedChanges = false,
  className,
}: DraftStatusDotProps) {
  const config = getStatusConfig(status, hasUnappliedChanges)

  return (
    <div
      className={cn(
        'h-2 w-2 rounded-full',
        status === 'saving' || status === 'applying' ? 'animate-pulse' : '',
        config.iconBg,
        className
      )}
      title={config.label}
      aria-label={config.label}
    />
  )
}
