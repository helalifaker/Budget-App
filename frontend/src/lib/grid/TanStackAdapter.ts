/**
 * TanStackAdapter
 *
 * Implementation of GridAdapter that wraps TanStack Table's Table instance
 * and external state management hooks.
 *
 * Unlike AG Grid which has built-in state management, TanStack Table is headless
 * and requires external state for focus, selection, and editing. This adapter
 * bridges that gap by accepting state/actions from useTableState hook.
 *
 * @see AGGridAdapter for comparison
 * @see useTableState for the state management hook
 */

import type { Table, Row, Column, ColumnDef } from '@tanstack/react-table'
import type {
  GridAdapter,
  CellId,
  RowNode,
  ColumnAdapter,
  FocusedCell,
  EditingCellInfo,
  SelectionChangeCallback,
  FocusChangeCallback,
  CellValueChangeCallback,
  Unsubscribe,
  GridAdapterOptions,
} from './GridAdapter'

// ============================================================================
// Types
// ============================================================================

/**
 * State interface that TanStackAdapter expects from external state management.
 * This is typically provided by useTableState hook.
 */
export interface TanStackTableState {
  focusedCell: CellId | null
  selectedRowIds: Set<string>
  editingCell: CellId | null
  editingInitialKey: string | null
}

/**
 * Actions interface for state mutations.
 * These are typically provided by useTableState hook.
 */
export interface TanStackTableActions<TData> {
  setFocusedCell: (cellId: CellId | null) => void
  selectRows: (rowIds: string[]) => void
  selectAll: (table: Table<TData>) => void
  deselectAll: () => void
  startEditing: (cellId: CellId, initialKey?: string) => void
  stopEditing: () => void
}

/**
 * Options for creating a TanStackAdapter.
 */
export interface TanStackAdapterOptions<TData> extends GridAdapterOptions<TData> {
  /** TanStack Table instance */
  table: Table<TData>
  /** External state from useTableState */
  state: TanStackTableState
  /** External actions from useTableState */
  actions: TanStackTableActions<TData>
  /** Callback when cell value is updated */
  onCellValueChange?: (rowId: string, columnId: string, value: unknown) => void
  /** Reference to scroll container for scroll operations */
  scrollContainerRef?: React.RefObject<HTMLDivElement | null>
}

// ============================================================================
// TanStackAdapter Implementation
// ============================================================================

/**
 * TanStack Table implementation of the GridAdapter interface.
 *
 * @template TData - The type of data in each row
 */
export class TanStackAdapter<TData extends Record<string, unknown>> implements GridAdapter<TData> {
  private readonly table: Table<TData>
  private readonly state: TanStackTableState
  private readonly actions: TanStackTableActions<TData>
  private readonly onCellValueChangeFn?: (rowId: string, columnId: string, value: unknown) => void
  private readonly scrollContainerRef?: React.RefObject<HTMLDivElement | null>

  /**
   * Function to derive row ID from data.
   */
  public readonly getRowId: (data: TData) => string

  // Event listener tracking
  private selectionListeners: SelectionChangeCallback[] = []
  private focusListeners: FocusChangeCallback[] = []
  private cellValueListeners: CellValueChangeCallback[] = []

  constructor(options: TanStackAdapterOptions<TData>) {
    this.table = options.table
    this.state = options.state
    this.actions = options.actions
    this.getRowId = options.getRowId
    this.onCellValueChangeFn = options.onCellValueChange
    this.scrollContainerRef = options.scrollContainerRef
  }

  /**
   * Update the adapter with new state.
   * Call this whenever the external state changes.
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public updateState(_newState: TanStackTableState): void {
    // State is passed by reference, so updates are automatic
    // This method exists for explicit state updates if needed
  }

  /**
   * Clean up event listeners.
   */
  public destroy(): void {
    this.selectionListeners = []
    this.focusListeners = []
    this.cellValueListeners = []
  }

  // ==========================================================================
  // Selection
  // ==========================================================================

  getSelectedRows(): TData[] {
    const rows = this.table.getRowModel().rows
    return rows.filter((row) => this.state.selectedRowIds.has(row.id)).map((row) => row.original)
  }

  getSelectedRowIds(): string[] {
    return Array.from(this.state.selectedRowIds)
  }

  getSelectedNodes(): RowNode<TData>[] {
    const rows = this.table.getRowModel().rows
    return rows
      .filter((row) => this.state.selectedRowIds.has(row.id))
      .map((row) => ({
        id: row.id,
        data: row.original,
        rowIndex: row.index,
      }))
  }

