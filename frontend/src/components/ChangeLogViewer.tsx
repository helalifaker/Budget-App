/**
 * ChangeLogViewer Component
 *
 * Component for viewing detailed change history with session grouping
 * Shows changes grouped by session_id with undo button for each session
 */

import { useMemo } from 'react'
import { ArrowRight, Undo2, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useChangeHistory } from '@/hooks/api/useChangeHistory'
import { useUndoRedo } from '@/hooks/state/useUndoRedo'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { ScrollArea } from './ui/scroll-area'
import { CellChange } from '@/types/writeback'

export interface ChangeLogViewerProps {
  versionId: string
  moduleCode?: string
}

/**
 * Change log viewer with session grouping
 *
 * @param versionId - Current version
 * @param moduleCode - Optional module filter
 *
 * @example
 * ```typescript
 * <ChangeLogViewer versionId={versionId} />
 * ```
 */
export function ChangeLogViewer({ versionId, moduleCode }: ChangeLogViewerProps) {
  const { changes, isLoading } = useChangeHistory(versionId, {
    module_code: moduleCode,
    limit: 100,
  })
  const { undo } = useUndoRedo(versionId, moduleCode)

  // Group changes by session
  const sessionGroups = useMemo(() => {
    if (!changes || changes.length === 0) return []

    const groups = new Map<string, CellChange[]>()

    changes.forEach((change) => {
      const sessionChanges = groups.get(change.session_id) || []
      sessionChanges.push(change)
      groups.set(change.session_id, sessionChanges)
    })

    // Sort by sequence_number within each session
    groups.forEach((sessionChanges) => {
      sessionChanges.sort((a, b) => a.sequence_number - b.sequence_number)
    })

    // Sort sessions by timestamp (most recent first)
    return Array.from(groups.entries()).sort((a, b) => {
      const aTime = a[1][0].changed_at
      const bTime = b[1][0].changed_at
      return new Date(bTime).getTime() - new Date(aTime).getTime()
    })
  }, [changes])

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-text-secondary" />
      </div>
    )
  }

  if (sessionGroups.length === 0) {
    return (
      <div className="text-center p-8 text-text-secondary">
        <p>No changes recorded</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary">Change History</h3>
        <Badge variant="outline" className="text-text-secondary">
          {sessionGroups.length} session{sessionGroups.length > 1 ? 's' : ''}
        </Badge>
      </div>

      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {sessionGroups.map(([sessionId, sessionChanges]) => {
            const firstChange = sessionChanges[0]
            const changeCount = sessionChanges.length

            // Get badge variant based on change type
            const getBadgeVariant = (changeType: string) => {
              switch (changeType) {
                case 'undo':
                  return 'destructive'
                case 'redo':
                  return 'default'
                case 'import':
                  return 'secondary'
                case 'spread':
                  return 'secondary'
                default:
                  return 'secondary'
              }
            }

            // Format change type label
            const getChangeTypeLabel = (changeType: string) => {
              const labels: Record<string, string> = {
                manual: 'Manuel',
                spread: 'Répartition',
                import: 'Import',
                undo: 'Annulation',
                redo: 'Rétablissement',
              }
              return labels[changeType] || changeType
            }

            return (
              <Card key={sessionId} className="p-4 bg-white border-border-light">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Session header */}
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={getBadgeVariant(firstChange.change_type)}>
                        {getChangeTypeLabel(firstChange.change_type)}
                      </Badge>
                      <span className="text-sm text-text-secondary">
                        {changeCount} cellule{changeCount > 1 ? 's' : ''}
                      </span>
                      <span className="text-xs text-text-tertiary">
                        {formatDistanceToNow(new Date(firstChange.changed_at), {
                          addSuffix: true,
                          locale: fr,
                        })}
                      </span>
                    </div>

                    {/* Show first 3 changes */}
                    <div className="space-y-1">
                      {sessionChanges.slice(0, 3).map((change) => (
                        <div key={change.id} className="flex items-center gap-2 text-sm">
                          <span className="font-medium text-text-secondary min-w-[120px]">
                            {change.field_name}
                          </span>
                          {change.old_value !== undefined && change.new_value !== undefined ? (
                            <>
                              <Badge variant="outline" className="font-mono text-xs">
                                {change.old_value.toLocaleString('fr-FR')}
                              </Badge>
                              <ArrowRight className="h-3 w-3 text-text-muted" />
                              <Badge
                                variant="default"
                                className="font-mono text-xs bg-gold-100 text-gold-800 border-gold-300"
                              >
                                {change.new_value.toLocaleString('fr-FR')}
                              </Badge>
                            </>
                          ) : change.new_value !== undefined ? (
                            <Badge
                              variant="default"
                              className="font-mono text-xs bg-success-100 text-success-800 border-success-300"
                            >
                              {change.new_value.toLocaleString('fr-FR')}
                            </Badge>
                          ) : change.old_value !== undefined ? (
                            <Badge
                              variant="default"
                              className="font-mono text-xs bg-error-100 text-error-800 border-error-300"
                            >
                              {change.old_value.toLocaleString('fr-FR')}
                            </Badge>
                          ) : null}
                        </div>
                      ))}
                      {changeCount > 3 && (
                        <p className="text-xs text-text-tertiary italic">
                          ... et {changeCount - 3} autre{changeCount - 3 > 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Undo button (only for non-undo changes) */}
                  {firstChange.change_type !== 'undo' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void undo()}
                      className="gap-1 text-text-secondary hover:text-text-primary hover:bg-subtle"
                    >
                      <Undo2 className="h-4 w-4" />
                      Undo
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
