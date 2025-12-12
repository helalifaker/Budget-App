import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { enrollmentProjectionApi } from '@/services/enrollmentProjection'
import { handleAPIErrorToast, toastMessages } from '@/lib/toast-messages'
import type {
  GradeOverride,
  GlobalOverrides,
  LevelOverride,
  ProjectionConfig,
} from '@/types/enrollmentProjection'

type LevelOverrideUpdate = Pick<LevelOverride, 'cycle_id' | 'class_size_ceiling' | 'max_divisions'>
type GradeOverrideUpdate = Pick<
  GradeOverride,
  'level_id' | 'retention_rate' | 'lateral_entry' | 'max_divisions' | 'class_size_ceiling'
>

export const projectionKeys = {
  all: ['enrollment-projection'] as const,
  scenarios: () => [...projectionKeys.all, 'scenarios'] as const,
  config: (versionId: string) => [...projectionKeys.all, 'config', versionId] as const,
  results: (versionId: string) => [...projectionKeys.all, 'results', versionId] as const,
}

export function useEnrollmentScenarios() {
  return useQuery({
    queryKey: projectionKeys.scenarios(),
    queryFn: enrollmentProjectionApi.getScenarios,
    staleTime: Infinity,
  })
}

export function useEnrollmentProjectionConfig(versionId: string | undefined) {
  return useQuery({
    queryKey: projectionKeys.config(versionId ?? ''),
    queryFn: () => enrollmentProjectionApi.getConfig(versionId!),
    enabled: !!versionId,
    // PERFORMANCE FIX: 30s staleTime prevents rapid refetches during UI interactions
    staleTime: 30_000,
  })
}

export function useEnrollmentProjectionResults(
  versionId: string | undefined,
  includeFiscalProration = true
) {
  return useQuery({
    queryKey: projectionKeys.results(versionId ?? ''),
    queryFn: () => enrollmentProjectionApi.getResults(versionId!, includeFiscalProration),
    enabled: !!versionId,
    // PERFORMANCE FIX: 30s staleTime prevents rapid refetches during UI interactions
    staleTime: 30_000,
  })
}

export function useUpdateProjectionConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Partial<ProjectionConfig>
    }) => enrollmentProjectionApi.updateConfig(versionId, updates),

    // PERFORMANCE FIX: Optimistic update for instant UI feedback
    // This makes scenario changes feel instant (~50ms) instead of waiting 1-2s for server
    onMutate: async ({ versionId, updates }) => {
      // Cancel any outgoing refetches to prevent overwriting our optimistic update
      await queryClient.cancelQueries({ queryKey: projectionKeys.config(versionId) })

      // Snapshot the previous value for rollback on error
      const previousConfig = queryClient.getQueryData<ProjectionConfig>(
        projectionKeys.config(versionId)
      )

      // Optimistically update the cache with new values
      if (previousConfig) {
        queryClient.setQueryData<ProjectionConfig>(projectionKeys.config(versionId), {
          ...previousConfig,
          ...updates,
        })
      }

      // Return context with previous value for rollback
      return { previousConfig }
    },

    onSuccess: (data, variables) => {
      // Replace optimistic data with actual server response
      // This ensures we have the complete, correct data
      queryClient.setQueryData(projectionKeys.config(variables.versionId), data)
      toastMessages.success.updated('Projection config')
    },

    onError: (error, variables, context) => {
      // Rollback to previous value on error
      if (context?.previousConfig) {
        queryClient.setQueryData(projectionKeys.config(variables.versionId), context.previousConfig)
      }
      handleAPIErrorToast(error)
    },
  })
}

export function useUpdateGlobalOverrides() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ versionId, overrides }: { versionId: string; overrides: GlobalOverrides }) =>
      enrollmentProjectionApi.updateGlobalOverrides(versionId, overrides),
    onSuccess: (_, variables) => {
      // FIX Issue #3: Only invalidate config - results are recalculated on-demand
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(variables.versionId) })
      toastMessages.success.updated('Global overrides')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useUpdateLevelOverrides() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      versionId,
      overrides,
    }: {
      versionId: string
      overrides: LevelOverrideUpdate[]
    }) => enrollmentProjectionApi.updateLevelOverrides(versionId, overrides),
    onSuccess: (_, variables) => {
      // FIX Issue #3: Only invalidate config - results are recalculated on-demand
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(variables.versionId) })
      toastMessages.success.updated('Level overrides')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useUpdateGradeOverrides() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      versionId,
      overrides,
    }: {
      versionId: string
      overrides: GradeOverrideUpdate[]
    }) => enrollmentProjectionApi.updateGradeOverrides(versionId, overrides),
    onSuccess: (_, variables) => {
      // FIX Issue #3: Only invalidate config - results are recalculated on-demand
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(variables.versionId) })
      toastMessages.success.updated('Grade overrides')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useCalculateProjections() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (versionId: string) => enrollmentProjectionApi.calculate(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId) })
      toastMessages.success.calculated()
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useValidateProjections() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ versionId, confirmation }: { versionId: string; confirmation: boolean }) =>
      enrollmentProjectionApi.validate(versionId, confirmation),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(variables.versionId) })
      toastMessages.success.updated('Projection validated')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useUnvalidateProjections() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (versionId: string) => enrollmentProjectionApi.unvalidate(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId) })
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId) })
      toastMessages.success.updated('Projection unvalidated')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}
