import { z } from 'zod'

// Pagination
export const PaginatedResponseSchema = z.object({
  items: z.array(z.any()),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  total_pages: z.number(),
})

export type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Budget Version
export const BudgetVersionSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  fiscal_year: z.number(),
  academic_year: z.string(),
  status: z.enum(['working', 'submitted', 'approved', 'forecast', 'superseded']),
  submitted_at: z.string().nullable(),
  approved_at: z.string().nullable(),
  is_baseline: z.boolean(),
  parent_version_id: z.string().uuid().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  notes: z.string().nullable(),
})

export type BudgetVersion = z.infer<typeof BudgetVersionSchema>

// System Configuration
export const SystemConfigSchema = z.object({
  id: z.string().uuid(),
  key: z.string(),
  value: z.record(z.string(), z.any()), // JSONB stored as key-value object
  category: z.string(),
  description: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type SystemConfig = z.infer<typeof SystemConfigSchema>

// Enrollment
export const EnrollmentSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  nationality_type_id: z.string().uuid(),
  student_count: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Enrollment = z.infer<typeof EnrollmentSchema>

// Nationality Distribution (per-level percentage breakdown)
export const NationalityDistributionSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  french_pct: z.number().min(0).max(100),
  saudi_pct: z.number().min(0).max(100),
  other_pct: z.number().min(0).max(100),
  created_at: z.string(),
  updated_at: z.string(),
})

export type NationalityDistribution = z.infer<typeof NationalityDistributionSchema>

// Enrollment Total (input by level, without nationality breakdown)
export const EnrollmentTotalSchema = z.object({
  level_id: z.string().uuid(),
  total_students: z.number().int().min(0),
})

export type EnrollmentTotal = z.infer<typeof EnrollmentTotalSchema>

// Enrollment Breakdown (calculated from totals + distribution percentages)
export const EnrollmentBreakdownSchema = z.object({
  level_id: z.string().uuid(),
  level_code: z.string(),
  level_name: z.string(),
  cycle_code: z.string(),
  total_students: z.number().int(),
  french_count: z.number().int(),
  saudi_count: z.number().int(),
  other_count: z.number().int(),
  french_pct: z.number(),
  saudi_pct: z.number(),
  other_pct: z.number(),
})

export type EnrollmentBreakdown = z.infer<typeof EnrollmentBreakdownSchema>

// Enrollment Summary
export const EnrollmentSummarySchema = z.object({
  total_students: z.number().int(),
  by_level: z.record(z.string(), z.number()),
  by_cycle: z.record(z.string(), z.number()),
  by_nationality: z.record(z.string(), z.number()),
  capacity_utilization: z.number(),
})

export type EnrollmentSummary = z.infer<typeof EnrollmentSummarySchema>

// Complete Enrollment Response (with distribution and breakdown)
export const EnrollmentWithDistributionSchema = z.object({
  totals: z.array(EnrollmentTotalSchema),
  distributions: z.array(NationalityDistributionSchema),
  breakdown: z.array(EnrollmentBreakdownSchema),
  summary: EnrollmentSummarySchema,
})

export type EnrollmentWithDistribution = z.infer<typeof EnrollmentWithDistributionSchema>

// Level (Academic Level)
export const LevelSchema = z.object({
  id: z.string().uuid(),
  cycle_id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  sort_order: z.number(),
  is_secondary: z.boolean(),
})

export type Level = z.infer<typeof LevelSchema>

// Nationality Type
export const NationalityTypeSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  vat_applicable: z.boolean(),
  sort_order: z.number(),
})

export type NationalityType = z.infer<typeof NationalityTypeSchema>

// Fee Category
export const FeeCategorySchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  account_code: z.string(),
  is_recurring: z.boolean(),
  allows_sibling_discount: z.boolean(),
})

export type FeeCategory = z.infer<typeof FeeCategorySchema>

// Fee Structure
export const FeeStructureSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  nationality_type_id: z.string().uuid(),
  fee_category_id: z.string().uuid(),
  amount_sar: z.number().min(0),
  trimester: z.number().min(1).max(3).nullable().optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type FeeStructure = z.infer<typeof FeeStructureSchema>

// Cycle (Academic Cycle)
export const CycleSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  sort_order: z.number(),
  requires_atsem: z.boolean(),
})

export type Cycle = z.infer<typeof CycleSchema>

// Class Size Parameters
export const ClassSizeParamSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid().nullable(),
  cycle_id: z.string().uuid().nullable(),
  min_class_size: z.number().int().min(1).max(50),
  target_class_size: z.number().int().min(1).max(50),
  max_class_size: z.number().int().min(1).max(50),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type ClassSizeParam = z.infer<typeof ClassSizeParamSchema>

