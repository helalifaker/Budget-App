import { z } from 'zod'
import { ScenarioTypeSchema } from '@/types/api'

export const budgetVersionSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  fiscal_year: z
    .number()
    .min(2020, 'Fiscal year must be 2020 or later')
    .max(2100, 'Fiscal year must be 2100 or earlier'),
  academic_year: z.string().regex(/^\d{4}-\d{4}$/, 'Academic year must be in format YYYY-YYYY'),
  scenario_type: ScenarioTypeSchema.default('BUDGET'),
  notes: z.string().optional(),
})

export type BudgetVersionFormData = z.infer<typeof budgetVersionSchema>

export const cloneBudgetVersionSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  fiscal_year: z
    .number()
    .min(2020, 'Fiscal year must be 2020 or later')
    .max(2100, 'Fiscal year must be 2100 or earlier'),
  academic_year: z.string().regex(/^\d{4}-\d{4}$/, 'Academic year must be in format YYYY-YYYY'),
  scenario_type: ScenarioTypeSchema.default('BUDGET'),
  clone_configuration: z.boolean().default(true),
})

export type CloneBudgetVersionFormData = z.infer<typeof cloneBudgetVersionSchema>
