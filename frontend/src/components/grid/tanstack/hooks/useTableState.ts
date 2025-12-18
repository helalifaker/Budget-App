/**
 * useTableState Hook
 *
 * Manages focus, selection, and edit state for TanStack Table.
 *
 * TanStack Table is headless and doesn't manage UI state like focus and selection
 * automatically. This hook provides that state management using stable row IDs
 * (not indices) for correct behavior across sorting/filtering.
 *
 * KEY DESIGN DECISIONS:
 * - All state uses rowId + columnId (never rowIndex)
 * - Selection is stored as a Set<string> of row IDs
 * - Focus and edit state use CellId (rowId + columnId)
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import type { Table } from '@tanstack/react-table'
import type { CellId } from '@/lib/grid'

// ============================================================================
// Types
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export interface TableState<_TData> {
  /** Currently focused cell (stable ID, not index) */
  focusedCell: CellId | null
  /** Set of selected row IDs */
  selectedRowIds: Set<string>
  /** Cell currently being edited (null if not editing) */
  editingCell: CellId | null
  /** Initial key that triggered editing (for type-to-edit) */
  editingInitialKey: string | null
}

export interface TableStateActions<TData> {
  // Focus
  setFocusedCell: (cellId: CellId | null) => void
  setFocusedCellByIndex: (rowIndex: number, columnId: string, table: Table<TData>) => void
  clearFocus: () => void

  // Selection
  selectRow: (rowId: string) => void
  deselectRow: (rowId: string) => void
  toggleRowSelection: (rowId: string) => void
  selectRows: (rowIds: string[]) => void
  selectAll: (table: Table<TData>) => void
  deselectAll: () => void
  isRowSelected: (rowId: string) => boolean

  // Editing
  startEditing: (cellId: CellId, initialKey?: string) => void
  stopEditing: () => void
  isEditing: () => boolean
  getEditingCell: () => CellId | null

  // Navigation helpers
  getNextCell: (
    current: CellId,
    direction: 'up' | 'down' | 'left' | 'right',
    table: Table<TData>
  ) => CellId | null
  getAdjacentCell: (
    current: CellId,
    direction: 'next' | 'prev',
    table: Table<TData>
  ) => CellId | null
}

export interface UseTableStateOptions<TData> {
  /** Function to get row ID from row data */
  getRowId: (row: TData) => string
  /** Initial focused cell */
  initialFocusedCell?: CellId | null
  /** Initial selected row IDs */
  initialSelectedRowIds?: string[]
  /** Callback when focus changes */
  onFocusChange?: (cellId: CellId | null) => void
  /** Callback when selection changes */
  onSelectionChange?: (selectedIds: string[]) => void
  /** Callback when editing starts */
  onEditStart?: (cellId: CellId, initialKey?: string) => void
  /** Callback when editing ends */
  onEditEnd?: (cellId: CellId | null) => void
}

