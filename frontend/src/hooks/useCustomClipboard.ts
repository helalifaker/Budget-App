import { useCallback } from 'react'
import type { GridApi, Column, EditableCallbackParams } from 'ag-grid-community'

export interface CellUpdate<TData = Record<string, unknown>> {
  rowId: string
  field: string
  newValue: string
  originalData: TData
}

interface UseCustomClipboardProps<TData> {
  gridApi: GridApi | null
  onPasteCells: (updates: CellUpdate<TData>[]) => Promise<void>
}

export function useCustomClipboard<TData>({
  gridApi,
  onPasteCells,
}: UseCustomClipboardProps<TData>) {
  const handlePaste = useCallback(
    async (event: React.ClipboardEvent) => {
      console.log('[useCustomClipboard] Paste event triggered')

      if (!gridApi) {
        console.log('[useCustomClipboard] No gridApi available')
        return
      }

      // prevent default paste behavior which might be limited in Community version
      // or conflict with our custom logic
      // We only prevent default if we successfully handle it, strictly speaking,
      // but for grid data paste, we usually want to take over.

      const clipboardText = event.clipboardData.getData('text/plain')
      console.log('[useCustomClipboard] Clipboard text:', clipboardText?.substring(0, 100))

      if (!clipboardText) {
        console.log('[useCustomClipboard] No clipboard text')
        return
      }

      event.preventDefault()

      // 1. Get the starting cell (focused cell)
      const focusedCell = gridApi.getFocusedCell()
      console.log('[useCustomClipboard] Focused cell:', focusedCell)

      if (!focusedCell) {
        console.log('[useCustomClipboard] No focused cell - try clicking on a cell first')
        return
      }

      const { rowIndex, column: resultColumn } = focusedCell
      const startRowIndex = rowIndex

      if (startRowIndex === null) return

      // We need to resolve the column index from the visual column order
      const allColumns = gridApi.getColumns()
      if (!allColumns) return

      const startColIndex = allColumns.indexOf(resultColumn as Column)
      if (startColIndex === -1) return

      // 2. Parse clipboard data (Excel format: rows by newline, cols by tab)
      // Remove trailing newline if present, then split
      const rows = clipboardText.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n')
      const data = rows.map((r) => r.split('\t'))

      // 3. Prepare updates
      const updates: CellUpdate<TData>[] = []

      // Loop through pasted data
      for (let i = 0; i < data.length; i++) {
        const rowOffset = i
        const currentRowIndex = startRowIndex + rowOffset

        // Get row node
        const rowNode = gridApi.getDisplayedRowAtIndex(currentRowIndex)
        // If we ran out of rows in the grid, stop
        if (!rowNode) break

        const rowData = rowNode.data as TData | undefined
        // Use rowNode.id which is set by getRowId callback, not rowData.id
        // This allows data with any ID field (e.g., level_id instead of id)
        const rowId = rowNode.id
        if (!rowData || !rowId) continue

        for (let j = 0; j < data[i].length; j++) {
          const colOffset = j
          const currentColIndex = startColIndex + colOffset

          // If we ran out of columns in the grid, stop for this row
          if (currentColIndex >= allColumns.length) break

          const column = allColumns[currentColIndex]
          const colDef = column.getColDef()
          const field = colDef.field

          // Skip if column is not editable or has no field
          if (!colDef.editable || !field) continue
          // Check if function is used for editable
          if (
            typeof colDef.editable === 'function' &&
            !colDef.editable({
              node: rowNode,
              data: rowData,
              colDef,
              column,
              api: gridApi,
              context: undefined,
              value: undefined,
            } as EditableCallbackParams)
          ) {
            continue
          }

          const newValue = data[i][j].trim()

          // Skip if value is empty (optional decision: Excel ignores empty cells usually?)
          // Let's allow empty string to clear value if that is desired,
          // but usually paste overwrites.

          updates.push({
            rowId: rowId,
            field: field,
            newValue: newValue,
            originalData: rowData,
          })
        }
      }

      console.log('[useCustomClipboard] Updates to apply:', updates.length)
      if (updates.length > 0) {
        console.log('[useCustomClipboard] Calling onPasteCells with updates:', updates)
        await onPasteCells(updates)
        console.log('[useCustomClipboard] Paste complete')
      } else {
        console.log('[useCustomClipboard] No updates to apply')
      }
    },
    [gridApi, onPasteCells]
  )

  return { handlePaste }
}
