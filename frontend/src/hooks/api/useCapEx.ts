import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { capexApi } from '@/services/capex'
import type { CapExItem } from '@/types/api'

export const capexKeys = {
  all: ['capex'] as const,
  lists: () => [...capexKeys.all, 'list'] as const,
  list: (versionId: string) => [...capexKeys.lists(), versionId] as const,
  details: () => [...capexKeys.all, 'detail'] as const,
  detail: (id: string) => [...capexKeys.details(), id] as const,
  depreciation: (id: string) => [...capexKeys.all, 'depreciation', id] as const,
}

export function useCapEx(versionId: string) {
  return useQuery({
    queryKey: capexKeys.list(versionId),
    queryFn: () => capexApi.getAll(versionId),
    enabled: !!versionId,
  })
}

export function useCapExItem(id: string) {
  return useQuery({
    queryKey: capexKeys.detail(id),
    queryFn: () => capexApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: capexApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: capexKeys.list(data.budget_version_id) })
    },
  })
}

export function useUpdateCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CapExItem> }) => {
      // Build update data, filtering out null values
      const updateData: Parameters<typeof capexApi.update>[1] = {}
      if ('description' in data && data.description) updateData.description = data.description
      if ('asset_type' in data && data.asset_type) updateData.asset_type = data.asset_type
      if ('account_code' in data && data.account_code) updateData.account_code = data.account_code
      if ('purchase_date' in data && data.purchase_date)
        updateData.purchase_date = data.purchase_date
      if ('cost' in data && data.cost !== undefined && data.cost !== null)
        updateData.cost = data.cost
      if (
        'useful_life_years' in data &&
        data.useful_life_years !== undefined &&
        data.useful_life_years !== null
      )
        updateData.useful_life_years = data.useful_life_years
      if ('depreciation_method' in data && data.depreciation_method)
        updateData.depreciation_method = data.depreciation_method
      if ('notes' in data && data.notes !== null && data.notes !== undefined)
        updateData.notes = data.notes
      return capexApi.update(id, updateData)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: capexKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: capexKeys.list(data.budget_version_id) })
    },
  })
}

export function useDeleteCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: capexApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: capexKeys.lists() })
    },
  })
}

export function useDepreciationSchedule(id: string) {
  return useQuery({
    queryKey: capexKeys.depreciation(id),
    queryFn: () => capexApi.getDepreciationSchedule(id),
    enabled: !!id,
  })
}
