/**
 * Lazy-loaded ExcelEditableTable Component (TanStack Table)
 *
 * This component lazy loads the ExcelEditableTable (TanStack Table + clipboard support)
 * to reduce initial bundle size. TanStack Table is ~50KB vs AG Grid's ~950KB.
 *
 * Features included:
 * - Full Clipboard Support: Ctrl+C/V for copy/paste, compatible with Excel
 * - Multi-row Selection: Click to select, checkbox selection
 * - Keyboard Navigation: Tab, Enter, Arrow keys navigate like Excel
 * - Edit on Type: Start typing to edit cell content directly
 * - Fill Down: Ctrl+D fills selected rows with first row's values
 * - Status Bar: Shows Sum, Average, Count of selected numeric cells
 * - Delete Key: Clear selected cells with Delete/Backspace
 *
 * Usage:
 * import { ExcelEditableTableLazy } from '@/components/grid/tanstack/ExcelEditableTableLazy'
 * <ExcelEditableTableLazy
 *   rowData={data}
 *   columnDefs={columns}
 *   getRowId={(row) => row.id}
 *   onCellValueChanged={handleCellChange}
 * />
 */

import { lazy, Suspense } from 'react'
import { GridSkeleton } from '@/components/LoadingSkeleton'
import type { ExcelEditableTableProps } from './ExcelEditableTable'

// Re-export the props type for consumers
export type { ExcelEditableTableProps }

// Lazy load the ExcelEditableTable component
const ExcelEditableTable = lazy(() =>
  import('./ExcelEditableTable').then((module) => ({
    default: module.ExcelEditableTable,
  }))
)

/**
 * Lazy-loaded wrapper for TanStack ExcelEditableTable with loading fallback
 *
 * Use this instead of AG Grid's ExcelDataTableLazy when migrating to TanStack Table.
 * Provides identical Excel-like features with ~90% smaller bundle size.
 */
export function ExcelEditableTableLazy<TData extends object>(
  props: ExcelEditableTableProps<TData>
) {
  // Cast props to satisfy React.lazy's loss of generic type information
  // This is safe because the underlying component accepts the same props
  // Use unknown as intermediate step for type-safe widening
  const typedProps = props as unknown as ExcelEditableTableProps<object>

  return (
    <Suspense fallback={<GridSkeleton />}>
      <ExcelEditableTable {...typedProps} />
    </Suspense>
  )
}
