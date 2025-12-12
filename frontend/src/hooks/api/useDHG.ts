import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dhgApi } from '@/services/dhg'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'

// PERFORMANCE: 10 minutes staleTime for DHG data
// DHG calculations are expensive and data changes rarely during a session
const DHG_STALE_TIME = 10 * 60 * 1000 // 10 minutes

export const dhgKeys = {
  all: ['dhg'] as const,
  subjectHours: (versionId: string) => [...dhgKeys.all, 'subject-hours', versionId] as const,
  teacherRequirements: (versionId: string) =>
    [...dhgKeys.all, 'teacher-requirements', versionId] as const,
  allocations: (versionId: string) => [...dhgKeys.all, 'allocations', versionId] as const,
  trmd: (versionId: string) => [...dhgKeys.all, 'trmd', versionId] as const,
}

// DHG Subject Hours
export function useSubjectHours(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.subjectHours(versionId),
    queryFn: () => dhgApi.getSubjectHours(versionId),
    enabled: !!versionId,
    staleTime: DHG_STALE_TIME,
  })
}

export function useCalculateSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      recalculateAll = false,
    }: {
      versionId: string
      recalculateAll?: boolean
    }) => dhgApi.calculateSubjectHours(versionId, recalculateAll),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.subjectHours(variables.versionId) })
      queryClient.invalidateQueries({
        queryKey: dhgKeys.teacherRequirements(variables.versionId),
      })
      toastMessages.success.calculated()
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

// DHG Teacher Requirements
export function useTeacherRequirements(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.teacherRequirements(versionId),
    queryFn: () => dhgApi.getTeacherRequirements(versionId),
    enabled: !!versionId,
    staleTime: DHG_STALE_TIME,
  })
}

export function useCalculateTeacherRequirements() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      recalculateAll = false,
    }: {
      versionId: string
      recalculateAll?: boolean
    }) => dhgApi.calculateTeacherRequirements(versionId, recalculateAll),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: dhgKeys.teacherRequirements(variables.versionId),
      })
      queryClient.invalidateQueries({ queryKey: dhgKeys.trmd(variables.versionId) })
      toastMessages.success.calculated()
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

// Teacher Allocations
export function useTeacherAllocations(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.allocations(versionId),
    queryFn: () => dhgApi.getAllocations(versionId),
    enabled: !!versionId,
    staleTime: DHG_STALE_TIME,
  })
}

export function useCreateAllocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      data,
    }: {
      versionId: string
      data: {
        subject_id: string
        cycle_id: string
        category_id: string
        fte_count: number
        notes?: string | null
      }
    }) => dhgApi.createAllocation(versionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.allocations(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: dhgKeys.trmd(variables.versionId) })
      toastMessages.success.created(entityNames.dhg)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useUpdateAllocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      allocationId,
      data,
    }: {
      allocationId: string
      data: { fte_count: number; notes?: string | null }
    }) => dhgApi.updateAllocation(allocationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
      toastMessages.success.updated(entityNames.dhg)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useDeleteAllocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (allocationId: string) => dhgApi.deleteAllocation(allocationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
      toastMessages.success.deleted(entityNames.dhg)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useBulkUpdateAllocations() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      allocations,
    }: {
      versionId: string
      allocations: Array<{
        subject_id: string
        cycle_id: string
        category_id: string
        fte_count: number
        notes?: string | null
      }>
    }) => dhgApi.bulkUpdateAllocations(versionId, allocations),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.allocations(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: dhgKeys.trmd(variables.versionId) })
      toastMessages.success.updated(entityNames.dhg)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

// TRMD Gap Analysis
// Note: This endpoint requires teacher requirements to be calculated first.
// Returns null when prerequisites are missing (422 error) - this is expected behavior.
export function useTRMDGapAnalysis(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.trmd(versionId),
    queryFn: () => dhgApi.getTRMDGapAnalysis(versionId),
    enabled: !!versionId,
    staleTime: DHG_STALE_TIME,
    retry: false, // Don't retry 422 validation errors
  })
}

// =============================================================================
// PERFORMANCE: Draft + Apply Pattern (BFF Hooks)
//
// These hooks support the "Auto-Draft + Manual Apply" UX pattern:
// - useSaveDHGDraft: Debounced background save without FTE recalculation
// - useApplyAndCalculateDHG: BFF endpoint for commit + calculate in one request
// =============================================================================

interface AllocationUpdate {
  subject_id: string
  cycle_id: string
  category_id: string
  fte_count: number
  notes?: string | null
}

/**
 * Hook for saving allocation changes without triggering FTE recalculation.
 * Use this for debounced auto-save as user edits allocation cells.
 *
 * This mutation:
 * - Does NOT show toast notifications (silent background save)
 * - Updates the cache optimistically for instant UI feedback
 * - Does NOT invalidate teacher requirements (no expensive recalculation)
 */
export function useSaveDHGDraft() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      allocations,
    }: {
      versionId: string
      allocations: AllocationUpdate[]
    }) => dhgApi.saveDraft(versionId, allocations),

    onSuccess: (data, variables) => {
      // Update allocations cache with server response (no toast - silent save)
      queryClient.setQueryData(dhgKeys.allocations(variables.versionId), data)
    },

    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook for applying allocation changes and running full FTE calculation.
 * This is the "Apply & Calculate" action that users explicitly trigger.
 *
 * This mutation:
 * - Saves any final allocation changes (if provided)
 * - Recalculates teacher FTE requirements
 * - Returns updated TRMD gap analysis
 * - Shows success toast when complete
 */
export function useApplyAndCalculateDHG() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      allocations,
    }: {
      versionId: string
      allocations?: AllocationUpdate[]
    }) => dhgApi.applyAndCalculate(versionId, allocations),

    onSuccess: (data, variables) => {
      // Update TRMD cache with new analysis data
      queryClient.setQueryData(dhgKeys.trmd(variables.versionId), data)
      // Invalidate teacher requirements and allocations to refresh
      queryClient.invalidateQueries({
        queryKey: dhgKeys.teacherRequirements(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: dhgKeys.allocations(variables.versionId),
      })
      toastMessages.success.calculated()
    },

    onError: (error) => handleAPIErrorToast(error),
  })
}
