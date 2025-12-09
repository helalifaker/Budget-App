/**
 * Historical Toggle Component
 *
 * Toggle button for showing/hiding historical comparison columns
 * in planning grids.
 */

import { History, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface HistoricalToggleProps {
  /** Whether historical columns are currently visible */
  showHistorical: boolean
  /** Callback when toggle is clicked */
  onToggle: (show: boolean) => void
  /** Whether the toggle is disabled */
  disabled?: boolean
  /** Whether historical data is loading */
  isLoading?: boolean
  /** Optional class name */
  className?: string
  /** Current fiscal year for display */
  currentFiscalYear?: number
}

export function HistoricalToggle({
  showHistorical,
  onToggle,
  disabled = false,
  isLoading = false,
  className,
  currentFiscalYear,
}: HistoricalToggleProps) {
  const n1Year = currentFiscalYear ? currentFiscalYear - 1 : null
  const n2Year = currentFiscalYear ? currentFiscalYear - 2 : null

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Button
        variant={showHistorical ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToggle(!showHistorical)}
        disabled={disabled || isLoading}
        className="gap-2"
      >
        <History className="h-4 w-4" />
        <span>{showHistorical ? 'Hide' : 'Show'} Historical</span>
        {showHistorical ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </Button>

      {showHistorical && n1Year && n2Year && (
        <span className="text-xs text-sand-500">
          Comparing to FY{n1Year} & FY{n2Year} actuals
        </span>
      )}

      {isLoading && (
        <span className="text-xs text-sand-500 animate-pulse">Loading historical data...</span>
      )}
    </div>
  )
}

/**
 * Summary card for historical comparison totals
 */
interface HistoricalSummaryProps {
  /** Current value */
  currentValue: number
  /** Prior year value */
  priorYearValue: number | null
  /** Percentage change vs prior year */
  changePercent: number | null
  /** Label for the metric */
  label: string
  /** Whether value is currency */
  isCurrency?: boolean
  /** Optional class name */
  className?: string
}

export function HistoricalSummary({
  currentValue,
  priorYearValue,
  changePercent,
  label,
  isCurrency = false,
  className,
}: HistoricalSummaryProps) {
  const formatValue = (val: number | null) => {
    if (val === null) return 'N/A'
    if (isCurrency) {
      return (
        val.toLocaleString('en-SA', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }) + ' SAR'
      )
    }
    return val.toLocaleString()
  }

  const getChangeColor = () => {
    if (changePercent === null) return 'text-sand-500'
    if (changePercent > 0) return 'text-success-600'
    if (changePercent < 0) return 'text-error-600'
    return 'text-sand-500'
  }

  const getChangeIcon = () => {
    if (changePercent === null) return ''
    if (changePercent > 0) return '↑'
    if (changePercent < 0) return '↓'
    return '→'
  }

  return (
    <div
      className={cn('flex flex-col p-3 rounded-lg bg-subtle border border-border-light', className)}
    >
      <span className="text-xs font-medium text-sand-500 uppercase tracking-wider">{label}</span>
      <span className="text-lg font-semibold text-sand-900 mt-1">{formatValue(currentValue)}</span>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-xs text-sand-500">vs Prior: {formatValue(priorYearValue)}</span>
        {changePercent !== null && (
          <span className={cn('text-xs font-medium', getChangeColor())}>
            {getChangeIcon()} {Math.abs(changePercent).toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  )
}
