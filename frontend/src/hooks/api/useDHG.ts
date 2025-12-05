import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dhgApi } from '@/services/dhg'

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
    },
  })
}

// DHG Teacher Requirements
export function useTeacherRequirements(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.teacherRequirements(versionId),
    queryFn: () => dhgApi.getTeacherRequirements(versionId),
    enabled: !!versionId,
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
    },
  })
}

// Teacher Allocations
export function useTeacherAllocations(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.allocations(versionId),
    queryFn: () => dhgApi.getAllocations(versionId),
    enabled: !!versionId,
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
    },
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
    },
  })
}

export function useDeleteAllocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (allocationId: string) => dhgApi.deleteAllocation(allocationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
    },
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
    },
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
    retry: false, // Don't retry 422 validation errors
  })
}
