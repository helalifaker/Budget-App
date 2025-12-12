import { useState, useEffect, type ReactNode } from 'react'
import { Settings, AlertTriangle, ChevronDown } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'

interface AdvancedFeaturesSectionProps {
  /** Unique key for localStorage persistence */
  storageKey?: string
  /** Content to show when expanded */
  children: ReactNode
  /** Whether the section is disabled */
  disabled?: boolean
  /** Optional className */
  className?: string
}

/**
 * AdvancedFeaturesSection - Checkbox-gated panel for advanced options
 *
 * UX Pattern: Progressive disclosure with acknowledgment gate
 * - Collapsed by default (checkbox unchecked)
 * - Shows explanation of what advanced features do
 * - User must check checkbox to acknowledge they want advanced options
 * - Smooth expand/collapse animation
 * - State persisted in localStorage
 *
 * This reduces cognitive load for typical users while still providing
 * power features for those who need them.
 */
export function AdvancedFeaturesSection({
  storageKey = 'enrollment-advanced-enabled',
  children,
  disabled = false,
  className,
}: AdvancedFeaturesSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)

  // Load persisted state from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(storageKey)
    if (stored === 'true') {
      setIsExpanded(true)
    }
    setHasLoaded(true)
  }, [storageKey])

  // Persist state to localStorage
  const handleToggle = (checked: boolean) => {
    setIsExpanded(checked)
    localStorage.setItem(storageKey, String(checked))
  }

  // Don't render until we've loaded from localStorage to prevent flash
  if (!hasLoaded) {
    return null
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with checkbox toggle */}
      <div
        className={cn(
          'rounded-lg border transition-colors duration-200',
          isExpanded
            ? 'border-sage bg-sage-lighter'
            : 'border-border-light bg-background hover:border-sage-light'
        )}
      >
        {/* Toggle Header */}
        <div className="p-4">
          <div className="flex items-start gap-3">
            {/* Checkbox */}
            <Checkbox
              id="advanced-features-toggle"
              checked={isExpanded}
              onCheckedChange={handleToggle}
              disabled={disabled}
              className="mt-0.5"
            />

            {/* Label and description */}
            <label
              htmlFor="advanced-features-toggle"
              className={cn(
                'flex-1 cursor-pointer select-none',
                disabled && 'cursor-not-allowed opacity-60'
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <Settings className="h-4 w-4 text-sage" />
                <span className="text-sm font-semibold text-text-primary uppercase tracking-wide">
                  Enable Advanced Adjustments
                </span>
              </div>

              {/* Always visible explanation */}
              <p className="text-sm text-text-secondary leading-relaxed mb-3">
                Advanced adjustments let you fine-tune projections beyond the selected scenario. Use
                these if you have specific information about next year that differs from typical
                patterns.
              </p>

              {/* What you can adjust */}
              <div className="space-y-1.5 mb-3">
                <p className="text-xs font-medium text-sage uppercase tracking-wider">
                  What You Can Adjust:
                </p>
                <ul className="text-xs text-text-secondary space-y-1 list-disc list-inside ml-1">
                  <li>Student retention rates per grade level</li>
                  <li>Mid-year transfer student numbers</li>
                  <li>Maximum class sizes and sections per cycle</li>
                  <li>Grade-specific enrollment overrides</li>
                </ul>
              </div>

              {/* Warning note */}
              <div className="flex items-start gap-2 p-2 rounded bg-gold/10 border border-gold/20">
                <AlertTriangle className="h-3.5 w-3.5 text-gold flex-shrink-0 mt-0.5" />
                <p className="text-xs text-text-secondary leading-relaxed">
                  <span className="font-medium text-gold">Note:</span> Most schools don't need these
                  adjustments. The scenario defaults work well for typical situations.
                </p>
              </div>
            </label>
          </div>

          {/* Expand indicator */}
          {isExpanded && (
            <div className="flex items-center justify-center mt-3 pt-3 border-t border-sage-light">
              <ChevronDown className="h-4 w-4 text-sage animate-bounce" />
              <span className="text-xs text-sage ml-1">Advanced options below</span>
            </div>
          )}
        </div>
      </div>

      {/* Expandable content with animation */}
      <div
        className={cn(
          'overflow-hidden transition-all duration-300 ease-in-out',
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="space-y-6">{children}</div>
      </div>
    </div>
  )
}

/**
 * AdvancedFeaturesBadge - Small badge to indicate advanced feature
 * Use next to section headers that are inside the advanced section
 */
export function AdvancedFeaturesBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium',
        'bg-sage-light text-sage uppercase tracking-wider',
        className
      )}
    >
      <Settings className="h-2.5 w-2.5" />
      Advanced
    </span>
  )
}
