import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { configurationApi } from '@/services/configuration'
import { toastMessages } from '@/lib/toast-messages'
import { useAuth } from '@/contexts/AuthContext'
import type { SystemConfig } from '@/types/api'

export const configurationKeys = {
  all: ['configuration'] as const,
  levels: () => [...configurationKeys.all, 'levels'] as const,
  level: (id: string) => [...configurationKeys.levels(), id] as const,
  levelsByCycle: (cycleId: string) => [...configurationKeys.levels(), 'cycle', cycleId] as const,
  nationalityTypes: () => [...configurationKeys.all, 'nationality-types'] as const,
  nationalityType: (id: string) => [...configurationKeys.nationalityTypes(), id] as const,
  cycles: () => [...configurationKeys.all, 'cycles'] as const,
  classSizeParams: (budgetVersionId: string) =>
    [...configurationKeys.all, 'class-size-params', budgetVersionId] as const,
  subjects: () => [...configurationKeys.all, 'subjects'] as const,
  subjectHours: (budgetVersionId: string) =>
    [...configurationKeys.all, 'subject-hours', budgetVersionId] as const,
  subjectHoursMatrix: (budgetVersionId: string, cycleCode: string) =>
    [...configurationKeys.all, 'subject-hours-matrix', budgetVersionId, cycleCode] as const,
  curriculumTemplates: () => [...configurationKeys.all, 'curriculum-templates'] as const,
  teacherCategories: () => [...configurationKeys.all, 'teacher-categories'] as const,
  teacherCosts: (budgetVersionId?: string) =>
    budgetVersionId
      ? ([...configurationKeys.all, 'teacher-costs', budgetVersionId] as const)
      : ([...configurationKeys.all, 'teacher-costs'] as const),
  feeCategories: () => [...configurationKeys.all, 'fee-categories'] as const,
  feeStructure: (budgetVersionId?: string) =>
    budgetVersionId
      ? ([...configurationKeys.all, 'fee-structure', budgetVersionId] as const)
      : ([...configurationKeys.all, 'fee-structure'] as const),
  systemConfigs: (category?: string) =>
    category
      ? ([...configurationKeys.all, 'system-configs', category] as const)
      : ([...configurationKeys.all, 'system-configs'] as const),
  timetableConstraints: (budgetVersionId: string) =>
    [...configurationKeys.all, 'timetable-constraints', budgetVersionId] as const,
}

/**
 * Fetch all levels with authentication check.
 * Query is disabled until session is available to prevent race conditions.
 */
export function useLevels() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.levels(),
    queryFn: () => configurationApi.levels.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
    enabled: !!session && !loading,
  })
}

export function useLevel(id: string) {
  return useQuery({
    queryKey: configurationKeys.level(id),
    queryFn: () => configurationApi.levels.getById(id),
    enabled: !!id,
    staleTime: 30 * 60 * 1000,
  })
}

export function useLevelsByCycle(cycleId: string) {
  return useQuery({
    queryKey: configurationKeys.levelsByCycle(cycleId),
    queryFn: () => configurationApi.levels.getByCycle(cycleId),
    enabled: !!cycleId,
    staleTime: 30 * 60 * 1000,
  })
}

/**
 * Fetch all nationality types with authentication check.
 */
export function useNationalityTypes() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.nationalityTypes(),
    queryFn: () => configurationApi.nationalityTypes.getAll(),
    staleTime: 30 * 60 * 1000,
    enabled: !!session && !loading,
  })
}

export function useNationalityType(id: string) {
  return useQuery({
    queryKey: configurationKeys.nationalityType(id),
    queryFn: () => configurationApi.nationalityTypes.getById(id),
    enabled: !!id,
    staleTime: 30 * 60 * 1000,
  })
}

/**
 * Fetch all cycles with authentication check.
 */
export function useCycles() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.cycles(),
    queryFn: () => configurationApi.cycles.getAll(),
    staleTime: 30 * 60 * 1000,
    enabled: !!session && !loading,
  })
}

export function useClassSizeParams(budgetVersionId: string | undefined) {
  return useQuery({
    queryKey: configurationKeys.classSizeParams(budgetVersionId ?? ''),
    queryFn: () => configurationApi.classSizeParams.getAll(budgetVersionId!),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
  })
}

export function useCreateClassSizeParam() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      level_id: string | null
      cycle_id: string | null
      min_class_size: number
      target_class_size: number
      max_class_size: number
      notes?: string | null
    }) => configurationApi.classSizeParams.create(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.classSizeParams(variables.budget_version_id),
      })
      toastMessages.success.created('Paramètre de taille de classe')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

export function useUpdateClassSizeParam() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      level_id: string | null
      cycle_id: string | null
      min_class_size: number
      target_class_size: number
      max_class_size: number
      notes?: string | null
    }) => configurationApi.classSizeParams.update(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.classSizeParams(variables.budget_version_id),
      })
      toastMessages.success.updated('Paramètre de taille de classe')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

export function useDeleteClassSizeParam() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id }: { id: string; budgetVersionId: string }) =>
      configurationApi.classSizeParams.delete(id),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.classSizeParams(variables.budgetVersionId),
      })
      toastMessages.success.deleted('Paramètre de taille de classe')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Fetch all subjects with authentication check.
 */
export function useSubjects() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.subjects(),
    queryFn: () => configurationApi.subjects.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - subjects rarely change
    enabled: !!session && !loading,
  })
}

export function useSubjectHours(budgetVersionId: string | undefined) {
  return useQuery({
    queryKey: configurationKeys.subjectHours(budgetVersionId ?? ''),
    queryFn: () => configurationApi.subjectHours.getAll(budgetVersionId!),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
  })
}

