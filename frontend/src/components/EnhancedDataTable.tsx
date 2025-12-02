/**
 * Enhanced DataTable Component
 *
 * AG Grid-based data table with cell-level writeback, realtime sync, and conflict resolution.
 * Provides Excel-like editing experience with instant save and visual feedback.
 *
 * Features:
 * - Cell-level writeback with optimistic updates
 * - Version conflict detection and resolution
 * - Locked cell visualization
 * - Active user presence indicators
 * - Context menu for comments and history
 * - Real-time updates from other users
 */

import { AgGridReact, type AgGridReactProps } from 'ag-grid-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import type {
  CellValueChangedEvent,
  CellClassParams,
  GetContextMenuItemsParams,
  MenuItemDef,
  GridApi,
} from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'
import { Loader2 } from 'lucide-react'
import { Badge } from './ui/badge'
import { cn } from '@/lib/utils'
import { usePlanningWriteback, VersionConflictError } from '@/hooks/api/usePlanningWriteback'
import { useRealtimeSync } from '@/hooks/useRealtimeSync'
import { useUserPresence } from '@/hooks/useUserPresence'
import type { RealtimeChange } from '@/types/writeback'
import { CellCommentDialog } from './CellCommentDialog'
import { CellHistoryDialog } from './CellHistoryDialog'

export interface EnhancedDataTableProps<TData = unknown>
  extends Omit<AgGridReactProps<TData>, 'onCellValueChanged'> {
  budgetVersionId: string
  moduleCode: string
  enableWriteback?: boolean
  onCellSaved?: (cellData: CellData) => void
  loading?: boolean
  error?: Error | null
}

export interface CellData {
  id: string
  field_name: string
  value: number
  version: number
  updated_at: string
  updated_by: string
  is_locked?: boolean
  _conflict?: boolean
}

/**
 * Enhanced DataTable with cell-level writeback support
 *
 * @param budgetVersionId - Current budget version
 * @param moduleCode - Module identifier ('enrollment', 'dhg', etc.)
 * @param enableWriteback - Enable cell editing and auto-save
 * @param onCellSaved - Optional callback after successful save
 * @param loading - Show loading overlay
 * @param error - Show error state
 */
