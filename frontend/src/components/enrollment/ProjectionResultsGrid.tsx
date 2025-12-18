import { Fragment, memo, useMemo } from 'react'
import { Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { HistoricalYearData, YearProjection } from '@/types/enrollment-projection'

interface ProjectionResultsGridProps {
  projections: YearProjection[]
  historical_years?: HistoricalYearData[]
  base_year_data?: HistoricalYearData | null
  /**
   * Whether a recalculation is in progress. When true, shows a visual overlay
   * while keeping the stale data visible (stale-while-revalidate pattern).
   */
  isRecalculating?: boolean
}

/**
 * Enhanced Projection Results Grid with multi-level headers.
 *
 * Layout:
 * - Historical section (2 years, gray header)
 * - Base year (current enrollment)
 * - Projection section (future years with R|L|T breakdown)
 *
 * Visual Design:
 * - Clear section separation with headers and borders
 * - Light, readable backgrounds
 * - Sage accent for Total columns (enrollment module color)
 */
export const ProjectionResultsGrid = memo(function ProjectionResultsGrid({
  projections,
  historical_years = [],
  base_year_data,
  isRecalculating = false,
}: ProjectionResultsGridProps) {
  // Memoize all computed values to prevent recalculation
  const { gradeRows, projectionYears, historicalSorted, baseYearActual } = useMemo(() => {
    const grades = projections.length > 0 ? projections[0].grades.map((g) => g.grade_code) : []

    // Historical years sorted oldest to newest
    const histSorted = [...historical_years].sort((a, b) => a.fiscal_year - b.fiscal_year)

    // KEY FIX: All projections are projection years (no longer treating first as base)
    const projYears = projections

    // KEY FIX: Base year is actual enrollment from base_year_data prop
    // This shows the ACTUAL enrollment data (e.g., 2025-26) not projections
    const baseActual = base_year_data || null

    return {
      gradeRows: grades,
      projectionYears: projYears,
      historicalSorted: histSorted,
      baseYearActual: baseActual,
    }
  }, [projections, historical_years, base_year_data])

  // Calculate column spans for section headers
  const historicalColSpan = historicalSorted.length
  const projectionColSpan = projectionYears.length * 3 // R, L, T for each year

  // Empty state
  if (!projections.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Projection Results</CardTitle>
        </CardHeader>
        <CardContent>No projections yet.</CardContent>
      </Card>
    )
  }

  return (
    <div className="relative">
      {/* Stale-While-Revalidate Overlay */}
      {isRecalculating && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/60 backdrop-blur-[1px] rounded-lg">
          <div className="flex items-center gap-2 px-4 py-2 bg-sage/90 text-white rounded-full shadow-lg animate-pulse">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm font-medium">Recalculating projections...</span>
          </div>
        </div>
      )}

      <Card
        className={cn(
          'overflow-hidden transition-opacity duration-200',
          isRecalculating && 'opacity-60'
        )}
      >
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Projection Results</CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              {/* ===== SECTION HEADERS ===== */}
              <thead>
                {/* Row 1: Section labels (Historical | Base | Projection) */}
                <tr>
                  {/* Empty cell above Grade column */}
                  <th className="bg-background" />

                  {/* Historical Section Header */}
                  {historicalColSpan > 0 && (
                    <th
                      colSpan={historicalColSpan}
                      className="px-1 py-1 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground bg-muted/50 border-b border-light"
                    >
                      Historical
                    </th>
                  )}

                  {/* Base year - no section header, just spacing */}
                  {baseYearActual && <th className="bg-background" />}

                  {/* Projection Section Header */}
                  {projectionColSpan > 0 && (
                    <th
                      colSpan={projectionColSpan}
                      className="px-1 py-1 text-center text-xs font-medium uppercase tracking-wide text-sage bg-sage-lighter border-b border-light"
                    >
                      Projection
                    </th>
                  )}
                </tr>

                {/* Row 2: Year labels */}
                <tr className="bg-muted/5">
                  {/* Grade column header */}
                  <th
                    rowSpan={2}
                    className="text-left px-2 py-1.5 font-semibold bg-background border-r-2 border-medium sticky left-0 z-10"
                  >
                    Grade
                  </th>

                  {/* Historical year columns */}
                  {historicalSorted.map((hy, idx) => (
                    <th
                      key={`hist-${hy.fiscal_year}`}
                      rowSpan={2}
                      className={`text-center px-1 py-1.5 font-medium bg-muted/50 min-w-[50px] ${
                        idx === historicalSorted.length - 1
                          ? 'border-r-2 border-medium'
                          : 'border-r border-light'
                      }`}
                    >
                      <div className="text-[10px] text-muted-foreground uppercase">
                        {hy.school_year.split('/')[0].slice(-2)}-
                        {hy.school_year.split('/')[1]?.slice(-2)}
                      </div>
                    </th>
                  ))}

                  {/* Base year column */}
                  {baseYearActual && (
                    <th
                      rowSpan={2}
                      className="text-center px-1 py-1.5 font-semibold bg-gold-lighter border-r-2 border-gold min-w-[54px]"
                    >
                      <div className="text-[10px] text-gold uppercase">Base</div>
                      <div className="text-gold">
                        {baseYearActual.school_year.split('/')[0].slice(-2)}-
                        {baseYearActual.school_year.split('/')[1]?.slice(-2)}
                      </div>
                    </th>
                  )}

                  {/* Projected year columns with R|L|T sub-columns */}
                  {projectionYears.map((py, idx) => (
                    <th
                      key={`proj-${py.fiscal_year}`}
                      colSpan={3}
                      className={`text-center px-1 py-1.5 font-medium bg-background ${
                        idx < projectionYears.length - 1 ? 'border-r border-light' : ''
                      }`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-foreground">
                          {py.school_year.split('/')[0].slice(-2)}-
                          {py.school_year.split('/')[1]?.slice(-2)}
                        </span>
                        {py.was_capacity_constrained && (
                          <span className="text-terracotta text-xs" title="Constrained by capacity">
                            *
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>

                {/* Row 3: Sub-column labels (R|L|T) for projected years */}
                <tr className="border-b-2 border-medium">
                  {/* R|L|T sub-headers for each projected year */}
                  {projectionYears.map((py, yearIdx) => (
                    <Fragment key={`sub-${py.fiscal_year}`}>
                      <th
                        className="text-center px-0.5 py-0.5 text-[10px] font-medium text-muted-foreground bg-muted/30 border-r border-light min-w-[32px]"
                        title="Retained from previous grade"
                      >
                        R
                      </th>
                      <th
                        className="text-center px-0.5 py-0.5 text-[10px] font-medium text-muted-foreground bg-muted/30 border-r border-light min-w-[32px]"
                        title="Lateral entry (new students)"
                      >
                        L
                      </th>
                      <th
                        className={`text-center px-0.5 py-0.5 text-[10px] font-semibold text-sage bg-sage-lighter min-w-[38px] ${
                          yearIdx < projectionYears.length - 1 ? 'border-r border-light' : ''
                        }`}
                        title="Total (R + L)"
                      >
                        T
                      </th>
                    </Fragment>
                  ))}
                </tr>
              </thead>

              {/* ===== DATA ROWS ===== */}
              <tbody className="divide-y divide-light">
                {gradeRows.map((grade) => {
                  const isPSGrade = grade === 'PS'

                  return (
                    <tr key={grade} className="hover:bg-muted/30 transition-colors">
                      {/* Grade label */}
                      <td className="px-2 py-1.5 font-medium text-foreground bg-background border-r-2 border-medium sticky left-0 z-10">
                        {grade}
                      </td>

                      {/* Historical year values */}
                      {historicalSorted.map((hy, idx) => (
                        <td
                          key={`${grade}-hist-${hy.fiscal_year}`}
                          className={`px-1 py-1.5 text-center tabular-nums text-foreground/80 ${
                            idx === historicalSorted.length - 1
                              ? 'border-r-2 border-medium'
                              : 'border-r border-light'
                          }`}
                        >
                          {hy.grades[grade] ?? '-'}
                        </td>
                      ))}

                      {/* Base year value - ACTUAL enrollment from historical data */}
                      {baseYearActual && (
                        <td className="px-1 py-1.5 text-center tabular-nums font-semibold text-gold bg-gold-lighter border-r-2 border-gold">
                          {baseYearActual.grades[grade] ?? '-'}
                        </td>
                      )}

                      {/* Projected years: R, L, T */}
                      {projectionYears.map((py, yearIdx) => {
                        const gradeData = py.grades.find((g) => g.grade_code === grade)
                        const retained = gradeData?.retained_students ?? 0
                        const lateral = gradeData?.lateral_students ?? 0
                        const total = gradeData?.projected_students ?? 0

                        return (
                          <Fragment key={`${grade}-rlt-${py.fiscal_year}`}>
                            {/* R (Retained) - PS has no retention */}
                            <td className="px-0.5 py-1.5 text-center tabular-nums text-muted-foreground border-r border-light">
                              {isPSGrade ? (
                                <span className="text-muted-foreground/30">—</span>
                              ) : (
                                retained
                              )}
                            </td>
                            {/* L (Lateral) */}
                            <td className="px-0.5 py-1.5 text-center tabular-nums text-muted-foreground border-r border-light">
                              {lateral}
                            </td>
                            {/* T (Total) - sage accent for enrollment module */}
                            <td
                              className={`px-0.5 py-1.5 text-center tabular-nums font-semibold text-sage bg-sage-lighter/50 ${
                                yearIdx < projectionYears.length - 1 ? 'border-r border-light' : ''
                              }`}
                            >
                              {total}
                            </td>
                          </Fragment>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>

              {/* ===== TOTAL ROW ===== */}
              <tfoot>
                <tr className="bg-muted/50 border-t-2 border-medium">
                  <td className="px-2 py-1.5 font-bold text-foreground bg-muted border-r-2 border-medium sticky left-0 z-10">
                    TOTAL
                  </td>

                  {/* Historical totals */}
                  {historicalSorted.map((hy, idx) => (
                    <td
                      key={`total-hist-${hy.fiscal_year}`}
                      className={`px-1 py-1.5 text-center tabular-nums font-semibold text-foreground ${
                        idx === historicalSorted.length - 1
                          ? 'border-r-2 border-medium'
                          : 'border-r border-light'
                      }`}
                    >
                      {hy.total_students}
                    </td>
                  ))}

                  {/* Base year total - ACTUAL enrollment from historical data */}
                  {baseYearActual && (
                    <td className="px-1 py-1.5 text-center tabular-nums font-bold text-gold bg-gold-light border-r-2 border-gold">
                      {baseYearActual.total_students}
                    </td>
                  )}

                  {/* Projected year totals: R, L, T */}
                  {projectionYears.map((py, yearIdx) => {
                    // Calculate totals across all grades
                    const totalRetained = py.grades.reduce(
                      (sum, g) => sum + (g.retained_students ?? 0),
                      0
                    )
                    const totalLateral = py.grades.reduce(
                      (sum, g) => sum + (g.lateral_students ?? 0),
                      0
                    )

                    return (
                      <Fragment key={`total-rlt-${py.fiscal_year}`}>
                        <td className="px-0.5 py-1.5 text-center tabular-nums font-medium text-foreground/80 border-r border-light">
                          {totalRetained}
                        </td>
                        <td className="px-0.5 py-1.5 text-center tabular-nums font-medium text-foreground/80 border-r border-light">
                          {totalLateral}
                        </td>
                        <td
                          className={`px-0.5 py-1.5 text-center tabular-nums font-bold text-sage bg-sage-light ${
                            yearIdx < projectionYears.length - 1 ? 'border-r border-light' : ''
                          }`}
                        >
                          {py.total_students}
                        </td>
                      </Fragment>
                    )
                  })}
                </tr>
              </tfoot>
            </table>

            {/* Legend */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground mt-3 px-3 pt-2 border-t border-light">
              <span className="flex items-center gap-1.5">
                <span className="font-semibold text-muted-foreground">R</span>
                <span>Retained (from previous grade)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="font-semibold text-muted-foreground">L</span>
                <span>Lateral Entry (new students)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="font-semibold text-sage">T</span>
                <span>Total (R + L)</span>
              </span>
              {projectionYears.some((py) => py.was_capacity_constrained) && (
                <span className="flex items-center gap-1.5 text-terracotta">
                  <span className="font-semibold">*</span>
                  <span>Constrained by school max capacity</span>
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
})
