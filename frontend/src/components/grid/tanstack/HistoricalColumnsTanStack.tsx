/**
 * Historical Columns for TanStack Table
 *
 * Factory functions for creating TanStack Table column definitions
 * that display historical comparison data.
 *
 * Port of HistoricalColumns.tsx from AG Grid to TanStack Table.
 */

import type { ColumnDef, CellContext } from '@tanstack/react-table'
import type { HistoricalComparison } from '@/types/historical'
import {
  formatPercentageChange,
  formatAbsoluteChange,
  getPercentageVariant,
} from '@/types/historical'

/**
 * Column width constants
 */
const COLUMN_WIDTHS = {
  historical: 100,
  current: 120,
  percentage: 90,
} as const

/**
 * Get CSS class for percentage change based on variant
 */
export function getPercentageClass(pct: number | null): string {
  const variant = getPercentageVariant(pct)
  switch (variant) {
    case 'positive':
      return 'text-success-600 font-medium'
    case 'negative':
      return 'text-error-600 font-medium'
    default:
      return 'text-sand-500'
  }
}

/**
 * Get arrow character for percentage change
 */
export function getPercentageArrow(pct: number | string | null | undefined): string {
  const numeric =
    pct === null || pct === undefined ? null : typeof pct === 'number' ? pct : Number(pct)

  if (numeric === null || Number.isNaN(numeric)) return ''
  if (numeric > 0) return '↑ '
  if (numeric < 0) return '↓ '
  return ''
}

/**
 * Options for historical column creation
 */
interface HistoricalColumnOptions {
  /** Field name for the historical comparison data */
  historyField: string
  /** Current fiscal year */
  currentFiscalYear: number
  /** Whether values are currency amounts */
  isCurrency?: boolean
  /** Base column width */
  columnWidth?: number
  /** Whether to show absolute change columns */
  showAbsoluteChange?: boolean
}

/**
 * Type for rows with historical data
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RowWithHistory = Record<string, any> & {
  history?: HistoricalComparison | null
}

/**
 * Create historical columns for TanStack Table
 *
 * Returns an array of column definitions:
 * - N-2 Actual
 * - N-1 Actual
 * - vs N-1 %
 * - vs N-2 %
 */
export function createHistoricalColumnsTanStack<TData extends RowWithHistory>(
  options: HistoricalColumnOptions
): ColumnDef<TData, unknown>[] {
  const {
    historyField,
    currentFiscalYear,
    isCurrency = false,
    columnWidth = COLUMN_WIDTHS.historical,
    showAbsoluteChange = false,
  } = options

  const n1Year = currentFiscalYear - 1
  const n2Year = currentFiscalYear - 2

  const columns: ColumnDef<TData, unknown>[] = [
    // N-2 Actual column
    {
      id: `${historyField}_n_minus_2`,
      header: `FY${n2Year} Actual`,
      size: columnWidth,
      meta: {
        editable: false,
        align: 'right' as const,
      },
      accessorFn: (row) => {
        const history = row[historyField] as HistoricalComparison | undefined
        return history?.n_minus_2?.value ?? null
      },
      cell: (info: CellContext<TData, unknown>) => {
        const row = info.row.original
        const history = row[historyField] as HistoricalComparison | undefined
        if (!history?.n_minus_2?.value) return <span className="text-sand-400">N/A</span>
        if (isCurrency) {
          return (
            <span className="text-sand-600 bg-subtle px-2 py-1 rounded">
              {history.n_minus_2.value.toLocaleString('en-SA', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
            </span>
          )
        }
        return (
          <span className="text-sand-600 bg-subtle px-2 py-1 rounded">
            {history.n_minus_2.value.toLocaleString()}
          </span>
        )
      },
    },
    // N-1 Actual column
    {
      id: `${historyField}_n_minus_1`,
      header: `FY${n1Year} Actual`,
      size: columnWidth,
      meta: {
        editable: false,
        align: 'right' as const,
      },
      accessorFn: (row) => {
        const history = row[historyField] as HistoricalComparison | undefined
        return history?.n_minus_1?.value ?? null
      },
      cell: (info: CellContext<TData, unknown>) => {
        const row = info.row.original
        const history = row[historyField] as HistoricalComparison | undefined
        if (!history?.n_minus_1?.value) return <span className="text-sand-400">N/A</span>
        if (isCurrency) {
          return (
            <span className="text-sand-600 bg-subtle px-2 py-1 rounded">
              {history.n_minus_1.value.toLocaleString('en-SA', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
            </span>
          )
        }
        return (
          <span className="text-sand-600 bg-subtle px-2 py-1 rounded">
            {history.n_minus_1.value.toLocaleString()}
          </span>
        )
      },
    },
    // vs N-1 percentage column
    {
      id: `${historyField}_vs_n_minus_1_pct`,
      header: `vs ${n1Year}`,
      size: COLUMN_WIDTHS.percentage,
      meta: {
        editable: false,
        align: 'right' as const,
      },
      accessorFn: (row) => {
        const history = row[historyField] as HistoricalComparison | undefined
        return history?.vs_n_minus_1_pct ?? null
      },
      cell: (info: CellContext<TData, unknown>) => {
        const row = info.row.original
        const history = row[historyField] as HistoricalComparison | undefined
        const pct = history?.vs_n_minus_1_pct ?? null
        const arrow = getPercentageArrow(pct)
        const formatted = formatPercentageChange(pct)
        const className = getPercentageClass(pct)
        return (
          <span className={className}>
            {arrow}
            {formatted}
          </span>
        )
      },
    },
    // vs N-2 percentage column
    {
      id: `${historyField}_vs_n_minus_2_pct`,
      header: `vs ${n2Year}`,
      size: COLUMN_WIDTHS.percentage,
      meta: {
        editable: false,
        align: 'right' as const,
      },
      accessorFn: (row) => {
        const history = row[historyField] as HistoricalComparison | undefined
        return history?.vs_n_minus_2_pct ?? null
      },
      cell: (info: CellContext<TData, unknown>) => {
        const row = info.row.original
        const history = row[historyField] as HistoricalComparison | undefined
        const pct = history?.vs_n_minus_2_pct ?? null
        const arrow = getPercentageArrow(pct)
        const formatted = formatPercentageChange(pct)
        const className = getPercentageClass(pct)
        return (
          <span className={className}>
            {arrow}
            {formatted}
          </span>
        )
      },
    },
  ]

  // Optionally add absolute change columns
  if (showAbsoluteChange) {
    columns.splice(2, 0, {
      id: `${historyField}_vs_n_minus_1_abs`,
      header: `Δ ${n1Year}`,
      size: columnWidth,
      meta: {
        editable: false,
        align: 'right' as const,
      },
      accessorFn: (row) => {
        const history = row[historyField] as HistoricalComparison | undefined
        return history?.vs_n_minus_1_abs ?? null
      },
      cell: (info: CellContext<TData, unknown>) => {
        const row = info.row.original
        const history = row[historyField] as HistoricalComparison | undefined
        return formatAbsoluteChange(history?.vs_n_minus_1_abs ?? null, isCurrency)
      },
    })
  }

  return columns
}