export function useCreateSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      subject_id: string
      level_id: string
      hours_per_week: number
      is_split: boolean
      notes?: string | null
    }) => configurationApi.subjectHours.create(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.subjectHours(variables.budget_version_id),
      })
      toastMessages.success.created('Heures par matière')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

export function useUpdateSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      subject_id: string
      level_id: string
      hours_per_week: number
      is_split: boolean
      notes?: string | null
    }) => configurationApi.subjectHours.update(data),
    onSuccess: () => {
      // Invalidate the subject hours query for the affected budget version
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' && query.queryKey[1] === 'subject-hours',
      })
      toastMessages.success.updated('Heures par matière')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ==============================================================================
// Subject Hours Matrix Hooks (Cycle-Based Matrix View)
// ==============================================================================

/**
 * Fetch subject hours matrix by cycle for a budget version.
 * Returns all subjects with hours organized by level columns.
 */
export function useSubjectHoursMatrix(budgetVersionId: string | null, cycleCode: string | null) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.subjectHoursMatrix(budgetVersionId ?? '', cycleCode ?? ''),
    queryFn: () => configurationApi.subjectHours.getMatrix(budgetVersionId!, cycleCode!),
    enabled: !!budgetVersionId && !!cycleCode && !!session && !loading,
    staleTime: 5 * 60 * 1000, // 5 minutes - matrix may be edited frequently
  })
}

/**
 * Batch save subject hours entries (up to 200 at a time).
 * Handles creates, updates, and deletes in a single transaction.
 */
export function useBatchSaveSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: configurationApi.subjectHours.batchSave,
    onSuccess: (_data, variables) => {
      // Invalidate all subject hours queries for this version
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' &&
          (query.queryKey[1] === 'subject-hours' || query.queryKey[1] === 'subject-hours-matrix') &&
          query.queryKey[2] === variables.budget_version_id,
      })
      toastMessages.success.updated('Heures par matière')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Fetch available curriculum templates.
 * Templates are static server-side data.
 */
export function useCurriculumTemplates() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.curriculumTemplates(),
    queryFn: () => configurationApi.subjectHours.getTemplates(),
    enabled: !!session && !loading,
    staleTime: 60 * 60 * 1000, // 1 hour - templates are static
  })
}

/**
 * Apply a curriculum template to populate subject hours.
 */
export function useApplyTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: configurationApi.subjectHours.applyTemplate,
    onSuccess: (data, variables) => {
      // Invalidate all subject hours queries for this version
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' &&
          (query.queryKey[1] === 'subject-hours' || query.queryKey[1] === 'subject-hours-matrix') &&
          query.queryKey[2] === variables.budget_version_id,
      })
      toastMessages.success.custom(
        `Applied template "${data.template_name}": ${data.applied_count} entries created, ${data.skipped_count} skipped`
      )
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Create a new custom subject.
 */
export function useCreateSubject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: configurationApi.subjects.create,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.subjects(),
      })
      toastMessages.success.created('Matière')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Fetch all teacher categories with authentication check.
 */
export function useTeacherCategories() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.teacherCategories(),
    queryFn: () => configurationApi.teacherCategories.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - teacher categories rarely change
    enabled: !!session && !loading,
  })
}

export function useTeacherCosts(budgetVersionId: string) {
  return useQuery({
    queryKey: configurationKeys.teacherCosts(budgetVersionId),
    queryFn: () => configurationApi.teacherCosts.getAll(budgetVersionId),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
  })
}

export function useUpdateTeacherCost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
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
    }) => configurationApi.teacherCosts.update(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.teacherCosts(variables.budget_version_id),
      })
      toastMessages.success.updated('Paramètre de coûts enseignants')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Fetch all fee categories with authentication check.
 */
export function useFeeCategories() {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.feeCategories(),
    queryFn: () => configurationApi.feeCategories.getAll(),
    staleTime: 30 * 60 * 1000,
    enabled: !!session && !loading,
  })
}

export function useFeeStructure(budgetVersionId: string) {
  return useQuery({
    queryKey: configurationKeys.feeStructure(budgetVersionId),
    queryFn: () => configurationApi.feeStructure.getAll(budgetVersionId),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000,
  })
}

export function useUpdateFeeStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      level_id: string
      nationality_type_id: string
      fee_category_id: string
      amount_sar: number
      trimester?: number | null
      notes?: string | null
    }) => configurationApi.feeStructure.update(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.feeStructure(variables.budget_version_id),
      })
      toastMessages.success.updated('Structure tarifaire')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ============================================================================
// System Configuration (Module 1)
// ============================================================================

/**
 * Fetch system configurations with authentication check.
 */
export function useSystemConfigs(category?: string) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: configurationKeys.systemConfigs(category),
    queryFn: () => configurationApi.systemConfig.getAll(category),
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
    enabled: !!session && !loading,
  })
}

export function useUpdateSystemConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: Partial<SystemConfig> }) =>
      configurationApi.systemConfig.update(key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.systemConfigs(),
      })
      toastMessages.success.updated('Configuration système')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ============================================================================
// Timetable Constraints (Module 6)
// ============================================================================

export function useTimetableConstraints(budgetVersionId: string) {
  return useQuery({
    queryKey: configurationKeys.timetableConstraints(budgetVersionId),
    queryFn: () => configurationApi.timetableConstraints.getAll(budgetVersionId),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000,
  })
}

export function useUpdateTimetableConstraint() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      budget_version_id: string
      level_id: string
      total_hours_per_week: number
      max_hours_per_day: number
      days_per_week: number
      requires_lunch_break: boolean
      min_break_duration_minutes: number
      notes?: string | null
    }) => configurationApi.timetableConstraints.update(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.timetableConstraints(variables.budget_version_id),
      })
      toastMessages.success.updated('Contrainte horaire')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}
