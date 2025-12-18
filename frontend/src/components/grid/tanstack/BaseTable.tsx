/**
 * BaseTable Component
 *
 * A foundational read-only table component using TanStack Table with
 * EFIR design system styling. This is the base for all TanStack tables.
 *
 * Features:
 * - Sorting with visual indicators
 * - Row selection (single/multi)
 * - Cell focus with keyboard navigation
 * - Sticky header
 * - Compact/default sizing
 * - Premium executive aesthetic
 *
 * @see VirtualizedTable for large dataset support
 * @see EditableTable for editable cells
 */

import { useMemo, useRef, useCallback, useState } from 'react'
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
import { cn } from '@/lib/utils'
import { useTableState } from './hooks/useTableState'

// ============================================================================
// Types
// ============================================================================

export interface BaseTableProps<TData extends object> {
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
}

// ============================================================================
// Component
// ============================================================================

export function BaseTable<TData extends object>({
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
}: BaseTableProps<TData>) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Sorting state (uncontrolled by default)
  const [sorting, setSorting] = useState<SortingState>(initialSorting)

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
        const rows = table.getRowModel().rows
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
    [enableRowSelection, selectionMode, actions, state.focusedCell, table]
  )

  // Handle cell click for focus
  const handleCellClick = useCallback(
    (rowId: string, columnId: string) => {
      actions.setFocusedCell({ rowId, columnId })
    },
    [actions]
  )

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

  const rows = table.getRowModel().rows

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative rounded-lg border border-[var(--color-border-light)] bg-[var(--color-paper)] shadow-sm overflow-hidden',
        className
      )}
    >
      {/* Table container with scroll */}
      <div className="overflow-auto">
        <table className="w-full border-collapse">
          {/* Header */}
          <thead className="sticky top-0 z-10 bg-[var(--color-paper)] shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
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

          {/* Body */}
          <tbody>
            {isLoading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={`skeleton-${i}`}>
                  {table.getVisibleLeafColumns().map((column) => (
                    <td
                      key={column.id}
                      className={cn(
                        'border-b border-[var(--color-border-light)] px-3',
                        compact ? 'h-9' : 'h-11'
                      )}
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
              // Data rows
              rows.map((row, rowIndex) => {
                const isSelected = state.selectedRowIds.has(row.id)

                return (
                  <tr
                    key={row.id}
                    onClick={(e) => handleRowClick(row, e)}
                    className={cn(
                      'transition-colors duration-150',
                      'bg-[var(--color-paper)]',
                      rowIndex % 2 === 1 && 'bg-[var(--color-subtle)]',
                      'hover:bg-[var(--color-warm)]',
                      isSelected && ['bg-[var(--color-muted)]', 'border-l-[3px]', accentColorClass],
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
                            compact ? 'h-9' : 'h-11',
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
              })
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
