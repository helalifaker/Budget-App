import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { costsApi } from '@/services/costs'

export const costsKeys = {
  all: ['costs'] as const,
  lists: () => [...costsKeys.all, 'list'] as const,
  list: (versionId: string, category?: 'PERSONNEL' | 'OPERATING') =>
    [...costsKeys.lists(), versionId, category || 'all'] as const,
  details: () => [...costsKeys.all, 'detail'] as const,
  detail: (id: string) => [...costsKeys.details(), id] as const,
}

export function useCosts(versionId: string, category?: 'PERSONNEL' | 'OPERATING') {
  return useQuery({
    queryKey: costsKeys.list(versionId, category),
    queryFn: () => costsApi.getAll(versionId, category),
    enabled: !!versionId,
  })
}

export function useCostItem(id: string) {
  return useQuery({
    queryKey: costsKeys.detail(id),
    queryFn: () => costsApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateCostItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: costsApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.list(data.budget_version_id) })
    },
  })
}

export function useUpdateCostItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: { p1_amount?: number; summer_amount?: number; p2_amount?: number; notes?: string }
    }) => costsApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: costsKeys.list(data.budget_version_id) })
    },
  })
}

export function useDeleteCostItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: costsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costsKeys.lists() })
    },
  })
}

export function useCalculatePersonnelCosts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: costsApi.calculatePersonnelCosts,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.list(versionId, 'PERSONNEL') })
    },
  })
}

export function useBulkUpdateCosts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Array<{ id: string; p1_amount?: number; summer_amount?: number; p2_amount?: number }>
    }) => costsApi.bulkUpdate(versionId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.list(variables.versionId) })
    },
  })
}
