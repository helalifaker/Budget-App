import { useQuery } from '@tanstack/react-query'
import { planningProgressApi } from '@/services/planning-progress'

/**
 * Query keys for planning progress
 */
export const planningProgressKeys = {
  all: ['planning-progress'] as const,
  byVersion: (versionId: string) => [...planningProgressKeys.all, versionId] as const,
}

/**
 * Hook to fetch planning progress for a version
 *
 * Automatically refreshes every 30 seconds to show real-time progress updates.
 *
 * @param versionId - Version UUID (optional)
 * @returns Query result with planning progress data
 */
export function usePlanningProgress(versionId: string | undefined) {
  return useQuery({
    queryKey: planningProgressKeys.byVersion(versionId ?? ''),
    queryFn: () => planningProgressApi.getProgress(versionId!),
    enabled: !!versionId,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  })
}
