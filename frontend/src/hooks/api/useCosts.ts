import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { costsApi } from '@/services/costs'

export const costsKeys = {
  all: ['costs'] as const,
  personnel: (versionId: string) => [...costsKeys.all, 'personnel', versionId] as const,
  operating: (versionId: string) => [...costsKeys.all, 'operating', versionId] as const,
  summary: (versionId: string) => [...costsKeys.all, 'summary', versionId] as const,
}

// Personnel Costs
export function usePersonnelCosts(versionId: string) {
  return useQuery({
    queryKey: costsKeys.personnel(versionId),
    queryFn: () => costsApi.getPersonnelCosts(versionId),
    enabled: !!versionId,
  })
}

export function useCalculatePersonnelCosts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, eurToSarRate = 4.0 }: { versionId: string; eurToSarRate?: number }) =>
      costsApi.calculatePersonnelCosts(versionId, eurToSarRate),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.personnel(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: costsKeys.summary(variables.versionId) })
    },
  })
}

export function useCreatePersonnelCost() {
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
        fte_count: number
        unit_cost_sar: number
        category_id: string
        cycle_id?: string | null
        is_calculated?: boolean
        calculation_driver?: string | null
        notes?: string | null
      }
    }) => costsApi.createPersonnelCost(versionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.personnel(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: costsKeys.summary(variables.versionId) })
    },
  })
}

// Operating Costs
export function useOperatingCosts(versionId: string) {
  return useQuery({
    queryKey: costsKeys.operating(versionId),
    queryFn: () => costsApi.getOperatingCosts(versionId),
    enabled: !!versionId,
  })
}

export function useCalculateOperatingCosts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      driverRates,
    }: {
      versionId: string
      driverRates: Record<string, number>
    }) => costsApi.calculateOperatingCosts(versionId, driverRates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.operating(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: costsKeys.summary(variables.versionId) })
    },
  })
}

export function useCreateOperatingCost() {
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
        amount_sar: number
        is_calculated?: boolean
        calculation_driver?: string | null
        notes?: string | null
      }
    }) => costsApi.createOperatingCost(versionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: costsKeys.operating(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: costsKeys.summary(variables.versionId) })
    },
  })
}

// Cost Summary
export function useCostSummary(versionId: string) {
  return useQuery({
    queryKey: costsKeys.summary(versionId),
    queryFn: () => costsApi.getCostSummary(versionId),
    enabled: !!versionId,
  })
}
