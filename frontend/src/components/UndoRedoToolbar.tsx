/**
 * UndoRedoToolbar Component
 *
 * Toolbar with undo/redo buttons and keyboard shortcuts
 * Shows undo/redo count badges and loading states
 */

import { Undo2, Redo2, Loader2 } from 'lucide-react'
import { useUndoRedo } from '@/hooks/state/useUndoRedo'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { cn } from '@/lib/utils'

export interface UndoRedoToolbarProps {
  versionId: string
  moduleCode?: string
  className?: string
}

/**
 * Toolbar with undo/redo buttons and keyboard shortcuts
 *
 * @param versionId - Current version
 * @param moduleCode - Optional module filter
 * @param className - Additional CSS classes
 *
 * @example
 * ```typescript
 * <UndoRedoToolbar versionId={versionId} moduleCode="enrollment" />
 * ```
 */
export function UndoRedoToolbar({ versionId, moduleCode, className }: UndoRedoToolbarProps) {
  const { undo, redo, canUndo, canRedo, isLoading, undoCount, redoCount } = useUndoRedo(
    versionId,
    moduleCode
  )

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Undo button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => void undo()}
        disabled={!canUndo || isLoading}
        className="gap-2"
        title="Undo last change (Ctrl+Z)"
      >
        <Undo2 className="h-4 w-4" />
        <span className="hidden sm:inline">Undo</span>
        {undoCount > 0 && (
          <Badge variant="secondary" className="ml-1">
            {undoCount}
          </Badge>
        )}
      </Button>

      {/* Redo button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => void redo()}
        disabled={!canRedo || isLoading}
        className="gap-2"
        title="Redo last undo (Ctrl+Y)"
      >
        <Redo2 className="h-4 w-4" />
        <span className="hidden sm:inline">Redo</span>
        {redoCount > 0 && (
          <Badge variant="secondary" className="ml-1">
            {redoCount}
          </Badge>
        )}
      </Button>

      {/* Loading indicator */}
      {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
    </div>
  )
}
