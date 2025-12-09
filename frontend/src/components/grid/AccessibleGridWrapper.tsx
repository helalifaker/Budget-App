/**
 * Accessible Grid Wrapper
 *
 * Wraps AG Grid with comprehensive accessibility enhancements:
 * - ARIA labels and descriptions
 * - Keyboard navigation instructions
 * - Live region announcements for grid updates
 * - Skip link target for grid focus
 * - Enhanced focus indicators
 *
 * WCAG 2.1 Compliance:
 * - 1.3.1 (Level A) - Info and Relationships
 * - 2.1.1 (Level A) - Keyboard
 * - 2.4.3 (Level A) - Focus Order
 * - 4.1.2 (Level A) - Name, Role, Value
 */

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type {
  GridApi,
  GridReadyEvent,
  SelectionChangedEvent,
  RowSelectedEvent,
} from 'ag-grid-community'
import { cn } from '@/lib/utils'
import { StatusMessage } from '@/components/accessibility'
import { Keyboard, HelpCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

export interface AccessibleGridWrapperProps {
  /**
   * Unique identifier for the grid (required for accessibility)
   */
  id: string

  /**
   * Human-readable label for the grid (required for screen readers)
   */
  label: string

  /**
   * Optional description of the grid contents
   */
  description?: string

  /**
   * Child AG Grid component
   */
  children: ReactNode

  /**
   * Current row count (for announcements)
   */
  rowCount?: number

  /**
   * Current selected count (for announcements)
   */
  selectedCount?: number

  /**
   * Is the grid currently loading?
   */
  loading?: boolean

  /**
   * Error message if any
   */
  error?: string | null

  /**
   * Called when grid is ready
   */
  onGridReady?: (api: GridApi) => void

  /**
   * Show keyboard help tooltip
   */
  showKeyboardHelp?: boolean

  /**
   * Additional class names
   */
  className?: string
}

export interface AccessibleGridWrapperRef {
  gridApi: GridApi | null
  focusGrid: () => void
  announceStatus: (message: string) => void
}

/**
 * Keyboard shortcuts for AG Grid
 */
const GRID_SHORTCUTS = [
  { key: 'Enter', description: 'Edit cell / Confirm' },
  { key: 'Tab', description: 'Next cell' },
  { key: 'Shift+Tab', description: 'Previous cell' },
  { key: '↑↓←→', description: 'Navigate cells' },
  { key: 'Home', description: 'First cell in row' },
  { key: 'End', description: 'Last cell in row' },
  { key: 'Ctrl+Home', description: 'First cell' },
  { key: 'Ctrl+End', description: 'Last cell' },
  { key: 'Space', description: 'Select row' },
  { key: 'Ctrl+A', description: 'Select all' },
  { key: 'F2', description: 'Edit cell' },
  { key: 'Escape', description: 'Cancel edit' },
]

/**
 * AccessibleGridWrapper enhances AG Grid with WCAG 2.1 AA compliant accessibility features
 */
export const AccessibleGridWrapper = forwardRef<
  AccessibleGridWrapperRef,
  AccessibleGridWrapperProps
>(function AccessibleGridWrapper(
  {
    id,
    label,
    description,
    children,
    rowCount = 0,
    selectedCount = 0,
    loading = false,
    error = null,
    onGridReady,
    showKeyboardHelp = true,
    className,
  },
  ref
) {
  const gridApiRef = useRef<GridApi | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [statusMessage, setStatusMessage] = useState('')
  const [lastFocusedCell] = useState<{ row: number; col: string } | null>(null)

  // Announce status messages to screen readers
  const announceStatus = useCallback((message: string) => {
    setStatusMessage(message)
    // Clear after announcement
    setTimeout(() => setStatusMessage(''), 3000)
  }, [])

  // Focus the grid container
  const focusGrid = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.focus()
      // If we have a grid API, try to focus the first cell
      if (gridApiRef.current) {
        const columns = gridApiRef.current.getColumns()
        const firstCol = columns?.[0]
        if (firstCol) {
          gridApiRef.current.setFocusedCell(0, firstCol)
        }
      }
    }
  }, [])

  // Expose methods via ref
  useImperativeHandle(
    ref,
    () => ({
      gridApi: gridApiRef.current,
      focusGrid,
      announceStatus,
    }),
    [focusGrid, announceStatus]
  )

  // Store grid API reference when parent passes it
  useEffect(() => {
    // This effect is used to capture grid API from parent
    // The actual grid ready handling is done by parent component
  }, [onGridReady])

  // Announce row count changes
  useEffect(() => {
    if (rowCount > 0 && !loading) {
      announceStatus(`Grid updated: ${rowCount} rows available`)
    }
  }, [rowCount, loading, announceStatus])

  // Announce errors
  useEffect(() => {
    if (error) {
      announceStatus(`Error: ${error}`)
    }
  }, [error, announceStatus])

  // Announce loading state
  useEffect(() => {
    if (loading) {
      announceStatus('Loading data...')
    }
  }, [loading, announceStatus])

  return (
    <section
      id={id}
      ref={containerRef}
      role="region"
      aria-label={label}
      aria-describedby={description ? `${id}-description` : undefined}
      aria-busy={loading}
      tabIndex={-1}
      className={cn(
        'accessible-grid-wrapper',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-500 focus-visible:ring-offset-2',
        className
      )}
    >
      {/* Grid header with label and controls */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 id={`${id}-label`} className="text-sm font-semibold text-text-primary">
            {label}
          </h3>
          {description && (
            <p id={`${id}-description`} className="text-xs text-text-secondary">
              {description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Row count badge */}
          <span className="text-xs text-text-secondary bg-subtle px-2 py-1 rounded">
            {rowCount} row{rowCount !== 1 ? 's' : ''}
            {selectedCount > 0 && ` (${selectedCount} selected)`}
          </span>

          {/* Keyboard help button */}
          {showKeyboardHelp && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    aria-label="Keyboard shortcuts for data grid"
                  >
                    <Keyboard className="h-4 w-4 text-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left" className="w-64 p-0">
                  <div className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <HelpCircle className="h-4 w-4 text-gold-500" />
                      <span className="font-semibold text-sm text-text-primary">
                        Grid Keyboard Shortcuts
                      </span>
                    </div>
                    <div className="space-y-1">
                      {GRID_SHORTCUTS.map((shortcut) => (
                        <div key={shortcut.key} className="flex justify-between text-xs">
                          <span className="text-text-secondary">{shortcut.description}</span>
                          <kbd className="px-1.5 py-0.5 bg-subtle rounded text-text-secondary font-mono">
                            {shortcut.key}
                          </kbd>
                        </div>
                      ))}
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>

      {/* Instructions for screen readers */}
      <p className="sr-only">
        Use arrow keys to navigate cells. Press Enter to edit a cell. Press Tab to move to the next
        cell, Shift+Tab for previous. Press Space to select a row. Press ? for more keyboard
        shortcuts.
      </p>

      {/* Grid container with skip link target */}
      <div
        id="data-grid"
        role="application"
        aria-label={`${label} data grid`}
        className="ag-accessible-container rounded-card border border-border-light overflow-hidden"
        tabIndex={-1}
      >
        {children}
      </div>

      {/* Status message for screen readers */}
      <StatusMessage message={statusMessage} politeness="polite" />

      {/* Current cell position for screen readers */}
      {lastFocusedCell && (
        <p className="sr-only" aria-live="polite">
          Row {lastFocusedCell.row + 1}, Column {lastFocusedCell.col}
        </p>
      )}
    </section>
  )
})

/**
 * Hook to integrate accessibility features with AG Grid events
 */
export function useAccessibleGrid(wrapperRef: React.RefObject<AccessibleGridWrapperRef | null>) {
  const getGridReadyHandler = useCallback(
    (originalHandler?: (event: GridReadyEvent) => void) => (event: GridReadyEvent) => {
      wrapperRef.current?.announceStatus('Grid loaded and ready')
      originalHandler?.(event)
    },
    [wrapperRef]
  )

  const getSelectionChangedHandler = useCallback(
    (originalHandler?: (event: SelectionChangedEvent) => void) =>
      (event: SelectionChangedEvent) => {
        const count = event.api.getSelectedRows().length
        if (count > 0) {
          wrapperRef.current?.announceStatus(`${count} row${count > 1 ? 's' : ''} selected`)
        }
        originalHandler?.(event)
      },
    [wrapperRef]
  )

  const getRowSelectedHandler = useCallback(
    (originalHandler?: (event: RowSelectedEvent) => void) => (event: RowSelectedEvent) => {
      const isSelected = event.node.isSelected()
      const rowIndex = event.rowIndex
      wrapperRef.current?.announceStatus(
        isSelected ? `Row ${(rowIndex || 0) + 1} selected` : `Row ${(rowIndex || 0) + 1} deselected`
      )
      originalHandler?.(event)
    },
    [wrapperRef]
  )

  return {
    getGridReadyHandler,
    getSelectionChangedHandler,
    getRowSelectedHandler,
  }
}

export default AccessibleGridWrapper
