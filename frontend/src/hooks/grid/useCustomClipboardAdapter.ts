/**
 * useCustomClipboardAdapter Hook
 *
 * Refactored version of useCustomClipboard that uses the GridAdapter interface
 * instead of AG Grid's GridApi directly.
 *
 * Handles React onPaste events and maps clipboard data to grid cells using
 * the adapter abstraction.
 *
 * KEY CHANGES FROM ORIGINAL:
 * - Uses GridAdapter instead of GridApi
 * - Uses CellId (rowId + columnId) instead of rowIndex for stability
 */

import { useCallback } from 'react'
import type { GridAdapter, CellId } from '@/lib/grid'

// ============================================================================
// Types
// ============================================================================

export interface CellUpdate<TData = Record<string, unknown>> {
  rowId: string
  field: string
  newValue: string
  originalData: TData
}

interface UseCustomClipboardAdapterProps<TData> {
  adapter: GridAdapter<TData> | null
  onPasteCells: (updates: CellUpdate<TData>[]) => Promise<void>
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useCustomClipboardAdapter<TData extends Record<string, unknown>>({
  adapter,
  onPasteCells,
}: UseCustomClipboardAdapterProps<TData>) {
  /**
   * Handle React onPaste event
   * Maps clipboard data to grid cells starting from focused cell
   */
  const handlePaste = useCallback(
    async (event: React.ClipboardEvent) => {
      if (!adapter) {
        return
      }

      // Prevent default paste behavior
      event.preventDefault()

      const clipboardText = event.clipboardData.getData('text/plain')

      if (!clipboardText) {
        return
      }

      // Get the starting cell (focused cell)
      const focusedCell = adapter.getFocusedCell()

      if (!focusedCell) {
        return
      }

      // Get visible columns and their order
      const visibleColumns = adapter.getVisibleColumns()
      const startColIndex = visibleColumns.findIndex((col) => col.id === focusedCell.columnId)
      if (startColIndex === -1) {
        return
      }

      // Get visible row IDs for mapping
      const visibleRowIds = adapter.getVisibleRowIds()
      const startRowIdIndex = visibleRowIds.indexOf(focusedCell.cellId.rowId)
      if (startRowIdIndex === -1) {
        return
      }

      // Parse clipboard data (Excel format: rows by newline, cols by tab)
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const data = rows.map((r) => r.split('\t'))

      // Prepare updates using stable row IDs
      const updates: CellUpdate<TData>[] = []

      // Loop through pasted data
      for (let i = 0; i < data.length; i++) {
        const currentRowIdIndex = startRowIdIndex + i

        // Check if we've run out of rows
        if (currentRowIdIndex >= visibleRowIds.length) break

        const rowId = visibleRowIds[currentRowIdIndex]
        const row = adapter.getRowById(rowId)
        if (!row) continue

        for (let j = 0; j < data[i].length; j++) {
          const currentColIndex = startColIndex + j

          // Check if we've run out of columns
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
        await onPasteCells(updates)
      }
    },
    [adapter, onPasteCells]
  )

  return { handlePaste }
}
