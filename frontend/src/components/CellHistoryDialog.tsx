/**
 * CellHistoryDialog Component
 *
 * Dialog for viewing cell change history (audit trail).
 * Shows all modifications with old/new values, timestamps, and user info.
 */

import { Loader2, ArrowRight } from 'lucide-react'
import { useCellHistory } from '@/hooks/api/useChangeHistory'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { ScrollArea } from './ui/scroll-area'
import { Badge } from './ui/badge'

export interface CellHistoryDialogProps {
  cellId: string
  budgetVersionId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Dialog for displaying cell change history
 *
 * @param cellId - Cell ID
 * @param budgetVersionId - Budget version ID
 * @param open - Dialog open state
 * @param onOpenChange - State change handler
 */
export function CellHistoryDialog({ cellId, open, onOpenChange }: CellHistoryDialogProps) {
  const { changes, isLoading } = useCellHistory(cellId)

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date)
  }

  const getChangeTypeLabel = (changeType: string) => {
    const labels: Record<string, string> = {
      INSERT: 'Création',
      UPDATE: 'Modification',
      DELETE: 'Suppression',
    }
    return labels[changeType] || changeType
  }

  const getChangeTypeBadgeVariant = (changeType: string) => {
    const variants: Record<
      string,
      'default' | 'secondary' | 'destructive' | 'success' | 'warning' | 'info'
    > = {
      INSERT: 'success',
      UPDATE: 'info',
      DELETE: 'destructive',
    }
    return variants[changeType] || 'default'
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Historique des modifications</DialogTitle>
          <DialogDescription>
            Voir toutes les modifications apportées à cette cellule
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="flex justify-center p-4">
              <Loader2 className="h-6 w-6 animate-spin text-text-secondary" />
            </div>
          ) : changes.length === 0 ? (
            <p className="text-center text-text-secondary p-4">Aucune modification enregistrée</p>
          ) : (
            <div className="space-y-2 pr-4">
              {changes.map((change) => (
                <div
                  key={change.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-border-light bg-white hover:bg-subtle transition-colors"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-text-secondary">{change.field_name}</p>
                    <p className="text-xs text-text-secondary mt-1">
                      {formatDate(change.changed_at)} • {change.changed_by}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    {change.old_value !== undefined && change.new_value !== undefined ? (
                      <>
                        <Badge variant="outline" className="font-mono">
                          {change.old_value?.toString() || 'N/A'}
                        </Badge>
                        <ArrowRight className="h-4 w-4 text-text-muted" />
                        <Badge className="font-mono bg-gold-100 text-gold-800 border-gold-300">
                          {change.new_value?.toString() || 'N/A'}
                        </Badge>
                      </>
                    ) : change.new_value !== undefined ? (
                      <Badge className="font-mono bg-success-100 text-success-800 border-success-300">
                        {change.new_value?.toString() || 'N/A'}
                      </Badge>
                    ) : (
                      <Badge className="font-mono bg-error-100 text-error-800 border-error-300">
                        {change.old_value?.toString() || 'N/A'}
                      </Badge>
                    )}
                    <Badge variant={getChangeTypeBadgeVariant(change.change_type)}>
                      {getChangeTypeLabel(change.change_type)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
