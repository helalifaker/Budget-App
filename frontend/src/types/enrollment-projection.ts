// Enrollment Projection types (Module 7 upgrade)

export interface EnrollmentScenario {
  id: string
  code: 'worst_case' | 'base' | 'best_case'
  name_en: string
  name_fr: string
  description_en: string | null
  description_fr: string | null
  ps_entry: number
  entry_growth_rate: number
  default_retention: number
  terminal_retention: number
  lateral_multiplier: number
  color_code: string | null
  sort_order: number
}

export interface GlobalOverrides {
  ps_entry_adjustment: number | null
  retention_adjustment: number | null
  lateral_multiplier_override: number | null
  class_size_override: number | null
}

export interface LevelOverride {
  cycle_id: string
  cycle_code: string
  cycle_name: string
  class_size_ceiling: number | null
  max_divisions: number | null
}

export interface GradeOverride {
  level_id: string
  level_code: string
  level_name: string
  retention_rate: number | null
  lateral_entry: number | null
  max_divisions: number | null
  class_size_ceiling: number | null
}

export interface ProjectionConfig {
  id: string
  version_id: string
  scenario_id: string
  scenario: EnrollmentScenario
  base_year: number
  projection_years: number
  school_max_capacity: number
  default_class_size: number
  status: 'draft' | 'validated'
  validated_at: string | null
  validated_by: string | null
  global_overrides: GlobalOverrides | null
  level_overrides: LevelOverride[]
  grade_overrides: GradeOverride[]
}

export interface GradeProjection {
  grade_code: string
  cycle_code: string
  projected_students: number // Total (T) = retained + lateral
  retained_students: number // Retain (R): Students from previous grade
  lateral_students: number // Lateral (L): New lateral entries
  divisions: number
  avg_class_size: number
  original_projection: number | null
  reduction_applied: number
  reduction_percentage: number | null
  historical_data?: number[] // Deprecated - use historical_years in ProjectionResults
}

export interface YearProjection {
  school_year: string
  fiscal_year: number
  grades: GradeProjection[]
  total_students: number
  utilization_rate: number
  was_capacity_constrained: boolean
  total_reduction_applied: number
  fiscal_weighted_enrollment?: Record<string, number>
}

/**
 * Historical enrollment data for a single year.
 * Used to display 2 previous years of actual enrollment data before projections.
 */
export interface HistoricalYearData {
  fiscal_year: number
  school_year: string // e.g., "2023/2024"
  grades: Record<string, number> // grade_code -> student_count
  total_students: number
}

export interface ProjectionResults {
  config: ProjectionConfig
  projections: YearProjection[]
  summary: {
    base_year_total: number
    final_year_total: number
    cagr: number
    years_at_capacity: number
  }
  historical_years: HistoricalYearData[] // Last 2 years of actual enrollment
  base_year_data?: HistoricalYearData | null // Actual enrollment for base year (e.g., 2025-26 for Budget 2026)
}

export const SLIDER_CONFIGS = {
  psEntryAdjustment: { min: -20, max: 20, step: 5, default: 0 },
  retentionAdjustment: { min: -0.05, max: 0.05, step: 0.01, default: 0 },
  lateralMultiplier: { min: 0.5, max: 1.5, step: 0.1, default: 1.0 },
  classSize: { min: 20, max: 30, step: 1, default: 25 },
  retention: { min: 0.85, max: 1.0, step: 0.01, default: 0.96 },
  lateralEntry: { min: 0, max: 50, step: 1, default: 0 },
  maxDivisions: { min: 2, max: 8, step: 1, default: 6 },
} as const

// ==============================================================================
// Unified Lateral Rates (Calibrated Model)
// ==============================================================================

/**
 * Entry point grades for UI badge display.
 * All grades now use percentage-based lateral entry.
 */
export const ENTRY_POINT_GRADES = ['MS', 'GS', 'CP', '6EME', '2NDE'] as const

/**
 * Cycle-based retention rates from historical analysis.
 */
export const CYCLE_RETENTION_RATES = {
  MAT: 0.96, // Maternelle: stable families
  ELEM: 0.96, // Élémentaire: stable families
  COLL: 0.97, // Collège: high commitment
  LYC: 0.93, // Lycée: students leave for France/other
} as const

/**
 * Unified lateral defaults from weighted historical analysis (70% N-1 + 30% N-2).
 * All grades now use percentage-based lateral entry.
 */
export const UNIFIED_LATERAL_DEFAULTS: Record<
  string,
  { lateral_rate: number; retention_rate: number }
