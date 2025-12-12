import { Info } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

export interface FieldDefinition {
  label: string
  shortLabel?: string
  description: string
  why?: string
  unit?: string
  range?: {
    min: number
    max: number
    step?: number
  }
  example?: string
  format?: 'percentage' | 'number' | 'multiplier'
  category?: 'basic' | 'advanced'
}

interface HelpTooltipProps {
  /** The field definition containing help content */
  field: FieldDefinition
  /** Size of the info icon */
  size?: 'sm' | 'md'
  /** Additional class names */
  className?: string
  /** Side where tooltip appears */
  side?: 'top' | 'right' | 'bottom' | 'left'
}

/**
 * HelpTooltip - Field-level help with structured content
 *
 * Displays an info icon (i) that shows a tooltip with:
 * - Description of what the field does
 * - Why it matters (business context)
 * - Valid range (if applicable)
 * - Example value
 *
 * Uses the app's sage accent color for the enrollment module.
 */
export function HelpTooltip({ field, size = 'sm', className, side = 'top' }: HelpTooltipProps) {
  const iconSize = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'

  const formatRange = () => {
    if (!field.range) return null

    const { min, max } = field.range
    const unit = field.unit || ''

    if (field.format === 'percentage') {
      return `${min * 100}% to ${max * 100}%`
    }
    if (field.format === 'multiplier') {
      return `${min}x to ${max}x`
    }
    return `${min} to ${max}${unit ? ` ${unit}` : ''}`
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={cn(
              'inline-flex items-center justify-center rounded-full',
              'text-sage hover:text-sage-hover hover:bg-sage-light',
              'focus:outline-none focus:ring-2 focus:ring-sage focus:ring-offset-1',
              'transition-colors duration-150',
              'p-0.5 -m-0.5',
              className
            )}
            aria-label={`Help: ${field.label}`}
          >
            <Info className={iconSize} />
          </button>
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className={cn(
            'max-w-xs p-3 space-y-2',
            'bg-paper border border-border-light shadow-lg',
            'text-text-primary'
          )}
        >
          {/* Description */}
          <p className="text-sm leading-relaxed">{field.description}</p>

          {/* Why it matters */}
          {field.why && (
            <p className="text-xs text-text-secondary leading-relaxed">
              <span className="font-medium text-sage">Why:</span> {field.why}
            </p>
          )}

          {/* Range */}
          {field.range && (
            <p className="text-xs text-text-secondary">
              <span className="font-medium">Range:</span> {formatRange()}
            </p>
          )}

          {/* Example */}
          {field.example && (
            <p className="text-xs text-text-tertiary italic">Example: {field.example}</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * FieldLabel - A label with integrated help tooltip
 *
 * Combines a text label with the help tooltip for consistent UI.
 */
interface FieldLabelProps {
  field: FieldDefinition
  /** Use short label if available */
  short?: boolean
  className?: string
}

export function FieldLabel({ field, short = false, className }: FieldLabelProps) {
  const label = short && field.shortLabel ? field.shortLabel : field.label

  return (
    <div className={cn('flex items-center gap-1.5', className)}>
      <span className="text-sm font-medium text-text-primary">{label}</span>
      <HelpTooltip field={field} />
    </div>
  )
}

/**
 * FieldHint - Shows range below input field
 *
 * Displays the valid range in a subtle way below form inputs.
 */
interface FieldHintProps {
  field: FieldDefinition
  className?: string
}

export function FieldHint({ field, className }: FieldHintProps) {
  if (!field.range) return null

  const { min, max } = field.range
  const unit = field.unit || ''

  let rangeText: string
  if (field.format === 'percentage') {
    rangeText = `${min * 100}% to ${max * 100}%`
  } else if (field.format === 'multiplier') {
    rangeText = `${min}x to ${max}x`
  } else {
    rangeText = `${min} to ${max}${unit ? ` ${unit}` : ''}`
  }

  return <span className={cn('text-xs text-text-tertiary', className)}>Range: {rangeText}</span>
}
