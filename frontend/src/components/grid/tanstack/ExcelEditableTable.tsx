/**
 * ExcelEditableTable Component
 *
 * EditableTable with full Excel-like keyboard shortcuts and clipboard support.
 *
 * Features:
 * - All EditableTable features (click-to-edit, F2, type-to-edit, navigation)
 * - Ctrl+C: Copy selected rows/cells to clipboard
 * - Ctrl+V: Paste from clipboard
 * - Ctrl+D: Fill down (copy first selected row to all selected rows)
 * - Ctrl+A: Select all rows
 * - Delete/Backspace: Clear selected cells
 * - Escape: Deselect all
 * - Selection statistics in status bar (sum, average, min, max)
 *
 * @example
 * ```tsx
 * <ExcelEditableTable
 *   rowData={data}
 *   columnDefs={columns}
 *   getRowId={(row) => row.id}
 *   onCellValueChanged={(event) => {
 *     // Handle cell change
 *   }}
 *   enableRowSelection
 * />
 * ```
 */

import React, { useCallback, useMemo, useRef, useState, useEffect } from 'react'
import { EditableTable, type EditableTableProps, type EditableTableApi } from './EditableTable'
import { toastMessages } from '@/lib/toast-messages'

// ============================================================================
// Types
// ============================================================================

export interface ExcelEditableTableProps<TData extends object> extends Omit<
  EditableTableProps<TData>,
  'onTableReady'
> {
  /** Enable clipboard operations (Ctrl+C, Ctrl+V) */
  enableClipboard?: boolean

  /** Enable fill down (Ctrl+D) */
  enableFillDown?: boolean

  /** Enable cell clearing (Delete key) */
  enableClear?: boolean

  /** Callback when cells are cleared */
  onCellsCleared?: (cells: Array<{ rowId: string; field: string; oldValue: unknown }>) => void

  /** Callback when cells are filled down */
  onCellsFilled?: (
    cells: Array<{ rowId: string; field: string; oldValue: unknown; newValue: unknown }>
  ) => void

  /** Custom value formatter for clipboard copy */
  formatCopiedValue?: (value: unknown, columnId: string) => string

  /** Show selection statistics in status bar */
  showSelectionStats?: boolean
}

/**
 * Selection statistics calculated from selected rows
 */
