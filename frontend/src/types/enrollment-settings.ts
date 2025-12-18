// Enrollment Settings types (Calibration System)

export type ConfidenceLevel = 'high' | 'medium' | 'low'

export type ScenarioCode = 'worst_case' | 'conservative' | 'base' | 'optimistic' | 'best_case'

// =============================================================================
// Calibration Status
// =============================================================================

export interface CalibrationStatus {
  last_calibrated: string | null
  source_years: string[]
  overall_confidence: ConfidenceLevel
  data_quality_score: number // 1-5 stars
  total_years_available: number
  has_sufficient_data: boolean
}

export interface CalibrationRequest {
  /**
   * Budget version ID - determines the target academic year for calibration.
   * For Budget 2026 (fiscal_year=2026), calibration targets 2026-2027.
   */
  version_id: string
  /** Force recalculation even if cached data is fresh */
  force?: boolean
}

export interface CalibrationResult {
  success: boolean
  message: string
  parameters_updated: number
  source_years: string[]
  /** Target academic year for which rates were calibrated (e.g., "2026/2027") */
  target_school_year: string | null
  calculated_at: string | null
  fallback_used: boolean
}

// =============================================================================
// Entry Point Rates (Percentage-Based)
// =============================================================================

export interface EntryPointRate {
  grade_code: string
  is_entry_point: boolean

  // Derived from history
  derived_rate: number | null
  derived_retention: number | null
  confidence: ConfidenceLevel

  // Override status
  override_enabled: boolean
  manual_rate: number | null
  manual_retention: number | null

  // Effective (resolved) values
  effective_rate: number
  effective_retention: number

  // UI helpers
  category: 'maternelle_funnel' | 'cycle_transition'
}

export interface EntryPointRateUpdate {
  grade_code: string
  override_enabled?: boolean
  manual_rate?: number | null
  manual_retention?: number | null
  override_reason?: string | null
}

// =============================================================================
// Incidental Lateral (Fixed Values)
// =============================================================================

export interface IncidentalLateral {
  grade_code: string
  is_entry_point: boolean

  // Derived from history
  derived_value: number | null
  derived_retention: number | null
  confidence: ConfidenceLevel

  // Override status
  override_enabled: boolean
  manual_value: number | null
  manual_retention: number | null

  // Effective (resolved) values
  effective_value: number
  effective_retention: number
}

export interface IncidentalLateralUpdate {
  grade_code: string
  override_enabled?: boolean
  manual_value?: number | null
  manual_retention?: number | null
  override_reason?: string | null
}

// =============================================================================
// Scenario Multipliers
// =============================================================================

export interface ScenarioMultiplier {
  id: string
  organization_id: string
  scenario_code: ScenarioCode
  lateral_multiplier: number
  updated_at: string

  // UI helpers
  scenario_name: string | null
  is_default: boolean
}

export interface ScenarioMultiplierUpdate {
  scenario_code: ScenarioCode
  lateral_multiplier: number
}

// =============================================================================
// Parameter Overrides (Unified)
// =============================================================================

export interface ParameterOverride {
  grade_code: string
  override_lateral_rate: boolean
  manual_lateral_rate: number | null
  override_retention_rate: boolean
  manual_retention_rate: number | null
  override_fixed_lateral: boolean
  manual_fixed_lateral: number | null
  override_reason: string | null
}

export interface ParameterOverrideUpdate {
  grade_code: string
  override_lateral_rate?: boolean
  manual_lateral_rate?: number | null
  override_retention_rate?: boolean
  manual_retention_rate?: number | null
  override_fixed_lateral?: boolean
  manual_fixed_lateral?: number | null
  override_reason?: string | null
}

// =============================================================================
// Combined Settings Response
// =============================================================================

export interface EnrollmentSettingsResponse {
  calibration_status: CalibrationStatus
  entry_point_rates: EntryPointRate[]
  incidental_lateral: IncidentalLateral[]
  scenario_multipliers: ScenarioMultiplier[]
}

// =============================================================================
// Historical Data Summary
// =============================================================================

export interface HistoricalYearSummary {
  school_year: string
  total_students: number
  grades_with_data: number
  is_complete: boolean
}

export interface HistoricalDataSummary {
  available_years: HistoricalYearSummary[]
  recommended_window: string[]
  total_years: number
  has_sufficient_data: boolean
  earliest_year: string | null
  latest_year: string | null
}

// =============================================================================
// Constants
// =============================================================================

export const ENTRY_POINT_GRADES = ['MS', 'GS', 'CP', '6EME', '2NDE'] as const
export const MATERNELLE_FUNNEL_GRADES = ['MS', 'GS'] as const
export const CYCLE_TRANSITION_GRADES = ['CP', '6EME', '2NDE'] as const
export const INCIDENTAL_LATERAL_GRADES = [
  'CE1',
  'CE2',
  'CM1',
  'CM2',
  '5EME',
  '4EME',
  '3EME',
  '1ERE',
  'TLE',
] as const

export const DEFAULT_SCENARIO_MULTIPLIERS: Record<ScenarioCode, number> = {
  worst_case: 0.3,
  conservative: 0.6,
  base: 1.0,
  optimistic: 1.3,
  best_case: 1.5,
}

export const SCENARIO_LABELS: Record<ScenarioCode, string> = {
  worst_case: 'Worst Case',
  conservative: 'Conservative',
  base: 'Base',
  optimistic: 'Optimistic',
  best_case: 'Best Case',
}

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
  high: 'text-green-600',
  medium: 'text-amber-600',
  low: 'text-red-600',
}

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  high: 'High Confidence',
  medium: 'Medium Confidence',
  low: 'Low Confidence',
}
