/**
 * Accessible DataTable Component - EFIR Luxury Warm Theme
 *
 * AG Grid wrapper with comprehensive accessibility support:
 * - Row hover: Subtle background (#F5F4F1)
 * - Header: Secondary text, medium weight
 * - Borders: Light (#E8E6E1)
 * - Warm themed styling throughout
 * - ARIA labels and descriptions
 * - Keyboard navigation (Tab, Enter, Arrow keys)
 * - Screen reader announcements for updates
 */

import { AgGridReact, AgGridReactProps } from 'ag-grid-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { themeQuartz } from 'ag-grid-community'
import type { GridReadyEvent, SelectionChangedEvent } from 'ag-grid-community'
import { AccessibleGridWrapper, type AccessibleGridWrapperRef } from './grid/AccessibleGridWrapper'
import { Loader2, AlertTriangle, WifiOff, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

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

interface DataTableProps<TData = unknown> extends AgGridReactProps<TData> {
  /**
   * Unique identifier for accessibility (defaults to 'data-table')
   */
  gridId?: string

  /**
   * Label for screen readers (required for accessibility)
   */
  gridLabel?: string

  /**
   * Optional description for the grid
   */
  gridDescription?: string

  /**
   * Show loading overlay
   */
  loading?: boolean

  /**
   * Error state
   */
  error?: Error | null

  /**
   * Callback to retry loading data
   */
  onRetry?: () => void

  /**
   * Show keyboard help tooltip
   */
  showKeyboardHelp?: boolean
}

export function DataTable<TData = unknown>({
  gridId = 'data-table',
  gridLabel = 'Data table',
  gridDescription,
  loading = false,
  error = null,
  onRetry,
  rowData,
  showKeyboardHelp = true,
  ...props
}: DataTableProps<TData>) {
  const wrapperRef = useRef<AccessibleGridWrapperRef>(null)
  const [selectedCount, setSelectedCount] = useState(0)

  const defaultColDef = useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      // Enable keyboard navigation
      suppressKeyboardEvent: () => false,
      ...props.defaultColDef,
    }),
    [props.defaultColDef]
  )

  const onGridReady = useCallback(
    (event: GridReadyEvent) => {
      // Announce grid ready to screen readers
      wrapperRef.current?.announceStatus(`${gridLabel} loaded with ${rowData?.length || 0} rows`)

      if (props.onGridReady) {
        props.onGridReady(event)
      }
    },
    [props, gridLabel, rowData?.length]
  )

  const onSelectionChanged = useCallback(
    (event: SelectionChangedEvent) => {
      const selected = event.api.getSelectedRows().length
      setSelectedCount(selected)

      if (selected > 0) {
        wrapperRef.current?.announceStatus(`${selected} row${selected > 1 ? 's' : ''} selected`)
      }

      if (props.onSelectionChanged) {
        props.onSelectionChanged(event)
      }
    },
    [props]
  )

  if (error) {
    const networkError = isNetworkError(error)

    return (
      <div
        role="alert"
        aria-live="assertive"
        className={cn(
          'flex items-center justify-center h-64',
          'bg-paper rounded-xl',
          'border border-border-light',
          'shadow-efir-sm'
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
          <p className="text-terracotta-600 font-body font-semibold text-lg">
            {networkError ? 'Cannot connect to server' : 'Error loading data'}
          </p>

          {/* Description */}
          <p className="text-sm font-body text-text-secondary mt-2">
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
                'bg-gold-100 hover:bg-gold-200 text-gold-800',
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

  return (
    <AccessibleGridWrapper
      ref={wrapperRef}
      id={gridId}
      label={gridLabel}
      description={gridDescription}
      rowCount={rowData?.length || 0}
      selectedCount={selectedCount}
      loading={loading}
      error={null}
      showKeyboardHelp={showKeyboardHelp}
    >
      <div
        className={cn(
          'h-[600px] relative',
          'rounded-xl overflow-hidden',
          'border border-border-light',
          'shadow-efir-sm'
        )}
      >
        {loading && (
          <div
            role="status"
            aria-live="polite"
            className="absolute inset-0 bg-paper/80 flex items-center justify-center z-10"
          >
            <div className="flex items-center gap-2 text-text-secondary font-body">
              <Loader2 className="h-5 w-5 animate-spin text-efir-gold-500" />
              <span>Loading data...</span>
            </div>
          </div>
        )}
        <AgGridReact
          {...props}
          rowData={rowData}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          pagination={props.pagination !== undefined ? props.pagination : true}
          paginationPageSize={props.paginationPageSize || 50}
          domLayout="normal"
          theme={themeQuartz}
          // Accessibility settings
          suppressCellFocus={false}
          ensureDomOrder={true}
          enableCellTextSelection={true}
          // Keyboard navigation - return false to use default behavior if null
          navigateToNextCell={(params) => params.nextCellPosition ?? params.previousCellPosition}
          tabToNextCell={(params) => params.nextCellPosition ?? false}
        />
      </div>
    </AccessibleGridWrapper>
  )
}
