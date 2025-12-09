/**
 * Historical Columns Component
 *
 * Factory functions for creating AG Grid column definitions
 * that display historical comparison data.
 */

import { ColDef, ColGroupDef, ValueFormatterParams } from 'ag-grid-community'
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
export function getPercentageArrow(pct: number | null): string {
  if (pct === null) return ''
  if (pct > 0) return '↑ '
  if (pct < 0) return '↓ '
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
 * Create historical columns for a data field
 *
 * Returns an array of column definitions:
 * - N-2 Actual
 * - N-1 Actual
 * - vs N-1 %
 * - vs N-2 %
 */
export function createHistoricalColumns(options: HistoricalColumnOptions): ColDef[] {
  const {
    historyField,
    currentFiscalYear,
    isCurrency = false,
    columnWidth = COLUMN_WIDTHS.historical,
    showAbsoluteChange = false,
  } = options

  const n1Year = currentFiscalYear - 1
  const n2Year = currentFiscalYear - 2

  const columns: ColDef[] = [
    // N-2 Actual column
    {
      field: `${historyField}.n_minus_2.value`,
      headerName: `FY${n2Year} Actual`,
      width: columnWidth,
      headerClass: 'ag-header-historical',
      cellClass: 'ag-cell-historical bg-subtle',
      editable: false,
      valueFormatter: (params: ValueFormatterParams) => {
        const history = params.data?.[historyField] as HistoricalComparison | undefined
        if (!history?.n_minus_2?.value) return 'N/A'
        if (isCurrency) {
          return history.n_minus_2.value.toLocaleString('en-SA', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          })
        }
        return history.n_minus_2.value.toLocaleString()
      },
    },
    // N-1 Actual column
    {
      field: `${historyField}.n_minus_1.value`,
      headerName: `FY${n1Year} Actual`,
      width: columnWidth,
      headerClass: 'ag-header-historical',
      cellClass: 'ag-cell-historical bg-subtle',
      editable: false,
      valueFormatter: (params: ValueFormatterParams) => {
        const history = params.data?.[historyField] as HistoricalComparison | undefined
        if (!history?.n_minus_1?.value) return 'N/A'
        if (isCurrency) {
          return history.n_minus_1.value.toLocaleString('en-SA', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          })
        }
        return history.n_minus_1.value.toLocaleString()
      },
    },
    // vs N-1 percentage column
    {
      field: `${historyField}.vs_n_minus_1_pct`,
      headerName: `vs ${n1Year}`,
      width: COLUMN_WIDTHS.percentage,
      headerClass: 'ag-header-change',
      editable: false,
      cellRenderer: (params: ValueFormatterParams) => {
        const history = params.data?.[historyField] as HistoricalComparison | undefined
        const pct = history?.vs_n_minus_1_pct ?? null
        const arrow = getPercentageArrow(pct)
        const formatted = formatPercentageChange(pct)
        const className = getPercentageClass(pct)
        return `<span class="${className}">${arrow}${formatted}</span>`
      },
    },
    // vs N-2 percentage column
    {
      field: `${historyField}.vs_n_minus_2_pct`,
      headerName: `vs ${n2Year}`,
      width: COLUMN_WIDTHS.percentage,
      headerClass: 'ag-header-change',
      editable: false,
      cellRenderer: (params: ValueFormatterParams) => {
        const history = params.data?.[historyField] as HistoricalComparison | undefined
        const pct = history?.vs_n_minus_2_pct ?? null
        const arrow = getPercentageArrow(pct)
        const formatted = formatPercentageChange(pct)
        const className = getPercentageClass(pct)
        return `<span class="${className}">${arrow}${formatted}</span>`
      },
    },
  ]

  // Optionally add absolute change columns
  if (showAbsoluteChange) {
    columns.splice(2, 0, {
      field: `${historyField}.vs_n_minus_1_abs`,
      headerName: `Δ ${n1Year}`,
      width: columnWidth,
      headerClass: 'ag-header-change',
      editable: false,
      valueFormatter: (params: ValueFormatterParams) => {
        const history = params.data?.[historyField] as HistoricalComparison | undefined
        return formatAbsoluteChange(history?.vs_n_minus_1_abs ?? null, isCurrency)
      },
    })
  }

  return columns
}

/**
 * Create a column group for historical data
 */
export function createHistoricalColumnGroup(
  options: HistoricalColumnOptions & { groupHeaderName?: string }
): ColGroupDef {
  const { groupHeaderName = 'Historical Comparison', ...columnOptions } = options

  return {
    headerName: groupHeaderName,
    headerClass: 'ag-header-group-historical',
    children: createHistoricalColumns(columnOptions),
  }
}

/**
 * Create toggle button for showing/hiding historical columns
 */
export interface HistoricalToggleProps {
  showHistorical: boolean
  onToggle: (show: boolean) => void
  disabled?: boolean
}

/**
 * CSS styles for historical columns
 * Add these to your AG Grid theme or global CSS
 */
export const HISTORICAL_COLUMN_STYLES = `
  .ag-header-historical {
    background-color: var(--color-sand-100) !important;
    font-style: italic;
  }
  .ag-cell-historical {
    background-color: var(--color-sand-50);
    color: var(--color-sand-600);
  }
  .ag-header-change {
    background-color: var(--color-twilight-50) !important;
  }
  .ag-header-group-historical {
    background-color: var(--color-sand-200) !important;
    font-weight: 600;
  }
`
