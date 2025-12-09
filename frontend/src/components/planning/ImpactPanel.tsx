/**
 * Impact Panel Component
 *
 * Floating panel that displays real-time impact metrics when users edit
 * budget data. Shows FTE, cost, revenue, and margin impacts.
 */

import { useEffect, useState } from 'react'
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  DollarSign,
  BarChart3,
  Percent,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  formatImpactCurrency,
  formatImpactFTE,
  formatImpactPercent,
} from '@/hooks/useImpactCalculation'
import type { ImpactCalculationResponse } from '@/services/impact'

interface ImpactPanelProps {
  /** Impact metrics to display */
  impact: ImpactCalculationResponse | null
  /** Whether calculation is loading */
  isLoading: boolean
  /** Whether there's a pending calculation (debouncing) */
  isPending?: boolean
  /** Callback when panel is dismissed */
  onDismiss?: () => void
  /** Additional class name */
  className?: string
}

/**
 * Individual metric row in the impact panel
 */
interface MetricRowProps {
  icon: React.ReactNode
  label: string
  value: number
  formatFn: (value: number) => string
  isPositive?: boolean // true = green (good), false = red (bad), undefined = neutral
}

function MetricRow({ icon, label, value, formatFn, isPositive }: MetricRowProps) {
  const TrendIcon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus

  return (
    <div className="flex items-center justify-between py-2 border-b border-border-light last:border-b-0">
      <div className="flex items-center gap-2 text-sand-600">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <TrendIcon
          className={cn(
            'w-4 h-4',
            value === 0
              ? 'text-sand-400'
              : isPositive === true
                ? 'text-success-500'
                : isPositive === false
                  ? 'text-error-500'
                  : value > 0
                    ? 'text-success-500'
                    : 'text-error-500'
          )}
        />
        <span
          className={cn(
            'text-sm font-semibold',
            value === 0
              ? 'text-sand-500'
              : isPositive === true
                ? 'text-success-600'
                : isPositive === false
                  ? 'text-error-600'
                  : value > 0
                    ? 'text-success-600'
                    : 'text-error-600'
          )}
        >
          {formatFn(value)}
        </span>
      </div>
    </div>
  )
}

/**
 * Floating panel that shows impact preview when users edit budget data.
 *
 * Position: Bottom-right corner of the viewport
 *
 * @example
 * ```tsx
 * const { impact, isLoading, isPending, clearImpact } = useImpactCalculation({
 *   versionId: selectedVersionId,
 * })
 *
 * return (
 *   <>
 *     <DataGrid onCellChange={handleCellChange} />
 *     <ImpactPanel
 *       impact={impact}
 *       isLoading={isLoading}
 *       isPending={isPending}
 *       onDismiss={clearImpact}
 *     />
 *   </>
 * )
 * ```
 */
export function ImpactPanel({
  impact,
  isLoading,
  isPending = false,
  onDismiss,
  className,
}: ImpactPanelProps) {
  const [isVisible, setIsVisible] = useState(false)

  // Show panel when impact data arrives or is loading
  useEffect(() => {
    if (impact || isLoading || isPending) {
      setIsVisible(true)
    }
  }, [impact, isLoading, isPending])

  // Hide panel after some inactivity
  useEffect(() => {
    if (!impact && !isLoading && !isPending) {
      const timer = setTimeout(() => setIsVisible(false), 500)
      return () => clearTimeout(timer)
    }
  }, [impact, isLoading, isPending])

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  if (!isVisible) {
    return null
  }

  return (
    <Card
      className={cn(
        'fixed bottom-6 right-6 w-80 shadow-lg border-border-light z-50',
        'animate-in slide-in-from-bottom-4 duration-200',
        className
      )}
    >
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-sand-700 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Impact Preview
        </CardTitle>
        <div className="flex items-center gap-2">
          {(isLoading || isPending) && (
            <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
          )}
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={handleDismiss}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading && !impact ? (
          <div className="py-6 text-center text-sand-500 text-sm">Calculating impact...</div>
        ) : impact ? (
          <div className="space-y-0">
            <MetricRow
              icon={<Users className="w-4 h-4" />}
              label="FTE Change"
              value={impact.fte_change}
              formatFn={formatImpactFTE}
              // More FTE typically means more cost (negative for budget)
              isPositive={undefined}
            />
            <MetricRow
              icon={<DollarSign className="w-4 h-4" />}
              label="Cost Impact"
              value={impact.cost_impact_sar}
              formatFn={formatImpactCurrency}
              // Lower costs are better
              isPositive={impact.cost_impact_sar <= 0}
            />
            <MetricRow
              icon={<DollarSign className="w-4 h-4" />}
              label="Revenue Impact"
              value={impact.revenue_impact_sar}
              formatFn={formatImpactCurrency}
              // Higher revenue is better
              isPositive={impact.revenue_impact_sar >= 0}
            />
            <MetricRow
              icon={<Percent className="w-4 h-4" />}
              label="Margin Impact"
              value={impact.margin_impact_pct}
              formatFn={formatImpactPercent}
              // Higher margin is better
              isPositive={impact.margin_impact_pct >= 0}
            />
            {impact.affected_steps.length > 0 && (
              <div className="pt-2 mt-2 border-t border-border-light">
                <p className="text-xs text-sand-500">Affects: {impact.affected_steps.join(', ')}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="py-6 text-center text-sand-500 text-sm">Edit a value to see impact</div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Minimal version of the impact panel for compact spaces
 */
export function ImpactPanelMini({
  impact,
  isLoading,
  className,
}: Pick<ImpactPanelProps, 'impact' | 'isLoading' | 'className'>) {
  if (!impact && !isLoading) {
    return null
  }

  return (
    <div
      className={cn('flex items-center gap-4 px-4 py-2 bg-subtle rounded-lg text-sm', className)}
    >
      {isLoading ? (
        <div className="flex items-center gap-2 text-sand-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Calculating...</span>
        </div>
      ) : impact ? (
        <>
          <div className="flex items-center gap-1.5">
            <Users className="w-4 h-4 text-sand-500" />
            <span className={cn(impact.fte_change >= 0 ? 'text-success-600' : 'text-error-600')}>
              {formatImpactFTE(impact.fte_change)}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-sand-500" />
            <span
              className={cn(impact.cost_impact_sar <= 0 ? 'text-success-600' : 'text-error-600')}
            >
              {formatImpactCurrency(impact.cost_impact_sar)}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Percent className="w-4 h-4 text-sand-500" />
            <span
              className={cn(impact.margin_impact_pct >= 0 ? 'text-success-600' : 'text-error-600')}
            >
              {formatImpactPercent(impact.margin_impact_pct)}
            </span>
          </div>
        </>
      ) : null}
    </div>
  )
}
