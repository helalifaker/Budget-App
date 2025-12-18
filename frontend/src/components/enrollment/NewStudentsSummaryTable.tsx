import { Fragment, memo, useMemo } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SkeletonLoader } from '@/components/LoadingState'
import { cn } from '@/lib/utils'
import type {
  NewStudentsSummary,
  NewStudentsSummaryRow,
  OptimizationDecision,
} from '@/types/enrollment-projection'

interface NewStudentsSummaryTableProps {
  data: NewStudentsSummary | undefined
  isLoading?: boolean
  className?: string
}

/**
 * Decision type color mappings for visual indication of optimization outcomes.
 *
 * - ACCEPT_ALL (green): Demand ≤ fill_to_target - comfortable capacity
 * - ACCEPT_FILL_MAX (yellow): Fills to max class size
 * - RESTRICT (orange): Demand capped in awkward middle zone
 * - NEW_CLASS (blue): Demand justifies opening new class
 * - RESTRICT_AT_CEILING (red): At max_divisions limit, cannot expand
 */
const DECISION_STYLES: Record<OptimizationDecision, { badge: string; row: string; label: string }> =
  {
    accept_all: {
      badge: 'bg-green-100 text-green-700 border-green-200 hover:bg-green-100',
      row: 'bg-green-50/50',
      label: 'Accept All',
    },
    accept_fill_max: {
      badge: 'bg-yellow-100 text-yellow-700 border-yellow-200 hover:bg-yellow-100',
      row: 'bg-yellow-50/50',
      label: 'Fill Max',
    },
    restrict: {
      badge: 'bg-orange-100 text-orange-700 border-orange-200 hover:bg-orange-100',
      row: 'bg-orange-50/50',
      label: 'Restricted',
    },
    new_class: {
      badge: 'bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-100',
      row: 'bg-blue-50/50',
      label: 'New Class',
    },
    restrict_at_ceiling: {
      badge: 'bg-red-100 text-red-700 border-red-200 hover:bg-red-100',
      row: 'bg-red-50/50',
      label: 'At Ceiling',
    },
    insufficient_demand: {
      badge: 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-100',
      row: 'bg-gray-50/50',
      label: 'Low Demand',
    },
  }

const CYCLE_COLORS: Record<string, string> = {
  MAT: 'bg-purple-500',
  ELEM: 'bg-green-500',
  COLL: 'bg-blue-500',
  LYC: 'bg-amber-500',
}

const CYCLE_ORDER: Record<string, number> = {
  MAT: 1,
  ELEM: 2,
  COLL: 3,
  LYC: 4,
}

/**
 * NewStudentsSummaryTable - Displays capacity-aware lateral entry optimization results.
 *
 * This component shows how many new students can be efficiently accommodated
 * at each grade level while minimizing rejections and maintaining optimal class structure.
 *
 * Features:
 * - Color-coded decision types for quick visual scanning
 * - Entry point vs incidental grade categorization
 * - Totals with acceptance rate summary
 * - Grouped by cycle for easier navigation
 */
