import { Link } from '@tanstack/react-router'
import { CheckCircle2, ArrowRight, Edit3, type LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/**
 * Definition of a next step in the workflow
 */
export interface NextStep {
  /** Step number (1, 2, 3) */
  number: number
  /** Title of the step */
  title: string
  /** Description of what this step does */
  description: string
  /** Icon to display */
  icon: LucideIcon
  /** Navigation href */
  href: string
}

interface WhatsNextCardProps {
  /** Title shown in the success header */
  successTitle: string
  /** Description of what was accomplished */
  successDescription: string
  /** List of next steps to show */
  nextSteps: NextStep[]
  /** Callback when user wants to edit/unlock */
  onEdit?: () => void
  /** Label for the edit button */
  editLabel?: string
  /** Label for the stay button */
  stayLabel?: string
  /** Footer help text */
  footerText?: string
  /** Theme accent color */
  accentColor?: 'sage' | 'gold' | 'blue' | 'purple'
  /** Additional CSS classes */
  className?: string
}

/**
 * Color theme mappings for different modules
 */
const COLOR_THEMES = {
  sage: {
    border: 'border-sage',
    bg: 'bg-sage-lighter',
    iconBg: 'bg-sage',
    iconText: 'text-white',
    title: 'text-sage',
    sectionTitle: 'text-sage',
    stepBg: 'bg-sage-light',
    stepText: 'text-sage',
    stepBorder: 'border-sage-light',
    buttonBorder: 'border-sage',
    buttonText: 'text-sage',
    buttonHoverBg: 'hover:bg-sage',
    buttonHoverText: 'hover:text-white',
    footerBorder: 'border-sage-light',
  },
  gold: {
    border: 'border-efir-gold-500',
    bg: 'bg-efir-gold-50',
    iconBg: 'bg-efir-gold-500',
    iconText: 'text-white',
    title: 'text-efir-gold-700',
    sectionTitle: 'text-efir-gold-700',
    stepBg: 'bg-efir-gold-100',
    stepText: 'text-efir-gold-700',
    stepBorder: 'border-efir-gold-200',
    buttonBorder: 'border-efir-gold-500',
    buttonText: 'text-efir-gold-700',
    buttonHoverBg: 'hover:bg-efir-gold-500',
    buttonHoverText: 'hover:text-white',
    footerBorder: 'border-efir-gold-200',
  },
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-50',
    iconBg: 'bg-blue-500',
    iconText: 'text-white',
    title: 'text-blue-700',
    sectionTitle: 'text-blue-700',
    stepBg: 'bg-blue-100',
    stepText: 'text-blue-700',
    stepBorder: 'border-blue-200',
    buttonBorder: 'border-blue-500',
    buttonText: 'text-blue-700',
    buttonHoverBg: 'hover:bg-blue-500',
    buttonHoverText: 'hover:text-white',
    footerBorder: 'border-blue-200',
  },
  purple: {
    border: 'border-purple-500',
    bg: 'bg-purple-50',
    iconBg: 'bg-purple-500',
    iconText: 'text-white',
    title: 'text-purple-700',
    sectionTitle: 'text-purple-700',
    stepBg: 'bg-purple-100',
    stepText: 'text-purple-700',
    stepBorder: 'border-purple-200',
    buttonBorder: 'border-purple-500',
    buttonText: 'text-purple-700',
    buttonHoverBg: 'hover:bg-purple-500',
    buttonHoverText: 'hover:text-white',
    footerBorder: 'border-purple-200',
  },
}

/**
 * WhatsNextCard - Post-completion navigation guide
 *
 * Shows users what to do after completing a workflow step:
 * - Success message with what was accomplished
 * - Recommended next steps with navigation buttons
 * - Option to edit/unlock if needed
 *
 * Can be themed for different modules using accentColor prop.
 */
export function WhatsNextCard({
  successTitle,
  successDescription,
  nextSteps,
  onEdit,
  editLabel = 'Edit',
  stayLabel = 'Stay on this page',
  footerText = 'Want to make changes?',
  accentColor = 'sage',
  className,
}: WhatsNextCardProps) {
  const theme = COLOR_THEMES[accentColor]

  return (
    <Card className={cn(theme.border, theme.bg, className)}>
      <CardContent className="p-6 space-y-6">
        {/* Success Header */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div
              className={cn(
                'flex items-center justify-center h-12 w-12 rounded-full',
                theme.iconBg,
                theme.iconText
              )}
            >
              <CheckCircle2 className="h-6 w-6" />
            </div>
          </div>
          <div>
            <h3 className={cn('text-lg font-semibold', theme.title)}>{successTitle}</h3>
            <p className="text-sm text-text-secondary mt-1">{successDescription}</p>
          </div>
        </div>

        {/* Recommended Next Steps */}
        <div className="space-y-3">
          <h4 className={cn('text-xs font-semibold uppercase tracking-wider', theme.sectionTitle)}>
            Recommended Next Steps
          </h4>

          <div className="space-y-3">
            {nextSteps.map((step) => {
              const Icon = step.icon
              return (
                <div
                  key={step.number}
                  className={cn(
                    'flex items-start gap-4 p-4 rounded-lg',
                    'bg-white border',
                    theme.stepBorder,
                    'hover:shadow-sm transition-shadow duration-200'
                  )}
                >
                  {/* Step Number */}
                  <div
                    className={cn(
                      'flex items-center justify-center h-8 w-8 rounded-full text-sm font-bold flex-shrink-0',
                      theme.stepBg,
                      theme.stepText
                    )}
                  >
                    {step.number}
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Icon className={cn('h-4 w-4 flex-shrink-0', theme.stepText)} />
                      <span className="font-semibold text-text-primary">{step.title}</span>
                    </div>
                    <p className="text-sm text-text-secondary mt-1">{step.description}</p>
                  </div>

                  {/* Navigation Button */}
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className={cn(
                      'flex-shrink-0 gap-1',
                      theme.buttonBorder,
                      theme.buttonText,
                      theme.buttonHoverBg,
                      theme.buttonHoverText
                    )}
                  >
                    <Link to={step.href}>
                      Go
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer Actions */}
        <div className={cn('flex items-center justify-between pt-4 border-t', theme.footerBorder)}>
          <p className="text-xs text-text-tertiary">{footerText}</p>
          <div className="flex gap-2">
            {onEdit && (
              <Button type="button" variant="ghost" size="sm" onClick={onEdit} className="gap-1.5">
                <Edit3 className="h-3.5 w-3.5" />
                {editLabel}
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className={cn(theme.buttonBorder, theme.buttonText)}
            >
              {stayLabel}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
