import { apiRequest } from '@/lib/api-client'
import {
  Level,
  NationalityType,
  Cycle,
  ClassSizeParam,
  SubjectHours,
  Subject,
  TeacherCategory,
  TeacherCostParam,
  FeeCategory,
  FeeStructure,
  SystemConfig,
  TimetableConstraint,
  SubjectHoursMatrixResponse,
  SubjectHoursBatchRequest,
  SubjectHoursBatchResponse,
  TemplateInfo,
  ApplyTemplateResponse,
  SubjectCreateRequest,
} from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const configurationApi = {
  levels: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<Level[]>({
          method: 'GET',
          url: '/academic-levels',
        }),
        'configuration: get levels'
      )
    },

    getById: async (id: string) => {
      return withServiceErrorHandling(
        apiRequest<Level>({
          method: 'GET',
          url: `/academic-levels/${id}`,
        }),
        'configuration: get level'
      )
    },

    getByCycle: async (cycleId: string) => {
      return withServiceErrorHandling(
        apiRequest<Level[]>({
          method: 'GET',
          url: `/academic-levels?cycle_id=${cycleId}`,
        }),
        'configuration: get levels by cycle'
      )
    },
  },

  nationalityTypes: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<NationalityType[]>({
          method: 'GET',
          url: '/nationality-types',
        }),
        'configuration: get nationality types'
      )
    },

    getById: async (id: string) => {
      return withServiceErrorHandling(
        apiRequest<NationalityType>({
          method: 'GET',
          url: `/nationality-types/${id}`,
        }),
        'configuration: get nationality type'
      )
    },
  },

  cycles: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<Cycle[]>({
          method: 'GET',
          url: '/academic-cycles',
        }),
        'configuration: get cycles'
      )
    },
  },

  classSizeParams: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<ClassSizeParam[]>({
          method: 'GET',
          url: `/class-size-params?version_id=${budgetVersionId}`,
        }),
        'configuration: get class size params'
      )
    },

    create: async (data: {
      budget_version_id: string
      level_id: string | null
      cycle_id: string | null
      min_class_size: number
      target_class_size: number
      max_class_size: number
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<ClassSizeParam>({
          method: 'PUT',
          url: '/class-size-params',
          data,
        }),
        'configuration: create class size param'
      )
    },

    update: async (data: {
      budget_version_id: string
      level_id: string | null
      cycle_id: string | null
      min_class_size: number
      target_class_size: number
      max_class_size: number
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<ClassSizeParam>({
          method: 'PUT',
          url: '/class-size-params',
          data,
        }),
        'configuration: update class size param'
      )
    },

    delete: async (id: string) => {
      return withServiceErrorHandling(
        apiRequest<void>({
          method: 'DELETE',
          url: `/class-size-params/${id}`,
        }),
        'configuration: delete class size param'
      )
    },
  },

  subjectHours: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHours[]>({
          method: 'GET',
          url: `/subject-hours?version_id=${budgetVersionId}`,
        }),
        'configuration: get subject hours'
      )
    },

    create: async (data: {
      budget_version_id: string
      subject_id: string
      level_id: string
      hours_per_week: number
      is_split: boolean
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHours>({
          method: 'PUT',
          url: '/subject-hours',
          data,
        }),
        'configuration: create subject hours'
      )
    },

    update: async (data: {
      budget_version_id: string
      subject_id: string
      level_id: string
      hours_per_week: number
      is_split: boolean
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHours>({
          method: 'PUT',
          url: '/subject-hours',
          data,
        }),
        'configuration: update subject hours'
      )
    },

    // Matrix view by cycle (new endpoint)
    getMatrix: async (budgetVersionId: string, cycleCode: string) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHoursMatrixResponse>({
          method: 'GET',
          url: `/subject-hours/matrix?version_id=${budgetVersionId}&cycle_code=${cycleCode}`,
        }),
        'configuration: get subject hours matrix'
      )
    },

    // Batch save (up to 200 entries)
    batchSave: async (data: SubjectHoursBatchRequest) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHoursBatchResponse>({
          method: 'POST',
          url: '/subject-hours/batch',
          data,
        }),
        'configuration: batch save subject hours'
      )
    },

    // Get available curriculum templates
    getTemplates: async () => {
      return withServiceErrorHandling(
        apiRequest<TemplateInfo[]>({
          method: 'GET',
          url: '/subject-hours/templates',
        }),
        'configuration: get curriculum templates'
      )
    },

    // Apply curriculum template
    applyTemplate: async (data: {
      budget_version_id: string
      template_code: string
      cycle_codes: string[]
      overwrite_existing: boolean
    }) => {
      return withServiceErrorHandling(
        apiRequest<ApplyTemplateResponse>({
          method: 'POST',
          url: '/subject-hours/apply-template',
          data,
        }),
        'configuration: apply curriculum template'
      )
    },
  },

  subjects: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<Subject[]>({
          method: 'GET',
          url: '/subjects',
        }),
        'configuration: get subjects'
      )
    },

    // Create custom subject
    create: async (data: SubjectCreateRequest) => {
      return withServiceErrorHandling(
        apiRequest<Subject>({
          method: 'POST',
          url: '/subjects',
          data,
        }),
        'configuration: create subject'
      )
    },
  },

  teacherCategories: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<TeacherCategory[]>({
          method: 'GET',
          url: '/teacher-categories',
        }),
        'configuration: get teacher categories'
      )
    },
  },

  teacherCosts: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<TeacherCostParam[]>({
          method: 'GET',
          url: `/teacher-costs?version_id=${budgetVersionId}`,
        }),
        'configuration: get teacher cost params'
      )
    },

    update: async (data: {
      budget_version_id: string
      category_id: string
      cycle_id: string | null
      prrd_contribution_eur: number | null
      avg_salary_sar: number | null
      social_charges_rate: number
      benefits_allowance_sar: number
      hsa_hourly_rate_sar: number
      max_hsa_hours: number
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<TeacherCostParam>({
          method: 'PUT',
          url: '/teacher-costs',
          data,
        }),
        'configuration: upsert teacher cost param'
      )
    },
  },

  feeCategories: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<FeeCategory[]>({
          method: 'GET',
          url: '/fee-categories',
        }),
        'configuration: get fee categories'
      )
    },
  },

  feeStructure: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<FeeStructure[]>({
          method: 'GET',
          url: `/fee-structure?version_id=${budgetVersionId}`,
        }),
        'configuration: get fee structure'
      )
    },

    update: async (data: {
      budget_version_id: string
      level_id: string
      nationality_type_id: string
      fee_category_id: string
      amount_sar: number
      trimester?: number | null
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<FeeStructure>({
          method: 'PUT',
          url: '/fee-structure',
          data,
        }),
        'configuration: upsert fee structure'
      )
    },
  },

  // System Configuration (Module 1)
  systemConfig: {
    getAll: async (category?: string) => {
      const url = category ? `/config/system?category=${category}` : '/config/system'
      return withServiceErrorHandling(
        apiRequest<SystemConfig[]>({
          method: 'GET',
          url,
        }),
        'configuration: get system configs'
      )
    },

    getByKey: async (key: string) => {
      return withServiceErrorHandling(
        apiRequest<SystemConfig>({
          method: 'GET',
          url: `/config/system/${key}`,
        }),
        'configuration: get system config by key'
      )
    },

    update: async (key: string, data: Partial<SystemConfig>) => {
      return withServiceErrorHandling(
        apiRequest<SystemConfig>({
          method: 'PUT',
          url: `/config/system/${key}`,
          data,
        }),
        'configuration: update system config'
      )
    },
  },

  // Timetable Constraints (Module 6)
  timetableConstraints: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<TimetableConstraint[]>({
          method: 'GET',
          url: `/timetable-constraints?version_id=${budgetVersionId}`,
        }),
        'configuration: get timetable constraints'
      )
    },

    update: async (data: {
      budget_version_id: string
      level_id: string
      total_hours_per_week: number
      max_hours_per_day: number
      days_per_week: number
      requires_lunch_break: boolean
      min_break_duration_minutes: number
      notes?: string | null
    }) => {
      return withServiceErrorHandling(
        apiRequest<TimetableConstraint>({
          method: 'PUT',
          url: '/timetable-constraints',
          data,
        }),
        'configuration: upsert timetable constraint'
      )
    },
  },
}
