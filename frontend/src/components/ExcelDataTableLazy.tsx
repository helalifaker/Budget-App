/**
 * Lazy-loaded ExcelDataTable Component
 *
 * This component lazy loads the ExcelDataTable (which includes AG Grid + clipboard support)
 * to reduce initial bundle size. AG Grid is ~200KB and clipboard hooks add more.
 *
 * Features included:
 * - Full Clipboard Support: Ctrl+C/V for copy/paste, compatible with Excel
 * - Multi-row Selection: Click to select, Ctrl+Click for multiple, Shift+Click for range
 * - Keyboard Navigation: Tab, Enter, Arrow keys navigate like Excel
 * - Edit on Type: Start typing to edit cell content directly
 * - Undo/Redo: Built-in undo stack with Ctrl+Z/Y
 * - Fill Down: Ctrl+D fills selected rows with first row's values
 * - Status Bar: Shows Sum, Average, Count of selected numeric cells
 * - Delete Key: Clear selected cells with Delete/Backspace
 * - Context Menu: Right-click menu with copy/paste options
 *
 * Usage:
 * import { ExcelDataTableLazy } from '@/components/ExcelDataTableLazy'
 * <ExcelDataTableLazy
 *   rowData={data}
 *   columnDefs={columns}
 *   onPaste={handlePaste}
 *   onCellsCleared={handleClear}
 * />
 */

import { lazy, Suspense } from 'react'
import { GridSkeleton } from './LoadingSkeleton'
import type { ExcelDataTableProps } from './grid/ExcelDataTable'

// Re-export the props type for consumers
export type { ExcelDataTableProps }

// Re-export the cell types for paste/clear handlers
export type { ClearedCell, FilledCell } from '@/hooks/useExcelKeyboard'

// Lazy load the ExcelDataTable component (which includes AG Grid + clipboard hooks)
const ExcelDataTable = lazy(() =>
  import('./grid/ExcelDataTable').then((module) => ({ default: module.ExcelDataTable }))
)

/**
 * Lazy-loaded wrapper for ExcelDataTable with loading fallback
 *
 * Use this instead of DataTableLazy when you need:
 * - Copy/Paste support (Ctrl+C/V)
 * - Fill down (Ctrl+D)
 * - Delete key to clear cells
 * - Selection statistics in status bar
 */
export function ExcelDataTableLazy<TData = unknown>(props: ExcelDataTableProps<TData>) {
  return (
    <Suspense fallback={<GridSkeleton />}>
      <ExcelDataTable {...(props as ExcelDataTableProps<unknown>)} />
    </Suspense>
  )
}