interface SelectionStats {
  cellCount: number
  rowCount: number
  sum: number | null
  average: number | null
  min: number | null
  max: number | null
  numericCount: number
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Default value formatter for clipboard copy
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

/**
 * Calculate statistics from numeric values
 */
function calculateStats(values: unknown[]): Omit<SelectionStats, 'cellCount' | 'rowCount'> {
  const numericValues: number[] = []

  values.forEach((value) => {
    const num = parseFloat(String(value))
    if (!isNaN(num) && isFinite(num)) {
      numericValues.push(num)
    }
  })

  if (numericValues.length === 0) {
    return { sum: null, average: null, min: null, max: null, numericCount: 0 }
  }

  const sum = numericValues.reduce((a, b) => a + b, 0)
  return {
    sum,
    average: sum / numericValues.length,
    min: Math.min(...numericValues),
    max: Math.max(...numericValues),
    numericCount: numericValues.length,
  }
}

// ============================================================================
// Component
// ============================================================================

export function ExcelEditableTable<TData extends object>({
  rowData,
  columnDefs,
  getRowId,
  onCellValueChanged,
  enableClipboard = true,
  enableFillDown = true,
  enableClear = true,
  onCellsCleared,
  onCellsFilled,
  formatCopiedValue = defaultFormatValue,
  showSelectionStats = true,
  // Row selection defaults to enabled for Excel features
  enableRowSelection = true,
  showCheckboxColumn = true,
  // Explicitly extract onRowSelectionChange to prevent it from being in rest
  // (which would overwrite our handleRowSelectionChange when spread)
  onRowSelectionChange: userOnRowSelectionChange,
  ...rest
}: ExcelEditableTableProps<TData>) {
  const data = useMemo(() => rowData ?? [], [rowData])
  const containerRef = useRef<HTMLDivElement>(null)
  const tableApiRef = useRef<EditableTableApi<TData> | null>(null)

  // Selection statistics state
  const [selectionStats, setSelectionStats] = useState<SelectionStats>({
    cellCount: 0,
    rowCount: 0,
    sum: null,
    average: null,
    min: null,
    max: null,
    numericCount: 0,
  })

  // Track if we're currently editing
  const [isEditing, setIsEditing] = useState(false)

  // Handle table ready - capture the API
  const handleTableReady = useCallback((api: EditableTableApi<TData>) => {
    tableApiRef.current = api
  }, [])

  // Handle row selection change
  const handleRowSelectionChange = useCallback(
    (rowIds: string[]) => {
      // Calculate statistics from selected rows
      if (rowIds.length === 0) {
        setSelectionStats({
          cellCount: 0,
          rowCount: 0,
          sum: null,
          average: null,
          min: null,
          max: null,
          numericCount: 0,
        })
        // Call parent's onRowSelectionChange if provided
        userOnRowSelectionChange?.(rowIds)
        return
      }

      const tableApi = tableApiRef.current

      // Even if tableApi isn't ready yet, we can still show row count
      // This handles the case where selection happens before useEffect runs
      if (!tableApi) {
        setSelectionStats({
          cellCount: 0,
          rowCount: rowIds.length,
          sum: null,
          average: null,
          min: null,
          max: null,
          numericCount: 0,
        })
        // Call parent's onRowSelectionChange if provided
        userOnRowSelectionChange?.(rowIds)
        return
      }

      // Collect all values from selected rows
      const allValues: unknown[] = []
      const visibleColumns = tableApi.getVisibleColumns()

      rowIds.forEach((rowId) => {
        visibleColumns.forEach((columnId) => {
          const value = tableApi.getCellValue(rowId, columnId)
          if (value !== null && value !== undefined) {
            allValues.push(value)
          }
        })
      })

      const stats = calculateStats(allValues)
      setSelectionStats({
        cellCount: allValues.length,
        rowCount: rowIds.length,
        ...stats,
      })

      // Call parent's onRowSelectionChange if provided
      userOnRowSelectionChange?.(rowIds)
    },
    [userOnRowSelectionChange]
  )

  // ========================================================================
  // Clipboard Operations
  // ========================================================================

  /**
   * Copy selected rows to clipboard in Excel format (tab-separated)
   */
  const copyToClipboard = useCallback(async () => {
    const tableApi = tableApiRef.current
    if (!tableApi) return

    const selectedRows = tableApi.getSelectedRows()
    if (selectedRows.length === 0) {
      // Try to copy focused cell
      const focusedCell = tableApi.getFocusedCell()
      if (focusedCell) {
        const value = tableApi.getCellValue(focusedCell.rowId, focusedCell.columnId)
        const text = formatCopiedValue(value, focusedCell.columnId)
        try {
          await navigator.clipboard.writeText(text)
          toastMessages.success.custom('Copied 1 cell to clipboard')
        } catch (err) {
          console.error('[ExcelEditableTable] Failed to copy:', err)
        }
      }
      return
    }

    // Get visible columns
    const visibleColumns = tableApi.getVisibleColumns()

    // Build tab-separated values for each row
    const lines = selectedRows.map((row) => {
      const rowId = getRowId(row)
      return visibleColumns
        .map((columnId) => {
          const value = tableApi.getCellValue(rowId, columnId)
          return formatCopiedValue(value, columnId)
        })
        .join('\t')
    })

    const text = lines.join('\n')

    try {
      await navigator.clipboard.writeText(text)
      toastMessages.success.custom(
        `Copied ${selectedRows.length} row${selectedRows.length > 1 ? 's' : ''} to clipboard`
      )
    } catch (err) {
      console.error('[ExcelEditableTable] Failed to copy:', err)
    }
  }, [formatCopiedValue, getRowId])

  /**
   * Paste from clipboard into cells
   */
  const pasteFromClipboard = useCallback(async () => {
    if (!enableClipboard || !onCellValueChanged) return

    const tableApi = tableApiRef.current
    if (!tableApi) return

    // Get the starting cell (focused cell)
    const focusedCell = tableApi.getFocusedCell()
    if (!focusedCell) {
      toastMessages.info.custom('Select a cell before pasting')
      return
    }

    try {
      // Read clipboard
      const clipboardText = await navigator.clipboard.readText()
      if (!clipboardText) return

      // Parse clipboard data (Excel format: rows by newline, cols by tab)
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const parsedData = rows.map((r) => r.split('\t'))

      // Get visible columns and find starting column index
      const visibleColumns = tableApi.getVisibleColumns()
      const startColIndex = visibleColumns.indexOf(focusedCell.columnId)
      if (startColIndex === -1) return

      // Get all row IDs and find starting row index
      const allRowIds = data.map((row) => getRowId(row))
      const startRowIndex = allRowIds.indexOf(focusedCell.rowId)
      if (startRowIndex === -1) return

      let pastedCount = 0

      // Apply pasted values
      for (let i = 0; i < parsedData.length; i++) {
        const currentRowIndex = startRowIndex + i
        if (currentRowIndex >= allRowIds.length) break

        const rowId = allRowIds[currentRowIndex]
        const row = data.find((r) => getRowId(r) === rowId)
        if (!row) continue

        for (let j = 0; j < parsedData[i].length; j++) {
          const currentColIndex = startColIndex + j
          if (currentColIndex >= visibleColumns.length) break

          const columnId = visibleColumns[currentColIndex]

          // Skip if not editable
          if (!tableApi.isCellEditable(rowId, columnId)) continue

          const newValue = parsedData[i][j].trim()
          const oldValue = tableApi.getCellValue(rowId, columnId)

          // Trigger cell change
          onCellValueChanged({
            data: row,
            field: columnId,
            oldValue,
            newValue,
            rowId,
            columnId,
            revertValue: () => {},
          })

          pastedCount++
        }
      }

      if (pastedCount > 0) {
        toastMessages.success.custom(`Pasted ${pastedCount} cell${pastedCount > 1 ? 's' : ''}`)
      }
    } catch (err) {
      console.error('[ExcelEditableTable] Failed to paste:', err)
      toastMessages.error.custom('Failed to paste from clipboard')
    }
  }, [enableClipboard, onCellValueChanged, data, getRowId])

  /**
   * Clear selected cells (Delete/Backspace)
   */
  const clearSelectedCells = useCallback(() => {
    if (!enableClear || !onCellValueChanged) return

    const tableApi = tableApiRef.current
    if (!tableApi) return

    const selectedRowIds = tableApi.getSelectedRowIds()
    const clearedCells: Array<{ rowId: string; field: string; oldValue: unknown }> = []

    if (selectedRowIds.length > 0) {
      // Clear all editable cells in selected rows
      const visibleColumns = tableApi.getVisibleColumns()

      selectedRowIds.forEach((rowId) => {
        const row = data.find((r) => getRowId(r) === rowId)
        if (!row) return

        visibleColumns.forEach((columnId) => {
          if (!tableApi.isCellEditable(rowId, columnId)) return

          const oldValue = tableApi.getCellValue(rowId, columnId)

          // Skip if already empty
          if (oldValue === null || oldValue === undefined || oldValue === '') return

          clearedCells.push({ rowId, field: columnId, oldValue })

          onCellValueChanged({
            data: row,
            field: columnId,
            oldValue,
            newValue: null,
            rowId,
            columnId,
            revertValue: () => {},
          })
        })
      })
    } else {
      // Clear single focused cell
      const focusedCell = tableApi.getFocusedCell()
      if (focusedCell && tableApi.isCellEditable(focusedCell.rowId, focusedCell.columnId)) {
        const row = data.find((r) => getRowId(r) === focusedCell.rowId)
        if (row) {
          const oldValue = tableApi.getCellValue(focusedCell.rowId, focusedCell.columnId)

          // Skip if already empty
          if (oldValue !== null && oldValue !== undefined && oldValue !== '') {
            clearedCells.push({
              rowId: focusedCell.rowId,
              field: focusedCell.columnId,
              oldValue,
            })

            onCellValueChanged({
              data: row,
              field: focusedCell.columnId,
              oldValue,
              newValue: null,
              rowId: focusedCell.rowId,
              columnId: focusedCell.columnId,
              revertValue: () => {},
            })
          }
        }
      }
    }

    if (clearedCells.length > 0) {
      onCellsCleared?.(clearedCells)
      toastMessages.success.custom(
        `Cleared ${clearedCells.length} cell${clearedCells.length > 1 ? 's' : ''}`
      )
    }
  }, [enableClear, onCellValueChanged, onCellsCleared, data, getRowId])

  /**
   * Fill down (Ctrl+D) - Copy first selected row's values to all other selected rows
   */
  const fillDown = useCallback(() => {
    if (!enableFillDown || !onCellValueChanged) return

    const tableApi = tableApiRef.current
    if (!tableApi) return

    const selectedRowIds = tableApi.getSelectedRowIds()
    if (selectedRowIds.length < 2) {
      toastMessages.info.custom('Select at least 2 rows to fill down')
      return
    }

    const firstRowId = selectedRowIds[0]
    const firstRow = data.find((r) => getRowId(r) === firstRowId)
    if (!firstRow) return

    const visibleColumns = tableApi.getVisibleColumns()
    const filledCells: Array<{
      rowId: string
      field: string
      oldValue: unknown
      newValue: unknown
    }> = []

    // Copy first row's values to all other selected rows
    selectedRowIds.slice(1).forEach((rowId) => {
      const row = data.find((r) => getRowId(r) === rowId)
      if (!row) return

      visibleColumns.forEach((columnId) => {
        if (!tableApi.isCellEditable(rowId, columnId)) return

        const newValue = tableApi.getCellValue(firstRowId, columnId)
        const oldValue = tableApi.getCellValue(rowId, columnId)

        // Skip if values are the same
        if (newValue === oldValue) return

        filledCells.push({ rowId, field: columnId, oldValue, newValue })

        onCellValueChanged({
          data: row,
          field: columnId,
          oldValue,
          newValue,
          rowId,
          columnId,
          revertValue: () => {},
        })
      })
    })

    if (filledCells.length > 0) {
      onCellsFilled?.(filledCells)
      toastMessages.success.custom(
        `Filled ${filledCells.length} cell${filledCells.length > 1 ? 's' : ''}`
      )
    }
  }, [enableFillDown, onCellValueChanged, onCellsFilled, data, getRowId])

  // ========================================================================
  // Keyboard Event Handler
  // ========================================================================

  const handleKeyDown = useCallback(
    async (e: React.KeyboardEvent) => {
      // Don't handle shortcuts when editing
      if (isEditing) return

      const isMod = e.ctrlKey || e.metaKey

      // Ctrl+C: Copy
      if (isMod && e.key === 'c' && enableClipboard) {
        e.preventDefault()
        await copyToClipboard()
        return
      }

      // Ctrl+V: Paste
      if (isMod && e.key === 'v' && enableClipboard) {
        e.preventDefault()
        await pasteFromClipboard()
        return
      }

      // Ctrl+D: Fill Down
      if (isMod && e.key === 'd' && enableFillDown) {
        e.preventDefault()
        fillDown()
        return
      }

      // Delete/Backspace: Clear (only when rows are selected)
      if ((e.key === 'Delete' || e.key === 'Backspace') && enableClear) {
        const tableApi = tableApiRef.current
        if (tableApi && tableApi.getSelectedRowIds().length > 0) {
          e.preventDefault()
          clearSelectedCells()
          return
        }
        // Let single-cell clearing be handled by EditableTable
      }
    },
    [
      isEditing,
      enableClipboard,
      enableFillDown,
      enableClear,
      copyToClipboard,
      pasteFromClipboard,
      fillDown,
      clearSelectedCells,
    ]
  )

  // Track editing state from container focus
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleFocusIn = (e: FocusEvent) => {
      // Check if focus is on an input/textarea (editing)
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        setIsEditing(true)
      }
    }

