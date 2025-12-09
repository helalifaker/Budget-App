/**
 * ExcelStatusBar Component
 *
 * A status bar that mimics Excel's behavior, showing:
 * - Number of selected cells/rows
 * - Sum, Average, Min, Max of numeric values
 * - Count of numeric cells
 *
 * This provides users with instant feedback about their selection,
 * just like in Microsoft Excel or Google Sheets.
 */

import { cn } from '@/lib/utils'
import type { SelectionInfo } from '@/hooks/useExcelKeyboard'

interface ExcelStatusBarProps {
  /** Selection statistics */
  selectionInfo: SelectionInfo
  /** Additional CSS classes */
  className?: string
  /** Show keyboard shortcuts hint */
  showShortcuts?: boolean
}

/**
 * Format a number for display
 */
function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return '—'

  // Format with commas and up to 2 decimal places
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value)
}

export function ExcelStatusBar({
  selectionInfo,
  className,
  showShortcuts = false,
}: ExcelStatusBarProps) {
  const { cellCount, rowCount, sum, average, min, max, numericCount } = selectionInfo
  const hasSelection = cellCount > 0

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Selection statistics"
      className={cn(
        'flex items-center justify-between px-4 py-2',
        'bg-gradient-to-r from-sand-50 to-cream-50',
        'border-t border-border-light',
        'text-xs font-mono',
        className
      )}
    >
      {/* Left side: Selection info */}
      <div className="flex items-center gap-4">
        {hasSelection ? (
          <>
            {/* Cell/Row count */}
            <div className="flex items-center gap-1.5">
              <span className="text-text-tertiary">Selected:</span>
              <span className="font-medium text-text-primary">
                {rowCount} row{rowCount !== 1 ? 's' : ''}
                {cellCount > rowCount && ` (${cellCount} cells)`}
              </span>
            </div>

            {/* Numeric statistics */}
            {numericCount > 0 && (
              <>
                <div className="h-3 w-px bg-subtle" aria-hidden="true" />

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <span className="text-text-tertiary">Sum:</span>
                    <span className="font-medium text-text-primary">{formatNumber(sum)}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className="text-text-tertiary">Avg:</span>
                    <span className="font-medium text-text-primary">{formatNumber(average)}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className="text-text-tertiary">Min:</span>
                    <span className="font-medium text-text-primary">{formatNumber(min)}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className="text-text-tertiary">Max:</span>
                    <span className="font-medium text-text-primary">{formatNumber(max)}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className="text-text-tertiary">Count:</span>
                    <span className="font-medium text-text-primary">{numericCount}</span>
                  </div>
                </div>
              </>
            )}
          </>
        ) : (
          <span className="text-text-tertiary italic">No selection</span>
        )}
      </div>

      {/* Right side: Keyboard shortcuts hint */}
      {showShortcuts && (
        <div className="flex items-center gap-3 text-text-tertiary">
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-border-light text-[10px]">
            Ctrl+C
          </kbd>
          <span>Copy</span>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-border-light text-[10px]">
            Ctrl+V
          </kbd>
          <span>Paste</span>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-border-light text-[10px]">
            F2
          </kbd>
          <span>Edit</span>
        </div>
      )}
    </div>
  )
}