export const NewStudentsSummaryTable = memo(function NewStudentsSummaryTable({
  data,
  isLoading = false,
  className,
}: NewStudentsSummaryTableProps) {
  // Group rows by cycle for organized display
  const groupedRows = useMemo(() => {
    if (!data?.by_grade) return {}

    return data.by_grade.reduce(
      (acc, row) => {
        const cycle = row.cycle_code || 'OTHER'
        if (!acc[cycle]) acc[cycle] = []
        acc[cycle].push(row)
        return acc
      },
      {} as Record<string, NewStudentsSummaryRow[]>
    )
  }, [data?.by_grade])

  // Sort cycles by educational order (MAT → ELEM → COLL → LYC)
  const sortedCycles = useMemo(() => {
    return Object.keys(groupedRows).sort((a, b) => (CYCLE_ORDER[a] ?? 99) - (CYCLE_ORDER[b] ?? 99))
  }, [groupedRows])

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>New Students Summary</CardTitle>
          <CardDescription>Loading optimization results...</CardDescription>
        </CardHeader>
        <CardContent>
          <SkeletonLoader rows={5} />
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>New Students Summary</CardTitle>
          <CardDescription>No optimization data available</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Run the projection calculation to see new student intake optimization.
          </p>
        </CardContent>
      </Card>
    )
  }

  // API returns Decimal as string in JSON, convert to number first
  const formatPercent = (value: number | string) => `${Number(value).toFixed(1)}%`

  const renderRow = (row: NewStudentsSummaryRow) => {
    const style = DECISION_STYLES[row.decision] || DECISION_STYLES.accept_all
    const hasRejections = row.rejected > 0

    return (
      <TableRow key={row.grade_code} className={cn(hasRejections && style.row)}>
        <TableCell className="font-medium">
          <div className="flex items-center gap-2">
            <div
              className={cn('w-2 h-2 rounded-full', CYCLE_COLORS[row.cycle_code] || 'bg-gray-400')}
            />
            {row.grade_name}
          </div>
        </TableCell>
        <TableCell>
          {row.is_entry_point ? (
            <Badge variant="secondary" className="text-xs bg-blue-50 text-blue-600 border-blue-200">
              Entry
            </Badge>
          ) : (
            <Badge variant="outline" className="text-xs">
              Incidental
            </Badge>
          )}
        </TableCell>
        <TableCell className="text-right tabular-nums">{row.historical_demand}</TableCell>
        <TableCell className="text-right tabular-nums">{row.available_slots}</TableCell>
        <TableCell className="text-right tabular-nums font-medium">{row.accepted}</TableCell>
        <TableCell className="text-right tabular-nums">
          <span className={cn(hasRejections && 'text-amber-600 font-medium')}>{row.rejected}</span>
        </TableCell>
        <TableCell className="text-right tabular-nums">
          <span className={cn(Number(row.acceptance_rate) < 100 && 'text-amber-600')}>
            {formatPercent(row.acceptance_rate)}
          </span>
        </TableCell>
        <TableCell className="text-right tabular-nums">
          {formatPercent(row.pct_of_total_intake)}
        </TableCell>
        <TableCell>
          <Badge variant="outline" className={cn('text-xs', style.badge)}>
            {style.label}
          </Badge>
        </TableCell>
      </TableRow>
    )
  }

  const renderCycleSection = (cycle: string, rows: NewStudentsSummaryRow[]) => {
    const cycleName =
      cycle === 'MAT'
        ? 'Maternelle'
        : cycle === 'ELEM'
          ? 'Élémentaire'
          : cycle === 'COLL'
            ? 'Collège'
            : cycle === 'LYC'
              ? 'Lycée'
              : cycle

    return (
      <Fragment key={cycle}>
        {/* Cycle header row - spans all columns */}
        <TableRow className="bg-muted/30 hover:bg-muted/30">
          <TableCell colSpan={9} className="py-2">
            <div className="flex items-center gap-2">
              <div className={cn('w-2 h-2 rounded-full', CYCLE_COLORS[cycle] || 'bg-gray-400')} />
              <span className="text-sm font-medium text-muted-foreground">{cycleName}</span>
            </div>
          </TableCell>
        </TableRow>
        {rows.map(renderRow)}
      </Fragment>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>New Students Summary</span>
          <Badge
            variant="outline"
            className={cn(
              'text-sm',
              Number(data.overall_acceptance_rate) >= 90
                ? 'bg-green-100 text-green-700 border-green-200'
                : Number(data.overall_acceptance_rate) >= 70
                  ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
                  : 'bg-red-100 text-red-700 border-red-200'
            )}
          >
            {formatPercent(data.overall_acceptance_rate)} Acceptance Rate
          </Badge>
        </CardTitle>
        <CardDescription>
          Capacity-aware optimization showing how many new students can be accommodated
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold">{data.total_demand}</div>
            <div className="text-xs text-muted-foreground">Total Demand</div>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold">{data.total_available}</div>
            <div className="text-xs text-muted-foreground">Available Slots</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-700">{data.total_accepted}</div>
            <div className="text-xs text-green-600">Accepted</div>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg">
            <div className="text-2xl font-bold text-amber-700">{data.total_rejected}</div>
            <div className="text-xs text-amber-600">Rejected</div>
          </div>
        </div>

        {/* Entry Points vs Incidental Breakdown */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-3 border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200">
                Entry Points
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Demand:</span>{' '}
                <span className="font-medium">{data.entry_point_demand}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Accepted:</span>{' '}
                <span className="font-medium text-green-600">{data.entry_point_accepted}</span>
              </div>
            </div>
          </div>
          <div className="p-3 border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline">Incidental</Badge>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Demand:</span>{' '}
                <span className="font-medium">{data.incidental_demand}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Accepted:</span>{' '}
                <span className="font-medium text-green-600">{data.incidental_accepted}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Table - max-height with scroll for compact view */}
        <div className="border rounded-lg overflow-hidden">
          <div className="max-h-[400px] overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 z-10">
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[140px] bg-muted/50">Grade</TableHead>
                  <TableHead className="w-[90px] bg-muted/50">Type</TableHead>
                  <TableHead className="text-right w-[80px] bg-muted/50">Demand</TableHead>
                  <TableHead className="text-right w-[80px] bg-muted/50">Available</TableHead>
                  <TableHead className="text-right w-[80px] bg-muted/50">Accepted</TableHead>
                  <TableHead className="text-right w-[80px] bg-muted/50">Rejected</TableHead>
                  <TableHead className="text-right w-[90px] bg-muted/50">Accept %</TableHead>
                  <TableHead className="text-right w-[90px] bg-muted/50">% Intake</TableHead>
                  <TableHead className="w-[100px] bg-muted/50">Decision</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedCycles.map((cycle) => renderCycleSection(cycle, groupedRows[cycle]))}
              </TableBody>
            </Table>
          </div>
          {/* Sticky Footer outside scroll container */}
          <Table>
            <TableFooter>
              <TableRow className="bg-muted/70 font-medium border-t">
                <TableCell className="w-[140px]" colSpan={1}>
                  Total
                </TableCell>
                <TableCell className="w-[90px]" />
                <TableCell className="text-right w-[80px] tabular-nums">
                  {data.total_demand}
                </TableCell>
                <TableCell className="text-right w-[80px] tabular-nums">
                  {data.total_available}
                </TableCell>
                <TableCell className="text-right w-[80px] tabular-nums">
                  {data.total_accepted}
                </TableCell>
                <TableCell className="text-right w-[80px] tabular-nums">
                  {data.total_rejected}
                </TableCell>
                <TableCell className="text-right w-[90px] tabular-nums">
                  {formatPercent(data.overall_acceptance_rate)}
                </TableCell>
                <TableCell className="text-right w-[90px] tabular-nums">100.0%</TableCell>
                <TableCell className="w-[100px]" />
              </TableRow>
            </TableFooter>
          </Table>
        </div>

        {/* Decision Legend */}
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs text-muted-foreground mr-2">Legend:</span>
          {Object.entries(DECISION_STYLES).map(([decision, style]) => (
            <Badge key={decision} variant="outline" className={cn('text-xs', style.badge)}>
              {style.label}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
})
