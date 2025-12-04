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
} from '@/types/api'

export const configurationApi = {
  levels: {
    getAll: async () => {
      return apiRequest<Level[]>({
        method: 'GET',
        url: '/configuration/levels',
      })
    },

    getById: async (id: string) => {
      return apiRequest<Level>({
        method: 'GET',
        url: `/configuration/levels/${id}`,
      })
    },

    getByCycle: async (cycleId: string) => {
      return apiRequest<Level[]>({
        method: 'GET',
        url: `/configuration/levels/cycle/${cycleId}`,
      })
    },
  },

  nationalityTypes: {
    getAll: async () => {
      return apiRequest<NationalityType[]>({
        method: 'GET',
        url: '/configuration/nationality-types',
      })
    },

    getById: async (id: string) => {
      return apiRequest<NationalityType>({
        method: 'GET',
        url: `/configuration/nationality-types/${id}`,
      })
    },
  },

  cycles: {
    getAll: async () => {
      return apiRequest<Cycle[]>({
        method: 'GET',
        url: '/configuration/cycles',
      })
    },
  },

  classSizeParams: {
    getAll: async (budgetVersionId: string) => {
      return apiRequest<ClassSizeParam[]>({
        method: 'GET',
        url: `/configuration/class-size-params?budget_version_id=${budgetVersionId}`,
      })
    },

    update: async (id: string, data: Partial<ClassSizeParam>) => {
      return apiRequest<ClassSizeParam>({
        method: 'PUT',
        url: `/configuration/class-size-params/${id}`,
        data,
      })
    },
  },

  subjects: {
    getAll: async () => {
      return apiRequest<Subject[]>({
        method: 'GET',
        url: '/configuration/subjects',
      })
    },
  },

  subjectHours: {
    getAll: async (budgetVersionId: string) => {
      return apiRequest<SubjectHours[]>({
        method: 'GET',
        url: `/configuration/subject-hours?version_id=${budgetVersionId}`,
      })
    },

    update: async (data: {
      budget_version_id: string
      subject_id: string
      level_id: string
      hours_per_week: number
      is_split: boolean
      notes?: string | null
    }) => {
      return apiRequest<SubjectHours>({
        method: 'PUT',
        url: '/configuration/subject-hours',
        data,
      })
    },
  },

  teacherCategories: {
    getAll: async () => {
      return apiRequest<TeacherCategory[]>({
        method: 'GET',
        url: '/configuration/teacher-categories',
      })
    },
  },

  teacherCosts: {
    getAll: async (budgetVersionId: string) => {
      return apiRequest<TeacherCostParam[]>({
        method: 'GET',
        url: `/configuration/teacher-costs?version_id=${budgetVersionId}`,
      })
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
      return apiRequest<TeacherCostParam>({
        method: 'PUT',
        url: '/configuration/teacher-costs',
        data,
      })
    },
  },

  feeCategories: {
    getAll: async () => {
      return apiRequest<FeeCategory[]>({
        method: 'GET',
        url: '/configuration/fee-categories',
      })
    },
  },

  feeStructure: {
    getAll: async (budgetVersionId: string) => {
      return apiRequest<FeeStructure[]>({
        method: 'GET',
        url: `/configuration/fee-structure?budget_version_id=${budgetVersionId}`,
      })
    },

    update: async (data: Partial<FeeStructure> & { id: string }) => {
      return apiRequest<FeeStructure>({
        method: 'PUT',
        url: '/configuration/fee-structure',
        data,
      })
    },
  },
}
