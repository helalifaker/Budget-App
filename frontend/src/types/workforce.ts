/**
 * TypeScript types for workforce/personnel management.
 *
 * Zod schemas for runtime validation with inferred TypeScript types.
 * Matches backend Pydantic schemas in backend/app/schemas/personnel.py
 *
 * KSA Labor Law Reference:
 * - Basic salary must be at least 50% of gross for EOS calculation
 * - GOSI: Saudi 21.5% (11.75% employer + 9.75% employee), Expat 2% employer only
 * - EOS: 0.5 months/year (years 1-5), 1.0 month/year (years 6+)
 * - Resignation factors: <2yr=0%, 2-5yr=33%, 5-10yr=67%, >10yr=100%
 */

import { z } from 'zod'

// ==============================================================================
// Enums
// ==============================================================================

export const EmployeeNationalitySchema = z.enum(['SAUDI', 'EXPATRIATE'])
export type EmployeeNationality = z.infer<typeof EmployeeNationalitySchema>

export const EmployeeCategorySchema = z.enum([
  'AEFE_DETACHED',
  'AEFE_FUNDED',
  'LOCAL_TEACHER',
  'ADMINISTRATIVE',
  'SUPPORT',
])
export type EmployeeCategory = z.infer<typeof EmployeeCategorySchema>

export const ContractTypeSchema = z.enum(['PERMANENT', 'FIXED_TERM', 'PROBATION'])
export type ContractType = z.infer<typeof ContractTypeSchema>

export const TerminationTypeSchema = z.enum([
  'RESIGNATION',
  'TERMINATION_BY_EMPLOYER',
  'END_OF_CONTRACT',
  'RETIREMENT',
  'DEATH',
])
export type TerminationType = z.infer<typeof TerminationTypeSchema>

export const AEFEPositionTypeSchema = z.enum(['DETACHED', 'FUNDED'])
export type AEFEPositionType = z.infer<typeof AEFEPositionTypeSchema>

// ==============================================================================
// Employee Schemas
// ==============================================================================

export const EmployeeBaseSchema = z.object({
  full_name: z.string().max(200),
  nationality: EmployeeNationalitySchema,
  category: EmployeeCategorySchema,
  hire_date: z.string(), // ISO date string
  contract_type: ContractTypeSchema.default('PERMANENT'),
  contract_end_date: z.string().nullable().optional(),
  cycle_id: z.string().uuid().nullable().optional(),
  subject_id: z.string().uuid().nullable().optional(),
  fte: z.number().min(0).max(1).default(1.0),
  department: z.string().max(100).nullable().optional(),
  job_title: z.string().max(100).nullable().optional(),
  basic_salary_percentage: z.number().min(0.5).max(1.0).default(0.5),
  is_active: z.boolean().default(true),
  is_placeholder: z.boolean().default(false),
  notes: z.string().nullable().optional(),
})
export type EmployeeBase = z.infer<typeof EmployeeBaseSchema>

export const EmployeeCreateSchema = EmployeeBaseSchema.extend({
  version_id: z.string().uuid(),
})
export type EmployeeCreate = z.infer<typeof EmployeeCreateSchema>

export const EmployeeUpdateSchema = z.object({
  full_name: z.string().max(200).optional(),
  nationality: EmployeeNationalitySchema.optional(),
  category: EmployeeCategorySchema.optional(),
  contract_type: ContractTypeSchema.optional(),
  contract_end_date: z.string().nullable().optional(),
  cycle_id: z.string().uuid().nullable().optional(),
  subject_id: z.string().uuid().nullable().optional(),
  fte: z.number().min(0).max(1).optional(),
  department: z.string().max(100).nullable().optional(),
  job_title: z.string().max(100).nullable().optional(),
  basic_salary_percentage: z.number().min(0.5).max(1.0).optional(),
  is_active: z.boolean().optional(),
  notes: z.string().nullable().optional(),
  termination_date: z.string().nullable().optional(),
  termination_type: TerminationTypeSchema.nullable().optional(),
})
export type EmployeeUpdate = z.infer<typeof EmployeeUpdateSchema>

