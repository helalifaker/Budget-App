/**
 * VirtualizedTable Component
 *
 * A high-performance table using TanStack Table + TanStack Virtual for
 * rendering large datasets (1000+ rows) efficiently.
 *
 * Features:
 * - Virtual scrolling (only renders visible rows)
 * - Sorting with visual indicators
 * - Row selection (single/multi)
 * - Cell focus with keyboard navigation
 * - Sticky header
 * - Compact/default sizing
 * - Premium executive aesthetic
 *
 * Performance:
 * - Renders ~30 rows regardless of dataset size
 * - Smooth 60fps scrolling
 * - Low memory footprint
 *
 * @see BaseTable for non-virtualized version (datasets < 100 rows)
 */

import { useMemo, useRef, useCallback, useEffect, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type RowSelectionState,
  type Row,
} from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { cn } from '@/lib/utils'
import { useTableState } from './hooks/useTableState'

// ============================================================================
// Types
// ============================================================================

export interface VirtualizedTableProps<TData extends object> {
  /** Data to display */
  data: TData[]
  /** Column definitions */
  columns: ColumnDef<TData, unknown>[]
  /** Function to get unique row ID */
  getRowId: (row: TData) => string
  /** Enable row selection */
  enableRowSelection?: boolean
  /** Selection mode: 'single' or 'multi' */
  selectionMode?: 'single' | 'multi'
  /** Compact row height (36px vs 44px) */
  compact?: boolean
  /** Enable column sorting */
  enableSorting?: boolean
  /** Initial sorting state */
  initialSorting?: SortingState
  /** Callback when selection changes */
  onSelectionChange?: (selectedRows: TData[]) => void
  /** Callback when sorting changes */
  onSortingChange?: (sorting: SortingState) => void
  /** Loading state */
  isLoading?: boolean
  /** Empty state message */
  emptyMessage?: string
  /** Additional class names for container */
  className?: string
  /** Module color accent (finance=gold, enrollment=sage, etc.) */
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
  /** Fixed height for container (required for virtualization) */
  height?: number | string
  /** Overscan count - rows to render above/below viewport */
  overscan?: number
}

// ============================================================================
// Constants
// ============================================================================

const ROW_HEIGHT_COMPACT = 36
const ROW_HEIGHT_DEFAULT = 44
const HEADER_HEIGHT_COMPACT = 40
const HEADER_HEIGHT_DEFAULT = 48

// ============================================================================
// Component
// ============================================================================

