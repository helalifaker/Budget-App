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
  /** Theme accent color (default: sage) */
  accentColor?: 'sage' | 'gold' | 'blue' | 'purple'
  /** Additional class names */
  className?: string
}

/**
 * Color theme mappings for different modules
 */
const COLOR_THEMES = {
  sage: {
    border: 'border-sage',
    bg: 'bg-sage-lighter',
    numberBg: 'bg-sage',
    numberText: 'text-white',
    sectionTitle: 'text-sage',
    stepBg: 'bg-sage-light',
    stepText: 'text-sage',
    tipBorder: 'border-sage-light',
  },
  gold: {
    border: 'border-efir-gold-500',
    bg: 'bg-efir-gold-50',
    numberBg: 'bg-efir-gold-500',
    numberText: 'text-white',
    sectionTitle: 'text-efir-gold-700',
    stepBg: 'bg-efir-gold-100',
    stepText: 'text-efir-gold-700',
    tipBorder: 'border-efir-gold-200',
  },
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-50',
    numberBg: 'bg-blue-500',
    numberText: 'text-white',
    sectionTitle: 'text-blue-700',
    stepBg: 'bg-blue-100',
    stepText: 'text-blue-700',
    tipBorder: 'border-blue-200',
  },
  purple: {
    border: 'border-purple-500',
    bg: 'bg-purple-50',
    numberBg: 'bg-purple-500',
    numberText: 'text-white',
    sectionTitle: 'text-purple-700',
    stepBg: 'bg-purple-100',
    stepText: 'text-purple-700',
    tipBorder: 'border-purple-200',
  },
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
 * Can be themed for different modules using accentColor prop.
 */
export function StepIntroCard({
  stepNumber,
  title,
  why,
  whatToDo,
  tip,
  accentColor = 'sage',
  className,
}: StepIntroCardProps) {
  const theme = COLOR_THEMES[accentColor]

  return (
    <div className={cn('rounded-lg border-l-4 p-4 shadow-sm', theme.border, theme.bg, className)}>
      {/* Header with step number and title */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className={cn(
            'flex items-center justify-center',
            'h-8 w-8 rounded-full',
            theme.numberBg,
            theme.numberText,
            'text-sm font-bold'
          )}
        >
          {stepNumber}
        </div>
        <h3 className="text-lg font-semibold text-text-primary uppercase tracking-wide">{title}</h3>
      </div>

      {/* WHY THIS STEP section */}
      <div className="mb-4">
        <h4
          className={cn('text-xs font-semibold uppercase tracking-wider mb-1', theme.sectionTitle)}
        >
          Why This Step
        </h4>
        <p className="text-sm text-text-secondary leading-relaxed">{why}</p>
      </div>

      {/* WHAT TO DO section */}
      <div className="mb-4">
        <h4
          className={cn('text-xs font-semibold uppercase tracking-wider mb-2', theme.sectionTitle)}
        >
          What To Do
        </h4>
        <ol className="space-y-1.5">
          {whatToDo.map((item, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-text-secondary">
              <span
                className={cn(
                  'flex-shrink-0 h-5 w-5 rounded-full text-xs font-medium flex items-center justify-center',
                  theme.stepBg,
                  theme.stepText
                )}
              >
                {index + 1}
              </span>
              <span className="leading-relaxed">{item}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Optional TIP section */}
      {tip && (
        <div className={cn('flex items-start gap-2 pt-3 border-t', theme.tipBorder)}>
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
  accentColor?: 'sage' | 'gold' | 'blue' | 'purple'
  className?: string
}

export function StepIntroCardCompact({
  stepNumber,
  title,
  description,
  accentColor = 'sage',
  className,
}: StepIntroCardCompactProps) {
  const theme = COLOR_THEMES[accentColor]

  return (
    <div className={cn('flex items-start gap-3 p-3 rounded-md', theme.bg, className)}>
      <div
        className={cn(
          'flex items-center justify-center',
          'h-6 w-6 rounded-full',
          theme.numberBg,
          theme.numberText,
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
