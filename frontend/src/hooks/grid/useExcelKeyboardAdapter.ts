/**
 * useExcelKeyboardAdapter Hook
 *
 * Refactored version of useExcelKeyboard that uses the GridAdapter interface
 * instead of AG Grid's GridApi directly. This allows the same Excel-like
 * keyboard functionality to work with both AG Grid and TanStack Table.
 *
 * Keyboard Shortcuts:
 * - Ctrl+C: Copy selected cells to clipboard
 * - Ctrl+V: Paste from clipboard
 * - Ctrl+A: Select all rows
 * - Delete/Backspace: Clear selected cells
 * - Tab: Move to next cell
 * - Shift+Tab: Move to previous cell
 * - Enter: Move to cell below (or finish edit)
 * - Shift+Enter: Move to cell above
 * - F2: Enter edit mode on focused cell
 * - Escape: Cancel current edit
 * - Ctrl+D: Fill down (copy first cell to selection)
 * - Type-to-edit: Start editing on keypress
 *
 * KEY CHANGES FROM ORIGINAL:
 * - Uses GridAdapter instead of GridApi
 * - Uses CellId (rowId + columnId) instead of rowIndex for stability
 * - Cleaner separation between grid implementation and features
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import type { GridAdapter, CellId, NavigationDirection } from '@/lib/grid'

// ============================================================================
// Types
// ============================================================================

export interface ExcelKeyboardAdapterOptions<TData> {
  /** Grid adapter instance */
  adapter: GridAdapter<TData> | null
  /** Enable editing features (default: true) */
  enableEditing?: boolean
  /** Callback when cells are cleared */
  onCellsCleared?: (clearedCells: ClearedCell[]) => void
  /** Callback when cells are filled */
  onCellsFilled?: (filledCells: FilledCell[]) => void
  /** Container element ref for keyboard events */
  containerRef: React.RefObject<HTMLElement | null>
  /** Callback when paste occurs (from Ctrl+V) */
  onPaste?: (
    updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
  ) => Promise<void>
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

// ============================================================================
// Hook Implementation
// ============================================================================

