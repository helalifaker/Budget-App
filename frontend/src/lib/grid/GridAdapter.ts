/**
 * GridAdapter Interface
 *
 * Abstraction layer that decouples Excel-like keyboard/clipboard hooks
 * from the underlying grid implementation (AG Grid or TanStack Table).
 *
 * KEY DESIGN DECISIONS:
 * - Focus/selection keyed by `rowId + columnId` (NOT rowIndex)
 *   This ensures stability across sorting, filtering, and virtualization.
 * - Row IDs come from the grid's getRowId callback (stable identifiers)
 * - Column IDs are the field names from column definitions
 *
 * @see TANSTACK_MIGRATION_PLAN.md for migration context
 */

// ============================================================================
// Core Types
// ============================================================================

/**
 * Cell identifier using stable IDs instead of indices.
 * This is critical for correct behavior with sorting/filtering.
 */
export interface CellId {
  /** Stable row ID from getRowId callback (NOT row index) */
  rowId: string
  /** Column field name (stable identifier) */
  columnId: string
}

/**
 * Row node with stable ID and current display index.
 * The rowIndex is for display purposes only and may change on sort/filter.
 */
export interface RowNode<TData> {
  /** Stable row ID (from getRowId callback) */
  id: string
  /** Row data object */
  data: TData
  /** Current display index (may change on sort/filter/virtualization) */
  rowIndex: number
}

/**
 * Column adapter interface providing grid-agnostic column access.
 */
export interface ColumnAdapter {
  /** Column field name (stable identifier) */
  id: string
  /** Whether the column is editable (static or function) */
  editable: boolean | ((row: RowNode<unknown>) => boolean)
  /** Column pinning position */
  pinned?: 'left' | 'right'
  /** Column width in pixels */
  width?: number
  /** Whether the column is currently visible */
  visible: boolean
  /** Value getter for computed columns */
  valueGetter?: (row: RowNode<unknown>) => unknown
  /** Value formatter for display */
  valueFormatter?: (value: unknown) => string
}

/**
 * Focused cell information including both stable ID and display index.
 */
export interface FocusedCell {
  /** Stable cell identifier */
  cellId: CellId
  /** Current display row index (for scrolling purposes) */
  rowIndex: number
  /** Column field name */
  columnId: string
}

/**
 * Information about cells currently being edited.
 */
export interface EditingCellInfo {
  cellId: CellId
  rowIndex: number
  columnId: string
}

// ============================================================================
// Event Types
// ============================================================================

export type SelectionChangeCallback = (selectedRowIds: string[]) => void
export type FocusChangeCallback = (focusedCell: FocusedCell | null) => void
export type CellValueChangeCallback = (cellId: CellId, oldValue: unknown, newValue: unknown) => void

/** Unsubscribe function returned by event subscriptions */
export type Unsubscribe = () => void

// ============================================================================
// GridAdapter Interface
// ============================================================================

/**
 * Grid adapter interface that abstracts the underlying grid implementation.
 *
 * Both AG Grid and TanStack Table will implement this interface,
 * allowing the Excel-like keyboard/clipboard hooks to work with either.
 *
 * @template TData - The type of data in each row
 */
export interface GridAdapter<TData> {
  // ==========================================================================
  // Selection (keyed by rowId, NOT index)
  // ==========================================================================

  /**
   * Get data objects of all selected rows.
   */
  getSelectedRows(): TData[]

  /**
   * Get stable IDs of all selected rows.
   */
  getSelectedRowIds(): string[]

  /**
   * Get row nodes of all selected rows (includes ID, data, and current index).
   */
  getSelectedNodes(): RowNode<TData>[]

  /**
   * Select rows by their stable IDs.
   * @param rowIds - Array of row IDs to select
   */
  selectRows(rowIds: string[]): void

  /**
   * Select all visible rows.
   */
  selectAll(): void

  /**
   * Deselect all rows.
   */
  deselectAll(): void

  // ==========================================================================
  // Focus (keyed by rowId + columnId, NOT index)
  // ==========================================================================

  /**
   * Get the currently focused cell.
   * Returns null if no cell is focused.
   */
  getFocusedCell(): FocusedCell | null

  /**
   * Set focus to a specific cell by its stable ID.
   * @param cellId - The cell to focus
   */
  setFocusedCell(cellId: CellId): void

  /**
   * Set focus by row index and column ID (convenience method).
   * Use when you have the display index but need to set focus.
   * @param rowIndex - Current display row index
   * @param columnId - Column field name
   */
  setFocusedCellByIndex(rowIndex: number, columnId: string): void