    const handleFocusOut = (e: FocusEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        setIsEditing(false)
      }
    }

    container.addEventListener('focusin', handleFocusIn)
    container.addEventListener('focusout', handleFocusOut)

    return () => {
      container.removeEventListener('focusin', handleFocusIn)
      container.removeEventListener('focusout', handleFocusOut)
    }
  }, [])

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div ref={containerRef} onKeyDown={handleKeyDown} className="relative flex flex-col">
      <EditableTable
        rowData={rowData}
        columnDefs={columnDefs}
        getRowId={getRowId}
        onCellValueChanged={onCellValueChanged}
        enableRowSelection={enableRowSelection}
        showCheckboxColumn={showCheckboxColumn}
        onRowSelectionChange={handleRowSelectionChange}
        onTableReady={handleTableReady}
        {...rest}
      />

      {/* Selection statistics status bar */}
      {showSelectionStats && selectionStats.rowCount > 0 && (
        <div className="flex items-center justify-end gap-4 px-3 py-1.5 bg-[var(--color-subtle)] border-t border-[var(--color-border-light)] text-xs text-[var(--color-text-secondary)]">
          <span>
            <span className="font-medium">{selectionStats.rowCount}</span> row
            {selectionStats.rowCount !== 1 ? 's' : ''} selected
            {selectionStats.cellCount > 0 && (
              <span className="ml-1">
                (<span className="font-medium">{selectionStats.cellCount}</span> cells)
              </span>
            )}
          </span>
          {selectionStats.numericCount > 0 && (
            <>
              <span className="text-[var(--color-border-medium)]">|</span>
              {selectionStats.sum !== null && (
                <span>
                  Sum:{' '}
                  <span className="font-medium">{selectionStats.sum.toLocaleString('fr-FR')}</span>
                </span>
              )}
              {selectionStats.average !== null && (
                <span>
                  Avg:{' '}
                  <span className="font-medium">
                    {selectionStats.average.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
                  </span>
                </span>
              )}
              {selectionStats.min !== null && selectionStats.max !== null && (
                <span>
                  Min:{' '}
                  <span className="font-medium">{selectionStats.min.toLocaleString('fr-FR')}</span>{' '}
                  / Max:{' '}
                  <span className="font-medium">{selectionStats.max.toLocaleString('fr-FR')}</span>
                </span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
