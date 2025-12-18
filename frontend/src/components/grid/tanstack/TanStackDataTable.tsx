/**
 * TanStackDataTable Component
 *
 * Drop-in replacement for DataTable/ExcelDataTable using TanStack Table.
 * Provides the same API surface for easy migration from AG Grid.
 *
 * Features:
 * - Automatic column conversion from AG Grid ColDefs
 * - Virtual scrolling for large datasets
 * - Selection (single/multi)
 * - Sorting with visual indicators
 * - Loading/error states
 * - Premium EFIR design system styling
 *
 * @example
 * ```tsx
 * <TanStackDataTable
 *   rowData={data}
 *   columnDefs={columns}
 *   getRowId={(data) => data.id}
 *   loading={isLoading}
 * />
 * ```
 */

import { useMemo, useCallback } from 'react'
import type { ColumnDef, SortingState } from '@tanstack/react-table'
import { Loader2, AlertTriangle, WifiOff, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { BaseTable } from './BaseTable'
import { VirtualizedTable } from './VirtualizedTable'
import {
  convertColumns,
  type AGGridColDef,
  type ConvertColumnsOptions,
} from '@/lib/grid/columnConverter'

// ============================================================================
// Types
// ============================================================================

/**
 * Cell renderer props for custom renderers.
 */
export interface CellRendererProps<TData = unknown> {
  value: unknown
  data: TData
  rowIndex: number
}

/**
 * Props matching AG Grid's ColDef for easy migration.
 * Supports both AG Grid ColDefs and TanStack ColumnDefs.
 */
export interface TanStackDataTableProps<TData extends object> {
  /** Row data to display */
  rowData: TData[] | null | undefined

  /**
   * Column definitions - supports AG Grid ColDef format.
   * Will be automatically converted to TanStack ColumnDef.
   */
  columnDefs: AGGridColDef<TData>[] | ColumnDef<TData, unknown>[]

  /**
   * Function to get unique row ID from data.
   * Required for stable row identification.
   */
  getRowId: (data: TData) => string

  /** Unique identifier for the table (for accessibility) */
  tableId?: string

  /** Label for screen readers */
  tableLabel?: string

  /** Description for screen readers */
  tableDescription?: string

  /** Show loading overlay */
  loading?: boolean

  /** Error state */
  error?: Error | null

  /** Callback to retry loading data */
  onRetry?: () => void

  /** Enable row selection */
  enableRowSelection?: boolean

  /** Selection mode: 'single' or 'multi' */
  selectionMode?: 'single' | 'multi'

  /** Callback when selection changes */
  onSelectionChange?: (selectedRows: TData[]) => void

  /** Enable column sorting */
  enableSorting?: boolean

  /** Initial sorting state */
  initialSorting?: SortingState

  /** Callback when sorting changes */
  onSortingChange?: (sorting: SortingState) => void

  /** Use compact row height (36px vs 44px) */
  compact?: boolean

  /** Custom height for table container */
  height?: number | string

  /** Empty state message */
  emptyMessage?: string

  /** Module color accent */
  moduleColor?:
    | 'gold'
    | 'sage'
    | 'terracotta'
    | 'slate'
    | 'wine'
    | 'orange'
    | 'teal'
    | 'blue'
    | 'purple'

  /** Additional class names for container */
  className?: string

  /**
   * Use virtualization for large datasets.
   * Auto-enabled when data > 100 rows.
   * Set to false to disable.
   */
  virtualize?: boolean

  /** Overscan rows for virtualization */
  overscan?: number

  /**
   * Map of cell renderer names to React components.
   * Used when AG Grid colDef has cellRenderer as a string.
   */
  cellRenderers?: Record<string, (props: CellRendererProps<TData>) => React.ReactNode>

  /**
   * If true, columns are already in TanStack ColumnDef format.
   * Skip conversion and use directly.
   */
  nativeColumns?: boolean
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if an error is a network error (backend unreachable).
 */
function isNetworkError(error: Error): boolean {
  const message = error.message.toLowerCase()
  return (
    message.includes('network error') ||
    message.includes('network request failed') ||
    message.includes('failed to fetch') ||
    message.includes('econnrefused') ||
    message.includes('connection refused')
  )
}

/**
 * Check if columns are AG Grid ColDefs or TanStack ColumnDefs.
 * TanStack columns have 'accessorKey' or 'accessorFn', AG Grid has 'field'.
 */
function isAGGridColumns<TData>(
  columns: AGGridColDef<TData>[] | ColumnDef<TData, unknown>[]
): columns is AGGridColDef<TData>[] {
  if (columns.length === 0) return false
  const first = columns[0]
  // AG Grid uses 'field', TanStack uses 'accessorKey' or 'accessorFn'
  return 'field' in first || ('headerName' in first && !('accessorKey' in first))
}

// ============================================================================
// Error Component
// ============================================================================

interface ErrorDisplayProps {
  error: Error
  onRetry?: () => void
}

function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const networkError = isNetworkError(error)

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={cn(
        'flex items-center justify-center h-64',
        'bg-[var(--color-paper)] rounded-xl',
        'border border-[var(--color-border-light)]',
        'shadow-sm'
      )}
    >
      <div className="text-center max-w-md px-4">
        {/* Icon */}
        <div className="flex justify-center mb-3">
          {networkError ? (
            <div className="p-3 bg-red-100 rounded-full">
              <WifiOff className="h-6 w-6 text-red-500" />
            </div>
          ) : (
            <div className="p-3 bg-amber-100 rounded-full">
              <AlertTriangle className="h-6 w-6 text-amber-600" />
            </div>
          )}
        </div>

        {/* Title */}
        <p className="text-[var(--color-terracotta)] font-semibold text-lg">
          {networkError ? 'Cannot connect to server' : 'Error loading data'}
        </p>

        {/* Description */}
        <p className="text-sm text-[var(--color-text-secondary)] mt-2">
          {networkError
            ? 'The backend server is not responding. Check the status indicator at the bottom-right for details.'
            : error.message}
        </p>

        {/* Retry button */}
        {onRetry && (
          <button
            onClick={onRetry}
            className={cn(
              'mt-4 inline-flex items-center gap-2 px-4 py-2',
              'bg-[var(--color-gold-lighter)] hover:bg-[var(--color-gold-light)] text-[var(--color-gold-dark)]',
              'rounded-md font-medium text-sm',
              'transition-colors duration-150'
            )}
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// Loading Component
// ============================================================================

interface LoadingOverlayProps {
  height?: number | string
}

function LoadingOverlay({ height = 400 }: LoadingOverlayProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={cn(
        'flex items-center justify-center',
        'bg-[var(--color-paper)] rounded-xl',
        'border border-[var(--color-border-light)]',
        'shadow-sm'
      )}
      style={{ height }}
    >
      <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
        <Loader2 className="h-5 w-5 animate-spin text-[var(--color-gold)]" />
        <span>Loading data...</span>
      </div>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * TanStackDataTable - Drop-in replacement for AG Grid DataTable.
 *
 * Automatically handles:
 * - Column definition conversion from AG Grid format
 * - Virtualization for large datasets (>100 rows)
 * - Loading and error states
 * - Selection and sorting
 */
export function TanStackDataTable<TData extends object>({
  rowData,
  columnDefs,
  getRowId,
  tableId = 'tanstack-table',
  tableLabel = 'Data table',
  loading = false,
  error = null,
  onRetry,
  enableRowSelection = false,
  selectionMode = 'multi',
  onSelectionChange,
  enableSorting = true,
  initialSorting = [],
  onSortingChange,
  compact = true,
  height = 600,
  emptyMessage = 'No data available',
  moduleColor = 'gold',
  className,
  virtualize,
  overscan = 5,
  cellRenderers = {},
  nativeColumns = false,
}: TanStackDataTableProps<TData>) {
  // Normalize data - must be before hooks that depend on it
  const data = rowData ?? []

  // Convert columns if needed - MUST call before any returns (React hooks rules)
  const convertedColumns = useMemo(() => {
    if (nativeColumns || !isAGGridColumns(columnDefs)) {
      // Already TanStack ColumnDefs
      return columnDefs as ColumnDef<TData, unknown>[]
    }

    // Convert AG Grid columns to TanStack
    const options: ConvertColumnsOptions<TData> = {
      cellRenderers: cellRenderers as Record<
        string,
        (props: { value: unknown; data: TData; rowIndex: number }) => React.ReactNode
      >,
      getRowId,
    }

    return convertColumns(columnDefs, options)
  }, [columnDefs, cellRenderers, getRowId, nativeColumns])

  // Determine if virtualization should be used - MUST call before any returns
  const shouldVirtualize = useMemo(() => {
    if (virtualize !== undefined) return virtualize
    return data.length > 100
  }, [virtualize, data.length])

  // Selection change handler - MUST call before any returns
  const handleSelectionChange = useCallback(
    (selectedRows: TData[]) => {
      onSelectionChange?.(selectedRows)
    },
    [onSelectionChange]
  )

  // Handle error state - AFTER all hooks
  if (error) {
    return <ErrorDisplay error={error} onRetry={onRetry} />
  }

  // Handle loading state with no data - AFTER all hooks
  if (loading && data.length === 0) {
    return <LoadingOverlay height={height} />
  }

  // Common props for both table variants
  const tableProps = {
    data,
    columns: convertedColumns,
    getRowId,
    enableRowSelection,
    selectionMode,
    onSelectionChange: handleSelectionChange,
    enableSorting,
    initialSorting,
    onSortingChange,
    compact,
    emptyMessage,
    moduleColor,
    isLoading: loading,
    className,
  }

  // Render virtualized or base table
  if (shouldVirtualize) {
    return (
      <VirtualizedTable
        {...tableProps}
        height={height}
        overscan={overscan}
        aria-label={tableLabel}
        aria-describedby={tableId ? `${tableId}-description` : undefined}
      />
    )
  }

  return (
    <BaseTable
      {...tableProps}
      aria-label={tableLabel}
      aria-describedby={tableId ? `${tableId}-description` : undefined}
    />
  )
}

// ============================================================================
// Re-exports for convenience
// ============================================================================

export { BaseTable, VirtualizedTable }
export type { BaseTableProps } from './BaseTable'
export type { VirtualizedTableProps } from './VirtualizedTable'