  // ==========================================================================
  // ID/Index Conversion (for display purposes)
  // ==========================================================================

  /**
   * Get the current display index for a row ID.
   * Returns null if the row is not currently visible (filtered out or virtualized).
   */
  getRowIndexById(rowId: string): number | null

  /**
   * Get the stable row ID at a display index.
   * Returns null if the index is out of bounds.
   */
  getRowIdByIndex(index: number): string | null

  // ==========================================================================
  // Data Access
  // ==========================================================================

  /**
   * Get all visible columns in their current order.
   */
  getVisibleColumns(): ColumnAdapter[]

  /**
   * Get all columns (including hidden) in their current order.
   */
  getAllColumns(): ColumnAdapter[]

  /**
   * Get a row node by its stable ID.
   * Returns null if the row doesn't exist.
   */
  getRowById(rowId: string): RowNode<TData> | null

  /**
   * Get a row node by its current display index.
   * Returns null if the index is out of bounds.
   */
  getRowByIndex(index: number): RowNode<TData> | null

  /**
   * Get the total count of displayed rows (after filtering).
   */
  getDisplayedRowCount(): number

  /**
   * Get all visible row IDs in their current display order.
   * Useful for keyboard navigation.
   */
  getVisibleRowIds(): string[]

  // ==========================================================================
  // Cell Values
  // ==========================================================================

  /**
   * Get the value of a specific cell.
   * @param cellId - The cell to read
   */
  getCellValue(cellId: CellId): unknown

  /**
   * Update the value of a specific cell.
   * This should trigger the grid's change detection and callbacks.
   * @param cellId - The cell to update
   * @param value - The new value
   */
  updateCellValue(cellId: CellId, value: unknown): void

  // ==========================================================================
  // Editing
  // ==========================================================================

  /**
   * Check if any cell is currently being edited.
   */
  isEditing(): boolean

  /**
   * Get information about the cell currently being edited.
   * Returns null if not editing.
   */
  getEditingCell(): EditingCellInfo | null

  /**
   * Start editing a cell.
   * @param cellId - The cell to edit
   * @param initialKey - Optional key that triggered editing (for type-to-edit)
   */
  startEditing(cellId: CellId, initialKey?: string): void

  /**
   * Start editing by row index and column ID (convenience method).
   * @param rowIndex - Current display row index
   * @param columnId - Column field name
   * @param initialKey - Optional key that triggered editing
   */
  startEditingByIndex(rowIndex: number, columnId: string, initialKey?: string): void

  /**
   * Stop editing the current cell.
   * @param cancel - If true, discard changes. If false, commit changes.
   */
  stopEditing(cancel: boolean): void

  // ==========================================================================
  // Column Editability Check
  // ==========================================================================

  /**
   * Check if a specific cell is editable.
   * Handles both static `editable: true` and function-based editability.
   * @param cellId - The cell to check
   */
  isCellEditable(cellId: CellId): boolean

  // ==========================================================================
  // Scrolling
  // ==========================================================================

  /**
   * Scroll to ensure a row is visible.
   * @param rowId - The row to scroll to
   */
  scrollToRow(rowId: string): void

  /**
   * Scroll to ensure a column is visible.
   * @param columnId - The column to scroll to
   */
  scrollToColumn(columnId: string): void

  /**
   * Scroll to ensure a cell is visible.
   * @param cellId - The cell to scroll to
   */
  scrollToCell(cellId: CellId): void

  // ==========================================================================
  // Event Subscriptions
  // ==========================================================================

  /**
   * Subscribe to selection changes.
   * @param callback - Called when selection changes
   * @returns Unsubscribe function
   */
  onSelectionChange(callback: SelectionChangeCallback): Unsubscribe

  /**
   * Subscribe to focus changes.
   * @param callback - Called when focused cell changes
   * @returns Unsubscribe function
   */
  onFocusChange(callback: FocusChangeCallback): Unsubscribe

  /**
   * Subscribe to cell value changes.
   * @param callback - Called when a cell value changes
   * @returns Unsubscribe function
   */
  onCellValueChange(callback: CellValueChangeCallback): Unsubscribe
}

// ============================================================================
// Helper Types for Implementation
// ============================================================================

/**
 * Options for creating a grid adapter.
 */
export interface GridAdapterOptions<TData> {
  /** Function to extract a stable ID from row data */
  getRowId: (data: TData) => string
}

/**
 * Navigation direction for keyboard movement.
 */
export type NavigationDirection = 'up' | 'down' | 'left' | 'right' | 'next' | 'prev'
