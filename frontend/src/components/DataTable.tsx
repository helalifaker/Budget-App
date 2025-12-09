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
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

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
    return (
      <div
        role="alert"
        aria-live="assertive"
        className={cn(
          'flex items-center justify-center h-64',
          'bg-paper rounded-xl',
          'border border-[#E8E6E1]',
          'shadow-efir-sm'
        )}
      >
        <div className="text-center">
          <p className="text-terracotta-600 font-body font-medium">Error loading data</p>
          <p className="text-sm font-body text-text-secondary mt-1">{error.message}</p>
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
          'border border-[#E8E6E1]',
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
