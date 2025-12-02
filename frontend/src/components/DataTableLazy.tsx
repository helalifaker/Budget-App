/**
 * Lazy-loaded DataTable Component
 *
 * This component lazy loads AG Grid to reduce initial bundle size.
 * AG Grid is ~200KB and only needed on data entry pages.
 *
 * Usage:
 * import { DataTableLazy } from '@/components/DataTableLazy'
 * <DataTableLazy rowData={data} columnDefs={columns} />
 */

import { lazy, Suspense } from 'react'
import { AgGridReactProps } from 'ag-grid-react'
import { GridSkeleton } from './LoadingSkeleton'

// Lazy load the DataTable component (which includes AG Grid)
const DataTable = lazy(() =>
  import('./DataTable').then((module) => ({ default: module.DataTable }))
)

interface DataTableProps<TData = unknown> extends AgGridReactProps<TData> {
  loading?: boolean
  error?: Error | null
}

/**
 * Lazy-loaded wrapper for DataTable with loading fallback
 */
export function DataTableLazy<TData = unknown>({ ...props }: DataTableProps<TData>) {
  return (
    <Suspense fallback={<GridSkeleton />}>
      <DataTable {...(props as DataTableProps<unknown>)} />
    </Suspense>
  )
}
