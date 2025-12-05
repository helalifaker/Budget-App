/**
 * useSidebarStats Hook
 *
 * Aggregates key metrics from multiple API endpoints for sidebar display.
 * Provides real-time stats for:
 * - Total enrollment (students)
 * - Total FTE (workforce)
 * - Total costs (SAR)
 * - CapEx total (investments)
 * - Net margin (financial health)
 *
 * Uses the global BudgetVersionContext for version selection.
 */

import { useMemo } from 'react'
import { useEnrollmentSummary } from '@/hooks/api/useEnrollment'
import { useTeacherRequirements } from '@/hooks/api/useDHG'
import { useCostSummary } from '@/hooks/api/useCosts'
import { useCapExSummary } from '@/hooks/api/useCapEx'
import { useConsolidationStatus } from '@/hooks/api/useConsolidation'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export interface SidebarStats {
  /** Total number of enrolled students */
  totalStudents: number | null
  /** Total FTE (Full-Time Equivalent) teachers */
  totalFTE: number | null
  /** Total costs in SAR */
  totalCosts: number | null
  /** Total CapEx in SAR */
  totalCapEx: number | null
  /** Net margin percentage */
  netMargin: number | null
  /** Total revenue in SAR */
  totalRevenue: number | null
  /** Whether any data is still loading */
  isLoading: boolean
  /** Whether all data has been loaded at least once */
  hasData: boolean
}

/**
 * Format a number for display in sidebar (compact notation)
 * Examples: 1247 → "1.2K", 8200000 → "8.2M"
 */
export function formatCompact(value: number | null): string {
  if (value === null || value === undefined) return '—'

  const absValue = Math.abs(value)

  if (absValue >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (absValue >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`
  }
  return value.toFixed(1)
}

/**
 * Format percentage for display
 */
export function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

/**
 * Format a count number (no decimals)
 */
export function formatCount(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-US').format(Math.round(value))
}

export function useSidebarStats(): SidebarStats {
  const { selectedVersionId } = useBudgetVersion()

  // Fetch all relevant data - only when we have a selected version
  const {
    data: enrollmentData,
    isLoading: enrollmentLoading,
    isSuccess: enrollmentSuccess,
  } = useEnrollmentSummary(selectedVersionId)

  const {
    data: teacherData,
    isLoading: teacherLoading,
    isSuccess: teacherSuccess,
  } = useTeacherRequirements(selectedVersionId ?? '')

  const {
    data: costData,
    isLoading: costLoading,
    isSuccess: costSuccess,
  } = useCostSummary(selectedVersionId ?? '')

  const {
    data: capexData,
    isLoading: capexLoading,
    isSuccess: capexSuccess,
  } = useCapExSummary(selectedVersionId ?? '')

  const {
    data: consolidationData,
    isLoading: consolidationLoading,
    isSuccess: consolidationSuccess,
  } = useConsolidationStatus(selectedVersionId)

  // Aggregate stats from all sources
  const stats = useMemo<SidebarStats>(() => {
    // Calculate total students from enrollment summary
    const totalStudents = enrollmentData?.total_students ?? null

    // Calculate total FTE from teacher requirements
    // Teacher requirements data structure depends on API response
    let totalFTE: number | null = null
    if (teacherData && Array.isArray(teacherData)) {
      totalFTE = teacherData.reduce((sum, item) => {
        // Each item should have fte_required
        return sum + (item.fte_required ?? 0)
      }, 0)
    }

    // Get total costs from cost summary
    const totalCosts = costData?.total_cost ?? null

    // Get total CapEx from summary
    const totalCapEx = capexData?.total_acquisition_cost ?? null

    // Calculate net margin from consolidation data
    let totalRevenue: number | null = null
    let netMargin: number | null = null

    if (consolidationData) {
      totalRevenue = consolidationData.total_revenue ?? null
      const totalExpenses = consolidationData.total_costs ?? null

      if (totalRevenue !== null && totalExpenses !== null && totalRevenue !== 0) {
        const netIncome = totalRevenue - totalExpenses
        netMargin = (netIncome / totalRevenue) * 100
      }
    }

    // Determine loading state
    const isLoading =
      enrollmentLoading || teacherLoading || costLoading || capexLoading || consolidationLoading

    // Has data if at least one endpoint has successfully loaded
    const hasData =
      enrollmentSuccess || teacherSuccess || costSuccess || capexSuccess || consolidationSuccess

    return {
      totalStudents,
      totalFTE,
      totalCosts,
      totalCapEx,
      netMargin,
      totalRevenue,
      isLoading,
      hasData,
    }
  }, [
    enrollmentData,
    teacherData,
    costData,
    capexData,
    consolidationData,
    enrollmentLoading,
    teacherLoading,
    costLoading,
    capexLoading,
    consolidationLoading,
    enrollmentSuccess,
    teacherSuccess,
    costSuccess,
    capexSuccess,
    consolidationSuccess,
  ])

  return stats
}

/**
 * Module-specific stat configuration for sidebar display
 */
export interface ModuleStat {
  /** Display label */
  label: string
  /** Formatted value */
  value: string
  /** Whether this stat is loading */
  loading: boolean
  /** Optional trend indicator: 'up' | 'down' | 'neutral' */
  trend?: 'up' | 'down' | 'neutral'
}

/**
 * Get stats formatted for each sidebar module
 */
export function useModuleStats(): Record<string, ModuleStat | null> {
  const stats = useSidebarStats()

  return useMemo(
    () => ({
      enrollment:
        stats.totalStudents !== null
          ? {
              label: 'Students',
              value: formatCount(stats.totalStudents),
              loading: stats.isLoading,
            }
          : null,

      workforce:
        stats.totalFTE !== null
          ? {
              label: 'FTE',
              value: stats.totalFTE.toFixed(1),
              loading: stats.isLoading,
            }
          : null,

      costs:
        stats.totalCosts !== null
          ? {
              label: 'SAR',
              value: formatCompact(stats.totalCosts),
              loading: stats.isLoading,
            }
          : null,

      investment:
        stats.totalCapEx !== null
          ? {
              label: 'SAR',
              value: formatCompact(stats.totalCapEx),
              loading: stats.isLoading,
            }
          : null,

      financial:
        stats.netMargin !== null
          ? {
              label: 'Margin',
              value: formatPercent(stats.netMargin),
              loading: stats.isLoading,
              trend: stats.netMargin > 0 ? 'up' : stats.netMargin < 0 ? 'down' : 'neutral',
            }
          : null,
    }),
    [stats]
  )
}
