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
  budget_version_id: string
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
  projected_students: number
  divisions: number
  avg_class_size: number
  original_projection: number | null
  reduction_applied: number
  reduction_percentage: number | null
  historical_data?: number[]
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

export interface ProjectionResults {
  config: ProjectionConfig
  projections: YearProjection[]
  summary: {
    base_year_total: number
    final_year_total: number
    cagr: number
    years_at_capacity: number
  }
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
