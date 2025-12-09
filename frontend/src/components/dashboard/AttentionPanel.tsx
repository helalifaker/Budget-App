/**
 * AttentionPanel - Alerts and attention items with severity badges
 *
 * Displays a list of items that need attention, with:
 * - Severity indicator (critical/warning/info)
 * - Title and description
 * - Optional action button
 * - Click navigation to related page
 *
 * Used in module dashboards to highlight issues requiring action.
 */

import { cn } from '@/lib/utils'
import { AlertTriangle, AlertCircle, Info, ArrowRight, type LucideIcon } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export type AttentionSeverity = 'critical' | 'warning' | 'info'

export interface AttentionItem {
  id: string
  title: string
  description?: string
  severity: AttentionSeverity
  link?: string
  action?: {
    label: string
    onClick: () => void
  }
  icon?: LucideIcon
}

interface AttentionPanelProps {
  items: AttentionItem[]
  title?: string
  maxItems?: number
  className?: string
  emptyMessage?: string
}

/**
 * Get severity styling and icon
 */
function getSeverityInfo(severity: AttentionSeverity) {
  switch (severity) {
    case 'critical':
      return {
        icon: AlertTriangle,
        bgColor: 'bg-error-50',
        borderColor: 'border-error-200',
        iconColor: 'text-error-600',
        textColor: 'text-error-700',
        badgeBg: 'bg-error-100',
        badgeText: 'text-error-700',
      }
    case 'warning':
      return {
        icon: AlertCircle,
        bgColor: 'bg-warning-50',
        borderColor: 'border-warning-200',
        iconColor: 'text-warning-600',
        textColor: 'text-warning-700',
        badgeBg: 'bg-warning-100',
        badgeText: 'text-warning-700',
      }
    default:
      return {
        icon: Info,
        bgColor: 'bg-info-50',
        borderColor: 'border-info-200',
        iconColor: 'text-info-600',
        textColor: 'text-info-700',
        badgeBg: 'bg-info-100',
        badgeText: 'text-info-700',
      }
  }
}

/**
 * Individual attention item card
 */
function AttentionItemCard({ item }: { item: AttentionItem }) {
  const severityInfo = getSeverityInfo(item.severity)
  const SeverityIcon = item.icon || severityInfo.icon

  const content = (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg border',
        'transition-all duration-200',
        item.link && 'hover:shadow-sm cursor-pointer group',
        severityInfo.bgColor,
        severityInfo.borderColor
      )}
    >
      {/* Icon */}
      <div className={cn('p-1.5 rounded-lg', severityInfo.badgeBg)}>
        <SeverityIcon className={cn('w-4 h-4', severityInfo.iconColor)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('text-sm font-medium', severityInfo.textColor)}>{item.title}</span>
          {item.link && (
            <ArrowRight
              className={cn(
                'w-3.5 h-3.5 transition-transform',
                'group-hover:translate-x-0.5',
                severityInfo.iconColor
              )}
            />
          )}
        </div>
        {item.description && (
          <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{item.description}</p>
        )}
      </div>

      {/* Action button */}
      {item.action && (
        <Button
          variant="ghost"
          size="sm"
          className={cn('text-xs h-7 px-2', severityInfo.textColor)}
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            item.action?.onClick()
          }}
        >
          {item.action.label}
        </Button>
      )}
    </motion.div>
  )

  if (item.link) {
    return <Link to={item.link}>{content}</Link>
  }

  return content
}

export function AttentionPanel({
  items,
  title = 'Needs Attention',
  maxItems = 5,
  className,
  emptyMessage = 'No items need attention',
}: AttentionPanelProps) {
  // Sort by severity (critical first)
  const sortedItems = [...items].sort((a, b) => {
    const severityOrder: Record<AttentionSeverity, number> = {
      critical: 0,
      warning: 1,
      info: 2,
    }
    return severityOrder[a.severity] - severityOrder[b.severity]
  })

  const displayedItems = sortedItems.slice(0, maxItems)
  const remainingCount = items.length - maxItems

  return (
    <div className={cn('bg-white rounded-xl border border-border-light p-4', className)}>
      {/* Header with count */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        {items.length > 0 && (
          <span
            className={cn(
              'text-xs font-bold px-2 py-0.5 rounded-full',
              items.some((i) => i.severity === 'critical')
                ? 'bg-error-100 text-error-700'
                : items.some((i) => i.severity === 'warning')
                  ? 'bg-warning-100 text-warning-700'
                  : 'bg-info-100 text-info-700'
            )}
          >
            {items.length}
          </span>
        )}
      </div>

      {/* Items list */}
      {items.length === 0 ? (
        <div className="flex items-center justify-center py-6 text-sm text-text-tertiary">
          {emptyMessage}
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {displayedItems.map((item) => (
              <AttentionItemCard key={item.id} item={item} />
            ))}
          </AnimatePresence>

          {/* Show more indicator */}
          {remainingCount > 0 && (
            <div className="text-center pt-2">
              <span className="text-xs text-text-tertiary">
                +{remainingCount} more item{remainingCount !== 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
