/**
 * EditableTable Component
 *
 * TanStack Table with inline cell editing support.
 * Provides AG Grid-like editing experience with keyboard navigation.
 *
 * Features:
 * - Click-to-edit, F2, type-to-edit, Enter
 * - Keyboard navigation (Tab, Arrow keys)
 * - Cell change callback compatible with AG Grid's onCellValueChanged
 * - Support for text, number, and checkbox editors
 *
 * @example
 * ```tsx
 * <EditableTable
 *   rowData={data}
 *   columnDefs={columns}
 *   getRowId={(row) => row.id}
 *   onCellValueChanged={(event) => {
 *     console.log('Cell changed:', event.data, event.field, event.newValue)
 *   }}
 * />
 * ```
 */

import React, { useMemo, useCallback, useRef, useEffect, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type Row,
  type Cell,
  type Table,
} from '@tanstack/react-table'
import { cn } from '@/lib/utils'
import { EditableCell } from './EditableCell'
import { useTableState } from './hooks'
import type { EditorType } from './editors'
import type { CellId } from '@/lib/grid'
import { Loader2, AlertTriangle, WifiOff, RefreshCw, Check, Minus } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

/**
 * Cell value changed event - compatible with AG Grid's CellValueChangedEvent
 */
export interface CellValueChangedEvent<TData> {
  /** The row data */
  data: TData
  /** The field/column that changed */
  field: string
  /** The old value */
  oldValue: unknown
  /** The new value */
  newValue: unknown
  /** The row ID */
  rowId: string
  /** The column ID */
  columnId: string
  /** Helper to revert the value (for validation failures) */
  revertValue: () => void
}

/**
 * Extended column definition with editing metadata
 */
export interface EditableColumnMeta {
  /** Whether this column is editable */
  editable?: boolean
  /** Type of editor to use */
  editorType?: EditorType
  /** Min value for number editor */
  min?: number
  /** Max value for number editor */
  max?: number
  /** Step for number editor */
  step?: number
  /** Decimal precision for number editor */
  precision?: number
  /** Placeholder text */
  placeholder?: string
  /** Max length for text editor */
  maxLength?: number
  /** Custom cell alignment */
  align?: 'left' | 'center' | 'right'
  /** Number of rows for large text editor */
  rows?: number
  /** Enable JSON validation for large text editor */
  validateJson?: boolean
}

export interface EditableTableProps<TData extends object> {
  /** Row data to display */
  rowData: TData[] | null | undefined

  /** Column definitions with editing metadata in `meta` */
  columnDefs: ColumnDef<TData, unknown>[]

  /** Function to get unique row ID from data */
  getRowId: (data: TData) => string

  /** Callback when a cell value changes */
  onCellValueChanged?: (event: CellValueChangedEvent<TData>) => void

  /** Show loading overlay */
  loading?: boolean

  /** Error state */
  error?: Error | null

  /** Callback to retry loading */
  onRetry?: () => void

  /** Enable sorting */
  enableSorting?: boolean

  /** Initial sorting state */
  initialSorting?: SortingState

  /** Compact row height (36px vs 44px) */
  compact?: boolean

  /** Table height */
  height?: number | string

  /** Empty state message */
  emptyMessage?: string

  /** Module color accent */
  moduleColor?:
    | 'gold'
    | 'sage'
    | 'terracotta'
    | 'slate'
    | 'wine'
    | 'orange'
    | 'teal'
    | 'blue'
    | 'purple'

  /** Additional class names */
  className?: string

  /** Unique table ID for accessibility */
  tableId?: string

  /** Table label for screen readers */
  tableLabel?: string

  /** Make all cells in certain columns read-only */
  readOnlyColumns?: string[]

  // ========== Row Selection Props ==========

  /** Enable row selection (default: false) */
  enableRowSelection?: boolean

  /** Callback when row selection changes */
  onRowSelectionChange?: (selectedRowIds: string[]) => void

  /** Show checkbox column for selection (default: false) */
  showCheckboxColumn?: boolean

  /** Initial selected row IDs */
  initialSelectedRowIds?: string[]

  /** Callback to get table state for external integration (e.g., keyboard hooks) */
  onTableReady?: (tableApi: EditableTableApi<TData>) => void
}

/**
 * Table API exposed for external integration (e.g., useGridExcelKeyboard)
 */
