import { useState, useEffect, useCallback } from 'react'
import { Lightbulb, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface ContextualTipProps {
  /** Unique identifier for this tip (used for localStorage) */
  tipId: string
  /** The tip content to display */
  children: React.ReactNode
  /** Storage key prefix for all tips */
  storageKeyPrefix?: string
  /** Whether tips are globally disabled */
  globalDisabled?: boolean
  /** Callback when tip is dismissed */
  onDismiss?: () => void
  /** Callback when "Don't show tips" is clicked */
  onDisableAll?: () => void
  /** Show the "Don't show tips" option */
  showDisableOption?: boolean
  /** Additional CSS classes */
  className?: string
  /** Variant for different visual styles */
  variant?: 'default' | 'compact'
}

/**
 * ContextualTip - Dismissible inline tips for guidance
 *
 * Provides contextual help at key decision points in the UI.
 * Features:
 * - Per-tip dismissal (remembered in localStorage)
 * - Global "Don't show tips" option
 * - Light sage background matching the enrollment theme
 * - Compact variant for less intrusive guidance
 *
 * Usage:
 * ```tsx
 * <ContextualTip tipId="scenario-selection-hint">
 *   Most schools start with the "Base Case" scenario.
 *   Only adjust parameters if you have specific information.
 * </ContextualTip>
 * ```
 */
export function ContextualTip({
  tipId,
  children,
  storageKeyPrefix = 'tip-dismissed',
  globalDisabled = false,
  onDismiss,
  onDisableAll,
  showDisableOption = true,
  className,
  variant = 'default',
}: ContextualTipProps) {
  const [isDismissed, setIsDismissed] = useState(true) // Start hidden to prevent flash
  const [isGloballyDisabled, setIsGloballyDisabled] = useState(globalDisabled)

  // Check localStorage on mount
  useEffect(() => {
    const globalKey = `${storageKeyPrefix}-global`
    const tipKey = `${storageKeyPrefix}-${tipId}`

    const isGlobalOff = localStorage.getItem(globalKey) === 'true'
    const isTipDismissed = localStorage.getItem(tipKey) === 'true'

    setIsGloballyDisabled(isGlobalOff || globalDisabled)
    setIsDismissed(isTipDismissed || isGlobalOff || globalDisabled)
  }, [storageKeyPrefix, tipId, globalDisabled])

  const handleDismiss = useCallback(() => {
    const tipKey = `${storageKeyPrefix}-${tipId}`
    localStorage.setItem(tipKey, 'true')
    setIsDismissed(true)
    onDismiss?.()
  }, [storageKeyPrefix, tipId, onDismiss])

  const handleDisableAll = useCallback(() => {
    const globalKey = `${storageKeyPrefix}-global`
    localStorage.setItem(globalKey, 'true')
    setIsGloballyDisabled(true)
    setIsDismissed(true)
    onDisableAll?.()
  }, [storageKeyPrefix, onDisableAll])

  // Don't render if dismissed or globally disabled
  if (isDismissed || isGloballyDisabled) {
    return null
  }

  if (variant === 'compact') {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-sage-lighter border border-sage-light',
          'text-xs text-text-secondary',
          className
        )}
      >
        <Lightbulb className="h-3.5 w-3.5 text-sage flex-shrink-0" />
        <span className="flex-1">{children}</span>
        <button
          type="button"
          onClick={handleDismiss}
          className="text-text-tertiary hover:text-text-secondary p-0.5 rounded"
          aria-label="Dismiss tip"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    )
  }

  return (
    <div className={cn('rounded-lg border border-sage-light bg-sage-lighter p-4', className)}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Lightbulb className="h-5 w-5 text-sage" />
        </div>

        {/* Content */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sage uppercase tracking-wider">Tip</span>
          </div>
          <div className="text-sm text-text-secondary leading-relaxed">{children}</div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-1">
            {showDisableOption && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleDisableAll}
                className="text-xs text-text-tertiary hover:text-text-secondary"
              >
                Don't show tips
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleDismiss}
              className="text-xs"
            >
              Got it
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
