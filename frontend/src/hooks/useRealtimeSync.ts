import { useEffect, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'
import type { CellData, SubscriptionStatus, RealtimeSyncOptions } from '@/types/writeback'

/**
 * Realtime payload structure from Supabase
 */
interface RealtimePayload<T> {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE'
  new: T | Record<string, never>
  old: T | Record<string, never>
  errors: string[] | null
}

/**
 * Hook for real-time synchronization of planning cells
 *
 * Subscribes to changes on planning_cells table and updates React Query cache.
 * Shows toast notifications when another user edits a cell the current user is viewing.
 * Implements automatic reconnection on network failures.
 *
 * @param options - Configuration options for realtime sync
 * @param options.budgetVersionId - Current budget version to subscribe to
 * @param options.onCellChanged - Optional callback when cell changes (from other users)
 * @param options.onConnectionChange - Optional callback for connection status changes
 * @param options.showNotifications - Whether to show toast notifications (default: true)
 *
 * @returns Object containing connection status and manual reconnect function
 *
 * @example
 * ```tsx
 * function EnrollmentPlanningGrid() {
 *   const budgetVersionId = useBudgetVersion();
 *   const { status } = useRealtimeSync({
 *     budgetVersionId,
 *     onCellChanged: (change) => {
 *       console.log('Cell changed by:', change.userId);
 *       highlightCell(change.cell.id);
 *     },
 *   });
 *
 *   return <div>Status: {status}</div>;
 * }
 * ```
 */
export function useRealtimeSync(options: RealtimeSyncOptions) {
  const { budgetVersionId, onCellChanged, onConnectionChange, showNotifications = true } = options

  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [status, setStatus] = useState<SubscriptionStatus>('IDLE')
  const [channel, setChannel] = useState<RealtimeChannel | null>(null)

  // Update status and notify callback
  const updateStatus = useCallback(
    (newStatus: SubscriptionStatus) => {
      setStatus(newStatus)
      onConnectionChange?.(newStatus)
    },
    [onConnectionChange]
  )

  // Handle realtime change events
  const handleChange = useCallback(
    (payload: RealtimePayload<CellData>) => {
      const { eventType, new: newRecord, old: oldRecord } = payload

      // Determine the record to use - type narrowing
      const record = (eventType === 'DELETE' ? oldRecord : newRecord) as CellData

      if (!record || Object.keys(record).length === 0) {
        console.warn('Realtime payload has no record:', payload)
        return
      }

      // Ignore changes from current user (they already have optimistic update)
      if (record.modified_by === user?.id) {
        console.log('Ignoring own change:', record.id)
        return
      }

      console.log('Realtime change received:', {
        eventType,
        cellId: record.id,
        userId: record.modified_by,
      })

      // Update React Query cache based on event type
      if (eventType === 'UPDATE') {
        // Update the specific cell in the cache
        queryClient.setQueryData<CellData[]>(['cells', budgetVersionId], (oldData) => {
          if (!oldData) return oldData

          return oldData.map((cell) => (cell.id === record.id ? record : cell))
        })

        // Show notification
        if (showNotifications) {
          toast.info('Cellule mise à jour par un autre utilisateur', {
            description: `${record.field_name} modifié`,
            duration: 3000,
          })
        }
      } else if (eventType === 'INSERT') {
        // Add new cell to cache
        queryClient.setQueryData<CellData[]>(['cells', budgetVersionId], (oldData) => {
          if (!oldData) return [record]
          return [...oldData, record]
        })

        if (showNotifications) {
          toast.info('Nouvelle cellule créée', {
            description: `${record.field_name}`,
            duration: 2000,
          })
        }
      } else if (eventType === 'DELETE') {
        // Remove deleted cell from cache
        queryClient.setQueryData<CellData[]>(['cells', budgetVersionId], (oldData) => {
          if (!oldData) return oldData
          return oldData.filter((cell) => cell.id !== record.id)
        })

        if (showNotifications) {
          toast.info('Cellule supprimée', {
            description: `${record.field_name}`,
            duration: 2000,
          })
        }
      }

      // Call optional callback
      if (onCellChanged) {
        onCellChanged({
          eventType,
          cell: record,
          userId: record.modified_by,
        })
      }
    },
    [budgetVersionId, user?.id, queryClient, onCellChanged, showNotifications]
  )

  // Setup subscription
  useEffect(() => {
    if (!budgetVersionId || !user) {
      console.log('Realtime sync: waiting for budget version or user')
      return
    }

    console.log('Setting up realtime subscription for budget:', budgetVersionId)
    updateStatus('CONNECTING')

    // Create channel for this budget version
    const realtimeChannel = supabase.channel(`budget:${budgetVersionId}`, {
      config: {
        broadcast: { self: false },
        presence: { key: user.id },
      },
    })

    // Subscribe to postgres changes
    realtimeChannel
      .on(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        'postgres_changes' as any,
        {
          event: '*', // INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'planning_cells',
          filter: `budget_version_id=eq.${budgetVersionId}`,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        handleChange as any
      )
      .subscribe((subscriptionStatus) => {
        console.log('Realtime subscription status:', subscriptionStatus)

        if (subscriptionStatus === 'SUBSCRIBED') {
          updateStatus('SUBSCRIBED')
          console.log('Realtime subscription active for budget:', budgetVersionId)
        } else if (subscriptionStatus === 'CLOSED') {
          updateStatus('CLOSED')
          console.log('Realtime subscription closed')
        } else if (subscriptionStatus === 'CHANNEL_ERROR') {
          updateStatus('CHANNEL_ERROR')
          console.error('Realtime subscription error')

          if (showNotifications) {
            toast.error('Erreur de synchronisation temps réel', {
              description: 'Reconnexion en cours...',
              duration: 5000,
            })
          }
        }
      })

    setChannel(realtimeChannel)

    // Cleanup on unmount or dependency change
    return () => {
      console.log('Cleaning up realtime subscription')
      updateStatus('CLOSED')

      // Unsubscribe and remove channel
      if (realtimeChannel) {
        supabase.removeChannel(realtimeChannel).then(() => {
          console.log('Realtime channel removed')
        })
      }
    }
  }, [budgetVersionId, user, handleChange, updateStatus, showNotifications])

  // Manual reconnect function
  const reconnect = useCallback(() => {
    if (channel) {
      console.log('Manually reconnecting realtime channel')
      supabase.removeChannel(channel).then(() => {
        // The useEffect will automatically create a new channel
        setChannel(null)
      })
    }
  }, [channel])

  return {
    status,
    reconnect,
    isConnected: status === 'SUBSCRIBED',
    isError: status === 'CHANNEL_ERROR',
  }
}
