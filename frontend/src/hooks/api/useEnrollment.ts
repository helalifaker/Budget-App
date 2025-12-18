import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { enrollmentApi } from '@/services/enrollment'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'

// PERFORMANCE: 10 minutes staleTime for enrollment data
// Enrollment changes rarely during a session, so we can cache it longer
const ENROLLMENT_STALE_TIME = 10 * 60 * 1000 // 10 minutes

export const enrollmentKeys = {
  all: ['enrollments'] as const,
  lists: () => [...enrollmentKeys.all, 'list'] as const,
  list: (versionId: string, filters: string) =>
    [...enrollmentKeys.lists(), versionId, { filters }] as const,
  byVersion: (versionId: string) => [...enrollmentKeys.all, 'by-version', versionId] as const,
  summary: (versionId: string) => [...enrollmentKeys.all, 'summary', versionId] as const,
  withDistribution: (versionId: string) =>
    [...enrollmentKeys.all, 'with-distribution', versionId] as const,
  distributions: (versionId: string) =>
    [...enrollmentKeys.all, 'distributions', versionId] as const,
}

export function useEnrollments(versionId: string | undefined, page = 1, pageSize = 100) {
  return useQuery({
    queryKey: enrollmentKeys.list(versionId ?? '', `page=${page}&pageSize=${pageSize}`),
    queryFn: () => enrollmentApi.getAll(versionId!, { page, page_size: pageSize }),
    enabled: !!versionId,
    staleTime: ENROLLMENT_STALE_TIME,
  })
}

export function useEnrollmentSummary(versionId: string | undefined) {
  return useQuery({
    queryKey: enrollmentKeys.summary(versionId ?? ''),
    queryFn: () => enrollmentApi.getSummary(versionId!),
    enabled: !!versionId,
    staleTime: ENROLLMENT_STALE_TIME,
  })
}

export function useCreateEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: enrollmentApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(data.version_id),
      })
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
      toastMessages.success.created(entityNames.enrollment)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useUpdateEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { student_count: number } }) =>
      enrollmentApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(data.version_id),
      })
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
      toastMessages.success.updated(entityNames.enrollment)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useDeleteEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: enrollmentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
      toastMessages.success.deleted(entityNames.enrollment)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useProjectEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      data,
    }: {
      versionId: string
      data: {
        years_to_project?: number
        growth_scenario?: string
        custom_growth_rates?: Record<string, number>
      }
    }) =>
      enrollmentApi.project(versionId, {
        years_to_project: data.years_to_project ?? 5,
        growth_scenario: data.growth_scenario ?? 'moderate',
        custom_growth_rates: data.custom_growth_rates,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.summary(variables.versionId),
      })
      toastMessages.success.calculated()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// =============================================================================
// Enrollment with Distribution Hooks
// =============================================================================

/**
 * Fetch complete enrollment data with nationality distributions and breakdown.
 * Used for the enrollment planning grid UI.
 */
export function useEnrollmentWithDistribution(versionId: string | undefined) {
  return useQuery({
    queryKey: enrollmentKeys.withDistribution(versionId ?? ''),
    queryFn: () => enrollmentApi.getWithDistribution(versionId!),
    enabled: !!versionId,
    staleTime: ENROLLMENT_STALE_TIME,
  })
}

/**
 * Fetch nationality distributions for a budget version.
 */
export function useDistributions(versionId: string | undefined) {
  return useQuery({
    queryKey: enrollmentKeys.distributions(versionId ?? ''),
    queryFn: () => enrollmentApi.getDistributions(versionId!),
    enabled: !!versionId,
    staleTime: ENROLLMENT_STALE_TIME,
  })
}

/**
 * Bulk upsert enrollment totals by level.
 * Distributes students according to nationality percentages.
 */
export function useBulkUpsertEnrollmentTotals() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      totals,
    }: {
      versionId: string
      totals: Array<{ level_id: string; total_students: number }>
    }) => enrollmentApi.bulkUpsertTotals(versionId, totals),
    onSuccess: (_, variables) => {
      // Invalidate all enrollment-related queries for this version
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.withDistribution(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.summary(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.lists(),
      })
      toastMessages.success.updated(entityNames.enrollment)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

/**
 * Bulk upsert nationality distributions.
 * Each distribution must have percentages summing to 100%.
 */
export function useBulkUpsertDistributions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      distributions,
    }: {
      versionId: string
      distributions: Array<{
        level_id: string
        french_pct: number
        saudi_pct: number
        other_pct: number
      }>
    }) => enrollmentApi.bulkUpsertDistributions(versionId, distributions),
    onSuccess: (_, variables) => {
      // Invalidate distribution and enrollment queries
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.distributions(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.withDistribution(variables.versionId),
      })
      toastMessages.success.updated('Distribution')
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}
