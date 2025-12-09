/**
 * ExcelDataTable Component
 *
 * A premium AG Grid wrapper that provides a true Excel-like experience:
 *
 * ## Features
 * - **Full Clipboard Support**: Ctrl+C/V for copy/paste, compatible with Excel
 * - **Multi-row Selection**: Click to select, Ctrl+Click for multiple, Shift+Click for range
 * - **Keyboard Navigation**: Tab, Enter, Arrow keys navigate like Excel
 * - **Edit on Type**: Start typing to edit cell content directly
 * - **Undo/Redo**: Built-in undo stack with Ctrl+Z/Y
 * - **Fill Down**: Ctrl+D fills selected rows with first row's values
 * - **Status Bar**: Shows Sum, Average, Count of selected numeric cells
 * - **Delete Key**: Clear selected cells with Delete/Backspace
 * - **Context Menu**: Right-click menu with copy/paste options
 *
 * ## Keyboard Shortcuts
 * | Shortcut | Action |
 * |----------|--------|
 * | Ctrl+C | Copy selection |
 * | Ctrl+V | Paste from clipboard |
 * | Ctrl+Z | Undo |
 * | Ctrl+Y | Redo |
 * | Ctrl+A | Select all rows |
 * | Ctrl+D | Fill down |
 * | Tab | Next cell |
 * | Shift+Tab | Previous cell |
 * | Enter | Next row / Finish edit |
 * | F2 | Edit current cell |
 * | Delete | Clear selected cells |
 * | Escape | Cancel edit / Deselect |
 *
 * @example
 * ```tsx
 * <ExcelDataTable
 *   rowData={data}
 *   columnDefs={columns}
 *   onCellValueChanged={(e) => handleSave(e)}
 * />
 * ```
 */

import { AgGridReact, type AgGridReactProps } from 'ag-grid-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import type {
  GridReadyEvent,
  GridApi,
  GetContextMenuItems,
  GetRowIdParams,
} from 'ag-grid-community'
import { themeQuartz } from 'ag-grid-community'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useExcelKeyboard, type ClearedCell, type FilledCell } from '@/hooks/useExcelKeyboard'
import { useCustomClipboard } from '@/hooks/useCustomClipboard'
import { ExcelStatusBar } from './ExcelStatusBar'

export interface ExcelDataTableProps<TData = unknown> extends Omit<
  AgGridReactProps<TData>,
  'theme'
> {
  /** Unique identifier for the table */
  tableId?: string
  /** Label for accessibility */
  tableLabel?: string
  /** Show loading overlay */
  loading?: boolean
  /** Error state */
  error?: Error | null
  /** Show the Excel-like status bar */
  showStatusBar?: boolean
  /** Show keyboard shortcuts in status bar */
  showShortcuts?: boolean
  /** Custom height (default: 600px) */
  height?: string | number
  /** Callback when cells are cleared via Delete key */
  onCellsCleared?: (cells: ClearedCell[]) => void
  /** Callback when cells are filled via Ctrl+D */
  onCellsFilled?: (cells: FilledCell[]) => void
  /** Callback when paste occurs */
  onPaste?: (
    updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
  ) => Promise<void>
  /** Enable row selection (default: true) */
  enableSelection?: boolean
  /** Get row ID for clipboard operations - receives the row data and returns the ID string */
  rowIdGetter?: (data: TData) => string
}

