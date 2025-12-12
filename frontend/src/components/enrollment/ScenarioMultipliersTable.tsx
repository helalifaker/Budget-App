import { memo, useState, useCallback } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { RotateCcw, TrendingDown, BarChart3, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type {
  ScenarioMultiplier,
  ScenarioMultiplierUpdate,
  ScenarioCode,
} from '@/types/enrollmentSettings'
import { DEFAULT_SCENARIO_MULTIPLIERS } from '@/types/enrollmentSettings'

interface ScenarioMultipliersTableProps {
  multipliers: ScenarioMultiplier[]
  onUpdate: (update: ScenarioMultiplierUpdate) => void
  onReset: () => void
  disabled?: boolean
}

const SCENARIO_CONFIG: Record<
  ScenarioCode,
  {
    icon: typeof TrendingDown
    iconColor: string
    bgColor: string
    label: string
    description: string
  }
> = {
  worst_case: {
    icon: TrendingDown,
    iconColor: 'text-red-600',
    bgColor: 'bg-red-50',
    label: 'Worst Case',
    description: 'Crisis scenario with minimal lateral entry',
  },
  conservative: {
    icon: TrendingDown,
    iconColor: 'text-orange-600',
    bgColor: 'bg-orange-50',
    label: 'Conservative',
    description: 'Cautious planning with reduced expectations',
  },
  base: {
    icon: BarChart3,
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-50',
    label: 'Base Case',
    description: 'Standard projection based on historical trends',
  },
  optimistic: {
    icon: TrendingUp,
    iconColor: 'text-green-600',
    bgColor: 'bg-green-50',
    label: 'Optimistic',
    description: 'Growth scenario with increased lateral entry',
  },
  best_case: {
    icon: TrendingUp,
    iconColor: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    label: 'Best Case',
    description: 'Maximum growth potential scenario',
  },
}

const SCENARIO_ORDER: ScenarioCode[] = [
  'worst_case',
  'conservative',
  'base',
  'optimistic',
  'best_case',
]

/**
 * ScenarioMultipliersTable - Configure lateral entry multipliers for each scenario.
 *
 * Scenario multipliers affect how lateral entry is calculated across all grades:
 * - Base (1.0x): Uses derived/override rates as-is
 * - Conservative (0.6x): Reduces lateral entry by 40%
 * - Optimistic (1.3x): Increases lateral entry by 30%
 *
 * This allows users to model different growth scenarios without changing
 * the underlying grade-level rates.
 */
export const ScenarioMultipliersTable = memo(function ScenarioMultipliersTable({
  multipliers,
  onUpdate,
  onReset,
  disabled = false,
}: ScenarioMultipliersTableProps) {
  const [pendingChanges, setPendingChanges] = useState<Record<string, number>>({})

  const handleSliderChange = useCallback((scenarioCode: string, value: number[]) => {
    setPendingChanges((prev) => ({
      ...prev,
      [scenarioCode]: value[0],
    }))
  }, [])

  const handleSliderCommit = useCallback(
    (scenarioCode: string) => {
      const value = pendingChanges[scenarioCode]
      if (value !== undefined) {
        onUpdate({
          scenario_code: scenarioCode as ScenarioCode,
          lateral_multiplier: value,
        })
        setPendingChanges((prev) => {
          const newChanges = { ...prev }
          delete newChanges[scenarioCode]
          return newChanges
        })
      }
    },
    [pendingChanges, onUpdate]
  )

  // Sort multipliers by scenario order
  const sortedMultipliers = [...multipliers].sort((a, b) => {
    const orderA = SCENARIO_ORDER.indexOf(a.scenario_code as ScenarioCode)
    const orderB = SCENARIO_ORDER.indexOf(b.scenario_code as ScenarioCode)
    return orderA - orderB
  })

  const formatMultiplier = (value: number) => {
    return `${(value * 100).toFixed(0)}%`
  }

  const getMultiplierImpact = (value: number) => {
    if (value < 0.5) return 'Very Low'
    if (value < 0.8) return 'Low'
    if (value < 1.0) return 'Reduced'
    if (value === 1.0) return 'Normal'
    if (value < 1.3) return 'Increased'
    if (value < 1.6) return 'High'
    return 'Very High'
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-sm font-medium">Scenario Multipliers</h3>
          <p className="text-xs text-muted-foreground">
            Adjust how lateral entry rates scale for each scenario
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onReset} disabled={disabled}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset to Defaults
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-[200px]">Scenario</TableHead>
              <TableHead className="w-[300px]">Multiplier</TableHead>
              <TableHead className="w-[100px]">Value</TableHead>
              <TableHead>Impact</TableHead>
              <TableHead className="w-[100px]">Default</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedMultipliers.map((multiplier) => {
              const config = SCENARIO_CONFIG[multiplier.scenario_code as ScenarioCode]
              const currentValue =
                pendingChanges[multiplier.scenario_code] ?? multiplier.lateral_multiplier
              const defaultValue =
                DEFAULT_SCENARIO_MULTIPLIERS[multiplier.scenario_code as ScenarioCode]
              const isModified = Math.abs(multiplier.lateral_multiplier - defaultValue) > 0.001
              const Icon = config?.icon || BarChart3

              return (
                <TableRow key={multiplier.scenario_code}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className={cn('p-1.5 rounded', config?.bgColor || 'bg-gray-50')}>
                        <Icon className={cn('h-4 w-4', config?.iconColor || 'text-gray-600')} />
                      </div>
                      <div>
                        <div className="font-medium">
                          {config?.label || multiplier.scenario_code}
                        </div>
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {config?.description || ''}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Slider
                      value={[currentValue]}
                      min={0.1}
                      max={2.0}
                      step={0.05}
                      onValueChange={(value) => handleSliderChange(multiplier.scenario_code, value)}
                      onValueCommit={() => handleSliderCommit(multiplier.scenario_code)}
                      disabled={disabled}
                      className="w-full"
                    />
                  </TableCell>
                  <TableCell>
                    <span className="font-mono font-semibold">
                      {formatMultiplier(currentValue)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn(
                        currentValue < 1
                          ? 'bg-orange-50 text-orange-700 border-orange-200'
                          : currentValue > 1
                            ? 'bg-green-50 text-green-700 border-green-200'
                            : 'bg-blue-50 text-blue-700 border-blue-200'
                      )}
                    >
                      {getMultiplierImpact(currentValue)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {formatMultiplier(defaultValue)}
                      </span>
                      {isModified && (
                        <Badge variant="secondary" className="text-xs">
                          Modified
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Help Text */}
      <div className="text-xs text-muted-foreground p-3 bg-muted/30 rounded-lg">
        <p>
          <strong>How multipliers work:</strong> A multiplier of 100% uses the calculated lateral
          entry rates as-is. Lower values (e.g., 60%) reduce lateral entry for conservative
          planning. Higher values (e.g., 130%) increase lateral entry for optimistic scenarios.
        </p>
      </div>
    </div>
  )
})