export function useExcelKeyboardAdapter<TData extends Record<string, unknown>>({
  adapter,
  enableEditing = true,
  onCellsCleared,
  onCellsFilled,
  containerRef,
  onPaste,
}: ExcelKeyboardAdapterOptions<TData>) {
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

  /**
   * Get selected cells data for copy/analysis
   * Returns data in a grid format and detailed cell information
   */
  const getSelectedCellsData = useCallback((): {
    data: string[][]
    cells: Array<{
      rowId: string
      columnId: string
      value: unknown
      rowData: TData
    }>
  } => {
    if (!adapter) return { data: [], cells: [] }

    const selectedNodes = adapter.getSelectedNodes()
    const visibleColumns = adapter.getVisibleColumns()

    if (selectedNodes.length === 0) {
      // Single cell focused - use focused cell
      const focusedCell = adapter.getFocusedCell()
      if (focusedCell) {
        const row = adapter.getRowById(focusedCell.cellId.rowId)
        if (row) {
          const value = adapter.getCellValue(focusedCell.cellId)
          return {
            data: [[String(value ?? '')]],
            cells: [
              {
                rowId: focusedCell.cellId.rowId,
                columnId: focusedCell.cellId.columnId,
                value,
                rowData: row.data,
              },
            ],
          }
        }
      }
      return { data: [], cells: [] }
    }

    // Multi-row selection
    const data: string[][] = []
    const cells: Array<{
      rowId: string
      columnId: string
      value: unknown
      rowData: TData
    }> = []

    selectedNodes.forEach((node) => {
      const row: string[] = []
      visibleColumns.forEach((col) => {
        const cellId: CellId = { rowId: node.id, columnId: col.id }
        const value = adapter.getCellValue(cellId)
        row.push(String(value ?? ''))
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
  }, [adapter])

  /**
   * Update selection statistics
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

  /**
   * Copy selected cells to clipboard in Excel format (tab-separated)
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
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }, [getSelectedCellsData])

  /**
   * Paste from clipboard using Clipboard API (Ctrl+V)
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

      const startRowIndex = focusedCell.rowIndex
      const visibleColumns = adapter.getVisibleColumns()
      const startColIndex = visibleColumns.findIndex((col) => col.id === focusedCell.columnId)
      if (startColIndex === -1) return

      // Parse clipboard data (Excel format: rows by newline, cols by tab)
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const data = rows.map((r) => r.split('\t'))

      // Prepare updates using stable row IDs
      const updates: Array<{
        rowId: string
        field: string
        newValue: string
        originalData: unknown
      }> = []

      for (let i = 0; i < data.length; i++) {
        const currentRowIndex = startRowIndex + i
        const rowId = adapter.getRowIdByIndex(currentRowIndex)
        if (!rowId) break

        const row = adapter.getRowById(rowId)
        if (!row) continue

        for (let j = 0; j < data[i].length; j++) {
          const currentColIndex = startColIndex + j
          if (currentColIndex >= visibleColumns.length) break

          const column = visibleColumns[currentColIndex]
          const cellId: CellId = { rowId, columnId: column.id }

          // Skip if column is not editable
          if (!adapter.isCellEditable(cellId)) continue

          const newValue = data[i][j].trim()

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
      console.error('[useExcelKeyboardAdapter] Failed to paste from clipboard:', err)
    }
  }, [adapter, enableEditing, onPaste])

  /**
   * Clear selected cells (Delete/Backspace)
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

          if (adapter.isCellEditable(cellId)) {
            const oldValue = adapter.getCellValue(cellId)
            clearedCells.push({
              rowId: node.id,
              field: col.id,
              oldValue,
            })
            adapter.updateCellValue(cellId, null)
          }
        })
      })
    } else if (focusedCell) {
      // Clear single focused cell
      const cellId = focusedCell.cellId

      if (adapter.isCellEditable(cellId)) {
        const oldValue = adapter.getCellValue(cellId)
        clearedCells.push({
          rowId: cellId.rowId,
          field: cellId.columnId,
          oldValue,
        })
        adapter.updateCellValue(cellId, null)
      }
    }

    if (clearedCells.length > 0 && onCellsCleared) {
      onCellsCleared(clearedCells)
    }
  }, [adapter, enableEditing, onCellsCleared])

  /**
   * Fill down (Ctrl+D) - Copy first row's values to selected rows
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

        if (adapter.isCellEditable(targetCellId)) {
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
        }
      })
    })

    if (filledCells.length > 0 && onCellsFilled) {
      onCellsFilled(filledCells)
    }
  }, [adapter, enableEditing, onCellsFilled])

  /**
   * Select all rows (Ctrl+A)
   */
  const selectAll = useCallback(() => {
    if (!adapter) return
    adapter.selectAll()
  }, [adapter])

  /**
   * Navigate to next/previous cell
   * Uses rowId + columnId for stable navigation
   */
  const navigateCell = useCallback(
    (direction: NavigationDirection) => {
      if (!adapter) return

      const focusedCell = adapter.getFocusedCell()
      if (!focusedCell) return

      const visibleColumns = adapter.getVisibleColumns()
      const visibleRowIds = adapter.getVisibleRowIds()

      const currentColIndex = visibleColumns.findIndex((col) => col.id === focusedCell.columnId)
      const currentRowIdIndex = visibleRowIds.indexOf(focusedCell.cellId.rowId)

      if (currentColIndex === -1 || currentRowIdIndex === -1) return

      let newColIndex = currentColIndex
      let newRowIdIndex = currentRowIdIndex

      switch (direction) {
        case 'next': // Tab
        case 'right':
          newColIndex++
          if (newColIndex >= visibleColumns.length) {
            newColIndex = 0
            newRowIdIndex++
          }
          break
        case 'prev': // Shift+Tab
        case 'left':
          newColIndex--
          if (newColIndex < 0) {
            newColIndex = visibleColumns.length - 1
            newRowIdIndex--
          }
          break
        case 'down': // Enter
          newRowIdIndex++
          break
        case 'up': // Shift+Enter
          newRowIdIndex--
          break
      }

      // Bounds checking
      if (newRowIdIndex < 0) newRowIdIndex = 0
      if (newRowIdIndex >= visibleRowIds.length) newRowIdIndex = visibleRowIds.length - 1
      if (newColIndex < 0) newColIndex = 0
      if (newColIndex >= visibleColumns.length) newColIndex = visibleColumns.length - 1

      const newRowId = visibleRowIds[newRowIdIndex]
      const newColumnId = visibleColumns[newColIndex].id

      if (newRowId && newColumnId) {
        const newCellId: CellId = { rowId: newRowId, columnId: newColumnId }
        adapter.setFocusedCell(newCellId)
        adapter.scrollToCell(newCellId)
      }
    },
    [adapter]
  )

  /**
   * Enter edit mode on focused cell (F2)
   */
  const startEditing = useCallback(() => {
    if (!adapter || !enableEditing) return

    const focusedCell = adapter.getFocusedCell()
    if (!focusedCell) return

    if (adapter.isCellEditable(focusedCell.cellId)) {
      adapter.startEditing(focusedCell.cellId)
    }
  }, [adapter, enableEditing])

  /**
   * Stop editing (Escape)
   */
  const stopEditing = useCallback(() => {
    if (!adapter) return
    adapter.stopEditing(true) // true = cancel, false = accept
  }, [adapter])

  /**
   * Main keyboard event handler
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!adapter) return

      const { key, ctrlKey, metaKey, shiftKey } = event
      const isModKey = ctrlKey || metaKey

      // Don't intercept if we're editing a cell
      if (adapter.isEditing()) {
        // Only handle Escape and Enter during editing
        if (key === 'Escape') {
          stopEditing()
          event.preventDefault()
          return
        }
        if (key === 'Enter' && !shiftKey) {
          adapter.stopEditing(false) // Accept edit
          navigateCell('down')
          event.preventDefault()
          return
        }
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

      // Delete / Backspace: Clear cells
      if (key === 'Delete' || key === 'Backspace') {
        clearSelectedCells()
        event.preventDefault()
        return
      }

      // Tab: Next cell
      if (key === 'Tab') {
        navigateCell(shiftKey ? 'prev' : 'next')
        event.preventDefault()
        return
      }

      // Enter: Next row (when not editing)
      if (key === 'Enter') {
        navigateCell(shiftKey ? 'up' : 'down')
        event.preventDefault()
        return
      }

      // F2: Start editing
      if (key === 'F2') {
        startEditing()
        event.preventDefault()
        return
      }

      // Escape: Stop editing / deselect
      if (key === 'Escape') {
        stopEditing()
        adapter.deselectAll()
        event.preventDefault()
        return
      }

      // Start typing to edit (like Excel)
      if (enableEditing && key.length === 1 && !isModKey && /^[a-zA-Z0-9]$/.test(key)) {
        const focusedCell = adapter.getFocusedCell()
        if (focusedCell && adapter.isCellEditable(focusedCell.cellId)) {
          adapter.startEditing(focusedCell.cellId, key)
          event.preventDefault()
        }
      }
    },
    [
      adapter,
      copyToClipboard,
      pasteFromClipboard,
      selectAll,
      fillDown,
      clearSelectedCells,
      navigateCell,
      startEditing,
      stopEditing,
      enableEditing,
    ]
  )

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

    const unsubSelection = adapter.onSelectionChange(() => {
      updateSelectionInfo()
    })

    const unsubFocus = adapter.onFocusChange(() => {
      updateSelectionInfo()
    })

    return () => {
      unsubSelection()
      unsubFocus()
    }
  }, [adapter, updateSelectionInfo])

  return {
    /** Selection statistics for status bar */
    selectionInfo,
    /** Manually copy to clipboard */
    copyToClipboard,
    /** Clear selected cells */
    clearSelectedCells,
    /** Fill down selected rows */
    fillDown,
    /** Select all rows */
    selectAll,
    /** Navigate to adjacent cell */
    navigateCell,
    /** Start editing focused cell */
    startEditing,
    /** Stop editing */
    stopEditing,
  }
}
