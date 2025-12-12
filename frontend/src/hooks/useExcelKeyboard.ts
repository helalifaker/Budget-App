/**
 * useExcelKeyboard Hook
 *
 * Provides Excel-like keyboard shortcuts for AG Grid:
 * - Ctrl+C: Copy selected cells to clipboard
 * - Ctrl+V: Paste from clipboard (handled separately)
 * - Ctrl+Z: Undo last edit
 * - Ctrl+Y / Ctrl+Shift+Z: Redo
 * - Ctrl+A: Select all rows
 * - Delete/Backspace: Clear selected cells
 * - Tab: Move to next cell
 * - Shift+Tab: Move to previous cell
 * - Enter: Move to cell below (or finish edit)
 * - Shift+Enter: Move to cell above
 * - F2: Enter edit mode on focused cell
 * - Escape: Cancel current edit
 * - Ctrl+D: Fill down (copy first cell to selection)
 * - Ctrl+R: Fill right (copy leftmost cell to selection)
 *
 * Also provides copy functionality that formats data in Excel-compatible
 * tab-separated format for seamless copy/paste with Excel.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import type { GridApi } from 'ag-grid-community'

export interface ExcelKeyboardOptions {
  /** AG Grid API reference */
  gridApi: GridApi | null
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

export function useExcelKeyboard({
  gridApi,
  enableEditing = true,
  onCellsCleared,
  onCellsFilled,
  containerRef,
  onPaste,
}: ExcelKeyboardOptions) {
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
   */
  const getSelectedCellsData = useCallback((): {
    data: string[][]
    cells: Array<{
      rowIndex: number
      colIndex: number
      value: unknown
      field: string
      rowData: unknown
    }>
  } => {
    if (!gridApi) return { data: [], cells: [] }

    const selectedRows = gridApi.getSelectedRows()
    const allColumns = gridApi.getColumns()?.filter((col) => col.isVisible()) || []

    if (selectedRows.length === 0) {
      // Single cell focused
      const focusedCell = gridApi.getFocusedCell()
      if (focusedCell) {
        const rowNode = gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex)
        if (rowNode?.data) {
          const field = focusedCell.column.getColDef().field
          const value = field ? rowNode.data[field] : ''
          return {
            data: [[String(value ?? '')]],
            cells: [
              {
                rowIndex: focusedCell.rowIndex,
                colIndex: allColumns.indexOf(focusedCell.column),
                value,
                field: field || '',
                rowData: rowNode.data,
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
      rowIndex: number
      colIndex: number
      value: unknown
      field: string
      rowData: unknown
    }> = []

    selectedRows.forEach((rowData, rowIdx) => {
      const row: string[] = []
      allColumns.forEach((col, colIdx) => {
        const field = col.getColDef().field
        const value = field ? rowData[field] : ''
        row.push(String(value ?? ''))
        cells.push({
          rowIndex: rowIdx,
          colIndex: colIdx,
          value,
          field: field || '',
          rowData,
        })
      })
      data.push(row)
    })

    return { data, cells }
  }, [gridApi])

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

    const uniqueRows = new Set(cells.map((c) => c.rowIndex))
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
      // Flash indication could be added here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }, [getSelectedCellsData])

  /**
   * Paste from clipboard using Clipboard API (Ctrl+V)
   * This uses the async Clipboard API to read text directly,
   * bypassing React's onPaste event which may not fire correctly.
   */
  const pasteFromClipboard = useCallback(async () => {
    if (!gridApi || !enableEditing || !onPaste) {
      console.log('[useExcelKeyboard] Paste: missing gridApi, enableEditing, or onPaste callback')
      return
    }

    // Get the starting cell (focused cell)
    const focusedCell = gridApi.getFocusedCell()
    if (!focusedCell) {
      console.log('[useExcelKeyboard] Paste: no focused cell')
      return
    }

    try {
      // Read clipboard using Clipboard API
      const clipboardText = await navigator.clipboard.readText()
      console.log('[useExcelKeyboard] Paste: clipboard text:', clipboardText?.substring(0, 100))

      if (!clipboardText) {
        console.log('[useExcelKeyboard] Paste: no clipboard text')
        return
      }

      const { rowIndex, column: resultColumn } = focusedCell
      const startRowIndex = rowIndex

      // Get all visible columns
      const allColumns = gridApi.getColumns()
      if (!allColumns) return

      const startColIndex = allColumns.indexOf(resultColumn)
      if (startColIndex === -1) return

      // Parse clipboard data (Excel format: rows by newline, cols by tab)
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const data = rows.map((r) => r.split('\t'))

      // Prepare updates
      const updates: Array<{
        rowId: string
        field: string
        newValue: string
        originalData: unknown
      }> = []

      for (let i = 0; i < data.length; i++) {
        const currentRowIndex = startRowIndex + i
        const rowNode = gridApi.getDisplayedRowAtIndex(currentRowIndex)
        if (!rowNode) break

        const rowData = rowNode.data
        const rowId = rowNode.id
        if (!rowData || !rowId) continue

        for (let j = 0; j < data[i].length; j++) {
          const currentColIndex = startColIndex + j
          if (currentColIndex >= allColumns.length) break

          const column = allColumns[currentColIndex]
          const colDef = column.getColDef()
          const field = colDef.field

          // Skip if column is not editable or has no field
          if (!colDef.editable || !field) continue

          const newValue = data[i][j].trim()

          updates.push({
            rowId,
            field,
            newValue,
            originalData: rowData,
          })
        }
      }

      console.log('[useExcelKeyboard] Paste: updates to apply:', updates.length)

      if (updates.length > 0) {
        await onPaste(updates)
        console.log('[useExcelKeyboard] Paste: complete')
      }
    } catch (err) {
      console.error('[useExcelKeyboard] Failed to paste from clipboard:', err)
    }
  }, [gridApi, enableEditing, onPaste])

  /**
   * Clear selected cells (Delete/Backspace)
   */
  const clearSelectedCells = useCallback(() => {
    if (!gridApi || !enableEditing) return

    const selectedNodes = gridApi.getSelectedNodes()
    const focusedCell = gridApi.getFocusedCell()
    const clearedCells: ClearedCell[] = []

    if (selectedNodes.length > 0) {
      // Clear all editable cells in selected rows
      const allColumns = gridApi.getColumns() || []

      selectedNodes.forEach((node) => {
        if (!node.data || !node.id) return

        allColumns.forEach((col) => {
          const colDef = col.getColDef()
          if (colDef.editable && colDef.field) {
            const oldValue = node.data[colDef.field]
            clearedCells.push({
              rowId: node.id!, // Use node.id from getRowId callback
              field: colDef.field,
              oldValue,
            })
            node.setDataValue(colDef.field, null)
          }
        })
      })
    } else if (focusedCell) {
      // Clear single focused cell
      const rowNode = gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex)
      const colDef = focusedCell.column.getColDef()

      if (rowNode?.data && rowNode.id && colDef.editable && colDef.field) {
        const oldValue = rowNode.data[colDef.field]
        clearedCells.push({
          rowId: rowNode.id, // Use node.id from getRowId callback
          field: colDef.field,
          oldValue,
        })
        rowNode.setDataValue(colDef.field, null)
      }
    }

    if (clearedCells.length > 0 && onCellsCleared) {
      onCellsCleared(clearedCells)
    }
  }, [gridApi, enableEditing, onCellsCleared])

  /**
   * Fill down (Ctrl+D) - Copy first row's values to selected rows
   */
  const fillDown = useCallback(() => {
    if (!gridApi || !enableEditing) return

    const selectedNodes = gridApi.getSelectedNodes()
    if (selectedNodes.length < 2) return

    const firstNode = selectedNodes[0]
    if (!firstNode?.data) return

    const allColumns = gridApi.getColumns() || []
    const filledCells: FilledCell[] = []

    // Copy first row's values to all other selected rows
    selectedNodes.slice(1).forEach((node) => {
      if (!node.data || !node.id) return

      allColumns.forEach((col) => {
        const colDef = col.getColDef()
        if (colDef.editable && colDef.field) {
          const newValue = firstNode.data[colDef.field]
          const oldValue = node.data[colDef.field]

          if (newValue !== oldValue) {
            filledCells.push({
              rowId: node.id!, // Use node.id from getRowId callback
              field: colDef.field,
              newValue,
              oldValue,
            })
            node.setDataValue(colDef.field, newValue)
          }
        }
      })
    })

    if (filledCells.length > 0 && onCellsFilled) {
      onCellsFilled(filledCells)
    }
  }, [gridApi, enableEditing, onCellsFilled])

  /**
   * Select all rows (Ctrl+A)
   */
  const selectAll = useCallback(() => {
    if (!gridApi) return
    gridApi.selectAll()
  }, [gridApi])

  /**
   * Navigate to next/previous cell
   */
  const navigateCell = useCallback(
    (direction: 'next' | 'prev' | 'up' | 'down') => {
      if (!gridApi) return

      const focusedCell = gridApi.getFocusedCell()
      if (!focusedCell) return

      const allColumns = gridApi.getColumns()?.filter((col) => col.isVisible()) || []
      const currentColIndex = allColumns.indexOf(focusedCell.column)
      const currentRowIndex = focusedCell.rowIndex
      const rowCount = gridApi.getDisplayedRowCount()

      let newColIndex = currentColIndex
      let newRowIndex = currentRowIndex

      switch (direction) {
        case 'next': // Tab
          newColIndex++
          if (newColIndex >= allColumns.length) {
            newColIndex = 0
            newRowIndex++
          }
          break
        case 'prev': // Shift+Tab
          newColIndex--
          if (newColIndex < 0) {
            newColIndex = allColumns.length - 1
            newRowIndex--
          }
          break
        case 'down': // Enter
          newRowIndex++
          break
        case 'up': // Shift+Enter
          newRowIndex--
          break
      }

      // Bounds checking
      if (newRowIndex < 0) newRowIndex = 0
      if (newRowIndex >= rowCount) newRowIndex = rowCount - 1
      if (newColIndex < 0) newColIndex = 0
      if (newColIndex >= allColumns.length) newColIndex = allColumns.length - 1

      const targetColumn = allColumns[newColIndex]
      if (targetColumn) {
        gridApi.setFocusedCell(newRowIndex, targetColumn)
        gridApi.ensureIndexVisible(newRowIndex)
        gridApi.ensureColumnVisible(targetColumn)
      }
    },
    [gridApi]
  )

  /**
   * Enter edit mode on focused cell (F2)
   */
  const startEditing = useCallback(() => {
    if (!gridApi || !enableEditing) return

    const focusedCell = gridApi.getFocusedCell()
    if (!focusedCell) return

    gridApi.startEditingCell({
      rowIndex: focusedCell.rowIndex,
      colKey: focusedCell.column,
    })
  }, [gridApi, enableEditing])

  /**
   * Stop editing (Escape)
   */
  const stopEditing = useCallback(() => {
    if (!gridApi) return
    gridApi.stopEditing(true) // true = cancel, false = accept
  }, [gridApi])

  /**
   * Main keyboard event handler
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!gridApi) return

      const { key, ctrlKey, metaKey, shiftKey } = event
      const isModKey = ctrlKey || metaKey

      // Don't intercept if we're editing a cell
      const editingCell = gridApi.getEditingCells()
      if (editingCell.length > 0) {
        // Only handle Escape and Enter during editing
        if (key === 'Escape') {
          stopEditing()
          event.preventDefault()
          return
        }
        if (key === 'Enter' && !shiftKey) {
          gridApi.stopEditing(false) // Accept edit
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
        console.log('[useExcelKeyboard] Ctrl+V pressed, triggering pasteFromClipboard')
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
        gridApi.deselectAll()
        event.preventDefault()
        return
      }

      // Start typing to edit (like Excel)
      if (
        enableEditing &&
        key.length === 1 &&
        !isModKey &&
        !shiftKey &&
        /^[a-zA-Z0-9]$/.test(key)
      ) {
        const focusedCell = gridApi.getFocusedCell()
        if (focusedCell) {
          const colDef = focusedCell.column.getColDef()
          if (colDef.editable) {
            gridApi.startEditingCell({
              rowIndex: focusedCell.rowIndex,
              colKey: focusedCell.column,
              key: key, // Pass the key to start with that character
            })
            event.preventDefault()
          }
        }
      }
    },
    [
      gridApi,
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
    if (!gridApi) return

    const handleSelectionChanged = () => {
      updateSelectionInfo()
    }

    gridApi.addEventListener('selectionChanged', handleSelectionChanged)
    gridApi.addEventListener('cellFocused', handleSelectionChanged)

    return () => {
      gridApi.removeEventListener('selectionChanged', handleSelectionChanged)
      gridApi.removeEventListener('cellFocused', handleSelectionChanged)
    }
  }, [gridApi, updateSelectionInfo])

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