> = {
  // Maternelle (Entry Points - high lateral)
  MS: { lateral_rate: 0.363, retention_rate: 0.96 }, // 132.3%
  GS: { lateral_rate: 0.265, retention_rate: 0.96 }, // 122.5%

  // Élémentaire
  CP: { lateral_rate: 0.123, retention_rate: 0.96 }, // 108.3% (Entry)
  CE1: { lateral_rate: 0.085, retention_rate: 0.96 }, // 104.5%
  CE2: { lateral_rate: 0.05, retention_rate: 0.96 }, // 101.0%
  CM1: { lateral_rate: 0.017, retention_rate: 0.96 }, // 97.7%
  CM2: { lateral_rate: 0.071, retention_rate: 0.96 }, // 103.1%

  // Collège
  '6EME': { lateral_rate: 0.107, retention_rate: 0.97 }, // 107.7% (Entry)
  '5EME': { lateral_rate: 0.021, retention_rate: 0.97 }, // 99.1%
  '4EME': { lateral_rate: 0.03, retention_rate: 0.97 }, // 100.0%
  '3EME': { lateral_rate: 0.028, retention_rate: 0.97 }, // 99.8%

  // Lycée (lower retention - students leave for France)
  '2NDE': { lateral_rate: 0.108, retention_rate: 0.93 }, // 103.8% (Entry)
  '1ERE': { lateral_rate: 0.045, retention_rate: 0.93 }, // 97.5%
  TLE: { lateral_rate: 0.072, retention_rate: 0.93 }, // 100.2%
}

/**
 * Confidence levels for calibration data quality.
 */
export type CalibrationConfidence = 'low' | 'medium' | 'high'

/**
 * Lateral entry rate configuration for a single grade (unified model).
 * All grades now use percentage-based lateral entry.
 */
export interface GradeLateralRate {
  grade_code: string
  cycle_code: string
  is_entry_point: boolean

  // Calculated values from historical data
  calculated_retention: number
  calculated_lateral: number
  calculated_progression: number

  // User-editable overrides
  override_retention: number | null
  override_lateral: number | null

  // Effective values (override or calculated)
  effective_retention: number
  effective_lateral: number
  effective_progression: number

  // Source metadata
  progression_n1: number | null
  progression_n2: number | null
  confidence: CalibrationConfidence
}

/**
 * Complete lateral rates for all grades (unified table view).
 */
export interface LateralRatesData {
  grades: GradeLateralRate[]
  calibration_years: number[]
  weight_n1: number
  weight_n2: number

  // Summary statistics
  total_grades: number
  grades_with_overrides: number
  grades_at_default: number
}

/**
 * Request to override lateral rates for one or more grades.
 */
export interface GradeLateralRateOverride {
  grade_code: string
  override_retention: number | null
  override_lateral: number | null
}

/**
 * Helper to check if a grade is an entry point.
 */
export function isEntryPointGrade(gradeCode: string): boolean {
  return ENTRY_POINT_GRADES.includes(gradeCode as (typeof ENTRY_POINT_GRADES)[number])
}

/**
 * Get default lateral rate for a grade.
 */
export function getDefaultLateralRate(gradeCode: string): number {
  return UNIFIED_LATERAL_DEFAULTS[gradeCode]?.lateral_rate ?? 0
}

/**
 * Get default retention rate for a grade.
 */
export function getDefaultRetentionRate(gradeCode: string): number {
  return UNIFIED_LATERAL_DEFAULTS[gradeCode]?.retention_rate ?? 0.96
}

/**
 * Calculate progression rate from retention and lateral.
 */
export function calculateProgression(retention: number, lateral: number): number {
  return retention * (1 + lateral)
}

// ==============================================================================
// Lateral Entry Optimization (Class Structure Aware)
// ==============================================================================

export type OptimizationDecision =
  | 'accept_all'
  | 'accept_fill_max'
  | 'restrict'
  | 'new_class'
  | 'restrict_at_ceiling'
  | 'insufficient_demand'

export interface GradeOptimizationResult {
  grade_code: string
  cycle_code: string
  is_entry_point: boolean

  // Input values
  retained_students: number
  historical_demand: number

  // Class structure
  base_classes: number

  // Capacity calculations
  fill_to_target: number
  fill_to_max: number
  new_class_threshold: number

  // Decision and outputs
  decision: OptimizationDecision
  accepted: number
  rejected: number

  // Final structure
  final_classes: number
  final_students: number

  // Metrics
  avg_class_size: number
  utilization_pct: number
  acceptance_rate: number
}

export interface NewStudentsSummaryRow {
  grade_code: string
  grade_name: string
  cycle_code: string
  is_entry_point: boolean

  // Numbers
  historical_demand: number
  available_slots: number
  accepted: number
  rejected: number

  // Percentages
  acceptance_rate: number
  pct_of_total_intake: number

  // Decision
  decision: OptimizationDecision
}

export interface NewStudentsSummary {
  // Totals
  total_demand: number
  total_available: number
  total_accepted: number
  total_rejected: number

  // Overall metrics
  overall_acceptance_rate: number

  // Entry points vs incidental breakdown
  entry_point_demand: number
  entry_point_accepted: number
  incidental_demand: number
  incidental_accepted: number

  // Grades by decision type
  grades_accept_all: string[]
  grades_fill_max: string[]
  grades_restricted: string[]
  grades_new_class: string[]
  grades_at_ceiling: string[]

  // Breakdown by grade
  by_grade: NewStudentsSummaryRow[]
}

export interface LateralOptimizationResults {
  optimization_results: GradeOptimizationResult[]
  new_students_summary: NewStudentsSummary
}