  selectRows(rowIds: string[]): void {
    this.actions.selectRows(rowIds)
    this.notifySelectionChange()
  }

  selectAll(): void {
    this.actions.selectAll(this.table)
    this.notifySelectionChange()
  }

  deselectAll(): void {
    this.actions.deselectAll()
    this.notifySelectionChange()
  }

  // ==========================================================================
  // Focus
  // ==========================================================================

  getFocusedCell(): FocusedCell | null {
    const cellId = this.state.focusedCell
    if (!cellId) return null

    const rows = this.table.getRowModel().rows
    const rowIndex = rows.findIndex((r) => r.id === cellId.rowId)
    if (rowIndex === -1) return null

    return {
      cellId,
      rowIndex,
      columnId: cellId.columnId,
    }
  }

  setFocusedCell(cellId: CellId): void {
    this.actions.setFocusedCell(cellId)
    this.notifyFocusChange()
  }

  setFocusedCellByIndex(rowIndex: number, columnId: string): void {
    const rows = this.table.getRowModel().rows
    if (rowIndex < 0 || rowIndex >= rows.length) return

    const row = rows[rowIndex]
    const cellId: CellId = { rowId: row.id, columnId }
    this.setFocusedCell(cellId)
  }

  // ==========================================================================
  // ID/Index Conversion
  // ==========================================================================

  getRowIndexById(rowId: string): number | null {
    const rows = this.table.getRowModel().rows
    const index = rows.findIndex((r) => r.id === rowId)
    return index === -1 ? null : index
  }

  getRowIdByIndex(index: number): string | null {
    const rows = this.table.getRowModel().rows
    const row = rows[index]
    return row?.id ?? null
  }

  // ==========================================================================
  // Data Access
  // ==========================================================================

  getVisibleColumns(): ColumnAdapter[] {
    const columns = this.table.getVisibleLeafColumns()
    return columns.map((col) => this.toColumnAdapter(col))
  }

  getAllColumns(): ColumnAdapter[] {
    const columns = this.table.getAllLeafColumns()
    return columns.map((col) => this.toColumnAdapter(col))
  }

  getRowById(rowId: string): RowNode<TData> | null {
    const rows = this.table.getRowModel().rows
    const row = rows.find((r) => r.id === rowId)
    if (!row) return null

    return {
      id: row.id,
      data: row.original,
      rowIndex: row.index,
    }
  }

  getRowByIndex(index: number): RowNode<TData> | null {
    const rows = this.table.getRowModel().rows
    const row = rows[index]
    if (!row) return null

    return {
      id: row.id,
      data: row.original,
      rowIndex: row.index,
    }
  }

  getDisplayedRowCount(): number {
    return this.table.getRowModel().rows.length
  }

  getVisibleRowIds(): string[] {
    return this.table.getRowModel().rows.map((row) => row.id)
  }

  // ==========================================================================
  // Cell Values
  // ==========================================================================

  getCellValue(cellId: CellId): unknown {
    const rows = this.table.getRowModel().rows
    const row = rows.find((r) => r.id === cellId.rowId)
    if (!row) return undefined

    return row.original[cellId.columnId as keyof TData]
  }

  updateCellValue(cellId: CellId, value: unknown): void {
    const oldValue = this.getCellValue(cellId)

    // Call external handler to actually update the data
    if (this.onCellValueChangeFn) {
      this.onCellValueChangeFn(cellId.rowId, cellId.columnId, value)
    }

    // Notify listeners
    this.cellValueListeners.forEach((cb) => cb(cellId, oldValue, value))
  }

  // ==========================================================================
  // Editing
  // ==========================================================================

  isEditing(): boolean {
    return this.state.editingCell !== null
  }

  getEditingCell(): EditingCellInfo | null {
    const cellId = this.state.editingCell
    if (!cellId) return null

    const rowIndex = this.getRowIndexById(cellId.rowId)
    if (rowIndex === null) return null

    return {
      cellId,
      rowIndex,
      columnId: cellId.columnId,
    }
  }

  startEditing(cellId: CellId, initialKey?: string): void {
    this.actions.startEditing(cellId, initialKey)
  }

