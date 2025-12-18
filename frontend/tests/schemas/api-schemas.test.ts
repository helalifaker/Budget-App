/**
 * API Schema Validation Tests
 *
 * These tests validate that frontend Zod schemas match the backend Pydantic schemas.
 * They use realistic mock data that mirrors actual backend responses to catch drift early.
 *
 * IMPORTANT: When the backend changes schema fields, these tests will fail,
 * providing an early warning to update frontend types.
 */

import { describe, it, expect } from 'vitest'
import {
  BudgetVersionSchema,
  LevelSchema,
  CycleSchema,
  NationalityTypeSchema,
  SubjectSchema,
  ClassStructureSchema,
  EnrollmentSchema,
  TeacherCostParamSchema,
  TimetableConstraintSchema,
  SubjectHoursSchema,
} from '@/types/api'

describe('API Schema Validation', () => {
  describe('BudgetVersionSchema', () => {
    it('should validate budget version with lowercase working status', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'working',
        scenario_type: 'BUDGET',
        submitted_at: null,
        approved_at: null,
        is_baseline: false,
        parent_version_id: null,
        organization_id: '123e4567-e89b-12d3-a456-426614174099',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        notes: null,
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).not.toThrow()
    })

    it('should validate budget version with submitted status', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025 Q1',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'submitted',
        scenario_type: 'BUDGET',
        submitted_at: '2025-02-01T10:00:00Z',
        approved_at: null,
        is_baseline: false,
        parent_version_id: null,
        organization_id: '123e4567-e89b-12d3-a456-426614174099',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-02-01T10:00:00Z',
        notes: 'Submitted for review',
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).not.toThrow()
    })

    it('should validate budget version with approved status', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025 Final',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'approved',
        scenario_type: 'BUDGET',
        submitted_at: '2025-02-01T10:00:00Z',
        approved_at: '2025-02-15T14:30:00Z',
        is_baseline: true,
        parent_version_id: null,
        organization_id: '123e4567-e89b-12d3-a456-426614174099',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-02-15T14:30:00Z',
        notes: 'Approved by Finance Director',
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).not.toThrow()
    })

    it('should validate budget version with forecast status', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025 Forecast Q2',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'forecast',
        scenario_type: 'FORECAST',
        submitted_at: null,
        approved_at: null,
        is_baseline: false,
        parent_version_id: '123e4567-e89b-12d3-a456-426614174001',
        organization_id: '123e4567-e89b-12d3-a456-426614174099',
        created_at: '2025-04-01T00:00:00Z',
        updated_at: '2025-04-01T00:00:00Z',
        notes: 'Q2 Forecast revision',
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).not.toThrow()
    })

    it('should validate budget version with superseded status', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2024 Old',
        fiscal_year: 2024,
        academic_year: '2023-2024',
        status: 'superseded',
        scenario_type: 'BUDGET',
        submitted_at: '2024-01-15T10:00:00Z',
        approved_at: '2024-02-01T14:30:00Z',
        is_baseline: false,
        parent_version_id: null,
        organization_id: '123e4567-e89b-12d3-a456-426614174099',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-12-01T00:00:00Z',
        notes: 'Superseded by Budget 2025',
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).not.toThrow()
    })

    it('should reject uppercase status values', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'WORKING', // UPPERCASE - should fail
        submitted_at: null,
        approved_at: null,
        is_baseline: false,
        parent_version_id: null,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        notes: null,
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).toThrow()
    })

    it('should reject invalid status values', () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        name: 'Budget 2025',
        fiscal_year: 2025,
        academic_year: '2024-2025',
        status: 'invalid_status',
        submitted_at: null,
        approved_at: null,
        is_baseline: false,
        parent_version_id: null,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        notes: null,
      }
      expect(() => BudgetVersionSchema.parse(mockResponse)).toThrow()
    })
  })

  describe('LevelSchema', () => {
    it('should validate level with bilingual names and sort_order', () => {
      const mockLevel = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        cycle_id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'CP',
        name_fr: 'Cours Préparatoire',
        name_en: 'Preparatory Course',
        sort_order: 1,
        is_secondary: false,
      }
      expect(() => LevelSchema.parse(mockLevel)).not.toThrow()
    })

    it('should validate secondary school level', () => {
      const mockLevel = {
        id: '123e4567-e89b-12d3-a456-426614174002',
        cycle_id: '123e4567-e89b-12d3-a456-426614174003',
        code: '6EME',
        name_fr: 'Sixième',
        name_en: 'Sixth Grade',
        sort_order: 7,
        is_secondary: true,
      }
      expect(() => LevelSchema.parse(mockLevel)).not.toThrow()
    })

    it('should reject level with old name field (schema drift detection)', () => {
      const oldSchemaLevel = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        cycle_id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'CP',
        name: 'Preparatory Course', // OLD field - should fail
        display_order: 1, // OLD field name - should fail
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => LevelSchema.parse(oldSchemaLevel)).toThrow()
    })
  })

  describe('CycleSchema', () => {
    it('should validate cycle with bilingual names and requires_atsem', () => {
      const mockCycle = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATERNELLE',
        name_fr: 'École Maternelle',
        name_en: 'Preschool',
        sort_order: 1,
        requires_atsem: true,
      }
      expect(() => CycleSchema.parse(mockCycle)).not.toThrow()
    })

    it('should validate elementary cycle (no ATSEM required)', () => {
      const mockCycle = {
        id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'ELEMENTAIRE',
        name_fr: 'École Élémentaire',
        name_en: 'Elementary School',
        sort_order: 2,
        requires_atsem: false,
      }
      expect(() => CycleSchema.parse(mockCycle)).not.toThrow()
    })

    it('should reject cycle with old name field (schema drift detection)', () => {
      const oldSchemaCycle = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATERNELLE',
        name: 'Preschool', // OLD field - should fail
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => CycleSchema.parse(oldSchemaCycle)).toThrow()
    })
  })

  describe('NationalityTypeSchema', () => {
    it('should validate nationality type with bilingual names and sort_order', () => {
      const mockNationalityType = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'FRENCH',
        name_fr: 'Français',
        name_en: 'French',
        vat_applicable: false,
        sort_order: 1,
      }
      expect(() => NationalityTypeSchema.parse(mockNationalityType)).not.toThrow()
    })

    it('should validate nationality type with VAT applicable', () => {
      const mockNationalityType = {
        id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'SAUDI',
        name_fr: 'Saoudien',
        name_en: 'Saudi',
        vat_applicable: true,
        sort_order: 2,
      }
      expect(() => NationalityTypeSchema.parse(mockNationalityType)).not.toThrow()
    })

    it('should reject nationality type with old name field (schema drift detection)', () => {
      const oldSchemaNationalityType = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'FRENCH',
        name: 'French', // OLD field - should fail
        vat_applicable: false,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => NationalityTypeSchema.parse(oldSchemaNationalityType)).toThrow()
    })
  })

  describe('SubjectSchema', () => {
    it('should validate subject with bilingual names and is_active', () => {
      const mockSubject = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATH',
        name_fr: 'Mathématiques',
        name_en: 'Mathematics',
        category: 'CORE',
        is_active: true,
      }
      expect(() => SubjectSchema.parse(mockSubject)).not.toThrow()
    })

    it('should validate inactive subject', () => {
      const mockSubject = {
        id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'LATIN',
        name_fr: 'Latin',
        name_en: 'Latin',
        category: 'ELECTIVE',
        is_active: false,
      }
      expect(() => SubjectSchema.parse(mockSubject)).not.toThrow()
    })

    it('should reject subject with old name and display_order fields (schema drift detection)', () => {
      const oldSchemaSubject = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATH',
        name: 'Mathematics', // OLD field - should fail
        category: 'CORE',
        display_order: 1, // OLD field - should fail
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => SubjectSchema.parse(oldSchemaSubject)).toThrow()
    })
  })

  describe('ClassStructureSchema', () => {
    it('should validate class structure with all required fields', () => {
      const mockClassStructure = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174002',
        total_students: 75,
        number_of_classes: 3,
        avg_class_size: 25,
        requires_atsem: false,
        atsem_count: 0,
        calculation_method: 'manual',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => ClassStructureSchema.parse(mockClassStructure)).not.toThrow()
    })

    it('should validate class structure with ATSEM requirements', () => {
      const mockClassStructure = {
        id: '123e4567-e89b-12d3-a456-426614174003',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174004',
        total_students: 60,
        number_of_classes: 3,
        avg_class_size: 20,
        requires_atsem: true,
        atsem_count: 3,
        calculation_method: 'auto',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => ClassStructureSchema.parse(mockClassStructure)).not.toThrow()
    })

    it('should reject class structure missing new required fields (schema drift detection)', () => {
      const oldSchemaClassStructure = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174002',
        number_of_classes: 3,
        avg_class_size: 25,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        // Missing: total_students, requires_atsem, atsem_count, calculation_method
      }
      expect(() => ClassStructureSchema.parse(oldSchemaClassStructure)).toThrow()
    })
  })

  describe('EnrollmentSchema', () => {
    it('should validate enrollment data', () => {
      const mockEnrollment = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174002',
        nationality_type_id: '123e4567-e89b-12d3-a456-426614174003',
        student_count: 45,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => EnrollmentSchema.parse(mockEnrollment)).not.toThrow()
    })
  })

  describe('TeacherCostParamSchema', () => {
    it('should validate teacher cost parameters', () => {
      const mockTeacherCost = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        category_id: '123e4567-e89b-12d3-a456-426614174002',
        cycle_id: '123e4567-e89b-12d3-a456-426614174003',
        prrd_contribution_eur: 41863.0,
        avg_salary_sar: 180000.0,
        social_charges_rate: 0.22,
        benefits_allowance_sar: 24000.0,
        hsa_hourly_rate_sar: 150.0,
        max_hsa_hours: 4.0,
        notes: 'AEFE detached teachers',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => TeacherCostParamSchema.parse(mockTeacherCost)).not.toThrow()
    })

    it('should validate teacher cost with null cycle_id (all cycles)', () => {
      const mockTeacherCost = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        category_id: '123e4567-e89b-12d3-a456-426614174002',
        cycle_id: null,
        prrd_contribution_eur: 0,
        avg_salary_sar: 120000.0,
        social_charges_rate: 0.18,
        benefits_allowance_sar: 12000.0,
        hsa_hourly_rate_sar: 100.0,
        max_hsa_hours: 2.0,
        notes: 'Local teachers - all cycles',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => TeacherCostParamSchema.parse(mockTeacherCost)).not.toThrow()
    })
  })

  describe('TimetableConstraintSchema', () => {
    it('should validate timetable constraints', () => {
      const mockConstraint = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174002',
        total_hours_per_week: 24.0,
        max_hours_per_day: 6.0,
        days_per_week: 5,
        requires_lunch_break: true,
        min_break_duration_minutes: 60,
        notes: 'Elementary schedule constraints',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => TimetableConstraintSchema.parse(mockConstraint)).not.toThrow()
    })

    it('should validate secondary school timetable constraints', () => {
      const mockConstraint = {
        id: '123e4567-e89b-12d3-a456-426614174003',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174004',
        total_hours_per_week: 30.0,
        max_hours_per_day: 7.0,
        days_per_week: 5,
        requires_lunch_break: true,
        min_break_duration_minutes: 45,
        notes: 'Secondary schedule constraints',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => TimetableConstraintSchema.parse(mockConstraint)).not.toThrow()
    })
  })

  describe('SubjectHoursSchema', () => {
    it('should validate subject hours', () => {
      const mockSubjectHours = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        subject_id: '123e4567-e89b-12d3-a456-426614174002',
        level_id: '123e4567-e89b-12d3-a456-426614174003',
        hours_per_week: 4.5,
        is_split: false,
        notes: 'Standard math hours',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => SubjectHoursSchema.parse(mockSubjectHours)).not.toThrow()
    })

    it('should validate subject hours with split class (dédoublement)', () => {
      const mockSubjectHours = {
        id: '123e4567-e89b-12d3-a456-426614174004',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        subject_id: '123e4567-e89b-12d3-a456-426614174005',
        level_id: '123e4567-e89b-12d3-a456-426614174003',
        hours_per_week: 2.0,
        is_split: true,
        notes: 'Sciences split for practical work',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => SubjectHoursSchema.parse(mockSubjectHours)).not.toThrow()
    })
  })

  describe('Schema Completeness Checks', () => {
    it('BudgetVersionSchema should have all 5 status values', () => {
      const schema = BudgetVersionSchema
      // Test each status is valid
      const statuses = ['working', 'submitted', 'approved', 'forecast', 'superseded']
      statuses.forEach((status) => {
        const testData = {
          id: '123e4567-e89b-12d3-a456-426614174000',
          name: 'Test',
          fiscal_year: 2025,
          academic_year: '2024-2025',
          status,
          scenario_type: 'BUDGET',
          submitted_at: null,
          approved_at: null,
          is_baseline: false,
          parent_version_id: null,
          organization_id: '123e4567-e89b-12d3-a456-426614174099',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          notes: null,
        }
        expect(() => schema.parse(testData)).not.toThrow()
      })
    })

    it('LevelSchema should require is_secondary boolean field', () => {
      const missingIsSecondary = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        cycle_id: '123e4567-e89b-12d3-a456-426614174001',
        code: 'CP',
        name_fr: 'Cours Préparatoire',
        name_en: 'Preparatory Course',
        sort_order: 1,
        // Missing is_secondary
      }
      expect(() => LevelSchema.parse(missingIsSecondary)).toThrow()
    })

    it('CycleSchema should require requires_atsem boolean field', () => {
      const missingRequiresAtsem = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATERNELLE',
        name_fr: 'École Maternelle',
        name_en: 'Preschool',
        sort_order: 1,
        // Missing requires_atsem
      }
      expect(() => CycleSchema.parse(missingRequiresAtsem)).toThrow()
    })

    it('SubjectSchema should require is_active boolean field', () => {
      const missingIsActive = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        code: 'MATH',
        name_fr: 'Mathématiques',
        name_en: 'Mathematics',
        category: 'CORE',
        // Missing is_active
      }
      expect(() => SubjectSchema.parse(missingIsActive)).toThrow()
    })

    it('ClassStructureSchema should require calculation_method field', () => {
      const missingCalculationMethod = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        version_id: '123e4567-e89b-12d3-a456-426614174001',
        level_id: '123e4567-e89b-12d3-a456-426614174002',
        total_students: 75,
        number_of_classes: 3,
        avg_class_size: 25,
        requires_atsem: false,
        atsem_count: 0,
        // Missing calculation_method
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }
      expect(() => ClassStructureSchema.parse(missingCalculationMethod)).toThrow()
    })
  })
})
