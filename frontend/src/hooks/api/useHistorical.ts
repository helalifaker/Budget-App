/**
 * Historical Comparison Hooks
 *
 * React Query hooks for fetching planning data with historical actuals.
 */

import { useQuery } from '@tanstack/react-query'
import { historicalService } from '@/services/historical'

/**
 * Query keys for historical data
 */
export const historicalKeys = {
  all: ['historical'] as const,
  enrollment: (versionId: string) => [...historicalKeys.all, 'enrollment', versionId] as const,
  classes: (versionId: string) => [...historicalKeys.all, 'classes', versionId] as const,
  dhg: (versionId: string) => [...historicalKeys.all, 'dhg', versionId] as const,
  revenue: (versionId: string) => [...historicalKeys.all, 'revenue', versionId] as const,
  costs: (versionId: string) => [...historicalKeys.all, 'costs', versionId] as const,
  capex: (versionId: string) => [...historicalKeys.all, 'capex', versionId] as const,
}

interface UseHistoricalOptions {
  /** Whether to include historical data (can be used as toggle) */
  enabled?: boolean
  /** Number of historical years to fetch */
  historyYears?: number
}

/**
 * Hook to fetch enrollment data with historical comparison
 */
export function useEnrollmentWithHistory(
  versionId: string | undefined,
  options?: UseHistoricalOptions
) {
  return useQuery({
    queryKey: historicalKeys.enrollment(versionId ?? ''),
    queryFn: () =>
      historicalService.getEnrollmentWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch class structure data with historical comparison
 */
export function useClassesWithHistory(
  versionId: string | undefined,
  options?: UseHistoricalOptions
) {
  return useQuery({
    queryKey: historicalKeys.classes(versionId ?? ''),
    queryFn: () =>
      historicalService.getClassesWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000,
  })
}

/**
 * Hook to fetch DHG data with historical comparison
 */
export function useDHGWithHistory(versionId: string | undefined, options?: UseHistoricalOptions) {
  return useQuery({
    queryKey: historicalKeys.dhg(versionId ?? ''),
    queryFn: () =>
      historicalService.getDHGWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000,
  })
}

/**
 * Hook to fetch revenue data with historical comparison
 */
export function useRevenueWithHistory(
  versionId: string | undefined,
  options?: UseHistoricalOptions
) {
  return useQuery({
    queryKey: historicalKeys.revenue(versionId ?? ''),
    queryFn: () =>
      historicalService.getRevenueWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000,
  })
}

/**
 * Hook to fetch costs data with historical comparison
 */
export function useCostsWithHistory(versionId: string | undefined, options?: UseHistoricalOptions) {
  return useQuery({
    queryKey: historicalKeys.costs(versionId ?? ''),
    queryFn: () =>
      historicalService.getCostsWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000,
  })
}

/**
 * Hook to fetch CapEx data with historical comparison
 */
export function useCapExWithHistory(versionId: string | undefined, options?: UseHistoricalOptions) {
  return useQuery({
    queryKey: historicalKeys.capex(versionId ?? ''),
    queryFn: () =>
      historicalService.getCapExWithHistory(versionId!, {
        history_years: options?.historyYears ?? 2,
      }),
    enabled: !!versionId && (options?.enabled ?? true),
    staleTime: 30000,
  })
}
