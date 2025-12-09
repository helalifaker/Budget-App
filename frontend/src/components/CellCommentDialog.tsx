/**
 * CellCommentDialog Component
 *
 * Dialog for adding and viewing cell-level comments.
 * Supports real-time updates and comment resolution.
 */

import { useState, FormEvent } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useCellComments } from '@/hooks/api/useCellComments'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { ScrollArea } from './ui/scroll-area'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'

export interface CellCommentDialogProps {
  cellId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Dialog for managing cell comments
 *
 * @param cellId - Cell ID
 * @param open - Dialog open state
 * @param onOpenChange - State change handler
 */
export function CellCommentDialog({ cellId, open, onOpenChange }: CellCommentDialogProps) {
  const { comments, addComment, resolveComment, isLoading } = useCellComments(cellId)
  const [newComment, setNewComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!newComment.trim()) return

    try {
      setIsSubmitting(true)
      await addComment(newComment)
      setNewComment('')
    } catch (error) {
      console.error('Failed to add comment:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResolve = async (commentId: string) => {
    try {
      await resolveComment(commentId)
    } catch (error) {
      console.error('Failed to resolve comment:', error)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Commentaires de cellule</DialogTitle>
          <DialogDescription>Ajoutez des notes et annotations pour cette cellule</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {/* Comment list */}
          <ScrollArea className="h-[300px]">
            {isLoading ? (
              <div className="flex justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-text-secondary" />
              </div>
            ) : comments.length === 0 ? (
              <p className="text-center text-text-secondary p-4">Aucun commentaire</p>
            ) : (
              <div className="space-y-3 pr-4">
                {comments.map((comment) => (
                  <div
                    key={comment.id}
                    className={cn(
                      'p-3 rounded-lg border border-border-light bg-white',
                      comment.is_resolved && 'opacity-50 bg-subtle'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-sm text-text-secondary whitespace-pre-wrap">
                          {comment.comment_text}
                        </p>
                        <p className="text-xs text-text-tertiary mt-1">
                          {comment.created_by} • {formatDate(comment.created_at)}
                        </p>
                        {comment.is_resolved && comment.resolved_by && (
                          <p className="text-xs text-success-600 mt-1">
                            Résolu par {comment.resolved_by} •{' '}
                            {comment.resolved_at && formatDate(comment.resolved_at)}
                          </p>
                        )}
                      </div>
                      {!comment.is_resolved && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleResolve(comment.id)}
                          className="shrink-0"
                        >
                          Résoudre
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Add comment form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Ajouter un commentaire..."
              className="flex-1"
              rows={2}
              disabled={isSubmitting}
            />
            <Button
              type="submit"
              disabled={!newComment.trim() || isSubmitting}
              className="shrink-0"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Envoi...
                </>
              ) : (
                'Ajouter'
              )}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  )
}
