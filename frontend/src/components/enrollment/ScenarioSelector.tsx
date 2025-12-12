import { memo } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, TrendingDown, TrendingUp, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EnrollmentScenario } from '@/types/enrollmentProjection'

interface ScenarioSelectorProps {
  scenarios: EnrollmentScenario[]
  selectedScenarioId: string | null
  onSelect: (scenarioId: string) => void
  disabled?: boolean
}

/**
 * Human-friendly scenario metadata
 * Maps technical scenario codes to explanations a school director can understand
 */
const SCENARIO_METADATA: Record<
  string,
  {
    icon: typeof TrendingDown
    iconColor: string
    title: string
    subtitle: string
    badge?: { text: string; variant: 'default' | 'secondary' | 'outline' }
    assumes: string[]
    useWhen: string
  }
> = {
  worst_case: {
    icon: TrendingDown,
    iconColor: 'text-terracotta',
    title: 'Conservative',
    subtitle: 'Prepare for challenges',
    assumes: [
      'Fewer new preschool students than average',
      'Lower student retention (more families leaving)',
      'Slower overall growth',
    ],
    useWhen:
      'Economic uncertainty, increased competition from other schools, or if you want a safety buffer in your budget planning.',
  },
  base: {
    icon: BarChart3,
    iconColor: 'text-sage',
    title: 'Base Case',
    subtitle: 'Expected typical year',
    badge: { text: 'Most Common', variant: 'default' },
    assumes: [
      'New enrollments matching historical average',
      'Typical retention rates (most students stay)',
      'Steady, predictable growth',
    ],
    useWhen:
      "No major changes expected. This is your best estimate based on past performance. Start here if you're unsure.",
  },
  best_case: {
    icon: TrendingUp,
    iconColor: 'text-gold',
    title: 'Optimistic',
    subtitle: 'Growth opportunity',
    assumes: [
      'More new enrollments than average',
      'Higher retention (fewer families leaving)',
      'Accelerated growth',
    ],
    useWhen:
      'New marketing initiatives, reduced competition, expansion plans, or known factors that will increase enrollment.',
  },
}

/**
 * ScenarioSelector - Human-friendly scenario selection cards
 *
 * Redesigned to help school directors understand:
 * - WHAT each scenario assumes
 * - WHEN to use each scenario
 * - Clear visual distinction between selected/unselected
 *
 * Uses sage accent for enrollment module theming.
 */
export const ScenarioSelector = memo(function ScenarioSelector({
  scenarios,
  selectedScenarioId,
  onSelect,
  disabled,
}: ScenarioSelectorProps) {
  return (
    <div className="space-y-4">
      {/* Section Header */}
      <div>
        <h3 className="text-lg font-semibold text-text-primary">Select Your Scenario</h3>
        <p className="text-sm text-text-secondary mt-1">
          Choose the projection scenario that best matches your expectations for next year.
        </p>
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {scenarios.map((scenario) => {
          const isSelected = scenario.id === selectedScenarioId
          const metadata = SCENARIO_METADATA[scenario.code] ?? {
            icon: BarChart3,
            iconColor: 'text-text-secondary',
            title: scenario.name_en,
            subtitle: '',
            assumes: [],
            useWhen: scenario.description_en ?? '',
          }

          const Icon = metadata.icon

          return (
            <Card
              key={scenario.id}
              className={cn(
                'relative transition-all duration-200 cursor-pointer',
                'hover:shadow-md',
                isSelected
                  ? 'border-2 border-sage bg-sage-lighter ring-1 ring-sage/20'
                  : 'border border-border-light hover:border-sage-light'
              )}
              onClick={() => !disabled && onSelect(scenario.id)}
            >
              <CardContent className="p-4 space-y-4">
                {/* Header with icon and title */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className={cn('h-5 w-5', metadata.iconColor)} />
                    <div>
                      <h4 className="font-semibold text-text-primary">{metadata.title}</h4>
                      <p className="text-xs text-text-secondary">{metadata.subtitle}</p>
                    </div>
                  </div>

                  {/* Badge or selected checkmark */}
                  <div className="flex items-center gap-2">
                    {metadata.badge && !isSelected && (
                      <Badge
                        variant={metadata.badge.variant}
                        className="bg-gold/10 text-gold border-gold/20 text-[10px]"
                      >
                        {metadata.badge.text}
                      </Badge>
                    )}
                    {isSelected && (
                      <div className="flex items-center justify-center h-6 w-6 rounded-full bg-sage text-white">
                        <Check className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                </div>

                {/* THIS SCENARIO ASSUMES section */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-sage uppercase tracking-wider">
                    This Scenario Assumes
                  </h5>
                  <ul className="space-y-1">
                    {metadata.assumes.map((assumption, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-text-secondary flex items-start gap-1.5"
                      >
                        <span className="text-sage mt-0.5">•</span>
                        <span>{assumption}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* USE THIS WHEN section */}
                <div className="space-y-1.5">
                  <h5 className="text-xs font-semibold text-sage uppercase tracking-wider">
                    Use This When
                  </h5>
                  <p className="text-xs text-text-secondary leading-relaxed">{metadata.useWhen}</p>
                </div>

                {/* Technical details (collapsed by default, shown on expansion) */}
                <details className="group">
                  <summary className="text-xs text-text-tertiary cursor-pointer hover:text-text-secondary">
                    View technical parameters
                  </summary>
                  <div className="mt-2 text-xs grid grid-cols-2 gap-1 text-text-secondary">
                    <div>PS Entry</div>
                    <div className="text-right font-medium">{scenario.ps_entry}</div>
                    <div>Entry Growth</div>
                    <div className="text-right font-medium">
                      {(Number(scenario.entry_growth_rate) * 100).toFixed(1)}%
                    </div>
                    <div>Retention</div>
                    <div className="text-right font-medium">
                      {(Number(scenario.default_retention) * 100).toFixed(1)}%
                    </div>
                    <div>Lateral Multiplier</div>
                    <div className="text-right font-medium">
                      {Number(scenario.lateral_multiplier).toFixed(2)}x
                    </div>
                  </div>
                </details>

                {/* Select Button */}
                <Button
                  type="button"
                  variant={isSelected ? 'default' : 'outline'}
                  className={cn(
                    'w-full transition-colors',
                    isSelected && 'bg-sage hover:bg-sage-hover'
                  )}
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelect(scenario.id)
                  }}
                  disabled={disabled}
                >
                  {isSelected ? (
                    <span className="flex items-center gap-2">
                      <Check className="h-4 w-4" />
                      Selected
                    </span>
                  ) : (
                    'Select This Scenario'
                  )}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
})
