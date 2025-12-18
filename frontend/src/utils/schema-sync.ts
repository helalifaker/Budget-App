/**
 * Schema Synchronization Utilities
 *
 * This module provides utilities for keeping frontend Zod schemas
 * synchronized with backend Pydantic schemas via OpenAPI.
 *
 * The workflow for preventing schema drift:
 *
 * 1. Backend changes a schema (e.g., adds a field to Level)
 * 2. Developer runs: pnpm generate:types
 * 3. TypeScript compiler catches type mismatches
 * 4. Developer updates Zod schema in api.ts to match
 * 5. Schema validation tests catch any remaining issues
 */

import { z } from 'zod'

/**
 * Type for bilingual entities (Level, Cycle, Subject, NationalityType)
 * Matches the backend pattern of name_fr + name_en
 */
export interface BilingualEntity {
  name_fr: string
  name_en: string
}

/**
 * Get the display name for a bilingual entity
 * Defaults to English, supports French via locale parameter
 *
 * @example
 * const level = { name_fr: 'Cours Préparatoire', name_en: 'Preparatory Course' }
 * getDisplayName(level) // 'Preparatory Course'
 * getDisplayName(level, 'fr') // 'Cours Préparatoire'
 */
export function getDisplayName(entity: BilingualEntity, locale: 'fr' | 'en' = 'en'): string {
  return locale === 'fr' ? entity.name_fr : entity.name_en
}

/**
 * Budget version status values (lowercase to match backend)
 * These are the only valid status values from the backend enum
 */
export const BUDGET_VERSION_STATUSES = [
  'working',
  'submitted',
  'approved',
  'forecast',
  'superseded',
] as const
export type BudgetVersionStatus = (typeof BUDGET_VERSION_STATUSES)[number]

/**
 * Check if a string is a valid version status
 * Useful for runtime validation when receiving data from external sources
 */
export function isValidBudgetVersionStatus(status: string): status is BudgetVersionStatus {
  return BUDGET_VERSION_STATUSES.includes(status as BudgetVersionStatus)
}

/**
 * Status display configuration
 * Maps lowercase backend status to display properties
 */
export const STATUS_CONFIG: Record<
  BudgetVersionStatus,
  {
    label: string
    labelFr: string
    variant: 'default' | 'info' | 'success' | 'warning'
    canEdit: boolean
    canSubmit: boolean
    canApprove: boolean
  }
> = {
  working: {
    label: 'Working',
    labelFr: 'En cours',
    variant: 'info',
    canEdit: true,
    canSubmit: true,
    canApprove: false,
  },
  submitted: {
    label: 'Submitted',
    labelFr: 'Soumis',
    variant: 'warning',
    canEdit: false,
    canSubmit: false,
    canApprove: true,
  },
  approved: {
    label: 'Approved',
    labelFr: 'Approuvé',
    variant: 'success',
    canEdit: false,
    canSubmit: false,
    canApprove: false,
  },
  forecast: {
    label: 'Forecast',
    labelFr: 'Prévision',
    variant: 'info',
    canEdit: true,
    canSubmit: true,
    canApprove: false,
  },
  superseded: {
    label: 'Superseded',
    labelFr: 'Remplacé',
    variant: 'default',
    canEdit: false,
    canSubmit: false,
    canApprove: false,
  },
}

/**
 * Get status display properties
 */
export function getStatusConfig(status: BudgetVersionStatus) {
  return STATUS_CONFIG[status]
}

/**
 * Create a typed paginated response schema
 * This is a helper factory to avoid z.any() in paginated responses
 *
 * @example
 * const PaginatedLevels = createPaginatedSchema(LevelSchema)
 * type PaginatedLevels = z.infer<typeof PaginatedLevels>
 */
export function createPaginatedSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number(),
    page: z.number(),
    page_size: z.number(),
    total_pages: z.number(),
  })
}

/**
 * Schema field comparison helper (for development/debugging)
 * Compares Zod schema shape with expected fields from OpenAPI
 *
 * @example
 * const zodFields = getZodSchemaFields(LevelSchema)
 * // ['id', 'cycle_id', 'code', 'name_fr', 'name_en', 'sort_order', 'is_secondary']
 */
export function getZodSchemaFields(schema: z.ZodObject<z.ZodRawShape>): string[] {
  return Object.keys(schema.shape)
}

/**
 * Validate that a Zod schema has all expected fields
 * Useful for CI checks to catch missing fields early
 *
 * @example
 * validateSchemaFields(LevelSchema, ['id', 'name_fr', 'name_en', 'sort_order', 'is_secondary'])
 */
export function validateSchemaFields(
  schema: z.ZodObject<z.ZodRawShape>,
  expectedFields: string[]
): { valid: boolean; missing: string[]; extra: string[] } {
  const actualFields = getZodSchemaFields(schema)
  const missing = expectedFields.filter((f) => !actualFields.includes(f))
  const extra = actualFields.filter((f) => !expectedFields.includes(f))

  return {
    valid: missing.length === 0 && extra.length === 0,
    missing,
    extra,
  }
}