export function VirtualizedTable<TData extends object>({
  data,
  columns,
  getRowId,
  enableRowSelection = false,
  selectionMode = 'multi',
  compact = true,
  enableSorting = true,
  initialSorting = [],
  onSelectionChange,
  onSortingChange,
  isLoading = false,
  emptyMessage = 'No data available',
  className,
  moduleColor = 'gold',
  height = 600,
  overscan = 5,
}: VirtualizedTableProps<TData>) {
  const parentRef = useRef<HTMLDivElement>(null)

  // Sorting state (uncontrolled by default)
  const [sorting, setSorting] = useState<SortingState>(initialSorting)

  // Row height based on compact mode
  const rowHeight = compact ? ROW_HEIGHT_COMPACT : ROW_HEIGHT_DEFAULT
  const headerHeight = compact ? HEADER_HEIGHT_COMPACT : HEADER_HEIGHT_DEFAULT

  // Table state management
  const { state, actions } = useTableState<TData>({
    getRowId,
    onSelectionChange: (selectedIds) => {
      if (onSelectionChange) {
        const selectedRows = data.filter((row) => selectedIds.includes(getRowId(row)))
        onSelectionChange(selectedRows)
      }
    },
  })

  // Convert our state to TanStack format
  const rowSelection: RowSelectionState = useMemo(() => {
    const selection: RowSelectionState = {}
    state.selectedRowIds.forEach((id) => {
      selection[id] = true
    })
    return selection
  }, [state.selectedRowIds])

  // TanStack Table instance
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      rowSelection,
    },
    getRowId: (row) => getRowId(row),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: getFilteredRowModel(),
    enableRowSelection,
    enableMultiRowSelection: selectionMode === 'multi',
    onRowSelectionChange: (updater) => {
      const newSelection = typeof updater === 'function' ? updater(rowSelection) : updater
      const selectedIds = Object.keys(newSelection).filter((id) => newSelection[id])
      actions.selectRows(selectedIds)
    },
    onSortingChange: (updater) => {
      setSorting((prev) => {
        const nextSorting = typeof updater === 'function' ? updater(prev) : updater
        onSortingChange?.(nextSorting)
        return nextSorting
      })
    },
  })

  const { rows } = table.getRowModel()

  // Compute pinned column offsets (for meta.pinned === 'left' | 'right')
  const visibleLeafColumns = table.getVisibleLeafColumns()
  const leftPinnedIds: string[] = []
  const rightPinnedIds: string[] = []

  visibleLeafColumns.forEach((col) => {
    const pinned = (col.columnDef.meta as { pinned?: 'left' | 'right' } | undefined)?.pinned
    if (pinned === 'left') leftPinnedIds.push(col.id)
    if (pinned === 'right') rightPinnedIds.push(col.id)
  })

  const leftPinnedOffsets = new Map<string, number>()
  {
    let offset = 0
    for (const id of leftPinnedIds) {
      const col = table.getColumn(id)
      leftPinnedOffsets.set(id, offset)
      offset += col?.getSize() ?? 0
    }
  }

  const rightPinnedOffsets = new Map<string, number>()
  {
    let offset = 0
    for (const id of [...rightPinnedIds].reverse()) {
      const col = table.getColumn(id)
      rightPinnedOffsets.set(id, offset)
      offset += col?.getSize() ?? 0
    }
  }

  const lastLeftPinnedId = leftPinnedIds[leftPinnedIds.length - 1]
  const firstRightPinnedId = rightPinnedIds[0]

  const getPinnedStyle = (
    columnId: string,
    opts: { isHeader: boolean }
  ): React.CSSProperties | undefined => {
    const left = leftPinnedOffsets.get(columnId)
    const right = rightPinnedOffsets.get(columnId)

    if (left === undefined && right === undefined) return undefined

    const style: React.CSSProperties = {
      position: 'sticky',
      zIndex: opts.isHeader ? 40 : 20,
    }

    if (left !== undefined) style.left = left
    if (right !== undefined) style.right = right

    if (columnId === lastLeftPinnedId) {
      style.boxShadow = '2px 0 4px rgba(0,0,0,0.06)'
    } else if (columnId === firstRightPinnedId) {
      style.boxShadow = '-2px 0 4px rgba(0,0,0,0.06)'
    }

    return style
  }

  // Virtualizer for rows
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan,
  })

  const virtualRows = rowVirtualizer.getVirtualItems()
  const totalSize = rowVirtualizer.getTotalSize()

  // Handle row click for selection
  const handleRowClick = useCallback(
    (row: Row<TData>, event: React.MouseEvent) => {
      if (!enableRowSelection) return

      if (selectionMode === 'single') {
        actions.selectRows([row.id])
      } else if (event.ctrlKey || event.metaKey) {
        actions.toggleRowSelection(row.id)
      } else if (event.shiftKey && state.focusedCell) {
        // Shift+click range selection
        const startIndex = rows.findIndex((r) => r.id === state.focusedCell?.rowId)
        const endIndex = rows.findIndex((r) => r.id === row.id)
        if (startIndex !== -1 && endIndex !== -1) {
          const [from, to] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex]
          const rangeIds = rows.slice(from, to + 1).map((r) => r.id)
          actions.selectRows(rangeIds)
        }
      } else {
        actions.selectRows([row.id])
      }

      // Update focus to first cell of clicked row
      const firstColumn = table.getVisibleLeafColumns()[0]
      if (firstColumn) {
        actions.setFocusedCell({ rowId: row.id, columnId: firstColumn.id })
      }
    },
    [enableRowSelection, selectionMode, actions, state.focusedCell, rows, table]
  )

  // Handle cell click for focus
  const handleCellClick = useCallback(
    (rowId: string, columnId: string) => {
      actions.setFocusedCell({ rowId, columnId })
    },
    [actions]
  )

  // Scroll to focused row when it changes
  useEffect(() => {
    if (state.focusedCell) {
      const rowIndex = rows.findIndex((r) => r.id === state.focusedCell?.rowId)
      if (rowIndex !== -1) {
        rowVirtualizer.scrollToIndex(rowIndex, { align: 'auto' })
      }
    }
  }, [state.focusedCell, rows, rowVirtualizer])

  // Get module-specific accent color
  const accentColorClass = {
    gold: 'border-l-[var(--color-gold)]',
    sage: 'border-l-[var(--color-sage)]',
    terracotta: 'border-l-[var(--color-terracotta)]',
    slate: 'border-l-[var(--color-slate)]',
    wine: 'border-l-[var(--color-wine)]',
    orange: 'border-l-orange-500',
    teal: 'border-l-teal-500',
    blue: 'border-l-blue-500',
    purple: 'border-l-purple-500',
  }[moduleColor]

  // Calculate padding for virtual scroll
  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0
  const paddingBottom =
    virtualRows.length > 0 ? totalSize - virtualRows[virtualRows.length - 1].end : 0

  return (
    <div
      className={cn(
        'relative rounded-lg border border-[var(--color-border-light)] bg-[var(--color-paper)] shadow-sm overflow-hidden flex flex-col',
        className
      )}
      style={{ height }}
    >
      {/* Scrollable container */}
      <div ref={parentRef} className="flex-1 overflow-auto">
        <table className="w-full border-collapse" style={{ minHeight: totalSize + headerHeight }}>
          {/* Sticky Header */}
          <thead
            className="sticky top-0 z-10 bg-[var(--color-paper)] shadow-[0_1px_2px_rgba(0,0,0,0.03)]"
            style={{ height: headerHeight }}
          >
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const isSorted = header.column.getIsSorted()
                  const canSort = header.column.getCanSort() && enableSorting
                  const pinnedStyle = getPinnedStyle(header.column.id, { isHeader: true })

                  return (
                    <th
                      key={header.id}
                      className={cn(
                        'border-b border-[var(--color-border-medium)] px-3 text-left text-[12px] font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]',
                        compact ? 'h-10' : 'h-12',
                        canSort && 'cursor-pointer select-none hover:bg-[var(--color-warm)]',
                        pinnedStyle && 'bg-[var(--color-paper)]'
                      )}
                      style={{
                        width: header.getSize(),
                        ...pinnedStyle,
                      }}
                      onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                    >
                      <div className="flex items-center gap-1">
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                        {canSort && (
                          <span className="ml-1 text-[var(--color-text-tertiary)]">
                            {isSorted === 'asc' ? (
                              <SortAscIcon />
                            ) : isSorted === 'desc' ? (
                              <SortDescIcon />
                            ) : (
                              <SortNoneIcon />
                            )}
                          </span>
                        )}
                      </div>
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>

          {/* Virtualized Body */}
          <tbody>
            {isLoading ? (
              // Loading skeleton
              Array.from({
                length: Math.min(
                  10,
                  Math.ceil((typeof height === 'number' ? height : 600) / rowHeight)
                ),
              }).map((_, i) => (
                <tr key={`skeleton-${i}`} style={{ height: rowHeight }}>
                  {table.getVisibleLeafColumns().map((column) => (
                    <td
                      key={column.id}
                      className="border-b border-[var(--color-border-light)] px-3"
                    >
                      <div className="h-4 w-3/4 animate-pulse rounded bg-[var(--color-muted)]" />
                    </td>
                  ))}
                </tr>
              ))
            ) : rows.length === 0 ? (
              // Empty state
              <tr>
                <td
                  colSpan={table.getVisibleLeafColumns().length}
                  className="h-32 text-center text-[var(--color-text-tertiary)]"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              <>
                {/* Top padding for virtual scroll */}
                {paddingTop > 0 && (
                  <tr>
                    <td
                      style={{ height: paddingTop }}
                      colSpan={table.getVisibleLeafColumns().length}
                    />
                  </tr>
                )}

                {/* Virtualized rows */}
                {virtualRows.map((virtualRow) => {
                  const row = rows[virtualRow.index]
                  const isSelected = state.selectedRowIds.has(row.id)

                  return (
                    <tr
                      key={row.id}
                      data-index={virtualRow.index}
                      ref={rowVirtualizer.measureElement}
                      onClick={(e) => handleRowClick(row, e)}
                      style={{ height: rowHeight }}
                      className={cn(
                        'transition-colors duration-150',
                        'bg-[var(--color-paper)]',
                        virtualRow.index % 2 === 1 && 'bg-[var(--color-subtle)]',
                        'hover:bg-[var(--color-warm)]',
                        isSelected && [
                          'bg-[var(--color-muted)]',
                          'border-l-[3px]',
                          accentColorClass,
                        ],
                        enableRowSelection && 'cursor-pointer'
                      )}
                    >
                      {row.getVisibleCells().map((cell) => {
                        const isFocused =
                          state.focusedCell?.rowId === row.id &&
                          state.focusedCell?.columnId === cell.column.id
                        const pinnedStyle = getPinnedStyle(cell.column.id, { isHeader: false })

                        return (
                          <td
                            key={cell.id}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCellClick(row.id, cell.column.id)
                            }}
                            className={cn(
                              'border-b border-[var(--color-border-light)] px-3 text-[13px] text-[var(--color-text-primary)]',
                              pinnedStyle && 'bg-inherit',
                              isFocused && [
                                'ring-2 ring-inset ring-[var(--color-gold)]',
                                'ring-offset-1',
                              ]
                            )}
                            style={pinnedStyle}
                          >
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}

                {/* Bottom padding for virtual scroll */}
                {paddingBottom > 0 && (
                  <tr>
                    <td
                      style={{ height: paddingBottom }}
                      colSpan={table.getVisibleLeafColumns().length}
                    />
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>
      </div>

      {/* Row count footer */}
      {!isLoading && rows.length > 0 && (
        <div className="flex items-center justify-between border-t border-[var(--color-border-light)] bg-[var(--color-subtle)] px-3 py-2 text-[12px] text-[var(--color-text-secondary)]">
          <span>
            {enableRowSelection && state.selectedRowIds.size > 0
              ? `${state.selectedRowIds.size} of ${rows.length} row(s) selected`
              : `${rows.length} row(s)`}
          </span>
          <span className="text-[var(--color-text-tertiary)]">
            Showing {virtualRows.length} of {rows.length}
          </span>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Sort Icons
// ============================================================================

function SortAscIcon() {
  return (
    <svg
      className="h-4 w-4 transition-transform duration-200"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
    </svg>
  )
}

function SortDescIcon() {
  return (
    <svg
      className="h-4 w-4 transition-transform duration-200"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  )
}

function SortNoneIcon() {
  return (
    <svg
      className="h-4 w-4 opacity-30"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
      />
    </svg>
  )
}
