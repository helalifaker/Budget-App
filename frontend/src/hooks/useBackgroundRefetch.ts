import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'

/**
 * Hook for automatically refetching queries in the background at a specified interval
 *
 * Useful for keeping dashboard data, KPIs, and activity feeds fresh without user interaction
 *
 * @param queryKey - The query key to refetch
 * @param intervalMs - Interval in milliseconds (default: 60000ms = 1 minute)
 *
 * @example
 * // Refetch KPIs every minute
 * useBackgroundRefetch(['kpi-dashboard', budgetVersionId], 60000)
 *
 * @example
 * // Refetch activity feed every 30 seconds
 * useBackgroundRefetch(['analysis', 'activity'], 30000)
 */
export function useBackgroundRefetch(queryKey: unknown[], intervalMs: number = 60000) {
  const queryClient = useQueryClient()

  useEffect(() => {
    // Don't set up interval if queryKey is empty
    if (queryKey.length === 0) {
      return
    }

    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey })
    }, intervalMs)

    return () => clearInterval(interval)
  }, [queryClient, queryKey, intervalMs])
}
