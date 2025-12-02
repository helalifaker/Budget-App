import { useState, useEffect, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiRequest } from '@/lib/api-client'
import { CellChange } from '@/types/writeback'

/**
 * Hook for undo/redo functionality with persistent history
 *
 * Features:
 * - Session-based undo/redo (undo all changes in one operation)
 * - Keyboard shortcuts (Ctrl+Z, Ctrl+Y, Cmd+Z, Cmd+Shift+Z)
 * - Stack management with max history (100 sessions)
 * - Persistent across page reloads
 *
 * @param budgetVersionId - Current budget version
 * @param moduleCode - Optional module filter
 *
 * @example
 * ```typescript
 * const { undo, redo, canUndo, canRedo, undoStack, redoStack } = useUndoRedo(budgetVersionId);
 *
 * // Undo last session
 * await undo();
 *
 * // Redo last undone session
 * await redo();
 * ```
 */
export function useUndoRedo(budgetVersionId: string, moduleCode?: string) {
  const queryClient = useQueryClient()
  const [undoStack, setUndoStack] = useState<string[]>([]) // session_ids
  const [redoStack, setRedoStack] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Load change history to build stacks
  const { data: changes } = useQuery({
    queryKey: ['cell-changes', budgetVersionId, moduleCode],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: '100',
      })

      if (moduleCode) {
        params.append('module_code', moduleCode)
      }

      const response = await apiRequest<CellChange[]>({
        method: 'GET',
        url: `/writeback/cells/changes/${budgetVersionId}?${params.toString()}`,
      })

      return response
    },
    enabled: !!budgetVersionId,
    staleTime: 10 * 1000, // 10 seconds
  })

  // Build undo/redo stacks from change history
  useEffect(() => {
    if (!changes || changes.length === 0) {
      setUndoStack([])
      setRedoStack([])
      return
    }

    // Group changes by session_id
    const sessionMap = new Map<string, CellChange[]>()
    changes.forEach((change) => {
      const sessionChanges = sessionMap.get(change.session_id) || []
      sessionChanges.push(change)
      sessionMap.set(change.session_id, sessionChanges)
    })

    // Sort sessions by timestamp (most recent first)
    const sortedSessions = Array.from(sessionMap.keys()).sort((a, b) => {
      const aTime = sessionMap.get(a)![0].changed_at
      const bTime = sessionMap.get(b)![0].changed_at
      return new Date(bTime).getTime() - new Date(aTime).getTime()
    })

    // Separate undo and redo stacks based on change_type
    const newUndoStack: string[] = []
    const newRedoStack: string[] = []

    sortedSessions.forEach((sessionId) => {
      const sessionChanges = sessionMap.get(sessionId)!
      const firstChange = sessionChanges[0]

      if (firstChange.change_type === 'undo') {
        // This was an undo operation, add to redo stack
        newRedoStack.push(sessionId)
      } else if (firstChange.change_type === 'redo') {
        // This was a redo operation, add back to undo stack
        newUndoStack.push(sessionId)
      } else {
        // Normal change (manual, spread, import), add to undo stack
        newUndoStack.push(sessionId)
      }
    })

    setUndoStack(newUndoStack.slice(0, 100)) // Max 100 in stack
    setRedoStack(newRedoStack.slice(0, 100))
  }, [changes])

  // Undo mutation
  const undoMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiRequest<{
        reverted_count: number
        new_session_id: string
      }>({
        method: 'POST',
        url: '/writeback/cells/undo',
        data: { session_id: sessionId },
      })

      return response
    },
    onSuccess: (data) => {
      toast.success(`${data.reverted_count} modification(s) annulée(s)`, {
        description: 'Ctrl+Y pour rétablir',
        duration: 3000,
      })

      // Invalidate queries to refetch data
      queryClient.invalidateQueries({ queryKey: ['cells', budgetVersionId] })
      queryClient.invalidateQueries({ queryKey: ['cell-changes', budgetVersionId] })
    },
    onError: (error: Error) => {
      toast.error("Erreur lors de l'annulation", {
        description: error.message,
      })
    },
  })

  // Redo mutation (undo the undo)
  const redoMutation = useMutation({
    mutationFn: async (undoSessionId: string) => {
      // To redo, we undo the undo session
      const response = await apiRequest<{
        reverted_count: number
        new_session_id: string
      }>({
        method: 'POST',
        url: '/writeback/cells/undo',
        data: { session_id: undoSessionId },
      })

      return response
    },
    onSuccess: (data) => {
      toast.success(`${data.reverted_count} modification(s) rétablie(s)`, {
        description: 'Ctrl+Z pour annuler',
        duration: 3000,
      })

      queryClient.invalidateQueries({ queryKey: ['cells', budgetVersionId] })
      queryClient.invalidateQueries({ queryKey: ['cell-changes', budgetVersionId] })
    },
    onError: (error: Error) => {
      toast.error('Erreur lors du rétablissement', {
        description: error.message,
      })
    },
  })

  // Undo callback
  const undo = useCallback(async () => {
    if (undoStack.length === 0 || isLoading) return

    setIsLoading(true)
    try {
      const sessionId = undoStack[0] // Most recent
      await undoMutation.mutateAsync(sessionId)
    } finally {
      setIsLoading(false)
    }
  }, [undoStack, isLoading, undoMutation])

  // Redo callback
  const redo = useCallback(async () => {
    if (redoStack.length === 0 || isLoading) return

    setIsLoading(true)
    try {
      const sessionId = redoStack[0] // Most recent undo
      await redoMutation.mutateAsync(sessionId)
    } finally {
      setIsLoading(false)
    }
  }, [redoStack, isLoading, redoMutation])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if typing in input/textarea
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return
      }

      // Ctrl+Z or Cmd+Z (Mac)
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault()
        if (undoStack.length > 0 && !isLoading) {
          void undo()
        }
      }

      // Ctrl+Y or Cmd+Shift+Z (Mac)
      if (
        ((event.ctrlKey || event.metaKey) && event.key === 'y') ||
        ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'z')
      ) {
        event.preventDefault()
        if (redoStack.length > 0 && !isLoading) {
          void redo()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [undoStack, redoStack, isLoading, undo, redo])

  // Computed values
  const canUndo = useMemo(() => undoStack.length > 0 && !isLoading, [undoStack.length, isLoading])
  const canRedo = useMemo(() => redoStack.length > 0 && !isLoading, [redoStack.length, isLoading])

  return {
    undo,
    redo,
    canUndo,
    canRedo,
    isLoading,
    undoStack,
    redoStack,
    undoCount: undoStack.length,
    redoCount: redoStack.length,
  }
}
