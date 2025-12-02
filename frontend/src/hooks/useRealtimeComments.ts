import { useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'
import type { CellComment, RealtimeCommentOptions } from '@/types/writeback'

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
 * Hook for real-time comment synchronization
 *
 * Subscribes to changes on cell_comments table for a specific cell.
 * Automatically invalidates comment queries when comments are added/updated/deleted.
 * Shows toast notifications for new comments from other users.
 *
 * @param options - Configuration options for comment sync
 * @param options.cellId - Cell ID to watch for comments (undefined disables subscription)
 * @param options.onCommentChanged - Optional callback when comment changes
 * @param options.showNotifications - Whether to show toast notifications (default: true)
 *
 * @example
 * ```tsx
 * function CellCommentsList({ cellId }: { cellId: string }) {
 *   useRealtimeComments({
 *     cellId,
 *     onCommentChanged: (change) => {
 *       if (change.eventType === 'INSERT') {
 *         console.log('New comment:', change.comment);
 *       }
 *     },
 *   });
 *
 *   // Render comments...
 * }
 * ```
 */
export function useRealtimeComments(options: RealtimeCommentOptions) {
  const { cellId, onCommentChanged, showNotifications = true } = options

  const queryClient = useQueryClient()
  const { user } = useAuth()

  // Handle comment change events
  const handleCommentChange = useCallback(
    (payload: RealtimePayload<CellComment>) => {
      const { eventType, new: newRecord, old: oldRecord } = payload

      // Determine the record to use - type narrowing
      const record = (eventType === 'DELETE' ? oldRecord : newRecord) as CellComment

      if (!record || Object.keys(record).length === 0) {
        console.warn('Comment realtime payload has no record:', payload)
        return
      }

      // Ignore changes from current user
      if (record.created_by === user?.id) {
        console.log('Ignoring own comment change:', record.id)
        return
      }

      console.log('Comment realtime change received:', {
        eventType,
        commentId: record.id,
        cellId: record.cell_id,
      })

      // Invalidate comments cache to refetch
      queryClient.invalidateQueries({
        queryKey: ['cell-comments', cellId],
      })

      // Show notifications based on event type
      if (eventType === 'INSERT' && showNotifications) {
        const preview =
          record.comment_text.length > 50
            ? record.comment_text.substring(0, 50) + '...'
            : record.comment_text

        toast.info('Nouveau commentaire ajouté', {
          description: preview,
          duration: 5000,
        })
      } else if (eventType === 'UPDATE' && showNotifications) {
        // Check if comment was resolved
        if (record.is_resolved) {
          toast.success('Commentaire résolu', {
            duration: 3000,
          })
        } else {
          toast.info('Commentaire mis à jour', {
            duration: 2000,
          })
        }
      } else if (eventType === 'DELETE' && showNotifications) {
        toast.info('Commentaire supprimé', {
          duration: 2000,
        })
      }

      // Call optional callback
      if (onCommentChanged) {
        onCommentChanged({
          eventType,
          comment: record,
          userId: record.created_by,
        })
      }
    },
    [cellId, user?.id, queryClient, onCommentChanged, showNotifications]
  )

  // Setup subscription
  useEffect(() => {
    if (!cellId || !user) {
      console.log('Comment sync: waiting for cellId or user')
      return
    }

    console.log('Setting up comment subscription for cell:', cellId)

    // Create channel for this cell's comments
    const channel = supabase.channel(`cell-comments:${cellId}`, {
      config: {
        broadcast: { self: false },
      },
    })

    // Subscribe to postgres changes
    channel
      .on(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        'postgres_changes' as any,
        {
          event: '*', // INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'cell_comments',
          filter: `cell_id=eq.${cellId}`,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        handleCommentChange as any
      )
      .subscribe((status) => {
        console.log('Comment subscription status:', status, 'for cell:', cellId)

        if (status === 'CHANNEL_ERROR') {
          console.error('Comment subscription error for cell:', cellId)
        }
      })

    // Cleanup on unmount or cellId change
    return () => {
      console.log('Cleaning up comment subscription for cell:', cellId)
      supabase.removeChannel(channel)
    }
  }, [cellId, user, handleCommentChange])
}
