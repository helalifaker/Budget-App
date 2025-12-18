import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { enrollmentProjectionApi } from '@/services/enrollment-projection'
import { handleAPIErrorToast, toastMessages } from '@/lib/toast-messages'
import type {
  GradeOverride,
  GlobalOverrides,
  LateralOptimizationResults,
  LevelOverride,
  ProjectionConfig,
} from '@/types/enrollment-projection'

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
  lateralOptimization: (versionId: string) =>
    [...projectionKeys.all, 'lateral-optimization', versionId] as const,
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
    // PERFORMANCE FIX (Phase 12): Prevent request cascades during re-renders
    staleTime: 5 * 60 * 1000, // 5 minutes - enrollment config changes rarely
    refetchOnMount: false, // Don't refetch on component mount
    refetchOnWindowFocus: false, // Don't refetch on window focus
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
    // PERFORMANCE FIX (Phase 12): Prevent request cascades during re-renders
    staleTime: 5 * 60 * 1000, // 5 minutes - projection results change rarely
    refetchOnMount: false, // Don't refetch on component mount
    refetchOnWindowFocus: false, // Don't refetch on window focus
  })
}

/**
 * Hook for fetching lateral entry optimization results.
 *
 * This provides capacity-aware lateral entry optimization data that helps
 * schools understand how many new students can be efficiently accommodated
 * while minimizing rejections and maintaining optimal class structure.
 *
 * Returns:
 * - optimization_results: Per-grade optimization decisions and capacities
 * - new_students_summary: Summary table with totals and breakdowns
 */
export function useLateralOptimization(
  versionId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery<LateralOptimizationResults>({
    queryKey: projectionKeys.lateralOptimization(versionId ?? ''),
    queryFn: () => enrollmentProjectionApi.getLateralOptimization(versionId!),
    enabled: !!versionId && (options?.enabled ?? true),
    // Lateral optimization depends on projection config, cache for same duration
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnMount: false,
    refetchOnWindowFocus: false,
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
    onSuccess: (data, variables) => {
      // PERFORMANCE FIX (Phase 12): Use setQueryData instead of invalidateQueries
      // This prevents unnecessary refetch since backend returns updated config
      queryClient.setQueryData(projectionKeys.config(variables.versionId), data)
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
    onSuccess: (data, variables) => {
      // PERFORMANCE FIX (Phase 12): Use setQueryData instead of invalidateQueries
      // This prevents unnecessary refetch since backend returns updated config
      queryClient.setQueryData(projectionKeys.config(variables.versionId), data)
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
    onSuccess: (data, variables) => {
      // PERFORMANCE FIX (Phase 12): Use setQueryData instead of invalidateQueries
      // This prevents unnecessary refetch since backend returns updated config
      queryClient.setQueryData(projectionKeys.config(variables.versionId), data)
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

// =============================================================================
// PERFORMANCE: Draft + Apply Pattern (BFF Hooks)
//
// These hooks support the "Auto-Draft + Manual Apply" UX pattern:
// - useSaveDraft: Debounced background save without calculations
// - useApplyAndCalculate: BFF endpoint for commit + calculate in one request
// =============================================================================

/**
 * Hook for saving draft configuration without triggering calculations.
 * Use this for debounced auto-save as user edits form fields.
 *
 * This mutation:
 * - Does NOT show toast notifications (silent background save)
 * - Updates the cache optimistically for instant UI feedback
 * - Does NOT invalidate results (no expensive recalculation)
 */
export function useSaveDraft() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Partial<ProjectionConfig>
    }) => enrollmentProjectionApi.saveDraft(versionId, updates),

    // Optimistic update for instant UI feedback
    onMutate: async ({ versionId, updates }) => {
      await queryClient.cancelQueries({ queryKey: projectionKeys.config(versionId) })

      const previousConfig = queryClient.getQueryData<ProjectionConfig>(
        projectionKeys.config(versionId)
      )

      if (previousConfig) {
        queryClient.setQueryData<ProjectionConfig>(projectionKeys.config(versionId), {
          ...previousConfig,
          ...updates,
        })
      }

      return { previousConfig }
    },

    onSuccess: (data, variables) => {
      // Update cache with server response (no toast - silent save)
      queryClient.setQueryData(projectionKeys.config(variables.versionId), data)
    },

    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousConfig) {
        queryClient.setQueryData(projectionKeys.config(variables.versionId), context.previousConfig)
      }
      handleAPIErrorToast(error)
    },
  })
}

/**
 * Hook for applying draft changes and running full projection calculation.
 * This is the "Apply & Calculate" action that users explicitly trigger.
 *
 * This mutation:
 * - Saves any final updates (if provided)
 * - Runs full projection calculation
 * - Invalidates results cache to show new projections
 * - Shows success toast when complete
 */
export function useApplyAndCalculate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates?: Partial<ProjectionConfig>
    }) => enrollmentProjectionApi.applyAndCalculate(versionId, updates),

    onSuccess: (data, variables) => {
      // Update results cache with new projection data
      queryClient.setQueryData(projectionKeys.results(variables.versionId), data)
      // Also refresh config in case it changed
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(variables.versionId) })
      toastMessages.success.calculated()
    },

    onError: (error) => handleAPIErrorToast(error),
  })
}
