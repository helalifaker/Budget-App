import { Lightbulb } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StepIntroCardProps {
  /** Step number (1, 2, 3) */
  stepNumber: number
  /** Title of the step */
  title: string
  /** Why this step is important (business context) */
  why: string
  /** List of things to do in this step */
  whatToDo: readonly string[] | string[]
  /** Optional tip for the user */
  tip?: string
  /** Additional class names */
  className?: string
}

/**
 * StepIntroCard - Explains each workflow step before the user takes action
 *
 * Displays:
 * - Step number and title
 * - WHY THIS STEP section (business context)
 * - WHAT TO DO section (numbered actions)
 * - Optional TIP with lightbulb icon
 *
 * Uses sage accent colors to match the enrollment module theme.
 */
export function StepIntroCard({
  stepNumber,
  title,
  why,
  whatToDo,
  tip,
  className,
}: StepIntroCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border-l-4 border-sage bg-sage-lighter p-4',
        'shadow-sm',
        className
      )}
    >
      {/* Header with step number and title */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className={cn(
            'flex items-center justify-center',
            'h-8 w-8 rounded-full',
            'bg-sage text-white',
            'text-sm font-bold'
          )}
        >
          {stepNumber}
        </div>
        <h3 className="text-lg font-semibold text-text-primary uppercase tracking-wide">{title}</h3>
      </div>

      {/* WHY THIS STEP section */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-sage uppercase tracking-wider mb-1">
          Why This Step
        </h4>
        <p className="text-sm text-text-secondary leading-relaxed">{why}</p>
      </div>

      {/* WHAT TO DO section */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-sage uppercase tracking-wider mb-2">
          What To Do
        </h4>
        <ol className="space-y-1.5">
          {whatToDo.map((item, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-text-secondary">
              <span className="flex-shrink-0 h-5 w-5 rounded-full bg-sage-light text-sage text-xs font-medium flex items-center justify-center">
                {index + 1}
              </span>
              <span className="leading-relaxed">{item}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Optional TIP section */}
      {tip && (
        <div className="flex items-start gap-2 pt-3 border-t border-sage-light">
          <Lightbulb className="h-4 w-4 text-gold flex-shrink-0 mt-0.5" />
          <p className="text-xs text-text-tertiary leading-relaxed">
            <span className="font-medium text-gold">Tip:</span> {tip}
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * StepIntroCardCompact - A more compact version for tighter spaces
 */
interface StepIntroCardCompactProps {
  stepNumber: number
  title: string
  description: string
  className?: string
}

export function StepIntroCardCompact({
  stepNumber,
  title,
  description,
  className,
}: StepIntroCardCompactProps) {
  return (
    <div className={cn('flex items-start gap-3 p-3 rounded-md bg-sage-lighter', className)}>
      <div
        className={cn(
          'flex items-center justify-center',
          'h-6 w-6 rounded-full',
          'bg-sage text-white',
          'text-xs font-bold flex-shrink-0'
        )}
      >
        {stepNumber}
      </div>
      <div>
        <h4 className="text-sm font-medium text-text-primary">{title}</h4>
        <p className="text-xs text-text-secondary mt-0.5">{description}</p>
      </div>
    </div>
  )
}
