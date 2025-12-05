import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { capexApi } from '@/services/capex'

export const capexKeys = {
  all: ['capex'] as const,
  lists: () => [...capexKeys.all, 'list'] as const,
  list: (versionId: string) => [...capexKeys.lists(), versionId] as const,
  summary: (versionId: string) => [...capexKeys.all, 'summary', versionId] as const,
  depreciation: (capexId: string) => [...capexKeys.all, 'depreciation', capexId] as const,
  annualDepreciation: (versionId: string, year: number) =>
    [...capexKeys.all, 'annual-depreciation', versionId, year] as const,
}

export function useCapEx(versionId: string) {
  return useQuery({
    queryKey: capexKeys.list(versionId),
    queryFn: () => capexApi.getAll(versionId),
    enabled: !!versionId,
  })
}

export function useCreateCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      data,
    }: {
      versionId: string
      data: {
        account_code: string
        description: string
        category: string
        quantity: number
        unit_cost_sar: number
        acquisition_date: string
        useful_life_years: number
        notes?: string | null
      }
    }) => capexApi.create(versionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: capexKeys.list(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: capexKeys.summary(variables.versionId) })
    },
  })
}

export function useUpdateCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      capexId,
      data,
    }: {
      versionId: string
      capexId: string
      data: {
        account_code?: string
        description?: string
        category?: string
        quantity?: number
        unit_cost_sar?: number
        acquisition_date?: string
        useful_life_years?: number
        notes?: string | null
      }
    }) => capexApi.update(versionId, capexId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: capexKeys.list(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: capexKeys.summary(variables.versionId) })
    },
  })
}

export function useDeleteCapExItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, capexId }: { versionId: string; capexId: string }) =>
      capexApi.delete(versionId, capexId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: capexKeys.list(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: capexKeys.summary(variables.versionId) })
    },
  })
}

export function useCalculateDepreciation() {
  return useMutation({
    mutationFn: ({ capexId, year }: { capexId: string; year: number }) =>
      capexApi.calculateDepreciation(capexId, year),
  })
}

export function useDepreciationSchedule(capexId: string, yearsAhead: number = 10) {
  return useQuery({
    queryKey: capexKeys.depreciation(capexId),
    queryFn: () => capexApi.getDepreciationSchedule(capexId, yearsAhead),
    enabled: !!capexId,
  })
}

export function useCapExSummary(versionId: string) {
  return useQuery({
    queryKey: capexKeys.summary(versionId),
    queryFn: () => capexApi.getSummary(versionId),
    enabled: !!versionId,
  })
}

export function useAnnualDepreciation(versionId: string, year: number) {
  return useQuery({
    queryKey: capexKeys.annualDepreciation(versionId, year),
    queryFn: () => capexApi.getAnnualDepreciation(versionId, year),
    enabled: !!versionId && !!year,
  })
}
