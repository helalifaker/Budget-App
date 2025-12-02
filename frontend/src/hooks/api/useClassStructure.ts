import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { classStructureApi } from '@/services/class-structure'

export const classStructureKeys = {
  all: ['class-structure'] as const,
  lists: () => [...classStructureKeys.all, 'list'] as const,
  list: (versionId: string, filters: string) =>
    [...classStructureKeys.lists(), versionId, { filters }] as const,
  details: () => [...classStructureKeys.all, 'detail'] as const,
  detail: (id: string) => [...classStructureKeys.details(), id] as const,
  byVersion: (versionId: string) => [...classStructureKeys.all, 'by-version', versionId] as const,
}

export function useClassStructures(versionId: string, page = 1, pageSize = 100) {
  return useQuery({
    queryKey: classStructureKeys.list(versionId, `page=${page}&pageSize=${pageSize}`),
    queryFn: () => classStructureApi.getAll(versionId, { page, page_size: pageSize }),
    enabled: !!versionId,
  })
}

export function useClassStructure(id: string) {
  return useQuery({
    queryKey: classStructureKeys.detail(id),
    queryFn: () => classStructureApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: classStructureApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.byVersion(data.budget_version_id),
      })
      queryClient.invalidateQueries({ queryKey: classStructureKeys.lists() })
    },
  })
}

export function useUpdateClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: { number_of_classes?: number; avg_class_size?: number }
    }) => classStructureApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.detail(data.id),
      })
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.byVersion(data.budget_version_id),
      })
      queryClient.invalidateQueries({ queryKey: classStructureKeys.lists() })
    },
  })
}

export function useDeleteClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: classStructureApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: classStructureKeys.lists() })
    },
  })
}

export function useCalculateClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: classStructureApi.calculateFromEnrollment,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.byVersion(versionId),
      })
    },
  })
}