export interface UseTableStateReturn<TData> {
  state: TableState<TData>
  actions: TableStateActions<TData>
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useTableState<TData>(
  options: UseTableStateOptions<TData>
): UseTableStateReturn<TData> {
  const {
    // getRowId is not used in this hook (TanStack Table has its own row ID system)
    // but it's kept in options for API compatibility with GridAdapter pattern
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    getRowId: _getRowId,
    initialFocusedCell = null,
    initialSelectedRowIds = [],
    onFocusChange,
    onSelectionChange,
    onEditStart,
    onEditEnd,
  } = options

  // State
  const [focusedCell, setFocusedCellInternal] = useState<CellId | null>(initialFocusedCell)
  const [selectedRowIds, setSelectedRowIds] = useState<Set<string>>(new Set(initialSelectedRowIds))
  const [editingCell, setEditingCell] = useState<CellId | null>(null)
  const [editingInitialKey, setEditingInitialKey] = useState<string | null>(null)

  // Track initial render to avoid calling onSelectionChange on mount
  const isInitialRender = useRef(true)

  // Call onSelectionChange when selectedRowIds changes (after state is committed)
  // This avoids the "Cannot update component while rendering another" React error
  useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false
      return
    }
    onSelectionChange?.(Array.from(selectedRowIds))
  }, [selectedRowIds, onSelectionChange])

  // State object
  const state: TableState<TData> = useMemo(
    () => ({
      focusedCell,
      selectedRowIds,
      editingCell,
      editingInitialKey,
    }),
    [focusedCell, selectedRowIds, editingCell, editingInitialKey]
  )

  // ========== Focus Actions ==========

  const setFocusedCell = useCallback(
    (cellId: CellId | null) => {
      setFocusedCellInternal(cellId)
      onFocusChange?.(cellId)
    },
    [onFocusChange]
  )

  const setFocusedCellByIndex = useCallback(
    (rowIndex: number, columnId: string, table: Table<TData>) => {
      const rows = table.getRowModel().rows
      if (rowIndex < 0 || rowIndex >= rows.length) return

      const row = rows[rowIndex]
      const rowId = row.id
      const cellId: CellId = { rowId, columnId }

      setFocusedCell(cellId)
    },
    [setFocusedCell]
  )

  const clearFocus = useCallback(() => {
    setFocusedCell(null)
  }, [setFocusedCell])

  // ========== Selection Actions ==========

  const selectRow = useCallback((rowId: string) => {
    setSelectedRowIds((prev) => {
      const next = new Set(prev)
      next.add(rowId)
      return next
    })
  }, [])

  const deselectRow = useCallback((rowId: string) => {
    setSelectedRowIds((prev) => {
      const next = new Set(prev)
      next.delete(rowId)
      return next
    })
  }, [])

  const toggleRowSelection = useCallback((rowId: string) => {
    setSelectedRowIds((prev) => {
      const next = new Set(prev)
      if (next.has(rowId)) {
        next.delete(rowId)
      } else {
        next.add(rowId)
      }
      return next
    })
  }, [])

  const selectRows = useCallback((rowIds: string[]) => {
    setSelectedRowIds(new Set(rowIds))
  }, [])

  const selectAll = useCallback((table: Table<TData>) => {
    const allRowIds = table.getRowModel().rows.map((row) => row.id)
    setSelectedRowIds(new Set(allRowIds))
  }, [])

  const deselectAll = useCallback(() => {
    setSelectedRowIds(new Set())
  }, [])

  const isRowSelected = useCallback((rowId: string) => selectedRowIds.has(rowId), [selectedRowIds])

  // ========== Editing Actions ==========

  const startEditing = useCallback(
    (cellId: CellId, initialKey?: string) => {
      setEditingCell(cellId)
      setEditingInitialKey(initialKey ?? null)
      setFocusedCell(cellId)
      onEditStart?.(cellId, initialKey)
    },
    [setFocusedCell, onEditStart]
  )

  const stopEditing = useCallback(() => {
    const prevEditingCell = editingCell
    setEditingCell(null)
    setEditingInitialKey(null)
    onEditEnd?.(prevEditingCell)
  }, [editingCell, onEditEnd])

  const isEditing = useCallback(() => editingCell !== null, [editingCell])

  const getEditingCell = useCallback(() => editingCell, [editingCell])

  // ========== Navigation Helpers ==========

  const getNextCell = useCallback(
    (
      current: CellId,
      direction: 'up' | 'down' | 'left' | 'right',
      table: Table<TData>
    ): CellId | null => {
      const rows = table.getRowModel().rows
      const visibleColumns = table.getVisibleLeafColumns()

      // Find current position
      const rowIndex = rows.findIndex((r) => r.id === current.rowId)
      const colIndex = visibleColumns.findIndex((c) => c.id === current.columnId)

      if (rowIndex === -1 || colIndex === -1) return null

      let newRowIndex = rowIndex
      let newColIndex = colIndex

      switch (direction) {
        case 'up':
          newRowIndex = Math.max(0, rowIndex - 1)
          break
        case 'down':
          newRowIndex = Math.min(rows.length - 1, rowIndex + 1)
          break
        case 'left':
          newColIndex = Math.max(0, colIndex - 1)
          break
        case 'right':
          newColIndex = Math.min(visibleColumns.length - 1, colIndex + 1)
          break
      }

      const newRow = rows[newRowIndex]
      const newColumn = visibleColumns[newColIndex]

      if (!newRow || !newColumn) return null

      return { rowId: newRow.id, columnId: newColumn.id }
    },
    []
  )

  const getAdjacentCell = useCallback(
    (current: CellId, direction: 'next' | 'prev', table: Table<TData>): CellId | null => {
      const rows = table.getRowModel().rows
      const visibleColumns = table.getVisibleLeafColumns()

      // Find current position
      const rowIndex = rows.findIndex((r) => r.id === current.rowId)
      const colIndex = visibleColumns.findIndex((c) => c.id === current.columnId)

      if (rowIndex === -1 || colIndex === -1) return null

      let newRowIndex = rowIndex
      let newColIndex = colIndex

      if (direction === 'next') {
        newColIndex++
        if (newColIndex >= visibleColumns.length) {
          newColIndex = 0
          newRowIndex++
        }
      } else {
        newColIndex--
        if (newColIndex < 0) {
          newColIndex = visibleColumns.length - 1
          newRowIndex--
        }
      }

      // Bounds checking
      if (newRowIndex < 0 || newRowIndex >= rows.length) return null

      const newRow = rows[newRowIndex]
      const newColumn = visibleColumns[newColIndex]

      if (!newRow || !newColumn) return null

      return { rowId: newRow.id, columnId: newColumn.id }
    },
    []
  )

  // ========== Actions Object ==========

  const actions: TableStateActions<TData> = useMemo(
    () => ({
      // Focus
      setFocusedCell,
      setFocusedCellByIndex,
      clearFocus,
      // Selection
      selectRow,
      deselectRow,
      toggleRowSelection,
      selectRows,
      selectAll,
      deselectAll,
      isRowSelected,
      // Editing
      startEditing,
      stopEditing,
      isEditing,
      getEditingCell,
      // Navigation
      getNextCell,
      getAdjacentCell,
    }),
    [
      setFocusedCell,
      setFocusedCellByIndex,
      clearFocus,
      selectRow,
      deselectRow,
      toggleRowSelection,
      selectRows,
      selectAll,
      deselectAll,
      isRowSelected,
      startEditing,
      stopEditing,
      isEditing,
      getEditingCell,
      getNextCell,
      getAdjacentCell,
    ]
  )

  return { state, actions }
}
