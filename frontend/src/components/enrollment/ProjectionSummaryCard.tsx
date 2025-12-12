import { memo, useMemo } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Users,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  ChevronDown,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { YearProjection } from '@/types/enrollmentProjection'

interface ProjectionSummaryCardProps {
  /** Projection results by year */
  projections: YearProjection[]
  /** Maximum school capacity */
  maxCapacity: number
  /** Current year student count (for comparison) */
  currentYearTotal?: number
  /** Callback when "View Detailed Breakdown" is clicked */
  onViewDetails?: () => void
  /** Additional CSS classes */
  className?: string
}

/**
 * ProjectionSummaryCard - Human-readable results summary
 *
 * Displays projection results in a way school directors can understand:
 * - Key metrics: Next Year, In 5 Years, Annual Growth
 * - Capacity warnings when projections exceed limits
 * - Budget impact explanations
 *
 * Uses sage accent for success state, terracotta for warnings.
 */
export const ProjectionSummaryCard = memo(function ProjectionSummaryCard({
  projections,
  maxCapacity,
  currentYearTotal,
  onViewDetails,
  className,
}: ProjectionSummaryCardProps) {
  // Calculate summary metrics
  const summary = useMemo(() => {
    if (projections.length === 0) {
      return null
    }

    const firstYear = projections[0]
    const lastYear = projections[projections.length - 1]
    const years = projections.length

    // Calculate CAGR (Compound Annual Growth Rate)
    const cagr =
      years > 1
        ? (Math.pow(lastYear.total_students / firstYear.total_students, 1 / (years - 1)) - 1) * 100
        : 0

    // Find years at or over capacity
    const yearsOverCapacity = projections.filter((p) => p.total_students >= maxCapacity * 0.95)

    // Change from current year
    const changeFromCurrent = currentYearTotal ? firstYear.total_students - currentYearTotal : null

    // Total change over projection period
    const totalChange = lastYear.total_students - firstYear.total_students

    return {
      nextYear: {
        schoolYear: firstYear.school_year,
        total: firstYear.total_students,
        changeFromCurrent,
        utilizationRate: firstYear.utilization_rate,
      },
      finalYear: {
        schoolYear: lastYear.school_year,
        total: lastYear.total_students,
        totalChange,
      },
      growth: {
        cagr,
        yearsOverCapacity: yearsOverCapacity.length,
        firstOverCapacityYear: yearsOverCapacity[0]?.school_year,
      },
    }
  }, [projections, maxCapacity, currentYearTotal])

  if (!summary) {
    return null
  }

  const hasCapacityWarning = summary.growth.yearsOverCapacity > 0
  const isPositiveGrowth = summary.growth.cagr > 0

  return (
    <Card
      className={cn(
        'border-2',
        hasCapacityWarning ? 'border-terracotta bg-terracotta/5' : 'border-sage bg-sage-lighter',
        className
      )}
    >
      <CardContent className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          {hasCapacityWarning ? (
            <div className="flex items-center justify-center h-10 w-10 rounded-full bg-terracotta text-white">
              <AlertTriangle className="h-5 w-5" />
            </div>
          ) : (
            <div className="flex items-center justify-center h-10 w-10 rounded-full bg-sage text-white">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          )}
          <div>
            <h3
              className={cn('font-semibold', hasCapacityWarning ? 'text-terracotta' : 'text-sage')}
            >
              {hasCapacityWarning
                ? 'Projection Calculated — Attention Needed'
                : 'Projection Calculated'}
            </h3>
            <p className="text-sm text-text-secondary">
              {hasCapacityWarning
                ? `Capacity exceeded in ${summary.growth.yearsOverCapacity} year(s)`
                : 'Your projections are within school capacity'}
            </p>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Next Year */}
          <div className="bg-white rounded-lg p-4 border border-border-light">
            <div className="flex items-center gap-2 text-text-secondary mb-2">
              <Calendar className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wider">Next Year</span>
            </div>
            <div className="text-2xl font-bold text-text-primary">
              {summary.nextYear.total.toLocaleString()}
            </div>
            <div className="text-xs text-text-secondary">{summary.nextYear.schoolYear}</div>
            {summary.nextYear.changeFromCurrent !== null && (
              <div
                className={cn(
                  'flex items-center gap-1 mt-2 text-sm',
                  summary.nextYear.changeFromCurrent >= 0 ? 'text-sage' : 'text-terracotta'
                )}
              >
                {summary.nextYear.changeFromCurrent >= 0 ? (
                  <ArrowUpRight className="h-4 w-4" />
                ) : (
                  <ArrowDownRight className="h-4 w-4" />
                )}
                <span>
                  {summary.nextYear.changeFromCurrent >= 0 ? '+' : ''}
                  {summary.nextYear.changeFromCurrent} vs today
                </span>
              </div>
            )}
          </div>

          {/* In 5 Years */}
          <div className="bg-white rounded-lg p-4 border border-border-light">
            <div className="flex items-center gap-2 text-text-secondary mb-2">
              <Users className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wider">
                In {projections.length - 1} Years
              </span>
            </div>
            <div className="text-2xl font-bold text-text-primary">
              {summary.finalYear.total.toLocaleString()}
            </div>
            <div className="text-xs text-text-secondary">{summary.finalYear.schoolYear}</div>
            <div
              className={cn(
                'flex items-center gap-1 mt-2 text-sm',
                summary.finalYear.totalChange >= 0 ? 'text-sage' : 'text-terracotta'
              )}
            >
              {summary.finalYear.totalChange >= 0 ? (
                <ArrowUpRight className="h-4 w-4" />
              ) : (
                <ArrowDownRight className="h-4 w-4" />
              )}
              <span>
                {summary.finalYear.totalChange >= 0 ? '+' : ''}
                {summary.finalYear.totalChange} total
              </span>
            </div>
          </div>

          {/* Annual Growth */}
          <div className="bg-white rounded-lg p-4 border border-border-light">
            <div className="flex items-center gap-2 text-text-secondary mb-2">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wider">Annual Growth</span>
            </div>
            <div
              className={cn(
                'text-2xl font-bold',
                isPositiveGrowth ? 'text-sage' : 'text-terracotta'
              )}
            >
              {isPositiveGrowth ? '+' : ''}
              {summary.growth.cagr.toFixed(1)}%
            </div>
            <div className="text-xs text-text-secondary">per year (CAGR)</div>
          </div>
        </div>

        {/* Capacity Warning */}
        {hasCapacityWarning && (
          <div className="bg-terracotta/10 border border-terracotta/30 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-terracotta flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-terracotta">Attention Needed</h4>
                <p className="text-sm text-text-secondary mt-1">
                  Year {summary.growth.firstOverCapacityYear} projections approach or exceed school
                  capacity ({maxCapacity.toLocaleString()} students). Consider planning for
                  expansion or enrollment caps.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Budget Impact */}
        <details className="group">
          <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-text-primary hover:text-sage">
            <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
            What this means for your budget
          </summary>
          <div className="mt-3 pl-6 space-y-2 text-sm text-text-secondary">
            <p className="flex items-start gap-2">
              <span className="text-sage font-medium">•</span>
              <span>
                <strong>More students → More tuition revenue</strong> — Revenue projections will
                increase proportionally.
              </span>
            </p>
            <p className="flex items-start gap-2">
              <span className="text-sage font-medium">•</span>
              <span>
                <strong>More students → More teachers needed</strong> — See DHG Planning for
                staffing requirements.
              </span>
            </p>
            <p className="flex items-start gap-2">
              <span className="text-sage font-medium">•</span>
              <span>
                <strong>Net financial impact</strong> — Review in Budget Consolidation for the
                complete picture.
              </span>
            </p>
          </div>
        </details>

        {/* View Details Button */}
        {onViewDetails && (
          <button
            type="button"
            onClick={onViewDetails}
            className="w-full text-center text-sm text-sage hover:text-sage-hover font-medium py-2 border-t border-border-light"
          >
            View Detailed Breakdown ↓
          </button>
        )}
      </CardContent>
    </Card>
  )
})