export const EmployeeResponseSchema = EmployeeBaseSchema.extend({
  id: z.string().uuid(),
  employee_code: z.string(),
  version_id: z.string().uuid(),
  termination_date: z.string().nullable().optional(),
  termination_type: TerminationTypeSchema.nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Employee = z.infer<typeof EmployeeResponseSchema>

export const EmployeeBulkResponseSchema = z.object({
  employees: z.array(EmployeeResponseSchema),
  total: z.number(),
  base_100_count: z.number(),
  planned_count: z.number(),
})
export type EmployeeBulkResponse = z.infer<typeof EmployeeBulkResponseSchema>

// ==============================================================================
// Placeholder Employee Schemas
// ==============================================================================

export const PlaceholderEmployeeCreateSchema = z.object({
  version_id: z.string().uuid(),
  category: EmployeeCategorySchema.default('LOCAL_TEACHER'),
  cycle_id: z.string().uuid().nullable().optional(),
  subject_id: z.string().uuid().nullable().optional(),
  fte: z.number().min(0).max(1).default(1.0),
  estimated_salary_sar: z.number().positive().nullable().optional(),
  notes: z.string().nullable().optional(),
})
export type PlaceholderEmployeeCreate = z.infer<typeof PlaceholderEmployeeCreateSchema>

export const PlaceholderValidationRequestSchema = z.object({
  placeholder_id: z.string().uuid(),
  confirmed: z.boolean().default(false),
})
export type PlaceholderValidationRequest = z.infer<typeof PlaceholderValidationRequestSchema>

// ==============================================================================
// Employee Salary Schemas
// ==============================================================================

export const EmployeeSalaryBaseSchema = z.object({
  effective_from: z.string(), // ISO date string
  effective_to: z.string().nullable().optional(),
  basic_salary_sar: z.number().positive(),
  housing_allowance_sar: z.number().nonnegative().default(0),
  transport_allowance_sar: z.number().nonnegative().default(0),
  other_allowances_sar: z.number().nonnegative().default(0),
  notes: z.string().nullable().optional(),
})
export type EmployeeSalaryBase = z.infer<typeof EmployeeSalaryBaseSchema>

export const EmployeeSalaryCreateSchema = EmployeeSalaryBaseSchema.extend({
  version_id: z.string().uuid(),
  employee_id: z.string().uuid(),
})
export type EmployeeSalaryCreate = z.infer<typeof EmployeeSalaryCreateSchema>

export const EmployeeSalaryUpdateSchema = z.object({
  effective_to: z.string().nullable().optional(),
  basic_salary_sar: z.number().positive().optional(),
  housing_allowance_sar: z.number().nonnegative().optional(),
  transport_allowance_sar: z.number().nonnegative().optional(),
  other_allowances_sar: z.number().nonnegative().optional(),
  notes: z.string().nullable().optional(),
})
export type EmployeeSalaryUpdate = z.infer<typeof EmployeeSalaryUpdateSchema>

export const EmployeeSalaryResponseSchema = EmployeeSalaryBaseSchema.extend({
  id: z.string().uuid(),
  version_id: z.string().uuid(),
  employee_id: z.string().uuid(),
  gross_salary_sar: z.number(),
  gosi_employer_rate: z.number(),
  gosi_employee_rate: z.number(),
  gosi_employer_sar: z.number(),
  gosi_employee_sar: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type EmployeeSalary = z.infer<typeof EmployeeSalaryResponseSchema>

export const SalaryBreakdownResponseSchema = z.object({
  employee_id: z.string().uuid(),
  employee_name: z.string(),
  nationality: EmployeeNationalitySchema,
  basic_salary_sar: z.number(),
  housing_allowance_sar: z.number(),
  transport_allowance_sar: z.number(),
  other_allowances_sar: z.number(),
  gross_salary_sar: z.number(),
  gosi_employer_sar: z.number(),
  gosi_employee_sar: z.number(),
  net_salary_sar: z.number(),
  total_employer_cost_sar: z.number(),
})
export type SalaryBreakdown = z.infer<typeof SalaryBreakdownResponseSchema>

// ==============================================================================
// EOS Provision Schemas
// ==============================================================================

export const EOSProvisionResponseSchema = z.object({
  id: z.string().uuid(),
  version_id: z.string().uuid(),
  employee_id: z.string().uuid(),
  as_of_date: z.string(),
  years_of_service: z.number().int(),
  months_of_service: z.number().int(),
  base_salary_sar: z.number(),
  years_1_to_5_amount_sar: z.number(),
  years_6_plus_amount_sar: z.number(),
  provision_amount_sar: z.number(),
  resignation_factor: z.number().nullable().optional(),
  adjusted_provision_sar: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type EOSProvision = z.infer<typeof EOSProvisionResponseSchema>

export const EOSCalculationRequestSchema = z.object({
  hire_date: z.string(),
  termination_date: z.string().nullable().optional(),
  basic_salary_sar: z.number().positive(),
  termination_type: TerminationTypeSchema.nullable().optional(),
})
export type EOSCalculationRequest = z.infer<typeof EOSCalculationRequestSchema>

export const EOSCalculationResponseSchema = z.object({
  years_of_service: z.number().int(),
  months_of_service: z.number().int(),
  total_service_years: z.number(),
  years_1_to_5_amount_sar: z.number(),
  years_6_plus_amount_sar: z.number(),
  gross_eos_sar: z.number(),
  resignation_factor: z.number().nullable().optional(),
  final_eos_sar: z.number(),
  calculation_breakdown: z.string(),
})
export type EOSCalculation = z.infer<typeof EOSCalculationResponseSchema>

export const EOSSummaryResponseSchema = z.object({
  version_id: z.string().uuid(),
  as_of_date: z.string(),
  total_employees: z.number().int(),
  total_provision_sar: z.number(),
  provision_by_category: z.record(z.string(), z.number()),
  year_over_year_change_sar: z.number().nullable().optional(),
})
export type EOSSummary = z.infer<typeof EOSSummaryResponseSchema>

// ==============================================================================
// AEFE Position Schemas
// ==============================================================================

export const AEFEPositionBaseSchema = z.object({
  position_number: z.number().int().min(1).max(28),
  position_type: AEFEPositionTypeSchema,
  cycle_id: z.string().uuid().nullable().optional(),
  subject_id: z.string().uuid().nullable().optional(),
  prrd_amount_eur: z.number().positive().default(41863.0),
  exchange_rate_eur_sar: z.number().positive().default(4.05),
  academic_year: z.string().max(20).nullable().optional(),
  notes: z.string().nullable().optional(),
})
export type AEFEPositionBase = z.infer<typeof AEFEPositionBaseSchema>

export const AEFEPositionCreateSchema = AEFEPositionBaseSchema.extend({
  version_id: z.string().uuid(),
  employee_id: z.string().uuid().nullable().optional(),
})
export type AEFEPositionCreate = z.infer<typeof AEFEPositionCreateSchema>

export const AEFEPositionUpdateSchema = z.object({
  cycle_id: z.string().uuid().nullable().optional(),
  subject_id: z.string().uuid().nullable().optional(),
  employee_id: z.string().uuid().nullable().optional(),
  prrd_amount_eur: z.number().positive().optional(),
  exchange_rate_eur_sar: z.number().positive().optional(),
  academic_year: z.string().max(20).nullable().optional(),
  notes: z.string().nullable().optional(),
})
export type AEFEPositionUpdate = z.infer<typeof AEFEPositionUpdateSchema>

export const AEFEPositionResponseSchema = AEFEPositionBaseSchema.extend({
  id: z.string().uuid(),
  version_id: z.string().uuid(),
  employee_id: z.string().uuid().nullable().optional(),
  prrd_amount_sar: z.number(),
  is_filled: z.boolean(),
  employee_name: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type AEFEPosition = z.infer<typeof AEFEPositionResponseSchema>

export const AEFEPositionSummaryResponseSchema = z.object({
  version_id: z.string().uuid(),
  total_positions: z.number().int().default(28),
  detached_positions: z.number().int().default(24),
  funded_positions: z.number().int().default(4),
  filled_positions: z.number().int(),
  vacant_positions: z.number().int(),
  total_prrd_eur: z.number(),
  total_prrd_sar: z.number(),
  positions: z.array(AEFEPositionResponseSchema),
})
export type AEFEPositionSummary = z.infer<typeof AEFEPositionSummaryResponseSchema>

export const InitializeAEFEPositionsRequestSchema = z.object({
  version_id: z.string().uuid(),
  academic_year: z.string().max(20),
  prrd_amount_eur: z.number().positive().default(41863.0),
  exchange_rate_eur_sar: z.number().positive().default(4.05),
})
export type InitializeAEFEPositionsRequest = z.infer<typeof InitializeAEFEPositionsRequestSchema>

// ==============================================================================
// Workforce Summary Schemas
// ==============================================================================

export const WorkforceSummaryResponseSchema = z.object({
  version_id: z.string().uuid(),
  total_employees: z.number().int(),
  active_employees: z.number().int(),
  base_100_count: z.number().int(),
  planned_count: z.number().int(),
  by_category: z.record(z.string(), z.number()),
  by_nationality: z.record(z.string(), z.number()),
  total_fte: z.number(),
  aefe_positions_filled: z.number().int(),
  aefe_positions_vacant: z.number().int(),
  total_monthly_payroll_sar: z.number(),
  total_gosi_employer_sar: z.number(),
  total_eos_provision_sar: z.number(),
})
export type WorkforceSummary = z.infer<typeof WorkforceSummaryResponseSchema>

// ==============================================================================
// Filter Types for AG Grid
// ==============================================================================

export interface EmployeeFilters {
  category?: EmployeeCategory
  nationality?: EmployeeNationality
  cycle_id?: string
  subject_id?: string
  is_active?: boolean
  is_placeholder?: boolean
  search?: string
}

export interface EmployeeSort {
  field: keyof Employee
  direction: 'asc' | 'desc'
}

// ==============================================================================
// Form State Types
// ==============================================================================

export interface EmployeeFormValues {
  full_name: string
  nationality: EmployeeNationality
  category: EmployeeCategory
  hire_date: string
  contract_type: ContractType
  contract_end_date?: string | null
  cycle_id?: string | null
  subject_id?: string | null
  fte: number
  department?: string | null
  job_title?: string | null
  basic_salary_percentage: number
  notes?: string | null
}

export interface SalaryFormValues {
  effective_from: string
  effective_to?: string | null
  basic_salary_sar: number
  housing_allowance_sar: number
  transport_allowance_sar: number
  other_allowances_sar: number
  notes?: string | null
}

export interface EOSCalculatorFormValues {
  hire_date: string
  termination_date?: string | null
  basic_salary_sar: number
  termination_type?: TerminationType | null
}

// ==============================================================================
// Display Helpers
// ==============================================================================

export const EMPLOYEE_CATEGORY_LABELS: Record<EmployeeCategory, string> = {
  AEFE_DETACHED: 'AEFE Detached',
  AEFE_FUNDED: 'AEFE Funded',
  LOCAL_TEACHER: 'Local Teacher',
  ADMINISTRATIVE: 'Administrative',
  SUPPORT: 'Support Staff',
}

export const NATIONALITY_LABELS: Record<EmployeeNationality, string> = {
  SAUDI: 'Saudi',
  EXPATRIATE: 'Expatriate',
}

export const CONTRACT_TYPE_LABELS: Record<ContractType, string> = {
  PERMANENT: 'Permanent',
  FIXED_TERM: 'Fixed Term',
  PROBATION: 'Probation',
}

export const TERMINATION_TYPE_LABELS: Record<TerminationType, string> = {
  RESIGNATION: 'Resignation',
  TERMINATION_BY_EMPLOYER: 'Termination by Employer',
  END_OF_CONTRACT: 'End of Contract',
  RETIREMENT: 'Retirement',
  DEATH: 'Death',
}

export const AEFE_POSITION_TYPE_LABELS: Record<AEFEPositionType, string> = {
  DETACHED: 'Detached (PRRD)',
  FUNDED: 'Funded (Zero Cost)',
}

// ==============================================================================
// GOSI Constants (for display)
// ==============================================================================

export const GOSI_RATES = {
  SAUDI: {
    employer: 0.1175, // 11.75%
    employee: 0.0975, // 9.75%
    total: 0.215, // 21.5%
  },
  EXPATRIATE: {
    employer: 0.02, // 2%
    employee: 0, // 0%
    total: 0.02, // 2%
  },
} as const

// ==============================================================================
// EOS Constants (for display)
// ==============================================================================

export const EOS_RATES = {
  YEARS_1_TO_5: 0.5, // 0.5 months per year
  YEARS_6_PLUS: 1.0, // 1.0 month per year
} as const

export const RESIGNATION_FACTORS = {
  LESS_THAN_2_YEARS: 0,
  BETWEEN_2_AND_5_YEARS: 0.33,
  BETWEEN_5_AND_10_YEARS: 0.67,
  MORE_THAN_10_YEARS: 1.0,
} as const
