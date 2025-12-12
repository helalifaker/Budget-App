import { AlertTriangle, Calculator, RotateCcw, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './button'

interface UnappliedChangesBannerProps {
  /**
   * Whether there are unapplied changes to show the banner
   */
  hasChanges: boolean

  /**
   * Summary of the impact of applying changes (e.g., "15 grades, 847 students")
   */
  impactSummary?: string

  /**
   * Callback when user clicks "Discard Draft"
   */
  onDiscard: () => void

  /**
   * Callback when user clicks "Apply & Calculate"
   */
  onApply: () => void

  /**
   * Whether the apply action is in progress
   */
  isApplying?: boolean

  /**
   * Whether the discard action is disabled
   */
  isDiscardDisabled?: boolean

  /**
   * Custom label for the apply button
   * @default "Apply & Calculate"
   */
  applyLabel?: string

  /**
   * Custom label for the discard button
   * @default "Discard Changes"
   */
  discardLabel?: string

  /**
   * Additional class names
   */
  className?: string
}

/**
 * UnappliedChangesBanner - Shows when there are draft changes that haven't been applied
 *
 * This banner appears between the form inputs and the results grid to clearly
 * communicate that the user has made changes that need to be applied.
 *
 * Features:
 * - Warning-style styling with gold/amber accent
 * - Impact summary showing what will be affected
 * - Discard and Apply buttons
 * - Loading state during apply
 *
 * @example
 * ```tsx
 * <UnappliedChangesBanner
 *   hasChanges={hasUnappliedChanges}
 *   impactSummary="15 grades, 847 students affected"
 *   onDiscard={() => discard()}
 *   onApply={() => apply()}
 *   isApplying={isApplying}
 * />
 * ```
 */
export function UnappliedChangesBanner({
  hasChanges,
  impactSummary,
  onDiscard,
  onApply,
  isApplying = false,
  isDiscardDisabled = false,
  applyLabel = 'Apply & Calculate',
  discardLabel = 'Discard Changes',
  className,
}: UnappliedChangesBannerProps) {
  if (!hasChanges) return null

  return (
    <div
      className={cn(
        'rounded-lg border-l-4 border-warning-500',
        'bg-warning-50 dark:bg-warning-900/20',
        'p-4 shadow-sm',
        'animate-in fade-in slide-in-from-top-2 duration-300',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Warning Icon and Message */}
        <div className="flex items-start gap-3 flex-1">
          <div className="flex-shrink-0">
            <AlertTriangle className="h-5 w-5 text-warning-600 dark:text-warning-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-warning-800 dark:text-warning-200">
              Unapplied Changes
            </h4>
            <p className="mt-0.5 text-sm text-warning-700 dark:text-warning-300">
              Your changes are saved as a draft. Click &quot;Apply &amp; Calculate&quot; to update
              the projections.
            </p>
            {impactSummary && (
              <p className="mt-1 text-xs text-warning-600 dark:text-warning-400 font-medium">
                Impact: {impactSummary}
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={onDiscard}
            disabled={isApplying || isDiscardDisabled}
            className="text-warning-700 hover:text-warning-800 hover:bg-warning-100 dark:text-warning-300 dark:hover:text-warning-200 dark:hover:bg-warning-900/30"
          >
            <RotateCcw className="h-4 w-4 mr-1" />
            {discardLabel}
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={onApply}
            disabled={isApplying}
            className="bg-warning-600 hover:bg-warning-700 text-white"
          >
            {isApplying ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <Calculator className="h-4 w-4 mr-1" />
                {applyLabel}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

/**
 * Compact version of the banner for use in tighter spaces
 */
interface UnappliedChangesBannerCompactProps {
  hasChanges: boolean
  onApply: () => void
  isApplying?: boolean
  className?: string
}

export function UnappliedChangesBannerCompact({
  hasChanges,
  onApply,
  isApplying = false,
  className,
}: UnappliedChangesBannerCompactProps) {
  if (!hasChanges) return null

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-2',
        'rounded-md bg-warning-50 dark:bg-warning-900/20',
        'px-3 py-2 border border-warning-200 dark:border-warning-800',
        className
      )}
    >
      <div className="flex items-center gap-2 text-sm text-warning-700 dark:text-warning-300">
        <AlertTriangle className="h-4 w-4" />
        <span>Pending changes</span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onApply}
        disabled={isApplying}
        className="h-7 text-xs text-warning-700 hover:text-warning-800 hover:bg-warning-100"
      >
        {isApplying ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <>
            <Calculator className="h-3 w-3 mr-1" />
            Apply
          </>
        )}
      </Button>
    </div>
  )
}