  startEditingByIndex(rowIndex: number, columnId: string, initialKey?: string): void {
    const rowId = this.getRowIdByIndex(rowIndex)
    if (!rowId) return

    this.startEditing({ rowId, columnId }, initialKey)
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  stopEditing(_cancel: boolean): void {
    // Note: _cancel parameter is for future undo support
    // Currently we just stop editing
    this.actions.stopEditing()
  }

  // ==========================================================================
  // Column Editability Check
  // ==========================================================================

  isCellEditable(cellId: CellId): boolean {
    const column = this.table.getColumn(cellId.columnId)
    if (!column) return false

    const columnDef = column.columnDef as ColumnDef<TData> & {
      meta?: { editable?: boolean | ((row: Row<TData>) => boolean) }
    }

    const editable = columnDef.meta?.editable
    if (editable === undefined) return false
    if (typeof editable === 'boolean') return editable

    // Function-based editability
    const rows = this.table.getRowModel().rows
    const row = rows.find((r) => r.id === cellId.rowId)
    if (!row) return false

    return editable(row)
  }

  // ==========================================================================
  // Scrolling
  // ==========================================================================

  scrollToRow(rowId: string): void {
    // TanStack virtual scroll handles this if virtualization is enabled
    // For basic scrolling, we need the scroll container reference
    if (!this.scrollContainerRef?.current) return

    const rowIndex = this.getRowIndexById(rowId)
    if (rowIndex === null) return

    // Approximate scroll position (assumes fixed row height)
    const rowHeight = 36 // Default compact row height
    this.scrollContainerRef.current.scrollTop = rowIndex * rowHeight
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  scrollToColumn(_columnId: string): void {
    // Column scrolling is more complex and depends on layout
    // For now, we skip this (horizontal scrolling is less common)
  }

  scrollToCell(cellId: CellId): void {
    this.scrollToRow(cellId.rowId)
  }

  // ==========================================================================
  // Event Subscriptions
  // ==========================================================================

  onSelectionChange(callback: SelectionChangeCallback): Unsubscribe {
    this.selectionListeners.push(callback)
    return () => {
      this.selectionListeners = this.selectionListeners.filter((cb) => cb !== callback)
    }
  }

  onFocusChange(callback: FocusChangeCallback): Unsubscribe {
    this.focusListeners.push(callback)
    return () => {
      this.focusListeners = this.focusListeners.filter((cb) => cb !== callback)
    }
  }

  onCellValueChange(callback: CellValueChangeCallback): Unsubscribe {
    this.cellValueListeners.push(callback)
    return () => {
      this.cellValueListeners = this.cellValueListeners.filter((cb) => cb !== callback)
    }
  }

  // ==========================================================================
  // Private Helpers
  // ==========================================================================

  private notifySelectionChange(): void {
    const selectedIds = this.getSelectedRowIds()
    this.selectionListeners.forEach((cb) => cb(selectedIds))
  }

  private notifyFocusChange(): void {
    const focused = this.getFocusedCell()
    this.focusListeners.forEach((cb) => cb(focused))
  }

  private toColumnAdapter(column: Column<TData, unknown>): ColumnAdapter {
    const columnDef = column.columnDef as ColumnDef<TData> & {
      meta?: {
        editable?: boolean | ((row: Row<TData>) => boolean)
        pinned?: 'left' | 'right'
      }
    }

    // Convert function-based editability to adapter-compatible format
    const rawEditable = columnDef.meta?.editable ?? false
    let editable: boolean | ((row: RowNode<unknown>) => boolean)

    if (typeof rawEditable === 'function') {
      // Wrap the function to convert from RowNode to Row lookup
      editable = (rowNode: RowNode<unknown>) => {
        const rows = this.table.getRowModel().rows
        const row = rows.find((r) => r.id === rowNode.id)
        return row ? rawEditable(row) : false
      }
    } else {
      editable = rawEditable
    }

    return {
      id: column.id,
      editable,
      pinned: columnDef.meta?.pinned,
      width: column.getSize(),
      visible: column.getIsVisible(),
    }
  }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a TanStackAdapter from a Table instance and state.
 *
 * @example
 * ```tsx
 * const { state, actions } = useTableState({ getRowId: (data) => data.id })
 *
 * const adapter = createTanStackAdapter({
 *   table,
 *   state,
 *   actions,
 *   getRowId: (data) => data.id,
 *   onCellValueChange: (rowId, columnId, value) => {
 *     // Update your data source
 *   },
 * })
 * ```
 */
export function createTanStackAdapter<TData extends Record<string, unknown>>(
  options: TanStackAdapterOptions<TData>
): TanStackAdapter<TData> {
  return new TanStackAdapter(options)
}