// Class Structure
export const ClassStructureSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  total_students: z.number(),
  number_of_classes: z.number(),
  avg_class_size: z.number(),
  requires_atsem: z.boolean(),
  atsem_count: z.number(),
  calculation_method: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type ClassStructure = z.infer<typeof ClassStructureSchema>

// DHG (Teacher Workforce)
export const DHGEntrySchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  subject_id: z.string().uuid(),
  total_hours: z.number(),
  fte_required: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type DHGEntry = z.infer<typeof DHGEntrySchema>

// Subject Hours (Configuration)
export const SubjectHoursSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  subject_id: z.string().uuid(),
  hours_per_week: z.number().min(0).max(12), // 0-12 hours, backend uses Decimal with 2 decimal places
  is_split: z.boolean(), // Whether classes are split (half-size groups)
  notes: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type SubjectHours = z.infer<typeof SubjectHoursSchema>

// Teacher FTE
export const TeacherFTESchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  cycle_id: z.string().uuid(),
  level_id: z.string().uuid().nullable(),
  subject_id: z.string().uuid(),
  total_hours: z.number(),
  standard_fte: z.number(),
  adjusted_fte: z.number(),
  hsa_hours: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type TeacherFTE = z.infer<typeof TeacherFTESchema>

// TRMD Gap Analysis
export const TRMDGapSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  subject_id: z.string().uuid(),
  hours_needed: z.number(),
  aefe_positions: z.number(),
  local_positions: z.number(),
  deficit_hours: z.number(),
  hsa_required: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type TRMDGap = z.infer<typeof TRMDGapSchema>

// HSA Planning
export const HSAPlanningSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  teacher_id: z.string().uuid(),
  subject_id: z.string().uuid(),
  hsa_hours: z.number(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type HSAPlanning = z.infer<typeof HSAPlanningSchema>

// Revenue Line Item
export const RevenueLineItemSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  account_code: z.string(),
  description: z.string(),
  category: z.string(),
  t1_amount: z.number().nullable(),
  t2_amount: z.number().nullable(),
  t3_amount: z.number().nullable(),
  annual_amount: z.number(),
  is_auto_calculated: z.boolean(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type RevenueLineItem = z.infer<typeof RevenueLineItemSchema>

// Cost Line Item
export const CostLineItemSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  account_code: z.string(),
  description: z.string(),
  category: z.enum(['PERSONNEL', 'OPERATING']),
  cost_type: z.string(),
  p1_amount: z.number(),
  summer_amount: z.number(),
  p2_amount: z.number(),
  annual_amount: z.number(),
  is_auto_calculated: z.boolean(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type CostLineItem = z.infer<typeof CostLineItemSchema>

// CapEx Item
export const CapExItemSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  description: z.string(),
  asset_type: z.enum(['EQUIPMENT', 'IT', 'FURNITURE', 'BUILDING_IMPROVEMENTS', 'SOFTWARE']),
  account_code: z.string(),
  purchase_date: z.string(),
  cost: z.number(),
  useful_life_years: z.number(),
  depreciation_method: z.enum(['STRAIGHT_LINE', 'DECLINING_BALANCE']),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type CapExItem = z.infer<typeof CapExItemSchema>

// Subject
export const SubjectSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  category: z.string(),
  is_active: z.boolean(),
})

export type Subject = z.infer<typeof SubjectSchema>

// Teacher Categories
export const TeacherCategorySchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_fr: z.string(),
  name_en: z.string(),
  description: z.string().nullable(),
  is_aefe: z.boolean(),
})

export type TeacherCategory = z.infer<typeof TeacherCategorySchema>

