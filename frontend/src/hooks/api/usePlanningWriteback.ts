import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiRequest } from '@/lib/api-client'
import {
  CellUpdate,
  BatchUpdate,
  CellUpdateResponse,
  BatchUpdateResponse,
  CellData,
  CellLockResponse,
  LockRequest,
  VersionConflictError,
  CellLockedError,
  BatchConflictError,
} from '@/types/writeback'

// Re-export error classes for use in components
export { VersionConflictError, CellLockedError, BatchConflictError }

/**
 * Lock cell request parameters
 */
export interface LockCellParams {
  cellId: string
  reason?: string
}

/**
 * Unlock cell request parameters
 */
export interface UnlockCellParams {
  cellId: string
  reason?: string
}

/**
 * Hook for cell-level writeback with optimistic updates
 *
 * Provides instant UI feedback by optimistically updating the cache before
 * server confirmation. Handles version conflicts, locked cells, and batch updates.
 *
 * @param versionId - Current version
 * @returns Functions for updating cells, batch updates, and loading state
 *
 * @example
 * ```typescript
 * const { updateCell, batchUpdate, isUpdating } = usePlanningWriteback(versionId);
 *
 * // Update single cell
 * await updateCell({
 *   cellId: '123',
 *   value: 150,
 *   version: 5
 * });
 *
 * // Batch update (spreading across periods)
 * await batchUpdate({
 *   sessionId: crypto.randomUUID(),
 *   updates: periods.map(p => ({
 *     cellId: p.cellId,
 *     value: p.value,
 *     version: p.version
 *   }))
 * });
 * ```
 */
