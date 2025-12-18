/**
 * Historical Comparison Types
 *
 * TypeScript type definitions for the historical comparison feature,
 * enabling comparison of current budget planning against 2 years of prior actuals.
 */

// =============================================================================
// Historical Data Point Types
// =============================================================================

/**
 * Single historical data point for a specific fiscal year
 */
export interface HistoricalDataPoint {
  /** Fiscal year of the data */
  fiscal_year: number
  /** The actual value (can be monetary, count, or decimal) */
  value: number | null
  /** Whether this is actual data (vs projected) */
  is_actual: boolean
}

/**
 * Historical comparison data showing N-2, N-1, and current values
 * with absolute and percentage changes
 */
export interface HistoricalComparison {
  /** Data from 2 fiscal years ago */
  n_minus_2: HistoricalDataPoint | null
  /** Data from 1 fiscal year ago */
  n_minus_1: HistoricalDataPoint | null
  /** Current plan value */
  current: number

  /** Absolute change vs prior year */
  vs_n_minus_1_abs: number | null
  /** Percentage change vs prior year */
  vs_n_minus_1_pct: number | null

  /** Absolute change vs 2 years ago */
  vs_n_minus_2_abs: number | null
  /** Percentage change vs 2 years ago */
  vs_n_minus_2_pct: number | null
}

// =============================================================================
// Enrollment with History
// =============================================================================

export interface EnrollmentWithHistoryRow {
  level_id: string
  level_code: string
  level_name: string
  student_count: number
  history: HistoricalComparison
}

export interface EnrollmentWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: EnrollmentWithHistoryRow[]
  totals: HistoricalComparison
}

// =============================================================================
// Class Structure with History
// =============================================================================

export interface ClassStructureWithHistoryRow {
  level_id: string
  level_code: string
  level_name: string
  class_count: number
  average_class_size: number
  history: HistoricalComparison
}

export interface ClassStructureWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: ClassStructureWithHistoryRow[]
  totals: HistoricalComparison
}

// =============================================================================
// DHG with History
// =============================================================================

export interface DHGWithHistoryRow {
  subject_id: string | null
  subject_code: string
  subject_name: string
  total_hours: number
  fte: number
  hours_history: HistoricalComparison
  fte_history: HistoricalComparison
}

export interface DHGWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: DHGWithHistoryRow[]
  totals_hours: HistoricalComparison
  totals_fte: HistoricalComparison
}

// =============================================================================
// Revenue with History
// =============================================================================

export interface RevenueWithHistoryRow {
  account_code: string
  account_name: string
  fee_type: string | null
  amount_sar: number
  history: HistoricalComparison
}

export interface RevenueWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: RevenueWithHistoryRow[]
  totals: HistoricalComparison
}

// =============================================================================
// Costs with History
// =============================================================================

export interface CostsWithHistoryRow {
  account_code: string
  account_name: string
  cost_category: string | null
  amount_sar: number
  history: HistoricalComparison
}

export interface CostsWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: CostsWithHistoryRow[]
  totals: HistoricalComparison
  personnel_totals: HistoricalComparison | null
  operating_totals: HistoricalComparison | null
}

// =============================================================================
// CapEx with History
// =============================================================================

export interface CapExWithHistoryRow {
  account_code: string
  account_name: string
  category: string | null
  amount_sar: number
  history: HistoricalComparison
}

export interface CapExWithHistoryResponse {
  version_id: string
  fiscal_year: number
  current_fiscal_year: number
  rows: CapExWithHistoryRow[]
  totals: HistoricalComparison
}

// =============================================================================
// Utility Types
// =============================================================================

/**
 * Module codes for historical data
 */
export type HistoricalModuleCode =
  | 'enrollment'
  | 'class_structure'
  | 'dhg'
  | 'revenue'
  | 'costs'
  | 'capex'

/**
 * Color variants for percentage change display
 */
export type PercentageChangeVariant = 'positive' | 'negative' | 'neutral'

type NumericLike = number | string | null | undefined

const toNumber = (value: NumericLike): number | null => {
  if (value === null || value === undefined) return null
  const num = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(num) ? num : null
}

/**
 * Get color variant based on percentage change
 */
export function getPercentageVariant(pct: NumericLike): PercentageChangeVariant {
  const numeric = toNumber(pct)
  if (numeric === null) return 'neutral'
  if (numeric > 0) return 'positive'
  if (numeric < 0) return 'negative'
  return 'neutral'
}

/**
 * Format percentage change with sign
 */
export function formatPercentageChange(pct: NumericLike): string {
  const numeric = toNumber(pct)
  if (numeric === null) return 'N/A'
  const sign = numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(1)}%`
}

/**
 * Format absolute change with sign
 */
export function formatAbsoluteChange(abs: NumericLike, isCurrency = false): string {
  const numeric = toNumber(abs)
  if (numeric === null) return 'N/A'
  const sign = numeric > 0 ? '+' : ''
  if (isCurrency) {
    return `${sign}${numeric.toLocaleString('en-SA', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} SAR`
  }
  return `${sign}${numeric.toLocaleString()}`
}
