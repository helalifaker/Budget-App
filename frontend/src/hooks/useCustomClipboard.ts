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

export function useCustomClipboard<TData extends { id: string }>({
  gridApi,
  onPasteCells,
}: UseCustomClipboardProps<TData>) {
  const handlePaste = useCallback(
    async (event: React.ClipboardEvent) => {
      if (!gridApi) return

      // prevent default paste behavior which might be limited in Community version
      // or conflict with our custom logic
      // We only prevent default if we successfully handle it, strictly speaking,
      // but for grid data paste, we usually want to take over.

      const clipboardText = event.clipboardData.getData('text/plain')
      if (!clipboardText) return

      event.preventDefault()

      // 1. Get the starting cell (focused cell)
      const focusedCell = gridApi.getFocusedCell()
      if (!focusedCell) return

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
        if (!rowData || !rowData.id) continue

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
            rowId: rowData.id,
            field: field,
            newValue: newValue,
            originalData: rowData,
          })
        }
      }

      if (updates.length > 0) {
        await onPasteCells(updates)
      }
    },
    [gridApi, onPasteCells]
  )

  return { handlePaste }
}
