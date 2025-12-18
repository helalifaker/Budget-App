/**
 * useGridExcelKeyboard Hook
 *
 * Grid-agnostic Excel-like keyboard shortcuts that work with any GridAdapter implementation
 * (AG Grid via AGGridAdapter or TanStack Table via TanStackAdapter).
 *
 * Features:
 * - Ctrl+C: Copy selected cells to clipboard (tab-separated for Excel compatibility)
 * - Ctrl+V: Paste from clipboard into cells
 * - Ctrl+A: Select all rows
 * - Ctrl+D: Fill down (copy first row's values to selection)
 * - Delete/Backspace: Clear selected cells
 * - Selection statistics (sum, average, min, max)
 *
 * Navigation (Tab, Enter, Arrow keys) is handled by the table component itself.
 *
 * @see GridAdapter for the interface
 * @see TanStackAdapter for TanStack Table implementation
 * @see AGGridAdapter for AG Grid implementation
 */

import { useCallback, useEffect, useState, useRef } from 'react'
import type { GridAdapter, CellId } from '@/lib/grid/GridAdapter'

// ============================================================================
// Types
// ============================================================================

export interface GridExcelKeyboardOptions<TData> {
  /** Grid adapter instance (AG Grid or TanStack) */
  adapter: GridAdapter<TData> | null
  /** Enable editing features (default: true) */
  enableEditing?: boolean
  /** Container element ref for keyboard events */
  containerRef: React.RefObject<HTMLElement | null>
  /** Callback when cells are cleared */
  onCellsCleared?: (clearedCells: ClearedCell[]) => void
  /** Callback when cells are filled */
  onCellsFilled?: (filledCells: FilledCell[]) => void
  /** Callback when paste occurs */
  onPaste?: (
    updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
  ) => Promise<void>
  /** Optional: Override copy format (default: tab-separated) */
  formatCopiedValue?: (value: unknown) => string
}

export interface ClearedCell {
  rowId: string
  field: string
  oldValue: unknown
}

export interface FilledCell {
  rowId: string
  field: string
  newValue: unknown
  oldValue: unknown
}

export interface SelectionInfo {
  /** Number of selected cells */
  cellCount: number
  /** Number of selected rows */
  rowCount: number
  /** Sum of numeric values in selection */
  sum: number | null
  /** Average of numeric values in selection */
  average: number | null
  /** Min value in selection */
  min: number | null
  /** Max value in selection */
  max: number | null
  /** Count of numeric cells */
  numericCount: number
}

