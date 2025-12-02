import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { revenueApi } from '@/services/revenue'

export const revenueKeys = {
  all: ['revenue'] as const,
  lists: () => [...revenueKeys.all, 'list'] as const,
  list: (versionId: string) => [...revenueKeys.lists(), versionId] as const,
  details: () => [...revenueKeys.all, 'detail'] as const,
  detail: (id: string) => [...revenueKeys.details(), id] as const,
}

export function useRevenue(versionId: string) {
  return useQuery({
    queryKey: revenueKeys.list(versionId),
    queryFn: () => revenueApi.getAll(versionId),
    enabled: !!versionId,
  })
}

export function useRevenueItem(id: string) {
  return useQuery({
    queryKey: revenueKeys.detail(id),
    queryFn: () => revenueApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(data.budget_version_id) })
    },
  })
}

export function useUpdateRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: {
        t1_amount?: number
        t2_amount?: number
        t3_amount?: number
        annual_amount?: number
        notes?: string
      }
    }) => revenueApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(data.budget_version_id) })
    },
  })
}

export function useDeleteRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.lists() })
    },
  })
}

export function useCalculateRevenue() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.calculateRevenue,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(versionId) })
    },
  })
}

export function useBulkUpdateRevenue() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Array<{
        id: string
        t1_amount?: number
        t2_amount?: number
        t3_amount?: number
        annual_amount?: number
      }>
    }) => revenueApi.bulkUpdate(versionId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(variables.versionId) })
    },
  })
}