export function ExcelDataTable<TData = unknown>({
  tableId = 'excel-table',
  tableLabel = 'Data table',
  loading = false,
  error = null,
  showStatusBar = true,
  showShortcuts = true,
  height = 600,
  onCellsCleared,
  onCellsFilled,
  onPaste,
  enableSelection = true,
  rowIdGetter,
  rowData,
  columnDefs,
  defaultColDef: userDefaultColDef,
  ...props
}: ExcelDataTableProps<TData>) {
  const gridRef = useRef<AgGridReact<TData>>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [gridApi, setGridApi] = useState<GridApi<TData> | null>(null)

  /**
   * Default paste handler if none provided
   */
  const handlePasteCells = useCallback(
    async (
      updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
    ) => {
      if (onPaste) {
        await onPaste(updates)
      } else {
        // Default: just update the grid directly
        if (!gridApi) return

        updates.forEach(({ rowId, field, newValue }) => {
          const rowNode = gridApi.getRowNode(rowId)
          if (rowNode) {
            rowNode.setDataValue(field, newValue)
          }
        })
      }
    },
    [gridApi, onPaste]
  )

  /**
   * Custom clipboard hook for paste operations
   */
  const { handlePaste } = useCustomClipboard({
    gridApi: gridApi as GridApi | null,
    onPasteCells: handlePasteCells,
  })

  /**
   * Excel keyboard shortcuts hook
   */
  const { selectionInfo, copyToClipboard, clearSelectedCells, fillDown } = useExcelKeyboard({
    gridApi: gridApi as GridApi | null,
    enableEditing: true,
    onCellsCleared,
    onCellsFilled,
    containerRef,
  })

  /**
   * Grid ready handler - store API reference
   */
  const onGridReady = useCallback(
    (event: GridReadyEvent<TData>) => {
      setGridApi(event.api)

      // Call user's onGridReady if provided
      if (props.onGridReady) {
        props.onGridReady(event)
      }
    },
    [props]
  )

  /**
   * Context menu with Excel-like options
   */
  const getContextMenuItems: GetContextMenuItems<TData> = useCallback(() => {
    return [
      {
        name: 'Copy',
        shortcut: 'Ctrl+C',
        action: () => copyToClipboard(),
        icon: '<span style="font-size: 14px;">📋</span>',
      },
      {
        name: 'Paste',
        shortcut: 'Ctrl+V',
        action: () => {
          // Paste is handled by the container's paste event
          // This is just for visual consistency
        },
        icon: '<span style="font-size: 14px;">📄</span>',
      },
      'separator',
      {
        name: 'Clear Contents',
        shortcut: 'Delete',
        action: () => clearSelectedCells(),
        icon: '<span style="font-size: 14px;">🗑️</span>',
      },
      {
        name: 'Fill Down',
        shortcut: 'Ctrl+D',
        action: () => fillDown(),
        icon: '<span style="font-size: 14px;">⬇️</span>',
      },
      'separator',
      'copy',
      'copyWithHeaders',
      'separator',
      'export',
    ]
  }, [copyToClipboard, clearSelectedCells, fillDown])

  /**
   * Enhanced default column definitions for Excel-like behavior
   */
  const defaultColDef = useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      editable: true,
      // Allow keyboard events to bubble for our handlers
      suppressKeyboardEvent: () => false,
      // Cell style for Excel-like appearance
      cellStyle: {
        borderRight: '1px solid #e5e5e5',
      },
      // Merge with user-provided defaults
      ...userDefaultColDef,
    }),
    [userDefaultColDef]
  )

  /**
   * Row ID getter for clipboard operations
   */
  const getRowIdCallback = useCallback(
    (params: GetRowIdParams<TData>) => {
      if (rowIdGetter) {
        return rowIdGetter(params.data)
      }
      // Default: look for 'id' property
      const data = params.data as Record<string, unknown>
      return String(data.id ?? data._id ?? Math.random())
    },
    [rowIdGetter]
  )

  // Error state
  if (error) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="flex items-center justify-center h-64 bg-white rounded-lg border border-border-light"
      >
        <div className="text-center">
          <p className="text-error-600 font-medium">Error loading data</p>
          <p className="text-sm text-text-secondary mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      id={tableId}
      role="application"
      aria-label={tableLabel}
      tabIndex={0}
      onPaste={handlePaste}
      className={cn(
        'flex flex-col rounded-lg overflow-hidden',
        'border border-border-light',
        'bg-white',
        'shadow-sm',
        // Excel-like styling
        'excel-table',
        // Focus visible for accessibility
        'focus-visible:ring-2 focus-visible:ring-gold-500 focus-visible:ring-offset-2'
      )}
    >
      {/* Grid container */}
      <div
        className="relative flex-1"
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
      >
        {/* Loading overlay */}
        {loading && (
          <div
            role="status"
            aria-live="polite"
            className="absolute inset-0 bg-white/80 flex items-center justify-center z-10"
          >
            <div className="flex items-center gap-2 text-text-secondary">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Loading data...</span>
            </div>
          </div>
        )}

        {/* AG Grid */}
        <AgGridReact
          ref={gridRef}
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          getContextMenuItems={getContextMenuItems}
          theme={themeQuartz}
          // Excel-like behavior
          rowSelection={enableSelection ? { mode: 'multiRow' } : undefined}
          suppressRowClickSelection={false}
          suppressCellFocus={false}
          ensureDomOrder={true}
          animateRows={true}
          // Clipboard support
          enableCellTextSelection={true}
          // Undo/Redo
          undoRedoCellEditing={true}
          undoRedoCellEditingLimit={50}
          // Navigation
          enterNavigatesVertically={true}
          enterNavigatesVerticallyAfterEdit={true}
          tabToNextCell={(params) => params.nextCellPosition ?? false}
          // Row ID for operations
          getRowId={getRowIdCallback}
          // Pagination (can be overridden)
          pagination={props.pagination !== undefined ? props.pagination : true}
          paginationPageSize={props.paginationPageSize ?? 50}
          paginationPageSizeSelector={props.paginationPageSizeSelector ?? [25, 50, 100, 200]}
          // Layout
          domLayout="normal"
          // Pass remaining props
          {...props}
        />
      </div>

      {/* Excel-like status bar */}
      {showStatusBar && (
        <ExcelStatusBar selectionInfo={selectionInfo} showShortcuts={showShortcuts} />
      )}
    </div>
  )
}