interface CellData {
  rowId: string
  columnId: string
  value: unknown
  rowData: unknown
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useGridExcelKeyboard<TData extends Record<string, unknown>>({
  adapter,
  enableEditing = true,
  containerRef,
  onCellsCleared,
  onCellsFilled,
  onPaste,
  formatCopiedValue = defaultFormatValue,
}: GridExcelKeyboardOptions<TData>) {
  // Selection statistics state
  const [selectionInfo, setSelectionInfo] = useState<SelectionInfo>({
    cellCount: 0,
    rowCount: 0,
    sum: null,
    average: null,
    min: null,
    max: null,
    numericCount: 0,
  })

  // Track last copied data for fill operations
  const lastCopiedRef = useRef<string[][] | null>(null)

  // ========================================================================
  // Get Selected Cells Data
  // ========================================================================

  /**
   * Get data from selected cells for copy/analysis.
   * Returns both formatted data (for clipboard) and cell metadata.
   */
  const getSelectedCellsData = useCallback((): {
    data: string[][]
    cells: CellData[]
  } => {
    if (!adapter) return { data: [], cells: [] }

    const selectedNodes = adapter.getSelectedNodes()
    const visibleColumns = adapter.getVisibleColumns()

    // No selection - try focused cell
    if (selectedNodes.length === 0) {
      const focusedCell = adapter.getFocusedCell()
      if (focusedCell) {
        const value = adapter.getCellValue(focusedCell.cellId)
        const row = adapter.getRowById(focusedCell.cellId.rowId)
        return {
          data: [[formatCopiedValue(value)]],
          cells: [
            {
              rowId: focusedCell.cellId.rowId,
              columnId: focusedCell.cellId.columnId,
              value,
              rowData: row?.data,
            },
          ],
        }
      }
      return { data: [], cells: [] }
    }

    // Multi-row selection - get all editable columns
    const data: string[][] = []
    const cells: CellData[] = []

    selectedNodes.forEach((node) => {
      const row: string[] = []
      visibleColumns.forEach((col) => {
        if (!col.visible) return

        const cellId: CellId = { rowId: node.id, columnId: col.id }
        const value = adapter.getCellValue(cellId)
        row.push(formatCopiedValue(value))
        cells.push({
          rowId: node.id,
          columnId: col.id,
          value,
          rowData: node.data,
        })
      })
      data.push(row)
    })

    return { data, cells }
  }, [adapter, formatCopiedValue])

  // ========================================================================
  // Selection Statistics
  // ========================================================================

  /**
   * Calculate and update selection statistics.
   */
  const updateSelectionInfo = useCallback(() => {
    const { cells } = getSelectedCellsData()

    if (cells.length === 0) {
      setSelectionInfo({
        cellCount: 0,
        rowCount: 0,
        sum: null,
        average: null,
        min: null,
        max: null,
        numericCount: 0,
      })
      return
    }

    const uniqueRows = new Set(cells.map((c) => c.rowId))
    const numericValues: number[] = []

    cells.forEach((cell) => {
      const num = parseFloat(String(cell.value))
      if (!isNaN(num) && isFinite(num)) {
        numericValues.push(num)
      }
    })

    const sum = numericValues.length > 0 ? numericValues.reduce((a, b) => a + b, 0) : null
    const average = numericValues.length > 0 ? sum! / numericValues.length : null
    const min = numericValues.length > 0 ? Math.min(...numericValues) : null
    const max = numericValues.length > 0 ? Math.max(...numericValues) : null

    setSelectionInfo({
      cellCount: cells.length,
      rowCount: uniqueRows.size,
      sum,
      average,
      min,
      max,
      numericCount: numericValues.length,
    })
  }, [getSelectedCellsData])

  // ========================================================================
  // Clipboard Operations
  // ========================================================================

  /**
   * Copy selected cells to clipboard in Excel format (tab-separated).
   */
  const copyToClipboard = useCallback(async () => {
    const { data } = getSelectedCellsData()
    if (data.length === 0) return

    // Store for fill operations
    lastCopiedRef.current = data

    // Format as tab-separated values (Excel compatible)
    const text = data.map((row) => row.join('\t')).join('\n')

    try {
      await navigator.clipboard.writeText(text)
      // Could add visual feedback here
    } catch (err) {
      console.error('[useGridExcelKeyboard] Failed to copy to clipboard:', err)
    }
  }, [getSelectedCellsData])

  /**
   * Paste from clipboard using Clipboard API.
   */
  const pasteFromClipboard = useCallback(async () => {
    if (!adapter || !enableEditing || !onPaste) {
      return
    }

    // Get the starting cell (focused cell)
    const focusedCell = adapter.getFocusedCell()
    if (!focusedCell) {
      return
    }

    try {
      // Read clipboard using Clipboard API
      const clipboardText = await navigator.clipboard.readText()

      if (!clipboardText) {
        return
      }

      // Get starting position
      const visibleColumns = adapter.getVisibleColumns()
      const startColIndex = visibleColumns.findIndex((c) => c.id === focusedCell.columnId)
      if (startColIndex === -1) return

      // Get visible row IDs for mapping row indices
      const visibleRowIds = adapter.getVisibleRowIds()
      const startRowIndex = visibleRowIds.indexOf(focusedCell.cellId.rowId)
      if (startRowIndex === -1) return

      // Parse clipboard data (Excel format: rows by newline, cols by tab)
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const parsedData = rows.map((r) => r.split('\t'))

      // Prepare updates
      const updates: Array<{
        rowId: string
        field: string
        newValue: string
        originalData: unknown
      }> = []

      for (let i = 0; i < parsedData.length; i++) {
        const currentRowIndex = startRowIndex + i
        if (currentRowIndex >= visibleRowIds.length) break

        const rowId = visibleRowIds[currentRowIndex]
        const row = adapter.getRowById(rowId)
        if (!row) continue

        for (let j = 0; j < parsedData[i].length; j++) {
          const currentColIndex = startColIndex + j
          if (currentColIndex >= visibleColumns.length) break

          const column = visibleColumns[currentColIndex]
          const cellId: CellId = { rowId, columnId: column.id }

          // Skip if column is not editable
          if (!adapter.isCellEditable(cellId)) continue

          const newValue = parsedData[i][j].trim()

          updates.push({
            rowId,
            field: column.id,
            newValue,
            originalData: row.data,
          })
        }
      }

      if (updates.length > 0) {
        await onPaste(updates)
      }
    } catch (err) {
      console.error('[useGridExcelKeyboard] Failed to paste from clipboard:', err)
    }
  }, [adapter, enableEditing, onPaste])

  // ========================================================================
  // Cell Operations
  // ========================================================================

  /**
   * Clear selected cells (Delete/Backspace).
   */
  const clearSelectedCells = useCallback(() => {
    if (!adapter || !enableEditing) return

    const selectedNodes = adapter.getSelectedNodes()
    const focusedCell = adapter.getFocusedCell()
    const clearedCells: ClearedCell[] = []

    if (selectedNodes.length > 0) {
      // Clear all editable cells in selected rows
      const visibleColumns = adapter.getVisibleColumns()

      selectedNodes.forEach((node) => {
        visibleColumns.forEach((col) => {
          const cellId: CellId = { rowId: node.id, columnId: col.id }

          // Only clear editable cells
          if (!adapter.isCellEditable(cellId)) return

          const oldValue = adapter.getCellValue(cellId)
          clearedCells.push({
            rowId: node.id,
            field: col.id,
            oldValue,
          })
          adapter.updateCellValue(cellId, null)
        })
      })
    } else if (focusedCell) {
      // Clear single focused cell
      if (adapter.isCellEditable(focusedCell.cellId)) {
        const oldValue = adapter.getCellValue(focusedCell.cellId)
        clearedCells.push({
          rowId: focusedCell.cellId.rowId,
          field: focusedCell.cellId.columnId,
          oldValue,
        })
        adapter.updateCellValue(focusedCell.cellId, null)
      }
    }

    if (clearedCells.length > 0 && onCellsCleared) {
      onCellsCleared(clearedCells)
    }
  }, [adapter, enableEditing, onCellsCleared])

  /**
   * Fill down (Ctrl+D) - Copy first row's values to selected rows.
   */
  const fillDown = useCallback(() => {
    if (!adapter || !enableEditing) return

    const selectedNodes = adapter.getSelectedNodes()
    if (selectedNodes.length < 2) return

    const firstNode = selectedNodes[0]
    const visibleColumns = adapter.getVisibleColumns()
    const filledCells: FilledCell[] = []

    // Copy first row's values to all other selected rows
    selectedNodes.slice(1).forEach((node) => {
      visibleColumns.forEach((col) => {
        const sourceCellId: CellId = { rowId: firstNode.id, columnId: col.id }
        const targetCellId: CellId = { rowId: node.id, columnId: col.id }

        // Only fill editable cells
        if (!adapter.isCellEditable(targetCellId)) return

        const newValue = adapter.getCellValue(sourceCellId)
        const oldValue = adapter.getCellValue(targetCellId)

        if (newValue !== oldValue) {
          filledCells.push({
            rowId: node.id,
            field: col.id,
            newValue,
            oldValue,
          })
          adapter.updateCellValue(targetCellId, newValue)
        }
      })
    })

    if (filledCells.length > 0 && onCellsFilled) {
      onCellsFilled(filledCells)
    }
  }, [adapter, enableEditing, onCellsFilled])

  /**
   * Select all rows (Ctrl+A).
   */
  const selectAll = useCallback(() => {
    if (!adapter) return
    adapter.selectAll()
  }, [adapter])

  /**
   * Deselect all rows (Escape).
   */
  const deselectAll = useCallback(() => {
    if (!adapter) return
    adapter.deselectAll()
  }, [adapter])

  // ========================================================================
  // Keyboard Event Handler
  // ========================================================================

  /**
   * Main keyboard event handler.
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!adapter) return

      const { key, ctrlKey, metaKey } = event
      const isModKey = ctrlKey || metaKey

      // Don't intercept if we're editing a cell
      if (adapter.isEditing()) {
        // Only handle Escape during editing (to cancel)
        if (key === 'Escape') {
          adapter.stopEditing(true)
          event.preventDefault()
          return
        }
        // Let the editor handle all other keys
        return
      }

      // Ctrl/Cmd + C: Copy
      if (isModKey && key === 'c') {
        copyToClipboard()
        event.preventDefault()
        return
      }

      // Ctrl/Cmd + V: Paste
      if (isModKey && key === 'v') {
        pasteFromClipboard()
        event.preventDefault()
        return
      }

      // Ctrl/Cmd + A: Select all
      if (isModKey && key === 'a') {
        selectAll()
        event.preventDefault()
        return
      }

      // Ctrl/Cmd + D: Fill down
      if (isModKey && key === 'd') {
        fillDown()
        event.preventDefault()
        return
      }

      // Delete / Backspace: Clear cells (handled by EditableTable for single cells)
      // This handles clearing multiple selected rows
      if (key === 'Delete' || key === 'Backspace') {
        const selectedNodes = adapter.getSelectedNodes()
        if (selectedNodes.length > 0) {
          clearSelectedCells()
          event.preventDefault()
          return
        }
        // Let single cell clearing be handled by the table
      }

      // Escape: Deselect
      if (key === 'Escape') {
        deselectAll()
        event.preventDefault()
        return
      }
    },
    [
      adapter,
      copyToClipboard,
      pasteFromClipboard,
      selectAll,
      fillDown,
      clearSelectedCells,
      deselectAll,
    ]
  )

  // ========================================================================
  // Event Listeners
  // ========================================================================

  // Attach keyboard listener
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('keydown', handleKeyDown)
    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }, [containerRef, handleKeyDown])

  // Update selection info when selection changes
  useEffect(() => {
    if (!adapter) return

    const unsubscribeSelection = adapter.onSelectionChange(() => {
      updateSelectionInfo()
    })

    const unsubscribeFocus = adapter.onFocusChange(() => {
      updateSelectionInfo()
    })

    return () => {
      unsubscribeSelection()
      unsubscribeFocus()
    }
  }, [adapter, updateSelectionInfo])

  // ========================================================================
  // Return Value
  // ========================================================================

  return {
    /** Selection statistics for status bar */
    selectionInfo,
    /** Update selection statistics manually */
    updateSelectionInfo,
    /** Copy selected cells to clipboard */
    copyToClipboard,
    /** Paste from clipboard */
    pasteFromClipboard,
    /** Clear selected cells */
    clearSelectedCells,
    /** Fill down selected rows */
    fillDown,
    /** Select all rows */
    selectAll,
    /** Deselect all rows */
    deselectAll,
  }
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Default value formatter for clipboard copy.
 */
function defaultFormatValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return String(value)
}
