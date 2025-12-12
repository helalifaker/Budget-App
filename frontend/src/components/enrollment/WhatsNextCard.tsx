import { Link } from '@tanstack/react-router'
import { CheckCircle2, Users, Calculator, BarChart3, ArrowRight, Edit3 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface WhatsNextCardProps {
  /** Callback when user wants to edit projections */
  onEdit?: () => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Next step destinations after enrollment validation
 * Each leads to a dependent module that uses enrollment data
 */
const NEXT_STEPS = [
  {
    number: 1,
    title: 'Class Structure',
    description:
      'Review how students are grouped into classes (auto-calculated based on your projections)',
    icon: Users,
    href: '/enrollment/class-structure',
  },
  {
    number: 2,
    title: 'Teacher Planning (DHG)',
    description: 'Calculate required teaching hours and staffing needs',
    icon: Calculator,
    href: '/planning/dhg',
  },
  {
    number: 3,
    title: 'Budget Consolidation',
    description: 'See the financial impact of your projections',
    icon: BarChart3,
    href: '/consolidation/budget',
  },
]

/**
 * WhatsNextCard - Post-validation navigation guide
 *
 * Shown after successful enrollment validation to help school directors
 * understand:
 * - That their projections are locked
 * - What modules to visit next
 * - The logical workflow order
 *
 * Provides clear navigation buttons to each recommended next step.
 */
export function WhatsNextCard({ onEdit, className }: WhatsNextCardProps) {
  return (
    <Card className={cn('border-sage bg-sage-lighter', className)}>
      <CardContent className="p-6 space-y-6">
        {/* Success Header */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center h-12 w-12 rounded-full bg-sage text-white">
              <CheckCircle2 className="h-6 w-6" />
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-sage">Enrollment Projections Locked</h3>
            <p className="text-sm text-text-secondary mt-1">
              You can now proceed to the next planning steps. Your enrollment numbers are feeding
              into the calculations below.
            </p>
          </div>
        </div>

        {/* Recommended Next Steps */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-sage uppercase tracking-wider">
            Recommended Next Steps
          </h4>

          <div className="space-y-3">
            {NEXT_STEPS.map((step) => {
              const Icon = step.icon
              return (
                <div
                  key={step.number}
                  className={cn(
                    'flex items-start gap-4 p-4 rounded-lg',
                    'bg-white border border-sage-light',
                    'hover:shadow-sm transition-shadow duration-200'
                  )}
                >
                  {/* Step Number */}
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-sage-light text-sage text-sm font-bold flex-shrink-0">
                    {step.number}
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-sage flex-shrink-0" />
                      <span className="font-semibold text-text-primary">{step.title}</span>
                    </div>
                    <p className="text-sm text-text-secondary mt-1">{step.description}</p>
                  </div>

                  {/* Navigation Button */}
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="flex-shrink-0 gap-1 border-sage text-sage hover:bg-sage hover:text-white"
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
        <div className="flex items-center justify-between pt-4 border-t border-sage-light">
          <p className="text-xs text-text-tertiary">
            Want to make changes? You can unlock your projections.
          </p>
          <div className="flex gap-2">
            {onEdit && (
              <Button type="button" variant="ghost" size="sm" onClick={onEdit} className="gap-1.5">
                <Edit3 className="h-3.5 w-3.5" />
                Edit Projections
              </Button>
            )}
            <Button type="button" variant="outline" size="sm" className="border-sage text-sage">
              Stay on this page
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
