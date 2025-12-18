/**
 * useCellComments Hook - Phase 3.3
 *
 * Manages cell-level comments with CRUD operations, realtime sync, and comprehensive features.
 * Provides functionality to add, resolve, unresolve, and delete comments for cells.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiRequest } from '@/lib/api-client'
import { CellComment } from '@/types/writeback'

/**
 * Hook for managing cell comments
 *
 * Provides functionality to add, resolve, and fetch comments for a specific cell.
 * Comments are used for collaboration, flagging issues, and documenting assumptions.
 *
 * @param cellId - Cell ID
 * @returns Comments, add function, resolve function, and loading state
 *
 * @example
 * ```typescript
 * const { comments, addComment, resolveComment, isLoading } = useCellComments(cellId);
 *
 * // Add a comment
 * await addComment('This value seems high for this period');
 *
 * // Resolve a comment
 * await resolveComment(commentId);
 *
 * // Render comments
 * {comments.map(comment => (
 *   <Comment
 *     key={comment.id}
 *     text={comment.comment_text}
 *     isResolved={comment.is_resolved}
 *     onResolve={() => resolveComment(comment.id)}
 *   />
 * ))}
 * ```
 */
export function useCellComments(cellId: string) {
  const queryClient = useQueryClient()

  // Fetch comments for a cell
  const {
    data: comments,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['cell-comments', cellId],
    queryFn: async (): Promise<CellComment[]> => {
      const response = await apiRequest<CellComment[]>({
        method: 'GET',
        url: `/writeback/cells/${cellId}/comments`,
      })
      return response
    },
    enabled: !!cellId,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes cache
  })

  // Add comment mutation
  const addCommentMutation = useMutation({
    mutationFn: async (commentText: string): Promise<CellComment> => {
      const response = await apiRequest<CellComment>({
        method: 'POST',
        url: `/writeback/cells/${cellId}/comments`,
        data: {
          comment_text: commentText,
        },
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cell-comments', cellId] })
      toast.success('Commentaire ajouté', {
        duration: 2000,
      })
    },
    onError: (err: unknown) => {
      const errorMessage =
        err instanceof Error ? err.message : "Erreur lors de l'ajout du commentaire"
      toast.error('Erreur de commentaire', {
        description: errorMessage,
        duration: 3000,
      })
    },
  })

  // Resolve comment mutation
  const resolveCommentMutation = useMutation({
    mutationFn: async (commentId: string): Promise<CellComment> => {
      const response = await apiRequest<CellComment>({
        method: 'POST',
        url: `/writeback/comments/${commentId}/resolve`,
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cell-comments', cellId] })
      toast.success('Commentaire résolu', {
        duration: 2000,
      })
    },
    onError: (err: unknown) => {
      const errorMessage =
        err instanceof Error ? err.message : 'Erreur lors de la résolution du commentaire'
      toast.error('Erreur de commentaire', {
        description: errorMessage,
        duration: 3000,
      })
    },
  })

  // Unresolve comment mutation (allow reopening resolved comments)
  const unresolveCommentMutation = useMutation({
    mutationFn: async (commentId: string): Promise<CellComment> => {
      const response = await apiRequest<CellComment>({
        method: 'POST',
        url: `/writeback/comments/${commentId}/unresolve`,
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cell-comments', cellId] })
      toast.success('Commentaire rouvert', {
        duration: 2000,
      })
    },
    onError: (err: unknown) => {
      const errorMessage =
        err instanceof Error ? err.message : 'Erreur lors de la réouverture du commentaire'
      toast.error('Erreur de commentaire', {
        description: errorMessage,
        duration: 3000,
      })
    },
  })

  // Delete comment mutation (admin only)
  const deleteCommentMutation = useMutation({
    mutationFn: async (commentId: string): Promise<void> => {
      await apiRequest<void>({
        method: 'DELETE',
        url: `/writeback/comments/${commentId}`,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cell-comments', cellId] })
      toast.success('Commentaire supprimé', {
        duration: 2000,
      })
    },
    onError: (err: unknown) => {
      const errorMessage =
        err instanceof Error ? err.message : 'Erreur lors de la suppression du commentaire'
      toast.error('Erreur de commentaire', {
        description: errorMessage,
        duration: 3000,
      })
    },
  })

  // Get counts (total, resolved, unresolved)
  const unresolvedCount = (comments || []).filter((c) => !c.is_resolved).length
  const resolvedCount = (comments || []).filter((c) => c.is_resolved).length
  const totalCount = (comments || []).length

  return {
    comments: comments || [],
    unresolvedComments: (comments || []).filter((c) => !c.is_resolved),
    resolvedComments: (comments || []).filter((c) => c.is_resolved),
    isLoading,
    isError,
    error,
    addComment: addCommentMutation.mutateAsync,
    resolveComment: resolveCommentMutation.mutateAsync,
    unresolveComment: unresolveCommentMutation.mutateAsync,
    deleteComment: deleteCommentMutation.mutateAsync,
    isAddingComment: addCommentMutation.isPending,
    isResolvingComment: resolveCommentMutation.isPending,
    isUnresolvingComment: unresolveCommentMutation.isPending,
    isDeletingComment: deleteCommentMutation.isPending,
    unresolvedCount,
    resolvedCount,
    totalCount,
    hasUnresolvedComments: unresolvedCount > 0,
  }
}

/**
 * Hook for fetching comments across multiple cells
 *
 * Useful for showing all comments in a module or entity view.
 *
 * @param cellIds - Array of cell IDs
 * @returns Comments grouped by cell ID
 *
 * @example
 * ```typescript
 * const { commentsByCellId, totalCount } = useMultipleCellComments(cellIds);
 *
 * // Render comments for each cell
 * {Object.entries(commentsByCellId).map(([cellId, comments]) => (
 *   <div key={cellId}>
 *     <h3>Cell {cellId}</h3>
 *     {comments.map(comment => <Comment key={comment.id} {...comment} />)}
 *   </div>
 * ))}
 * ```
 */
export function useMultipleCellComments(cellIds: string[]) {
  const query = useQuery({
    queryKey: ['multiple-cell-comments', cellIds],
    queryFn: async (): Promise<Record<string, CellComment[]>> => {
      const response = await apiRequest<CellComment[]>({
        method: 'POST',
        url: '/writeback/cells/comments/bulk',
        data: {
          cell_ids: cellIds,
        },
      })

      // Group comments by cell_id
      const grouped = response.reduce(
        (acc, comment) => {
          if (!acc[comment.cell_id]) {
            acc[comment.cell_id] = []
          }
          acc[comment.cell_id].push(comment)
          return acc
        },
        {} as Record<string, CellComment[]>
      )

      return grouped
    },
    enabled: cellIds.length > 0,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes cache
  })

  const commentsByCellId = query.data || {}
  const totalCount = Object.values(commentsByCellId).reduce(
    (sum, comments) => sum + comments.length,
    0
  )

  return {
    commentsByCellId,
    totalCount,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  }
}

/**
 * Hook for fetching all unresolved comments in a version
 *
 * Useful for showing a global list of issues that need attention.
 *
 * @param versionId - Version ID
 * @returns Unresolved comments across all cells
 *
 * @example
 * ```typescript
 * const { unresolvedComments, count } = useUnresolvedComments(versionId);
 *
 * // Show notification badge
 * <Badge count={count} />
 *
 * // Render issue list
 * {unresolvedComments.map(comment => (
 *   <IssueCard key={comment.id} comment={comment} />
 * ))}
 * ```
 */
export function useUnresolvedComments(versionId: string) {
  const query = useQuery({
    queryKey: ['unresolved-comments', versionId],
    queryFn: async (): Promise<CellComment[]> => {
      const response = await apiRequest<CellComment[]>({
        method: 'GET',
        url: `/writeback/versions/${versionId}/comments/unresolved`,
      })
      return response
    },
    enabled: !!versionId,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes cache
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  })

  return {
    unresolvedComments: query.data || [],
    count: (query.data || []).length,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  }
}
