import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { enrollmentApi } from '@/services/enrollment'

export const enrollmentKeys = {
  all: ['enrollments'] as const,
  lists: () => [...enrollmentKeys.all, 'list'] as const,
  list: (versionId: string, filters: string) =>
    [...enrollmentKeys.lists(), versionId, { filters }] as const,
  details: () => [...enrollmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...enrollmentKeys.details(), id] as const,
  byVersion: (versionId: string) => [...enrollmentKeys.all, 'by-version', versionId] as const,
}

export function useEnrollments(versionId: string, page = 1, pageSize = 100) {
  return useQuery({
    queryKey: enrollmentKeys.list(versionId, `page=${page}&pageSize=${pageSize}`),
    queryFn: () => enrollmentApi.getAll(versionId, { page, page_size: pageSize }),
    enabled: !!versionId,
  })
}

export function useEnrollment(id: string) {
  return useQuery({
    queryKey: enrollmentKeys.detail(id),
    queryFn: () => enrollmentApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: enrollmentApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(data.budget_version_id),
      })
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
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
        queryKey: enrollmentKeys.detail(data.id),
      })
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(data.budget_version_id),
      })
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
    },
  })
}

export function useDeleteEnrollment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: enrollmentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
    },
  })
}

export function useCalculateProjections() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: enrollmentApi.calculateProjections,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(versionId),
      })
    },
  })
}

export function useBulkUpdateEnrollments() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      enrollments,
    }: {
      versionId: string
      enrollments: Array<{
        level_id: string
        nationality_type_id: string
        student_count: number
      }>
    }) => enrollmentApi.bulkUpdate(versionId, enrollments),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: enrollmentKeys.byVersion(variables.versionId),
      })
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() })
    },
  })
}
