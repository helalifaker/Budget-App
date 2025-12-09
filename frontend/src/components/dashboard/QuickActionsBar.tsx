/**
 * QuickActionsBar - Primary action buttons for module dashboards
 *
 * Displays a row of action buttons with:
 * - Icon and label
 * - Optional badge/count
 * - Primary and secondary variants
 * - Links or click handlers
 *
 * Used at the bottom of module dashboards for quick access to common actions.
 */

import { cn } from '@/lib/utils'
import { type LucideIcon } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export interface QuickAction {
  id: string
  label: string
  icon: LucideIcon
  onClick?: () => void
  link?: string
  variant?: 'primary' | 'secondary' | 'outline'
  badge?: string | number
  disabled?: boolean
  tooltip?: string
}

interface QuickActionsBarProps {
  actions: QuickAction[]
  title?: string
  className?: string
}

/**
 * Individual action button
 */
function ActionButton({ action }: { action: QuickAction }) {
  const Icon = action.icon

  const buttonVariant =
    action.variant === 'primary'
      ? 'default'
      : action.variant === 'secondary'
        ? 'secondary'
        : 'outline'

  const buttonContent = (
    <Button
      variant={buttonVariant}
      size="sm"
      className={cn(
        'gap-2 relative',
        action.variant === 'primary' && 'bg-gold-600 hover:bg-gold-700 text-white'
      )}
      disabled={action.disabled}
      onClick={action.onClick}
      title={action.tooltip}
    >
      <Icon className="w-4 h-4" />
      <span>{action.label}</span>

      {/* Badge */}
      {action.badge !== undefined && (
        <span
          className={cn(
            'absolute -top-1.5 -right-1.5',
            'min-w-[18px] h-[18px] px-1',
            'text-[10px] font-bold',
            'rounded-full flex items-center justify-center',
            action.variant === 'primary' ? 'bg-white text-gold-700' : 'bg-gold-500 text-white'
          )}
        >
          {action.badge}
        </span>
      )}
    </Button>
  )

  if (action.link) {
    return <Link to={action.link}>{buttonContent}</Link>
  }

  return buttonContent
}

export function QuickActionsBar({
  actions,
  title = 'Quick Actions',
  className,
}: QuickActionsBarProps) {
  if (actions.length === 0) {
    return null
  }

  // Separate primary actions from others
  const primaryActions = actions.filter((a) => a.variant === 'primary')
  const otherActions = actions.filter((a) => a.variant !== 'primary')

  return (
    <div className={cn('bg-white rounded-xl border border-border-light p-4', className)}>
      {/* Header */}
      {title && <h3 className="text-sm font-semibold text-text-primary mb-3">{title}</h3>}

      {/* Actions row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Primary actions first */}
        {primaryActions.map((action) => (
          <ActionButton key={action.id} action={action} />
        ))}

        {/* Separator if both types exist */}
        {primaryActions.length > 0 && otherActions.length > 0 && (
          <div className="h-6 w-px bg-subtle mx-1" />
        )}

        {/* Other actions */}
        {otherActions.map((action) => (
          <ActionButton key={action.id} action={action} />
        ))}
      </div>
    </div>
  )
}
