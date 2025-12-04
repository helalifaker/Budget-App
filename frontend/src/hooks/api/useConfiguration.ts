import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { configurationApi } from '@/services/configuration'
import { toastMessages } from '@/lib/toast-messages'

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
}

export function useLevels() {
  return useQuery({
    queryKey: configurationKeys.levels(),
    queryFn: () => configurationApi.levels.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
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

export function useNationalityTypes() {
  return useQuery({
    queryKey: configurationKeys.nationalityTypes(),
    queryFn: () => configurationApi.nationalityTypes.getAll(),
    staleTime: 30 * 60 * 1000,
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

export function useCycles() {
  return useQuery({
    queryKey: configurationKeys.cycles(),
    queryFn: () => configurationApi.cycles.getAll(),
    staleTime: 30 * 60 * 1000,
  })
}

export function useClassSizeParams(budgetVersionId: string) {
  return useQuery({
    queryKey: configurationKeys.classSizeParams(budgetVersionId),
    queryFn: () => configurationApi.classSizeParams.getAll(budgetVersionId),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
  })
}

export function useUpdateClassSizeParam() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: Partial<import('@/types/api').ClassSizeParam>
    }) => configurationApi.classSizeParams.update(id, data),
    onSuccess: () => {
      // Invalidate the class size params query for the affected budget version
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' && query.queryKey[1] === 'class-size-params',
      })
      toastMessages.success.updated('Paramètre de taille de classe')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

export function useSubjects() {
  return useQuery({
    queryKey: configurationKeys.subjects(),
    queryFn: () => configurationApi.subjects.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - subjects rarely change
  })
}

export function useSubjectHours(budgetVersionId: string) {
  return useQuery({
    queryKey: configurationKeys.subjectHours(budgetVersionId),
    queryFn: () => configurationApi.subjectHours.getAll(budgetVersionId),
    enabled: !!budgetVersionId,
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
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

export function useTeacherCategories() {
  return useQuery({
    queryKey: configurationKeys.teacherCategories(),
    queryFn: () => configurationApi.teacherCategories.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - teacher categories rarely change
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
    onSuccess: () => {
      // Invalidate the teacher costs query for the affected budget version
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' && query.queryKey[1] === 'teacher-costs',
      })
      toastMessages.success.updated('Paramètre de coûts enseignants')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

export function useFeeCategories() {
  return useQuery({
    queryKey: configurationKeys.feeCategories(),
    queryFn: () => configurationApi.feeCategories.getAll(),
    staleTime: 30 * 60 * 1000,
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
    mutationFn: (data: Partial<import('@/types/api').FeeStructure> & { id: string }) =>
      configurationApi.feeStructure.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: configurationKeys.all,
        predicate: (query) =>
          query.queryKey[0] === 'configuration' && query.queryKey[1] === 'fee-structure',
      })
      toastMessages.success.updated('Structure tarifaire')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}
