/**
 * ChangeLogDialog Component
 *
 * Dialog wrapper for viewing change log
 * Provides modal interface for displaying detailed change history
 */

import { ChangeLogViewer } from './ChangeLogViewer'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'

export interface ChangeLogDialogProps {
  budgetVersionId: string
  moduleCode?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Dialog for viewing change log
 *
 * @param budgetVersionId - Current budget version
 * @param moduleCode - Optional module filter
 * @param open - Dialog open state
 * @param onOpenChange - Callback when dialog state changes
 *
 * @example
 * ```typescript
 * <ChangeLogDialog
 *   budgetVersionId={budgetVersionId}
 *   open={showLog}
 *   onOpenChange={setShowLog}
 * />
 * ```
 */
export function ChangeLogDialog({
  budgetVersionId,
  moduleCode,
  open,
  onOpenChange,
}: ChangeLogDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-twilight-900">Journal des modifications</DialogTitle>
          <DialogDescription className="text-twilight-600">
            Historique complet des modifications avec possibilité d&apos;annulation
          </DialogDescription>
        </DialogHeader>

        <ChangeLogViewer budgetVersionId={budgetVersionId} moduleCode={moduleCode} />
      </DialogContent>
    </Dialog>
  )
}
