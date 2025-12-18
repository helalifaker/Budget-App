/**
 * ChangeLogDialog Component
 *
 * Dialog wrapper for viewing change log
 * Provides modal interface for displaying detailed change history
 */

import { ChangeLogViewer } from './ChangeLogViewer'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'

export interface ChangeLogDialogProps {
  versionId: string
  moduleCode?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Dialog for viewing change log
 *
 * @param versionId - Current version
 * @param moduleCode - Optional module filter
 * @param open - Dialog open state
 * @param onOpenChange - Callback when dialog state changes
 *
 * @example
 * ```typescript
 * <ChangeLogDialog
 *   versionId={versionId}
 *   open={showLog}
 *   onOpenChange={setShowLog}
 * />
 * ```
 */
export function ChangeLogDialog({
  versionId,
  moduleCode,
  open,
  onOpenChange,
}: ChangeLogDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-text-primary">Journal des modifications</DialogTitle>
          <DialogDescription className="text-text-secondary">
            Historique complet des modifications avec possibilité d&apos;annulation
          </DialogDescription>
        </DialogHeader>

        <ChangeLogViewer versionId={versionId} moduleCode={moduleCode} />
      </DialogContent>
    </Dialog>
  )
}