// Teacher Cost Parameters
export const TeacherCostParamSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  category_id: z.string().uuid(),
  cycle_id: z.string().uuid().nullable(),
  prrd_contribution_eur: z.number().nullable(),
  avg_salary_sar: z.number().nullable(),
  social_charges_rate: z.number(),
  benefits_allowance_sar: z.number(),
  hsa_hourly_rate_sar: z.number(),
  max_hsa_hours: z.number(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type TeacherCostParam = z.infer<typeof TeacherCostParamSchema>

// Timetable Constraints
export const TimetableConstraintSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  total_hours_per_week: z.number(),
  max_hours_per_day: z.number(),
  days_per_week: z.number(),
  requires_lunch_break: z.boolean(),
  min_break_duration_minutes: z.number(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type TimetableConstraint = z.infer<typeof TimetableConstraintSchema>

// Consolidation
export const ConsolidationStatusSchema = z.object({
  budget_version_id: z.string().uuid(),
  is_complete: z.boolean(),
  modules_complete: z.object({
    enrollment: z.boolean(),
    classes: z.boolean(),
    dhg: z.boolean(),
    revenue: z.boolean(),
    costs: z.boolean(),
    capex: z.boolean(),
  }),
  total_revenue: z.number(),
  total_costs: z.number(),
  net_income: z.number(),
  operating_margin: z.number(),
  last_consolidated_at: z.string().nullable(),
})

export type ConsolidationStatus = z.infer<typeof ConsolidationStatusSchema>

export const BudgetLineItemSchema = z.object({
  id: z.string().uuid(),
  account_code: z.string(),
  description: z.string(),
  category: z.enum(['REVENUE', 'PERSONNEL', 'OPERATING', 'CAPEX']),
  annual_amount: z.number(),
  notes: z.string().nullable(),
})

export type BudgetLineItem = z.infer<typeof BudgetLineItemSchema>

// Financial Statements
export const StatementLineSchema = z.object({
  label: z.string(),
  amount: z.number(),
  indent: z.number(),
  is_bold: z.boolean(),
  is_underlined: z.boolean(),
  account_code: z.string().nullable(),
})

export type StatementLine = z.infer<typeof StatementLineSchema>

export const FinancialStatementSchema = z.object({
  budget_version_id: z.string().uuid(),
  statement_type: z.enum(['INCOME', 'BALANCE', 'CASHFLOW']),
  format: z.enum(['PCG', 'IFRS']),
  period: z.enum(['ANNUAL', 'P1', 'P2', 'SUMMER']),
  lines: z.array(StatementLineSchema),
  generated_at: z.string(),
})

export type FinancialStatement = z.infer<typeof FinancialStatementSchema>

// KPIs
export const KPISchema = z.object({
  id: z.string(),
  title: z.string(),
  value: z.number(),
  unit: z.string(),
  benchmark_min: z.number().nullable(),
  benchmark_max: z.number().nullable(),
  status: z.enum(['GOOD', 'WARNING', 'ALERT']),
  trend: z.enum(['UP', 'DOWN', 'STABLE']).nullable(),
  previous_value: z.number().nullable(),
})

export type KPI = z.infer<typeof KPISchema>

// Variance Analysis
export const VarianceLineSchema = z.object({
  account_code: z.string(),
  description: z.string(),
  category: z.enum(['REVENUE', 'PERSONNEL', 'OPERATING']),
  budget: z.number(),
  actual: z.number(),
  variance: z.number(),
  variance_percent: z.number(),
  is_favorable: z.boolean(),
  is_material: z.boolean(),
})

export type VarianceLine = z.infer<typeof VarianceLineSchema>

export const VarianceReportSchema = z.object({
  budget_version_id: z.string().uuid(),
  period: z.enum(['T1', 'T2', 'T3', 'ANNUAL']),
  lines: z.array(VarianceLineSchema),
  total_variance: z.number(),
  favorable_count: z.number(),
  unfavorable_count: z.number(),
  generated_at: z.string(),
})

export type VarianceReport = z.infer<typeof VarianceReportSchema>

// Strategic Planning
export const StrategicScenarioSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string(),
  enrollment_growth_rate: z.number(),
  fee_increase_rate: z.number(),
  salary_inflation_rate: z.number(),
  operating_growth_rate: z.number(),
})

export type StrategicScenario = z.infer<typeof StrategicScenarioSchema>

export const StrategicProjectionSchema = z.object({
  year: z.number(),
  students: z.number(),
  classes: z.number(),
  teachers: z.number(),
  revenue: z.number(),
  personnel_costs: z.number(),
  operating_costs: z.number(),
  net_income: z.number(),
  operating_margin: z.number(),
})

export type StrategicProjection = z.infer<typeof StrategicProjectionSchema>

export const StrategicPlanSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  base_version_id: z.string().uuid(),
  base_year: z.number(),
  years_count: z.number(),
  scenarios: z.array(StrategicScenarioSchema),
  created_at: z.string(),
  updated_at: z.string(),
})

export type StrategicPlan = z.infer<typeof StrategicPlanSchema>

// Dashboard
export const DashboardSummarySchema = z.object({
  version_id: z.string(),
  version_name: z.string(),
  fiscal_year: z.number(),
  status: z.string(),
  total_revenue_sar: z.number(),
  total_costs_sar: z.number(),
  net_result_sar: z.number(),
  operating_margin_pct: z.number(),
  total_students: z.number(),
  total_classes: z.number().optional(), // Backend doesn't return this yet
  total_teachers_fte: z.number(),
  student_teacher_ratio: z.number(),
  capacity_utilization_pct: z.number(),
  last_updated: z.string(),
})

