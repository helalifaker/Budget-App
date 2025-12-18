import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { CellChange, ChangeHistoryFilters } from '@/types/writeback'

/**
 * Hook for fetching cell change history with pagination
 *
 * Provides access to the audit trail of all cell modifications, supporting
 * undo/redo functionality and change tracking across users.
 *
 * @param versionId - Version ID
 * @param filters - Optional filters (module, entity, field)
 * @returns Change history with pagination controls
 *
 * @example
 * ```typescript
 * const { changes, isLoading, loadMore, hasMore } = useChangeHistory(versionId, {
 *   module_code: 'enrollment',
 *   entity_id: '123',
 *   limit: 50
 * });
 *
 * // Render change history
 * {changes.map(change => (
 *   <div key={change.id}>
 *     {change.field_name}: {change.old_value} → {change.new_value}
 *     <span>by {change.changed_by} at {change.changed_at}</span>
 *   </div>
 * ))}
 *
 * // Load more on scroll
 * {hasMore && <button onClick={loadMore}>Load More</button>}
 * ```
 */
export function useChangeHistory(versionId: string, filters?: ChangeHistoryFilters) {
  const [offset, setOffset] = useState(0)
  const limit = filters?.limit || 100

  // Query for fetching change history
  const query = useQuery({
    queryKey: ['cell-changes', versionId, filters, offset],
    queryFn: async (): Promise<CellChange[]> => {
      // Build query params
      const params = new URLSearchParams()

      if (filters?.module_code) {
        params.append('module_code', filters.module_code)
      }
      if (filters?.entity_id) {
        params.append('entity_id', filters.entity_id)
      }
      if (filters?.field_name) {
        params.append('field_name', filters.field_name)
      }

      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiRequest<CellChange[]>({
        method: 'GET',
        url: `/writeback/cells/changes/${versionId}?${params.toString()}`,
      })

      return response
    },
    enabled: !!versionId,
    staleTime: 30 * 1000, // 30 seconds (change history is relatively static)
    gcTime: 5 * 60 * 1000, // 5 minutes cache
  })

  // Load more changes (pagination)
  const loadMore = useCallback(() => {
    setOffset((prev) => prev + limit)
  }, [limit])

  // Reset to beginning
  const reset = useCallback(() => {
    setOffset(0)
  }, [])

  // Navigate to specific offset
  const goToOffset = useCallback((newOffset: number) => {
    setOffset(Math.max(0, newOffset))
  }, [])

  return {
    changes: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    loadMore,
    reset,
    goToOffset,
    hasMore: (query.data?.length || 0) === limit,
    offset,
    limit,
    refetch: query.refetch,
  }
}

/**
 * Hook for fetching change history for a specific cell
 *
 * Simplified version that fetches only changes for a single cell.
 * Useful for showing detailed change history in cell inspection modals.
 *
 * @param cellId - Cell ID
 * @param limit - Maximum number of changes to fetch (default: 50)
 * @returns Change history for the specific cell
 *
 * @example
 * ```typescript
 * const { changes, isLoading } = useCellHistory(cellId);
 *
 * // Render cell-specific history
 * {changes.map(change => (
 *   <div key={change.id}>
 *     {formatDate(change.changed_at)}: {change.old_value} → {change.new_value}
 *     <span>({change.change_type})</span>
 *   </div>
 * ))}
 * ```
 */
export function useCellHistory(cellId: string, limit = 50) {
  const query = useQuery({
    queryKey: ['cell-history', cellId],
    queryFn: async (): Promise<CellChange[]> => {
      const response = await apiRequest<CellChange[]>({
        method: 'GET',
        url: `/writeback/cells/${cellId}/history?limit=${limit}`,
      })
      return response
    },
    enabled: !!cellId,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  })

  return {
    changes: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  }
}

/**
 * Hook for fetching recent changes across all cells in a budget version
 *
 * Provides a feed of recent activity for dashboards and audit trails.
 *
 * @param versionId - Budget version ID
 * @param limit - Maximum number of changes to fetch (default: 20)
 * @returns Recent changes with auto-refresh
 *
 * @example
 * ```typescript
 * const { recentChanges, isLoading } = useRecentChanges(versionId, 20);
 *
 * // Render activity feed
 * <ActivityFeed>
 *   {recentChanges.map(change => (
 *     <ActivityItem key={change.id} change={change} />
 *   ))}
 * </ActivityFeed>
 * ```
 */
export function useRecentChanges(versionId: string, limit = 20) {
  const query = useQuery({
    queryKey: ['recent-changes', versionId, limit],
    queryFn: async (): Promise<CellChange[]> => {
      const response = await apiRequest<CellChange[]>({
        method: 'GET',
        url: `/writeback/cells/changes/${versionId}?limit=${limit}&offset=0`,
      })
      return response
    },
    enabled: !!versionId,
    staleTime: 10 * 1000, // 10 seconds (more frequent refresh for activity feed)
    gcTime: 2 * 60 * 1000, // 2 minutes cache
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
  })

  return {
    recentChanges: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  }
}
