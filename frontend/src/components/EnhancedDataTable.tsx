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
  GridApi,
  CellStyle,
  CellClickedEvent,
  GetContextMenuItems,
} from 'ag-grid-community'
import { themeQuartz } from 'ag-grid-community'
import { Loader2 } from 'lucide-react'
import { Badge } from './ui/badge'
import { cn } from '@/lib/utils'
import { usePlanningWriteback, VersionConflictError } from '@/hooks/api/usePlanningWriteback'
import { useRealtimeSync } from '@/hooks/useRealtimeSync'
import { useUserPresence } from '@/hooks/useUserPresence'
import type { RealtimeChange } from '@/types/writeback'
import { CellCommentDialog } from './CellCommentDialog'
import { CellHistoryDialog } from './CellHistoryDialog'
import { useCustomClipboard } from '@/hooks/useCustomClipboard'

export interface EnhancedDataTableProps<TData = unknown> extends Omit<
  AgGridReactProps<TData>,
  'onCellValueChanged'
> {
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

  // Writeback hook for cell updates and locking
  const { updateCell, lockCell, unlockCell, isUpdating, isLocking } =
    usePlanningWriteback(budgetVersionId)

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

  /*
   * Custom Clipboard Handler (Paste)
   */
  const onPasteCells = useCallback(
    async (
      updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
    ) => {
      if (!enableWriteback) return

      // Mark all as saving
      updates.forEach((u) => setSavingCells((prev) => new Set(prev).add(u.rowId)))

      try {
        const promises = updates.map(async (update) => {
          const { rowId, field, newValue, originalData } = update
          const cellData = originalData as CellData
          const version = cellData?.version || 1

          // 1. Update Grid UI immediately (Optimistic)
          const rowNode = gridRef.current?.api.getRowNode(rowId)
          if (rowNode) {
            rowNode.setDataValue(field, newValue)
          }

          // 2. Persist to Backend
          await updateCell({
            cellId: rowId,
            value: parseFloat(newValue),
            version,
          })
        })

        await Promise.all(promises)
      } catch (error) {
        console.error('Paste failed', error)
        // Ideally revert changes here if possible
      } finally {
        updates.forEach((u) =>
          setSavingCells((prev) => {
            const next = new Set(prev)
            next.delete(u.rowId)
            return next
          })
        )
      }
    },
    [enableWriteback, updateCell]
  )

  // Custom Clipboard Hook
  const { handlePaste } = useCustomClipboard({
    gridApi: gridRef.current?.api || null,
    onPasteCells,
  })

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
    (params: CellClassParams<TData>): CellStyle | null => {
      const cellData = params.data as CellData
      if (!cellData) return null

      const cellId = cellData.id
      const isLocked = cellData.is_locked
      const isSaving = savingCells.has(cellId)
      const hasConflict = conflictCells.has(cellId)

      if (hasConflict) {
        return {
          backgroundColor: 'var(--color-terracotta-light)',
          border: '2px solid var(--color-terracotta)',
        } as CellStyle
      }

      if (isLocked) {
        return {
          backgroundColor: 'var(--color-status-error-bg)',
          cursor: 'not-allowed',
        } as CellStyle
      }

      if (isSaving) {
        return { backgroundColor: 'var(--color-status-warning-bg)', opacity: 0.7 } as CellStyle
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
  const getContextMenuItems: GetContextMenuItems<TData> = useCallback(
    (params: GetContextMenuItemsParams<TData>) => {
      const cellData = params.node?.data as CellData | undefined
      const cellId = cellData?.id

      return [
        'copy',
        'copyWithHeaders',
        'paste',
        'separator',
        {
          name: 'Add comment',
          icon: '<span>💬</span>',
          action: () => {
            if (cellId) {
              setSelectedCellId(cellId)
              setCommentDialogOpen(true)
            }
          },
        },
        {
          name: 'View history',
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
          name: cellData?.is_locked ? 'Unlock cell' : 'Lock cell',
          icon: cellData?.is_locked ? '<span>🔓</span>' : '<span>🔒</span>',
          action: async () => {
            if (cellId) {
              if (cellData?.is_locked) {
                // Unlock the cell
                await unlockCell({ cellId })
              } else {
                // Lock the cell
                await lockCell({ cellId, reason: 'Manual lock' })
              }
            }
          },
        },
      ]
    },
    [lockCell, unlockCell]
  )

  /**
   * Cell selection handler - update presence
   */
  const onCellClicked = useCallback(
    (event: CellClickedEvent<TData>) => {
      const cellData = event.data as CellData | undefined
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
      <div className="flex items-center justify-center h-64 bg-white rounded-card border border-border-light">
        <div className="text-center">
          <p className="text-error-600 font-medium">Error loading data</p>
          <p className="text-sm text-text-secondary mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Active users indicator */}
      {activeUsers.length > 0 && (
        <div className="flex gap-2 items-center">
          <span className="text-sm text-text-secondary">Utilisateurs actifs:</span>
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
        className={cn('relative rounded-card border border-border-light overflow-hidden')}
        onPaste={handlePaste}
      >
        {(loading || isUpdating || isLocking) && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <div className="flex gap-2 items-center text-text-secondary">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{loading ? 'Loading...' : isLocking ? 'Locking...' : 'Saving...'}</span>
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
          animateRows={true}
          domLayout="normal"
          pagination={props.pagination !== undefined ? props.pagination : true}
          paginationPageSize={props.paginationPageSize || 50}
          theme={themeQuartz}
          // Community "Excel-like" Features
          undoRedoCellEditing={true}
          undoRedoCellEditingLimit={20}
          enableCellTextSelection={true}
          // enableCellChangeFlash={true} // Not available in all versions or redundant
          rowSelection={{ mode: 'multiRow' }}
          ensureDomOrder={true}
          // Custom Copy/Paste Support
          getRowId={(params) => (params.data as unknown as CellData).id} // Ensure we can find rows by ID
          onGridReady={(params) => {
            if (props.onGridReady) props.onGridReady(params)
            // We could store api in local ref if needed, but gridRef handles it
          }}
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