export function EnhancedDataTable<TData = unknown>({
  budgetVersionId,
  enableWriteback = true,
  onCellSaved,
  loading = false,
  error = null,
  rowData,
  ...props
}: EnhancedDataTableProps<TData>) {
  const gridRef = useRef<AgGridReact<TData>>(null)
  const [savingCells, setSavingCells] = useState<Set<string>>(new Set())
  const [conflictCells, setConflictCells] = useState<Set<string>>(new Set())
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null)
  const [commentDialogOpen, setCommentDialogOpen] = useState(false)
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false)

  // Writeback hook for cell updates
  const { updateCell, isUpdating } = usePlanningWriteback(budgetVersionId)

  // User presence tracking
  const { activeUsers, broadcast } = useUserPresence({
    budgetVersionId,
  })

  // Subscribe to realtime changes
  useRealtimeSync({
    budgetVersionId,
    onCellChanged: (change: RealtimeChange) => {
      if (change.eventType === 'UPDATE') {
        flashCell(change.cell.id)
      }
    },
  })

  /**
   * Flash cell to indicate external change
   */
  const flashCell = useCallback((cellId: string) => {
    const gridApi: GridApi | undefined = gridRef.current?.api
    if (!gridApi) return

    // Find row and column
    gridApi.forEachNode((node) => {
      const data = node.data as CellData
      if (data && data.id === cellId) {
        // Flash the cell yellow
        node.setDataValue('_flash', true)
        setTimeout(() => {
          node.setDataValue('_flash', false)
        }, 1000)
      }
    })
  }, [])

  /**
   * Highlight cell conflict
   */
  const highlightCellConflict = useCallback((cellId: string) => {
    setConflictCells((prev) => new Set(prev).add(cellId))

    // Remove highlight after 3 seconds
    setTimeout(() => {
      setConflictCells((prev) => {
        const next = new Set(prev)
        next.delete(cellId)
        return next
      })
    }, 3000)
  }, [])

  /**
   * Cell value changed handler - triggers auto-save
   */
  const onCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<TData>) => {
      if (!enableWriteback) return

      const { data, colDef, newValue, oldValue, node } = event

      // Skip if value didn't actually change
      if (newValue === oldValue) return

      const cellData = data as CellData
      const cellId = cellData.id
      const fieldName = colDef.field!

      // Check if cell is locked
      if (cellData.is_locked) {
        // Revert change
        node.setDataValue(fieldName, oldValue)
        return
      }

      try {
        // Add to saving state
        setSavingCells((prev) => new Set(prev).add(cellId))

        // Update cell via API
        const result = await updateCell({
          cellId,
          value: parseFloat(newValue),
          version: cellData.version || 1,
        })

        // Update row data with new version
        node.setData({
          ...cellData,
          [fieldName]: newValue,
          version: result.version,
          updated_at: result.updated_at,
          updated_by: result.updated_by,
        } as TData)

        // Success callback
        if (onCellSaved) {
          onCellSaved(result as unknown as CellData)
        }
      } catch (error) {
        // Revert cell on error
        node.setDataValue(fieldName, oldValue)

        if (error instanceof VersionConflictError) {
          // Highlight cell in red
          highlightCellConflict(cellId)

          // Refetch row data
          // (handled by React Query invalidation in hook)
        }
      } finally {
        // Remove from saving state
        setSavingCells((prev) => {
          const next = new Set(prev)
          next.delete(cellId)
          return next
        })
      }
    },
    [enableWriteback, updateCell, onCellSaved, highlightCellConflict]
  )

  /**
   * Cell style function - show locked cells, saving state, conflicts
   */
  const getCellStyle = useCallback(
    (params: CellClassParams<TData>) => {
      const cellData = params.data as CellData
      if (!cellData) return null

      const cellId = cellData.id
      const isLocked = cellData.is_locked
      const isSaving = savingCells.has(cellId)
      const hasConflict = conflictCells.has(cellId)

      if (hasConflict) {
        return { backgroundColor: '#fcc', border: '2px solid #f88' }
      }

      if (isLocked) {
        return { backgroundColor: '#fee', cursor: 'not-allowed' }
      }

      if (isSaving) {
        return { backgroundColor: '#ffe', opacity: 0.7 }
      }

      return null
    },
    [savingCells, conflictCells]
  )

  /**
   * Cell class rules for CSS styling
   */
  const cellClassRules = useMemo(
    () => ({
      'cell-locked': (params: CellClassParams<TData>) => {
        const cellData = params.data as CellData
        return cellData?.is_locked || false
      },
      'cell-saving': (params: CellClassParams<TData>) => {
        const cellData = params.data as CellData
        return cellData ? savingCells.has(cellData.id) : false
      },
      'cell-conflict': (params: CellClassParams<TData>) => {
        const cellData = params.data as CellData
        return cellData ? conflictCells.has(cellData.id) : false
      },
    }),
    [savingCells, conflictCells]
  )

  /**
   * Context menu items
   */
  const getContextMenuItems = useCallback(
    (params: GetContextMenuItemsParams<TData>): (string | MenuItemDef)[] => {
      const cellData = params.node?.data as CellData
      const cellId = cellData?.id

      return [
        'copy',
        'copyWithHeaders',
        'paste',
        'separator',
        {
          name: 'Ajouter un commentaire',
          icon: '<span>💬</span>',
          action: () => {
            if (cellId) {
              setSelectedCellId(cellId)
              setCommentDialogOpen(true)
            }
          },
        },
        {
          name: "Voir l'historique",
          icon: '<span>📋</span>',
          action: () => {
            if (cellId) {
              setSelectedCellId(cellId)
              setHistoryDialogOpen(true)
            }
          },
        },
        'separator',
        {
          name: 'Verrouiller la cellule',
          icon: '<span>🔒</span>',
          disabled: cellData?.is_locked,
          action: () => {
            if (cellId) {
              // TODO: Implement lock cell API call
              console.log('Lock cell:', cellId)
            }
          },
        },
      ]
    },
    []
  )

  /**
   * Cell selection handler - update presence
   */
  const onCellClicked = useCallback(
    (event: { data: TData }) => {
      const cellData = event.data as CellData
      if (cellData?.id) {
        broadcast({
          action: 'editing',
          cellId: cellData.id,
          timestamp: new Date().toISOString(),
        })
      }
    },
    [broadcast]
  )

  /**
   * Default column definitions
   */
  const defaultColDef = useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      editable: enableWriteback,
      cellStyle: getCellStyle,
      cellClassRules,
      ...props.defaultColDef,
    }),
    [enableWriteback, getCellStyle, cellClassRules, props.defaultColDef]
  )

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-card border border-sand-200">
        <div className="text-center">
          <p className="text-error-600 font-medium">Error loading data</p>
          <p className="text-sm text-twilight-600 mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Active users indicator */}
      {activeUsers.length > 0 && (
        <div className="flex gap-2 items-center">
          <span className="text-sm text-twilight-600">Utilisateurs actifs:</span>
          {activeUsers.map((user) => (
            <Badge key={user.user_id} variant="secondary" className="gap-1">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
              {user.user_email}
            </Badge>
          ))}
        </div>
      )}

      {/* AG Grid */}
      <div
        className={cn(
          'ag-theme-quartz',
          'relative rounded-card border border-sand-200 overflow-hidden'
        )}
      >
        {(loading || isUpdating) && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <div className="flex gap-2 items-center text-twilight-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{loading ? 'Chargement...' : 'Sauvegarde en cours...'}</span>
            </div>
          </div>
        )}

        <AgGridReact
          ref={gridRef}
          {...props}
          rowData={rowData}
          defaultColDef={defaultColDef}
          onCellValueChanged={onCellValueChanged}
          onCellClicked={onCellClicked}
          getContextMenuItems={getContextMenuItems}
          suppressCellFocus={false}
          enableCellChangeFlash={true}
          animateRows={true}
          domLayout="normal"
          pagination={props.pagination !== undefined ? props.pagination : true}
          paginationPageSize={props.paginationPageSize || 50}
        />
      </div>

      {/* Cell comment dialog */}
      {selectedCellId && (
        <CellCommentDialog
          cellId={selectedCellId}
          open={commentDialogOpen}
          onOpenChange={setCommentDialogOpen}
        />
      )}

      {/* Cell history dialog */}
      {selectedCellId && (
        <CellHistoryDialog
          cellId={selectedCellId}
          budgetVersionId={budgetVersionId}
          open={historyDialogOpen}
          onOpenChange={setHistoryDialogOpen}
        />
      )}
    </div>
  )
}
