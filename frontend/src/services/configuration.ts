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
} from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const configurationApi = {
  levels: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<Level[]>({
          method: 'GET',
          url: '/configuration/levels',
        }),
        'configuration: get levels'
      )
    },

    getById: async (id: string) => {
      return withServiceErrorHandling(
        apiRequest<Level>({
          method: 'GET',
          url: `/configuration/levels/${id}`,
        }),
        'configuration: get level'
      )
    },

    getByCycle: async (cycleId: string) => {
      return withServiceErrorHandling(
        apiRequest<Level[]>({
          method: 'GET',
          url: `/configuration/levels/cycle/${cycleId}`,
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
          url: '/configuration/nationality-types',
        }),
        'configuration: get nationality types'
      )
    },

    getById: async (id: string) => {
      return withServiceErrorHandling(
        apiRequest<NationalityType>({
          method: 'GET',
          url: `/configuration/nationality-types/${id}`,
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
          url: '/configuration/cycles',
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
          url: `/configuration/class-size-params?budget_version_id=${budgetVersionId}`,
        }),
        'configuration: get class size params'
      )
    },

    update: async (id: string, data: Partial<ClassSizeParam>) => {
      return withServiceErrorHandling(
        apiRequest<ClassSizeParam>({
          method: 'PUT',
          url: `/configuration/class-size-params/${id}`,
          data,
        }),
        'configuration: update class size param'
      )
    },
  },

  subjects: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<Subject[]>({
          method: 'GET',
          url: '/configuration/subjects',
        }),
        'configuration: get subjects'
      )
    },
  },

  subjectHours: {
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<SubjectHours[]>({
          method: 'GET',
          url: `/configuration/subject-hours?version_id=${budgetVersionId}`,
        }),
        'configuration: get subject hours'
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
          url: '/configuration/subject-hours',
          data,
        }),
        'configuration: update subject hours'
      )
    },
  },

  teacherCategories: {
    getAll: async () => {
      return withServiceErrorHandling(
        apiRequest<TeacherCategory[]>({
          method: 'GET',
          url: '/configuration/teacher-categories',
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
          url: `/configuration/teacher-costs?version_id=${budgetVersionId}`,
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
          url: '/configuration/teacher-costs',
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
          url: '/configuration/fee-categories',
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
          url: `/configuration/fee-structure?version_id=${budgetVersionId}`,
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
          url: '/configuration/fee-structure',
          data,
        }),
        'configuration: upsert fee structure'
      )
    },
  },

  // System Configuration (Module 1)
  systemConfig: {
    getAll: async (category?: string) => {
      const url = category
        ? `/configuration/system-config?category=${category}`
        : '/configuration/system-config'
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
          url: `/configuration/system-config/${key}`,
        }),
        'configuration: get system config by key'
      )
    },

    update: async (key: string, data: Partial<SystemConfig>) => {
      return withServiceErrorHandling(
        apiRequest<SystemConfig>({
          method: 'PUT',
          url: `/configuration/system-config/${key}`,
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
          url: `/configuration/timetable-constraints?version_id=${budgetVersionId}`,
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
          url: '/configuration/timetable-constraints',
          data,
        }),
        'configuration: upsert timetable constraint'
      )
    },
  },
}