export function usePlanningWriteback(versionId: string) {
  const queryClient = useQueryClient()

  // Mutation for single cell update
  const updateCellMutation = useMutation({
    mutationFn: async (update: CellUpdate): Promise<CellUpdateResponse> => {
      try {
        const response = await apiRequest<CellUpdateResponse>({
          method: 'PUT',
          url: `/writeback/cells/${update.cellId}`,
          data: {
            value_numeric: update.value,
            version: update.version,
          },
        })
        return response
      } catch (error: unknown) {
        // Parse error response and throw custom errors
        const errorResponse = (error as { response?: { status: number; data: unknown } }).response

        if (errorResponse?.status === 409) {
          const errorData = errorResponse.data as {
            detail?: {
              message?: string
              cell_id?: string
              expected_version?: number
              actual_version?: number
            }
          }
          throw new VersionConflictError(
            errorData.detail?.message || 'Version conflict detected',
            errorData.detail?.cell_id || update.cellId,
            errorData.detail?.expected_version || update.version,
            errorData.detail?.actual_version || 0
          )
        }

        if (errorResponse?.status === 423) {
          const errorData = errorResponse.data as {
            detail?: {
              message?: string
              cell_id?: string
            }
          }
          throw new CellLockedError(
            errorData.detail?.message || 'Cell is locked',
            errorData.detail?.cell_id || update.cellId
          )
        }

        throw error
      }
    },

    // Optimistic update - update UI immediately before server confirmation
    onMutate: async (update: CellUpdate) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: ['cells', versionId] })

      // Snapshot previous value for rollback on error
      const previousData = queryClient.getQueryData<CellData[]>(['cells', versionId])

      // Optimistically update cache
      queryClient.setQueryData<CellData[]>(['cells', versionId], (old) => {
        if (!old) return old
        return old.map((cell) =>
          cell.id === update.cellId
            ? {
                ...cell,
                value_numeric: update.value,
                version: cell.version + 1,
                modified_at: new Date().toISOString(),
              }
            : cell
        )
      })

      return { previousData }
    },

    // On error, rollback optimistic update
    onError: (err: unknown, _update: CellUpdate, context) => {
      // Rollback to previous state
      if (context?.previousData) {
        queryClient.setQueryData(['cells', versionId], context.previousData)
      }

      // Show appropriate error toast
      if (err instanceof VersionConflictError) {
        toast.error('Cellule modifiée par un autre utilisateur', {
          description: 'Les données ont été rechargées automatiquement.',
          duration: 4000,
        })
        // Refetch to get latest data
        queryClient.invalidateQueries({ queryKey: ['cells', versionId] })
      } else if (err instanceof CellLockedError) {
        toast.error('Cellule verrouillée', {
          description: 'Cette cellule ne peut pas être modifiée.',
          duration: 3000,
        })
      } else if (err instanceof Error) {
        toast.error('Erreur de sauvegarde', {
          description: err.message || 'Une erreur est survenue lors de la sauvegarde.',
          duration: 3000,
        })
      } else {
        toast.error('Erreur de sauvegarde', {
          description: 'Une erreur inconnue est survenue.',
          duration: 3000,
        })
      }
    },

    // On success, update cache with server response
    onSuccess: (data: CellUpdateResponse) => {
      // Brief success confirmation (1 second)
      toast.success('Cellule sauvegardée', {
        duration: 1000,
      })

      // Update cache with authoritative server response
      queryClient.setQueryData<CellData[]>(['cells', versionId], (old) => {
        if (!old) return old
        return old.map((cell) =>
          cell.id === data.id
            ? {
                ...cell,
                value_numeric: data.value_numeric,
                version: data.version,
                modified_by: data.modified_by,
                modified_at: data.modified_at,
              }
            : cell
        )
      })

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['cell-changes', versionId] })
    },
  })

  // Mutation for batch updates
  const batchUpdateMutation = useMutation({
    mutationFn: async (batch: BatchUpdate): Promise<BatchUpdateResponse> => {
      try {
        const response = await apiRequest<BatchUpdateResponse>({
          method: 'POST',
          url: '/writeback/cells/batch',
          data: {
            session_id: batch.sessionId,
            updates: batch.updates.map((u) => ({
              cell_id: u.cellId,
              value_numeric: u.value,
              version: u.version,
            })),
          },
        })
        return response
      } catch (error: unknown) {
        const errorResponse = (error as { response?: { status: number; data: unknown } }).response

        if (errorResponse?.status === 409) {
          const errorData = errorResponse.data as {
            detail?: {
              message?: string
              conflicts?: Array<{
                cell_id: string
                expected_version: number
                actual_version: number
                message: string
              }>
            }
          }
          throw new BatchConflictError(
            errorData.detail?.message || 'Batch update conflicts detected',
            errorData.detail?.conflicts || []
          )
        }

        throw error
      }
    },

    // Optimistic update for batch
    onMutate: async (batch: BatchUpdate) => {
      await queryClient.cancelQueries({ queryKey: ['cells', versionId] })

      const previousData = queryClient.getQueryData<CellData[]>(['cells', versionId])

      // Optimistically update all cells in batch
      queryClient.setQueryData<CellData[]>(['cells', versionId], (old) => {
        if (!old) return old

        const updateMap = new Map(batch.updates.map((u) => [u.cellId, u.value]))

        return old.map((cell) => {
          const newValue = updateMap.get(cell.id)
          if (newValue !== undefined) {
            return {
              ...cell,
              value_numeric: newValue,
              version: cell.version + 1,
              modified_at: new Date().toISOString(),
            }
          }
          return cell
        })
      })

      return { previousData }
    },

    onError: (err: unknown, _batch: BatchUpdate, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['cells', versionId], context.previousData)
      }

      if (err instanceof BatchConflictError) {
        toast.error('Conflits détectés lors de la sauvegarde groupée', {
          description: `${err.conflicts.length} cellule(s) ont été modifiées par un autre utilisateur.`,
          duration: 5000,
        })
        // Refetch to get latest
        queryClient.invalidateQueries({ queryKey: ['cells', versionId] })
      } else if (err instanceof Error) {
        toast.error('Erreur de sauvegarde groupée', {
          description: err.message || 'Une erreur est survenue lors de la sauvegarde.',
          duration: 3000,
        })
      } else {
        toast.error('Erreur de sauvegarde groupée', {
          description: 'Une erreur inconnue est survenue.',
          duration: 3000,
        })
      }
    },

    onSuccess: (data: BatchUpdateResponse) => {
      const hasConflicts = data.conflicts.length > 0

      if (hasConflicts) {
        toast.warning(`${data.updated_count} cellules sauvegardées`, {
          description: `${data.conflicts.length} conflit(s) détecté(s). Les données ont été rechargées.`,
          duration: 5000,
        })
      } else {
        toast.success(`${data.updated_count} cellules sauvegardées`, {
          duration: 2000,
        })
      }

      // Invalidate to refetch latest data
      queryClient.invalidateQueries({ queryKey: ['cells', versionId] })
      queryClient.invalidateQueries({ queryKey: ['cell-changes', versionId] })
    },
  })

  // Mutation for locking a cell
  const lockCellMutation = useMutation({
    mutationFn: async (params: LockCellParams): Promise<CellLockResponse> => {
      const response = await apiRequest<CellLockResponse>({
        method: 'POST',
        url: `/writeback/cells/${params.cellId}/lock`,
        data: {
          lock_reason: params.reason || 'Cellule verrouillée manuellement',
        } as LockRequest,
      })
      return response
    },

    onSuccess: (data: CellLockResponse) => {
      toast.success('Cellule verrouillée', {
        description: data.lock_reason || 'La cellule ne peut plus être modifiée.',
        duration: 3000,
      })

      // Update cache to reflect locked state
      queryClient.setQueryData<CellData[]>(['cells', versionId], (old) => {
        if (!old) return old
        return old.map((cell) =>
          cell.id === data.id
            ? {
                ...cell,
                is_locked: true,
              }
            : cell
        )
      })

      // Invalidate to refetch latest data
      queryClient.invalidateQueries({ queryKey: ['cells', versionId] })
    },

    onError: (err: unknown) => {
      if (err instanceof Error) {
        toast.error('Erreur lors du verrouillage', {
          description: err.message || 'Impossible de verrouiller la cellule.',
          duration: 3000,
        })
      } else {
        toast.error('Erreur lors du verrouillage', {
          description: 'Une erreur inconnue est survenue.',
          duration: 3000,
        })
      }
    },
  })

  // Mutation for unlocking a cell
  const unlockCellMutation = useMutation({
    mutationFn: async (params: UnlockCellParams): Promise<CellLockResponse> => {
      const response = await apiRequest<CellLockResponse>({
        method: 'DELETE',
        url: `/writeback/cells/${params.cellId}/lock`,
        data: {
          unlock_reason: params.reason,
        },
      })
      return response
    },

    onSuccess: (data: CellLockResponse) => {
      toast.success('Cellule déverrouillée', {
        description: 'La cellule peut maintenant être modifiée.',
        duration: 3000,
      })

      // Update cache to reflect unlocked state
      queryClient.setQueryData<CellData[]>(['cells', versionId], (old) => {
        if (!old) return old
        return old.map((cell) =>
          cell.id === data.id
            ? {
                ...cell,
                is_locked: false,
              }
            : cell
        )
      })

      // Invalidate to refetch latest data
      queryClient.invalidateQueries({ queryKey: ['cells', versionId] })
    },

    onError: (err: unknown) => {
      if (err instanceof Error) {
        toast.error('Erreur lors du déverrouillage', {
          description: err.message || 'Impossible de déverrouiller la cellule.',
          duration: 3000,
        })
      } else {
        toast.error('Erreur lors du déverrouillage', {
          description: 'Une erreur inconnue est survenue.',
          duration: 3000,
        })
      }
    },
  })

  return {
    updateCell: updateCellMutation.mutateAsync,
    batchUpdate: batchUpdateMutation.mutateAsync,
    lockCell: lockCellMutation.mutateAsync,
    unlockCell: unlockCellMutation.mutateAsync,
    isUpdating: updateCellMutation.isPending || batchUpdateMutation.isPending,
    isLocking: lockCellMutation.isPending || unlockCellMutation.isPending,
    error: updateCellMutation.error || batchUpdateMutation.error,
    // Direct mutation access for advanced use cases
    updateCellMutation,
    batchUpdateMutation,
    lockCellMutation,
    unlockCellMutation,
  }
}