export type DashboardSummary = z.infer<typeof DashboardSummarySchema>

export const ActivitySchema = z.object({
  id: z.string(),
  action: z.string(),
  user: z.string(),
  timestamp: z.string(),
  details: z.string().nullable(),
})

export type Activity = z.infer<typeof ActivitySchema>

export const SystemAlertSchema = z.object({
  id: z.string(),
  type: z.enum(['INFO', 'WARNING', 'ERROR']),
  message: z.string(),
  timestamp: z.string(),
})

export type SystemAlert = z.infer<typeof SystemAlertSchema>

// API Error Response
export const APIErrorSchema = z.object({
  detail: z.string(),
  code: z.string().optional(),
  errors: z.array(z.any()).optional(),
})

export type APIError = z.infer<typeof APIErrorSchema>

// ==============================================================================
// Subject Hours Matrix Types (Cycle-Based Matrix View)
// ==============================================================================

// Level info for matrix columns
export const LevelInfoSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_en: z.string(),
  name_fr: z.string(),
  sort_order: z.number(),
})

export type LevelInfo = z.infer<typeof LevelInfoSchema>

// Hours configuration for a subject-level cell
export const SubjectLevelHoursSchema = z.object({
  hours_per_week: z.number().nullable(),
  is_split: z.boolean(),
  notes: z.string().nullable(),
})

export type SubjectLevelHours = z.infer<typeof SubjectLevelHoursSchema>

// Subject row in matrix with hours per level
export const SubjectWithHoursSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name_en: z.string(),
  name_fr: z.string(),
  category: z.string(),
  is_applicable: z.boolean(),
  hours: z.record(z.string(), SubjectLevelHoursSchema), // level_id -> hours
})

export type SubjectWithHours = z.infer<typeof SubjectWithHoursSchema>

// Full matrix response from backend
export const SubjectHoursMatrixResponseSchema = z.object({
  cycle_id: z.string().uuid(),
  cycle_code: z.string(),
  cycle_name: z.string(),
  levels: z.array(LevelInfoSchema),
  subjects: z.array(SubjectWithHoursSchema),
})

export type SubjectHoursMatrixResponse = z.infer<typeof SubjectHoursMatrixResponseSchema>

// Entry for batch save
export const SubjectHoursEntrySchema = z.object({
  subject_id: z.string().uuid(),
  level_id: z.string().uuid(),
  hours_per_week: z.number().min(0).max(12).nullable(),
  is_split: z.boolean(),
  notes: z.string().nullable().optional(),
})

export type SubjectHoursEntry = z.infer<typeof SubjectHoursEntrySchema>

// Batch request for saving multiple entries
export const SubjectHoursBatchRequestSchema = z.object({
  budget_version_id: z.string().uuid(),
  entries: z.array(SubjectHoursEntrySchema).min(1).max(200),
})

export type SubjectHoursBatchRequest = z.infer<typeof SubjectHoursBatchRequestSchema>

// Batch response
export const SubjectHoursBatchResponseSchema = z.object({
  created_count: z.number(),
  updated_count: z.number(),
  deleted_count: z.number(),
  errors: z.array(z.string()),
})

export type SubjectHoursBatchResponse = z.infer<typeof SubjectHoursBatchResponseSchema>

// Curriculum template info
export const TemplateInfoSchema = z.object({
  code: z.string(),
  name: z.string(),
  description: z.string(),
  cycle_codes: z.array(z.string()),
})

export type TemplateInfo = z.infer<typeof TemplateInfoSchema>

// Apply template request
export const ApplyTemplateRequestSchema = z.object({
  budget_version_id: z.string().uuid(),
  template_code: z.string(),
  cycle_codes: z.array(z.string()).min(1),
  overwrite_existing: z.boolean(),
})

export type ApplyTemplateRequest = z.infer<typeof ApplyTemplateRequestSchema>

// Apply template response
export const ApplyTemplateResponseSchema = z.object({
  applied_count: z.number(),
  skipped_count: z.number(),
  template_name: z.string(),
})

export type ApplyTemplateResponse = z.infer<typeof ApplyTemplateResponseSchema>

// Create subject request
export const SubjectCreateRequestSchema = z.object({
  code: z
    .string()
    .min(2)
    .max(6)
    .regex(/^[A-Z0-9]+$/),
  name_fr: z.string().min(1).max(100),
  name_en: z.string().min(1).max(100),
  category: z.enum(['core', 'elective', 'specialty', 'local']),
  applicable_cycles: z.array(z.string()).min(1),
})

export type SubjectCreateRequest = z.infer<typeof SubjectCreateRequestSchema>
