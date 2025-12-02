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
  status: z.enum(['WORKING', 'SUBMITTED', 'APPROVED', 'SUPERSEDED']),
  submitted_at: z.string().nullable(),
  approved_at: z.string().nullable(),
  is_baseline: z.boolean(),
  parent_version_id: z.string().uuid().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  notes: z.string().nullable(),
})

export type BudgetVersion = z.infer<typeof BudgetVersionSchema>

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

// Level (Academic Level)
export const LevelSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name: z.string(),
  cycle_id: z.string().uuid(),
  display_order: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Level = z.infer<typeof LevelSchema>

// Nationality Type
export const NationalityTypeSchema = z.object({
  id: z.string().uuid(),
  code: z.string(),
  name: z.string(),
  vat_applicable: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type NationalityType = z.infer<typeof NationalityTypeSchema>

// Class Structure
export const ClassStructureSchema = z.object({
  id: z.string().uuid(),
  budget_version_id: z.string().uuid(),
  level_id: z.string().uuid(),
  number_of_classes: z.number(),
  avg_class_size: z.number(),
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

// API Error Response
export const APIErrorSchema = z.object({
  detail: z.string(),
  code: z.string().optional(),
  errors: z.array(z.any()).optional(),
})

export type APIError = z.infer<typeof APIErrorSchema>
