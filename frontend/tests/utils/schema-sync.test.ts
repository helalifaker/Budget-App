/**
 * Schema Synchronization Utilities Tests
 */

import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import {
  getDisplayName,
  isValidBudgetVersionStatus,
  getStatusConfig,
  createPaginatedSchema,
  getZodSchemaFields,
  validateSchemaFields,
  BUDGET_VERSION_STATUSES,
  STATUS_CONFIG,
} from '@/utils/schema-sync'
import { LevelSchema, CycleSchema, SubjectSchema, NationalityTypeSchema } from '@/types/api'

describe('Schema Synchronization Utilities', () => {
  describe('getDisplayName', () => {
    it('should return English name by default', () => {
      const entity = { name_fr: 'Mathématiques', name_en: 'Mathematics' }
      expect(getDisplayName(entity)).toBe('Mathematics')
    })

    it('should return French name when locale is fr', () => {
      const entity = { name_fr: 'Mathématiques', name_en: 'Mathematics' }
      expect(getDisplayName(entity, 'fr')).toBe('Mathématiques')
    })

    it('should return English name when locale is en', () => {
      const entity = { name_fr: 'École Maternelle', name_en: 'Preschool' }
      expect(getDisplayName(entity, 'en')).toBe('Preschool')
    })

    it('should handle empty strings', () => {
      const entity = { name_fr: '', name_en: 'Test' }
      expect(getDisplayName(entity)).toBe('Test')
      expect(getDisplayName(entity, 'fr')).toBe('')
    })
  })

  describe('isValidBudgetVersionStatus', () => {
    it('should return true for valid lowercase statuses', () => {
      expect(isValidBudgetVersionStatus('working')).toBe(true)
      expect(isValidBudgetVersionStatus('submitted')).toBe(true)
      expect(isValidBudgetVersionStatus('approved')).toBe(true)
      expect(isValidBudgetVersionStatus('forecast')).toBe(true)
      expect(isValidBudgetVersionStatus('superseded')).toBe(true)
    })

    it('should return false for uppercase statuses (old format)', () => {
      expect(isValidBudgetVersionStatus('WORKING')).toBe(false)
      expect(isValidBudgetVersionStatus('SUBMITTED')).toBe(false)
      expect(isValidBudgetVersionStatus('APPROVED')).toBe(false)
      expect(isValidBudgetVersionStatus('SUPERSEDED')).toBe(false)
    })

    it('should return false for invalid statuses', () => {
      expect(isValidBudgetVersionStatus('invalid')).toBe(false)
      expect(isValidBudgetVersionStatus('')).toBe(false)
      expect(isValidBudgetVersionStatus('draft')).toBe(false)
      expect(isValidBudgetVersionStatus('pending')).toBe(false)
    })
  })

  describe('BUDGET_VERSION_STATUSES', () => {
    it('should contain exactly 5 status values', () => {
      expect(BUDGET_VERSION_STATUSES).toHaveLength(5)
    })

    it('should contain all expected statuses in lowercase', () => {
      expect(BUDGET_VERSION_STATUSES).toContain('working')
      expect(BUDGET_VERSION_STATUSES).toContain('submitted')
      expect(BUDGET_VERSION_STATUSES).toContain('approved')
      expect(BUDGET_VERSION_STATUSES).toContain('forecast')
      expect(BUDGET_VERSION_STATUSES).toContain('superseded')
    })

    it('should not contain uppercase statuses', () => {
      const hasUppercase = BUDGET_VERSION_STATUSES.some((s) => s !== s.toLowerCase())
      expect(hasUppercase).toBe(false)
    })
  })

  describe('getStatusConfig', () => {
    it('should return correct config for working status', () => {
      const config = getStatusConfig('working')
      expect(config.label).toBe('Working')
      expect(config.variant).toBe('info')
      expect(config.canEdit).toBe(true)
      expect(config.canSubmit).toBe(true)
      expect(config.canApprove).toBe(false)
    })

    it('should return correct config for submitted status', () => {
      const config = getStatusConfig('submitted')
      expect(config.label).toBe('Submitted')
      expect(config.variant).toBe('warning')
      expect(config.canEdit).toBe(false)
      expect(config.canApprove).toBe(true)
    })

    it('should return correct config for approved status', () => {
      const config = getStatusConfig('approved')
      expect(config.label).toBe('Approved')
      expect(config.variant).toBe('success')
      expect(config.canEdit).toBe(false)
      expect(config.canSubmit).toBe(false)
      expect(config.canApprove).toBe(false)
    })

    it('should return correct config for forecast status', () => {
      const config = getStatusConfig('forecast')
      expect(config.label).toBe('Forecast')
      expect(config.variant).toBe('info')
      expect(config.canEdit).toBe(true)
    })

    it('should return correct config for superseded status', () => {
      const config = getStatusConfig('superseded')
      expect(config.label).toBe('Superseded')
      expect(config.variant).toBe('default')
      expect(config.canEdit).toBe(false)
    })

    it('should have French labels for all statuses', () => {
      Object.keys(STATUS_CONFIG).forEach((status) => {
        const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG]
        expect(config.labelFr).toBeDefined()
        expect(config.labelFr.length).toBeGreaterThan(0)
      })
    })
  })

  describe('createPaginatedSchema', () => {
    it('should create a valid paginated schema', () => {
      const ItemSchema = z.object({ id: z.string(), name: z.string() })
      const PaginatedSchema = createPaginatedSchema(ItemSchema)

      const validData = {
        items: [
          { id: '1', name: 'Item 1' },
          { id: '2', name: 'Item 2' },
        ],
        total: 100,
        page: 1,
        page_size: 10,
        total_pages: 10,
      }

      expect(() => PaginatedSchema.parse(validData)).not.toThrow()
    })

    it('should reject invalid items', () => {
      const ItemSchema = z.object({ id: z.string(), name: z.string() })
      const PaginatedSchema = createPaginatedSchema(ItemSchema)

      const invalidData = {
        items: [{ id: 123, name: 'Item 1' }], // id should be string
        total: 100,
        page: 1,
        page_size: 10,
        total_pages: 10,
      }

      expect(() => PaginatedSchema.parse(invalidData)).toThrow()
    })

    it('should reject missing pagination fields', () => {
      const ItemSchema = z.object({ id: z.string() })
      const PaginatedSchema = createPaginatedSchema(ItemSchema)

      const invalidData = {
        items: [{ id: '1' }],
        total: 100,
        // missing page, page_size, total_pages
      }

      expect(() => PaginatedSchema.parse(invalidData)).toThrow()
    })
  })

  describe('getZodSchemaFields', () => {
    it('should extract field names from LevelSchema', () => {
      const fields = getZodSchemaFields(LevelSchema)
      expect(fields).toContain('id')
      expect(fields).toContain('cycle_id')
      expect(fields).toContain('code')
      expect(fields).toContain('name_fr')
      expect(fields).toContain('name_en')
      expect(fields).toContain('sort_order')
      expect(fields).toContain('is_secondary')
    })

    it('should not include old field names in LevelSchema', () => {
      const fields = getZodSchemaFields(LevelSchema)
      expect(fields).not.toContain('name')
      expect(fields).not.toContain('display_order')
      expect(fields).not.toContain('created_at')
      expect(fields).not.toContain('updated_at')
    })

    it('should extract field names from CycleSchema', () => {
      const fields = getZodSchemaFields(CycleSchema)
      expect(fields).toContain('name_fr')
      expect(fields).toContain('name_en')
      expect(fields).toContain('sort_order')
      expect(fields).toContain('requires_atsem')
    })

    it('should extract field names from SubjectSchema', () => {
      const fields = getZodSchemaFields(SubjectSchema)
      expect(fields).toContain('name_fr')
      expect(fields).toContain('name_en')
      expect(fields).toContain('is_active')
      expect(fields).not.toContain('display_order')
    })

    it('should extract field names from NationalityTypeSchema', () => {
      const fields = getZodSchemaFields(NationalityTypeSchema)
      expect(fields).toContain('name_fr')
      expect(fields).toContain('name_en')
      expect(fields).toContain('sort_order')
      expect(fields).toContain('vat_applicable')
    })
  })

  describe('validateSchemaFields', () => {
    it('should return valid when all fields match', () => {
      const TestSchema = z.object({
        id: z.string(),
        name: z.string(),
        value: z.number(),
      })

      const result = validateSchemaFields(TestSchema, ['id', 'name', 'value'])
      expect(result.valid).toBe(true)
      expect(result.missing).toHaveLength(0)
      expect(result.extra).toHaveLength(0)
    })

    it('should detect missing fields', () => {
      const TestSchema = z.object({
        id: z.string(),
        name: z.string(),
      })

      const result = validateSchemaFields(TestSchema, ['id', 'name', 'value', 'extra'])
      expect(result.valid).toBe(false)
      expect(result.missing).toContain('value')
      expect(result.missing).toContain('extra')
    })

    it('should detect extra fields', () => {
      const TestSchema = z.object({
        id: z.string(),
        name: z.string(),
        extra_field: z.string(),
      })

      const result = validateSchemaFields(TestSchema, ['id', 'name'])
      expect(result.valid).toBe(false)
      expect(result.extra).toContain('extra_field')
    })

    it('should validate LevelSchema has correct fields', () => {
      const expectedFields = [
        'id',
        'cycle_id',
        'code',
        'name_fr',
        'name_en',
        'sort_order',
        'is_secondary',
      ]
      const result = validateSchemaFields(LevelSchema, expectedFields)
      expect(result.valid).toBe(true)
    })

    it('should validate CycleSchema has correct fields', () => {
      const expectedFields = ['id', 'code', 'name_fr', 'name_en', 'sort_order', 'requires_atsem']
      const result = validateSchemaFields(CycleSchema, expectedFields)
      expect(result.valid).toBe(true)
    })

    it('should validate SubjectSchema has correct fields', () => {
      const expectedFields = ['id', 'code', 'name_fr', 'name_en', 'category', 'is_active']
      const result = validateSchemaFields(SubjectSchema, expectedFields)
      expect(result.valid).toBe(true)
    })

    it('should validate NationalityTypeSchema has correct fields', () => {
      const expectedFields = ['id', 'code', 'name_fr', 'name_en', 'vat_applicable', 'sort_order']
      const result = validateSchemaFields(NationalityTypeSchema, expectedFields)
      expect(result.valid).toBe(true)
    })
  })
})
