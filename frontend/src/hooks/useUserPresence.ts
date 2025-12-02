import { useEffect, useState, useCallback } from 'react'
import { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'
import type { PresenceUser, UserActivityPayload, UserPresenceOptions } from '@/types/writeback'

/**
 * Hook for tracking user presence in a budget version
 *
 * Shows which users are currently viewing/editing the same budget.
 * Supports broadcasting user activity (which cell they're editing).
 * Provides real-time list of active users.
 *
 * @param options - Configuration options for presence tracking
 * @param options.budgetVersionId - Budget version to track presence for
 * @param options.onUserJoin - Optional callback when user joins
 * @param options.onUserLeave - Optional callback when user leaves
 * @param options.broadcastActivity - Whether to broadcast user activity (default: true)
 *
 * @returns Object with active users list and broadcast function
 *
 * @example
 * ```tsx
 * function BudgetCollaboration({ budgetVersionId }: { budgetVersionId: string }) {
 *   const { activeUsers, broadcast } = useUserPresence({
 *     budgetVersionId,
 *     onUserJoin: (user) => console.log('User joined:', user.user_email),
 *     onUserLeave: (user) => console.log('User left:', user.user_email),
 *   });
 *
 *   // Broadcast when editing a cell
 *   const handleCellEdit = (cellId: string) => {
 *     broadcast({
 *       action: 'editing',
 *       cellId,
 *       timestamp: new Date().toISOString(),
 *     });
 *   };
 *
 *   return (
 *     <div>
 *       <h3>Active Users ({activeUsers.length})</h3>
 *       {activeUsers.map((user) => (
 *         <div key={user.user_id}>
 *           {user.user_email}
 *           {user.editing_cell && ` - editing cell ${user.editing_cell}`}
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useUserPresence(options: UserPresenceOptions) {
  const { budgetVersionId, onUserJoin, onUserLeave, broadcastActivity = true } = options

  const { user } = useAuth()
  const [activeUsers, setActiveUsers] = useState<PresenceUser[]>([])
  const [channel, setChannel] = useState<RealtimeChannel | null>(null)

  // Broadcast user activity
  const broadcast = useCallback(
    async (payload: UserActivityPayload) => {
      if (!channel || !broadcastActivity) {
        console.log('Cannot broadcast: channel not ready or broadcasting disabled')
        return
      }

      try {
        await channel.send({
          type: 'broadcast',
          event: 'user-activity',
          payload: {
            ...payload,
            user_id: user?.id,
            user_email: user?.email,
          },
        })

        console.log('Broadcast sent:', payload)
      } catch (error) {
        console.error('Failed to broadcast activity:', error)
      }
    },
    [channel, user, broadcastActivity]
  )

  // Setup presence tracking
  useEffect(() => {
    if (!budgetVersionId || !user) {
      console.log('Presence: waiting for budget version or user')
      return
    }

    console.log('Setting up presence tracking for budget:', budgetVersionId)

    // Create presence channel
    const presenceChannel = supabase.channel(`presence:${budgetVersionId}`, {
      config: {
        presence: {
          key: user.id,
        },
        broadcast: { self: false },
      },
    })

    // Track presence state changes
    presenceChannel
      .on('presence', { event: 'sync' }, () => {
        const state = presenceChannel.presenceState<PresenceUser>()

        // Convert presence state to array of users
        const users = Object.values(state).flat()

        console.log('Presence synced, active users:', users.length)
        setActiveUsers(users.filter((u) => u.user_id !== user.id))
      })
      .on('presence', { event: 'join' }, ({ newPresences }) => {
        console.log('User(s) joined:', newPresences)

        const newUsers = newPresences as unknown as PresenceUser[]

        // Filter out current user and show notification for others
        const otherUsers = newUsers.filter((u) => u.user_id !== user.id)

        if (otherUsers.length > 0) {
          toast.info('Utilisateur connecté', {
            description: otherUsers[0].user_email,
            duration: 2000,
          })

          // Call optional callback
          otherUsers.forEach((newUser) => {
            onUserJoin?.(newUser)
          })
        }
      })
      .on('presence', { event: 'leave' }, ({ leftPresences }) => {
        console.log('User(s) left:', leftPresences)

        const leftUsers = leftPresences as unknown as PresenceUser[]

        // Filter out current user
        const otherUsers = leftUsers.filter((u) => u.user_id !== user.id)

        if (otherUsers.length > 0) {
          // Call optional callback
          otherUsers.forEach((leftUser) => {
            onUserLeave?.(leftUser)
          })
        }
      })

    // Listen for broadcast events (user activity)
    if (broadcastActivity) {
      presenceChannel.on(
        'broadcast',
        { event: 'user-activity' },
        (payload: { payload: UserActivityPayload & { user_id: string; user_email: string } }) => {
          console.log('User activity broadcast received:', payload.payload)

          // Update active users with current activity
          setActiveUsers((prev) =>
            prev.map((u) =>
              u.user_id === payload.payload.user_id
                ? {
                    ...u,
                    editing_cell: payload.payload.cellId,
                    last_activity: payload.payload.timestamp,
                  }
                : u
            )
          )
        }
      )
    }

    // Subscribe and announce presence
    presenceChannel.subscribe(async (status) => {
      console.log('Presence subscription status:', status)

      if (status === 'SUBSCRIBED') {
        // Announce presence
        await presenceChannel.track({
          user_id: user.id,
          user_email: user.email || 'Unknown',
          joined_at: new Date().toISOString(),
        })

        console.log('Presence announced for user:', user.email)
      } else if (status === 'CHANNEL_ERROR') {
        console.error('Presence subscription error')
      }
    })

    setChannel(presenceChannel)

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up presence tracking')

      if (presenceChannel) {
        // Untrack presence before removing channel
        presenceChannel.untrack().then(() => {
          supabase.removeChannel(presenceChannel).then(() => {
            console.log('Presence channel removed')
          })
        })
      }
    }
  }, [budgetVersionId, user, onUserJoin, onUserLeave, broadcastActivity])

  return {
    activeUsers,
    broadcast,
    isTracking: channel !== null && activeUsers.length >= 0,
  }
}
