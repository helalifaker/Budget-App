import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dhgApi } from '@/services/dhg'

export const dhgKeys = {
  all: ['dhg'] as const,
  subjectHours: (versionId: string) => [...dhgKeys.all, 'subject-hours', versionId] as const,
  teacherFTE: (versionId: string) => [...dhgKeys.all, 'teacher-fte', versionId] as const,
  trmdGaps: (versionId: string) => [...dhgKeys.all, 'trmd-gaps', versionId] as const,
  hsaPlanning: (versionId: string) => [...dhgKeys.all, 'hsa-planning', versionId] as const,
}

export function useSubjectHours(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.subjectHours(versionId),
    queryFn: () => dhgApi.getSubjectHours(versionId),
    enabled: !!versionId,
  })
}

export function useUpdateSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: { hours_per_week: number; is_split: boolean }
    }) => dhgApi.updateSubjectHours(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
    },
  })
}

export function useBulkUpdateSubjectHours() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Array<{ id: string; hours_per_week: number; is_split: boolean }>
    }) => dhgApi.bulkUpdateSubjectHours(versionId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.subjectHours(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: dhgKeys.teacherFTE(variables.versionId) })
    },
  })
}

export function useTeacherFTE(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.teacherFTE(versionId),
    queryFn: () => dhgApi.getTeacherFTE(versionId),
    enabled: !!versionId,
  })
}

export function useCalculateFTE() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dhgApi.calculateFTE,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.teacherFTE(versionId) })
      queryClient.invalidateQueries({ queryKey: dhgKeys.trmdGaps(versionId) })
    },
  })
}

export function useTRMDGaps(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.trmdGaps(versionId),
    queryFn: () => dhgApi.getTRMDGaps(versionId),
    enabled: !!versionId,
  })
}

export function useUpdateTRMDGap() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: { aefe_positions: number; local_positions: number }
    }) => dhgApi.updateTRMDGap(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
    },
  })
}

export function useHSAPlanning(versionId: string) {
  return useQuery({
    queryKey: dhgKeys.hsaPlanning(versionId),
    queryFn: () => dhgApi.getHSAPlanning(versionId),
    enabled: !!versionId,
  })
}

export function useCreateHSAPlanning() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dhgApi.createHSAPlanning,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.hsaPlanning(data.budget_version_id) })
    },
  })
}

export function useUpdateHSAPlanning() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { hsa_hours: number; notes?: string } }) =>
      dhgApi.updateHSAPlanning(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.hsaPlanning(data.budget_version_id) })
    },
  })
}

export function useDeleteHSAPlanning() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dhgApi.deleteHSAPlanning,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dhgKeys.all })
    },
  })
}