export interface EditableTableApi<TData> {
  /** Get all selected row IDs */
  getSelectedRowIds: () => string[]
  /** Get selected row data */
  getSelectedRows: () => TData[]
  /** Select specific rows */
  selectRows: (rowIds: string[]) => void
  /** Select all rows */
  selectAll: () => void
  /** Deselect all rows */
  deselectAll: () => void
  /** Get focused cell */
  getFocusedCell: () => CellId | null
  /** Check if a cell is editable */
  isCellEditable: (rowId: string, columnId: string) => boolean
  /** Get cell value */
  getCellValue: (rowId: string, columnId: string) => unknown
  /** Get all visible columns */
  getVisibleColumns: () => string[]
  /** Get row count */
  getRowCount: () => number
  /** Get container ref for keyboard events */
  getContainerRef: () => React.RefObject<HTMLDivElement | null>
}

// ============================================================================
// Utility Functions
// ============================================================================

function isNetworkError(error: Error): boolean {
  const message = error.message.toLowerCase()
  return (
    message.includes('network error') ||
    message.includes('failed to fetch') ||
    message.includes('econnrefused')
  )
}

// ============================================================================
// Component
// ============================================================================

export function EditableTable<TData extends object>({
  rowData,
  columnDefs,
  getRowId,
  onCellValueChanged,
  loading = false,
  error = null,
  onRetry,
  enableSorting = true,
  initialSorting = [],
  compact = true,
  height = 'auto',
  emptyMessage = 'No data available',
  // moduleColor is reserved for future styling extensions
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  moduleColor: _moduleColor = 'gold',
  className,
  // tableId and tableLabel reserved for accessibility enhancements
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  tableId: _tableId = 'editable-table',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  tableLabel: _tableLabel = 'Editable data table',
  readOnlyColumns = [],
  // Row selection props
  enableRowSelection = false,
  onRowSelectionChange,
  showCheckboxColumn = false,
  initialSelectedRowIds = [],
  onTableReady,
}: EditableTableProps<TData>) {
  const data = useMemo(() => rowData ?? [], [rowData])
  const containerRef = useRef<HTMLDivElement>(null)
  const tableRef = useRef<Table<TData> | null>(null)

  // Selection anchor for Shift+click range selection
  const selectionAnchorRef = useRef<string | null>(null)

  // Table state for focus, selection, and editing
  const { state: tableState, actions: tableActions } = useTableState<TData>({
    getRowId,
    initialSelectedRowIds,
    onSelectionChange: onRowSelectionChange,
  })

  const { focusedCell, editingCell, editingInitialKey, selectedRowIds } = tableState
  const {
    setFocusedCell,
    startEditing,
    stopEditing,
    isEditing,
    getNextCell,
    getAdjacentCell,
    // selectRow is available but not used in current implementation
    // selectRow,
    selectRows,
    toggleRowSelection,
    selectAll: selectAllRows,
    deselectAll,
    isRowSelected,
  } = tableActions

  // Track previous data for revert functionality
  const previousDataRef = useRef<Map<string, TData>>(new Map())

  // Update previous data when data changes
  useEffect(() => {
    const map = new Map<string, TData>()
    data.forEach((row) => {
      map.set(getRowId(row), { ...row })
    })
    previousDataRef.current = map
  }, [data, getRowId])

  // Handle row click for selection
  const handleRowClick = useCallback(
    (rowId: string, event: React.MouseEvent) => {
      if (!enableRowSelection) return

      const rows = tableRef.current?.getRowModel().rows ?? []
      const rowIndex = rows.findIndex((r) => r.id === rowId)

      if (event.shiftKey && selectionAnchorRef.current) {
        // Shift+click: range selection from anchor to clicked row
        const anchorIndex = rows.findIndex((r) => r.id === selectionAnchorRef.current)
        if (anchorIndex !== -1 && rowIndex !== -1) {
          const startIndex = Math.min(anchorIndex, rowIndex)
          const endIndex = Math.max(anchorIndex, rowIndex)
          const rangeRowIds = rows.slice(startIndex, endIndex + 1).map((r) => r.id)
          selectRows(rangeRowIds)
        }
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle selection
        toggleRowSelection(rowId)
        selectionAnchorRef.current = rowId
      } else {
        // Regular click: single select (deselect others)
        selectRows([rowId])
        selectionAnchorRef.current = rowId
      }
    },
    [enableRowSelection, selectRows, toggleRowSelection]
  )

  // Handle header checkbox click (select/deselect all)
  const handleHeaderCheckboxClick = useCallback(() => {
    if (!tableRef.current) return
    const allSelected = selectedRowIds.size === data.length && data.length > 0
    if (allSelected) {
      deselectAll()
    } else {
      selectAllRows(tableRef.current)
    }
  }, [data.length, selectedRowIds.size, deselectAll, selectAllRows])

  // Handle row checkbox click
  const handleRowCheckboxClick = useCallback(
    (rowId: string, event: React.MouseEvent) => {
      event.stopPropagation() // Don't trigger row click
      toggleRowSelection(rowId)
      selectionAnchorRef.current = rowId
    },
    [toggleRowSelection]
  )

  // Sorting state
  const [sorting, setSorting] = useState<SortingState>(initialSorting)

  // TanStack Table instance
  const table = useReactTable({
    data,
    columns: columnDefs,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: getFilteredRowModel(),
    getRowId: (row) => getRowId(row),
    state: {
      sorting,
    },
    onSortingChange: setSorting,
  })

  // Store table reference for state actions
  tableRef.current = table

  // Create and expose table API for external integration
  const isCellEditableById = useCallback(
    (rowId: string, columnId: string): boolean => {
      const row = table.getRowModel().rows.find((r) => r.id === rowId)
      if (!row) return false
      const cell = row.getVisibleCells().find((c) => c.column.id === columnId)
      if (!cell) return false

      const meta = cell.column.columnDef.meta as EditableColumnMeta | undefined
      if (meta?.editable === false) return false
      if (readOnlyColumns.includes(columnId)) return false
      return meta?.editable ?? false
    },
    [table, readOnlyColumns]
  )

  const getCellValueById = useCallback(
    (rowId: string, columnId: string): unknown => {
      const row = table.getRowModel().rows.find((r) => r.id === rowId)
      if (!row) return undefined
      const cell = row.getVisibleCells().find((c) => c.column.id === columnId)
      if (!cell) return undefined
      return cell.getValue()
    },
    [table]
  )

  // Table API for external integration (keyboard hooks, etc.)
  useEffect(() => {
    if (!onTableReady) return

    const tableApi: EditableTableApi<TData> = {
      getSelectedRowIds: () => Array.from(selectedRowIds),
      getSelectedRows: () => {
        const rows = table.getRowModel().rows
        return rows.filter((r) => selectedRowIds.has(r.id)).map((r) => r.original)
      },
      selectRows,
      selectAll: () => tableRef.current && selectAllRows(tableRef.current),
      deselectAll,
      getFocusedCell: () => focusedCell,
      isCellEditable: isCellEditableById,
      getCellValue: getCellValueById,
      getVisibleColumns: () => table.getVisibleLeafColumns().map((c) => c.id),
      getRowCount: () => table.getRowModel().rows.length,
      getContainerRef: () => containerRef,
    }

    onTableReady(tableApi)
  }, [
    onTableReady,
    selectedRowIds,
    selectRows,
    selectAllRows,
    deselectAll,
    focusedCell,
    isCellEditableById,
    getCellValueById,
    table,
  ])

  // Navigate to a cell by direction
  const navigateCell = useCallback(
    (
      direction: 'up' | 'down' | 'left' | 'right' | 'next' | 'prev',
      currentCell: CellId | null = focusedCell
    ) => {
      if (!currentCell || !tableRef.current) return

      let nextCell: CellId | null = null

      if (direction === 'next' || direction === 'prev') {
        nextCell = getAdjacentCell(currentCell, direction, tableRef.current)
      } else {
        const navDirection =
          direction === 'left' ? 'left' : direction === 'right' ? 'right' : direction
        nextCell = getNextCell(currentCell, navDirection, tableRef.current)
      }

      if (nextCell) {
        setFocusedCell(nextCell)
      }
    },
    [focusedCell, getNextCell, getAdjacentCell, setFocusedCell]
  )

  // Handle cell commit
  const handleCellCommit = useCallback(
    (rowId: string, columnId: string, newValue: unknown) => {
      const row = table.getRowModel().rows.find((r) => r.id === rowId)
      if (!row) return

      const column = table.getColumn(columnId)
      if (!column) return

      // Get the field name (accessorKey)
      const field =
        'accessorKey' in column.columnDef ? (column.columnDef.accessorKey as string) : columnId

      const rowData = row.original
      const oldValue = rowData[field as keyof TData]

      // Call the change handler
      if (onCellValueChanged && oldValue !== newValue) {
        const event: CellValueChangedEvent<TData> = {
          data: rowData,
          field,
          oldValue,
          newValue,
          rowId,
          columnId,
          revertValue: () => {
            // Revert is handled by the parent component updating rowData
          },
        }
        onCellValueChanged(event)
      }

      stopEditing()
    },
    [table, onCellValueChanged, stopEditing]
  )

  // Handle cell cancel
  const handleCellCancel = useCallback(() => {
    stopEditing()
  }, [stopEditing])

  // Handle cell navigation (Tab / Shift+Tab)
  const handleNavigate = useCallback(
    (direction: 'next' | 'prev') => {
      navigateCell(direction)
    },
    [navigateCell]
  )

  // Handle row navigation (Enter / Shift+Enter)
  const handleNavigateRow = useCallback(
    (direction: 'up' | 'down') => {
      navigateCell(direction)
    },
    [navigateCell]
  )

  // Handle container keyboard events (when not editing)
  const handleContainerKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (isEditing()) return

      // Ctrl+A to select all rows
      if ((e.ctrlKey || e.metaKey) && e.key === 'a' && enableRowSelection) {
        e.preventDefault()
        if (tableRef.current) {
          selectAllRows(tableRef.current)
        }
        return
      }

      // Escape to deselect all
      if (e.key === 'Escape' && enableRowSelection) {
        e.preventDefault()
        deselectAll()
        return
      }

      // If no cell is focused, focus the first cell
      if (!focusedCell && tableRef.current) {
        const rows = tableRef.current.getRowModel().rows
        const columns = tableRef.current.getVisibleLeafColumns()
        if (rows.length > 0 && columns.length > 0) {
          setFocusedCell({ rowId: rows[0].id, columnId: columns[0].id })
        }
        return
      }

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault()
          navigateCell('up')
          break
        case 'ArrowDown':
          e.preventDefault()
          navigateCell('down')
          break
        case 'ArrowLeft':
          e.preventDefault()
          navigateCell('left')
          break
        case 'ArrowRight':
          e.preventDefault()
          navigateCell('right')
          break
        case 'Tab':
          e.preventDefault()
          navigateCell(e.shiftKey ? 'prev' : 'next')
          break
      }
    },
    [
      isEditing,
      focusedCell,
      setFocusedCell,
      navigateCell,
      enableRowSelection,
      selectAllRows,
      deselectAll,
    ]
  )

  // Check if a cell is editable
  const isCellEditable = useCallback(
    (cell: Cell<TData, unknown>) => {
      const meta = cell.column.columnDef.meta as EditableColumnMeta | undefined
      if (meta?.editable === false) return false
      if (readOnlyColumns.includes(cell.column.id)) return false
      return meta?.editable ?? false
    },
    [readOnlyColumns]
  )

  // Get editor type for a cell
  const getEditorType = useCallback((cell: Cell<TData, unknown>): EditorType => {
    const meta = cell.column.columnDef.meta as EditableColumnMeta | undefined
    return meta?.editorType ?? 'text'
  }, [])

  // Get editor props for a cell
  const getEditorProps = useCallback((cell: Cell<TData, unknown>) => {
    const meta = cell.column.columnDef.meta as EditableColumnMeta | undefined
    return {
      min: meta?.min,
      max: meta?.max,
      step: meta?.step,
      precision: meta?.precision,
      placeholder: meta?.placeholder,
      maxLength: meta?.maxLength,
      rows: meta?.rows,
      validateJson: meta?.validateJson,
    }
  }, [])

  // Render cell content
  const renderCell = useCallback(
    (cell: Cell<TData, unknown>, row: Row<TData>) => {
      const rowId = row.id
      const columnId = cell.column.id
      const value = cell.getValue()
      const editable = isCellEditable(cell)
      const editorType = getEditorType(cell)
      const editorProps = getEditorProps(cell)

      const cellIsFocused = focusedCell?.rowId === rowId && focusedCell?.columnId === columnId
      const cellIsEditing = editingCell?.rowId === rowId && editingCell?.columnId === columnId

      if (!editable) {
        // Non-editable cell - just render the value
        return (
          <div
            className={cn(
              'px-3 py-2 truncate',
              cellIsFocused && 'ring-2 ring-inset ring-gold-500/50 bg-gold-50/30'
            )}
            onClick={() => setFocusedCell({ rowId, columnId })}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </div>
        )
      }

      return (
        <EditableCell
          rowId={rowId}
          columnId={columnId}
          value={value}
          editorType={editorType}
          isEditing={cellIsEditing}
          isFocused={cellIsFocused}
          onStartEdit={(initialKey) => startEditing({ rowId, columnId }, initialKey)}
          onCommit={(newValue) => handleCellCommit(rowId, columnId, newValue)}
          onCancel={handleCellCancel}
          onNavigate={handleNavigate}
          onNavigateRow={handleNavigateRow}
          editable={editable}
          initialKey={cellIsEditing ? editingInitialKey : null}
          displayRenderer={() => flexRender(cell.column.columnDef.cell, cell.getContext())}
          {...editorProps}
        />
      )
    },
    [
      focusedCell,
      editingCell,
      editingInitialKey,
      isCellEditable,
      getEditorType,
      getEditorProps,
      setFocusedCell,
      startEditing,
      handleCellCommit,
      handleCellCancel,
      handleNavigate,
      handleNavigateRow,
    ]
  )

  // Error state
  if (error) {
    const networkError = isNetworkError(error)
    return (
      <div
        role="alert"
        className={cn(
          'flex items-center justify-center h-64',
          'bg-[var(--color-paper)] rounded-xl',
          'border border-[var(--color-border-light)]'
        )}
      >
        <div className="text-center max-w-md px-4">
          <div className="flex justify-center mb-3">
            {networkError ? (
              <div className="p-3 bg-red-100 rounded-full">
                <WifiOff className="h-6 w-6 text-red-500" />
              </div>
            ) : (
              <div className="p-3 bg-amber-100 rounded-full">
                <AlertTriangle className="h-6 w-6 text-amber-600" />
              </div>
            )}
          </div>
          <p className="text-[var(--color-terracotta)] font-semibold text-lg">
            {networkError ? 'Cannot connect to server' : 'Error loading data'}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">
            {networkError ? 'The backend server is not responding.' : error.message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className={cn(
                'mt-4 inline-flex items-center gap-2 px-4 py-2',
                'bg-[var(--color-gold-lighter)] hover:bg-[var(--color-gold-light)]',
                'text-[var(--color-gold-dark)] rounded-md font-medium text-sm'
              )}
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  // Loading state
  if (loading && data.length === 0) {
    return (
      <div
        role="status"
        className={cn(
          'flex items-center justify-center',
          'bg-[var(--color-paper)] rounded-xl',
          'border border-[var(--color-border-light)]'
        )}
        style={{ height: typeof height === 'number' ? height : 400 }}
      >
        <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
          <Loader2 className="h-5 w-5 animate-spin text-[var(--color-gold)]" />
          <span>Loading data...</span>
        </div>
      </div>
    )
  }

  const rowHeight = compact ? 36 : 44
  const headerHeight = 40

  return (
    <div
      ref={containerRef}
      className={cn(
        'rounded-xl border border-[var(--color-border-light)]',
        'bg-[var(--color-paper)]',
        'shadow-sm overflow-hidden',
        className
      )}
      style={{ height }}
      onKeyDown={handleContainerKeyDown}
      tabIndex={-1}
    >
      {/* Header */}
      <div
        className={cn(
          'sticky top-0 z-10',
          'bg-[var(--color-paper)]',
          'border-b border-[var(--color-border-medium)]'
        )}
        style={{ height: headerHeight }}
      >
        <div className="flex">
          {/* Checkbox column header */}
          {showCheckboxColumn && enableRowSelection && (
            <div
              className={cn(
                'flex items-center justify-center',
                'text-xs font-semibold',
                'cursor-pointer select-none',
                'hover:bg-[var(--color-warm)]'
              )}
              style={{ width: 40, height: headerHeight }}
              onClick={handleHeaderCheckboxClick}
              role="columnheader"
              aria-label="Select all rows"
            >
              <div
                className={cn(
                  'w-4 h-4 rounded border flex items-center justify-center',
                  'transition-colors duration-150',
                  selectedRowIds.size === data.length && data.length > 0
                    ? 'bg-[var(--color-gold)] border-[var(--color-gold)] text-white'
                    : selectedRowIds.size > 0
                      ? 'bg-[var(--color-gold-lighter)] border-[var(--color-gold)]'
                      : 'border-[var(--color-border-medium)] bg-white'
                )}
              >
                {selectedRowIds.size === data.length && data.length > 0 ? (
                  <Check className="h-3 w-3" />
                ) : selectedRowIds.size > 0 ? (
                  <Minus className="h-3 w-3 text-[var(--color-gold)]" />
                ) : null}
              </div>
            </div>
          )}
          {table.getHeaderGroups().map((headerGroup) =>
            headerGroup.headers.map((header) => (
              <div
                key={header.id}
                className={cn(
                  'flex items-center px-3',
                  'text-xs font-semibold uppercase tracking-wide',
                  'text-[var(--color-text-secondary)]',
                  enableSorting && header.column.getCanSort() && 'cursor-pointer select-none',
                  enableSorting &&
                    header.column.getCanSort() &&
                    'hover:text-[var(--color-text-primary)]'
                )}
                style={{
                  width: header.getSize(),
                  height: headerHeight,
                }}
                onClick={
                  enableSorting && header.column.getCanSort()
                    ? header.column.getToggleSortingHandler()
                    : undefined
                }
              >
                {flexRender(header.column.columnDef.header, header.getContext())}
                {/* Sort indicator */}
                {header.column.getIsSorted() && (
                  <span className="ml-1">{header.column.getIsSorted() === 'asc' ? '↑' : '↓'}</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Body */}
      <div
        className="overflow-auto"
        style={{
          height:
            height === 'auto'
              ? 'auto'
              : `calc(${typeof height === 'number' ? `${height}px` : height} - ${headerHeight}px)`,
        }}
      >
        {data.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-[var(--color-text-secondary)]">
            {emptyMessage}
          </div>
        ) : (
          table.getRowModel().rows.map((row, rowIndex) => {
            const rowIsSelected = isRowSelected(row.id)
            return (
              <div
                key={row.id}
                className={cn(
                  'flex border-b border-[var(--color-border-light)]',
                  'transition-colors duration-150',
                  // Selection styling takes precedence
                  rowIsSelected
                    ? 'bg-[var(--color-gold-lighter)] border-l-[3px] border-l-[var(--color-gold)]'
                    : cn(
                        'hover:bg-[var(--color-warm)]',
                        rowIndex % 2 === 1 && 'bg-[var(--color-subtle)]'
                      ),
                  // Clickable when row selection is enabled
                  enableRowSelection && 'cursor-pointer'
                )}
                style={{ height: rowHeight }}
                onClick={enableRowSelection ? (e) => handleRowClick(row.id, e) : undefined}
                role={enableRowSelection ? 'row' : undefined}
                aria-selected={enableRowSelection ? rowIsSelected : undefined}
              >
                {/* Row checkbox */}
                {showCheckboxColumn && enableRowSelection && (
                  <div
                    className="flex items-center justify-center"
                    style={{ width: 40 }}
                    onClick={(e) => handleRowCheckboxClick(row.id, e)}
                  >
                    <div
                      className={cn(
                        'w-4 h-4 rounded border flex items-center justify-center',
                        'transition-colors duration-150',
                        rowIsSelected
                          ? 'bg-[var(--color-gold)] border-[var(--color-gold)] text-white'
                          : 'border-[var(--color-border-medium)] bg-white hover:border-[var(--color-gold)]'
                      )}
                    >
                      {rowIsSelected && <Check className="h-3 w-3" />}
                    </div>
                  </div>
                )}
                {row.getVisibleCells().map((cell) => (
                  <div
                    key={cell.id}
                    className="flex items-center"
                    style={{ width: cell.column.getSize() }}
                  >
                    {renderCell(cell, row)}
                  </div>
                ))}
              </div>
            )
          })
        )}
      </div>

      {/* Loading overlay when updating */}
      {loading && data.length > 0 && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-[var(--color-gold)]" />
        </div>
      )}
    </div>
  )
}
