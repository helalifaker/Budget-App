import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { classStructureApi } from '@/services/class-structure'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'

export const classStructureKeys = {
  all: ['class-structure'] as const,
  list: (versionId: string) => [...classStructureKeys.all, 'list', versionId] as const,
}

export function useClassStructures(versionId: string | undefined) {
  return useQuery({
    queryKey: classStructureKeys.list(versionId ?? ''),
    queryFn: () => classStructureApi.getAll(versionId!),
    enabled: !!versionId,
  })
}

export function useCalculateClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      data = {},
    }: {
      versionId: string
      data?: {
        method?: string
        override_by_level?: Record<string, { number_of_classes?: number; avg_class_size?: number }>
      }
    }) => classStructureApi.calculate(versionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.list(variables.versionId),
      })
      toastMessages.success.calculated()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
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
      data: {
        total_students?: number
        number_of_classes?: number
        avg_class_size?: number
        requires_atsem?: boolean
        atsem_count?: number
        calculation_method?: string
        notes?: string | null
      }
    }) => classStructureApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.list(data.version_id),
      })
      toastMessages.success.updated(entityNames.classStructure)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useBulkUpdateClassStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Array<{
        id: string
        total_students?: number
        number_of_classes?: number
        avg_class_size?: number
        requires_atsem?: boolean
        atsem_count?: number
        calculation_method?: string
        notes?: string | null
      }>
    }) => classStructureApi.updateBulk(versionId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: classStructureKeys.list(variables.versionId),
      })
      toastMessages.success.updated('Class structures')
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}
