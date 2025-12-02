import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { strategicService } from '@/services/strategic'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'

export const strategicKeys = {
  all: ['strategic'] as const,
  plans: () => [...strategicKeys.all, 'plans'] as const,
  plan: (planId: string) => [...strategicKeys.all, 'plan', planId] as const,
  projections: (planId: string, scenarioId: string) =>
    [...strategicKeys.all, 'projections', planId, scenarioId] as const,
}

export function useStrategicPlans() {
  return useQuery({
    queryKey: strategicKeys.plans(),
    queryFn: () => strategicService.getPlans(),
  })
}

export function useStrategicPlan(planId: string) {
  return useQuery({
    queryKey: strategicKeys.plan(planId),
    queryFn: () => strategicService.getPlan(planId),
    enabled: !!planId,
  })
}

export function useCreateStrategicPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: strategicService.createPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategicKeys.plans() })
      toastMessages.success.created(entityNames.strategicPlan)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useUpdateScenarioAssumptions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      planId,
      ...data
    }: {
      planId: string
      scenario_id: string
      enrollment_growth_rate: number
      fee_increase_rate: number
      salary_inflation_rate: number
      operating_growth_rate: number
    }) => strategicService.updateAssumptions(planId, data),
    onSuccess: (_, { planId }) => {
      queryClient.invalidateQueries({ queryKey: strategicKeys.plan(planId) })
      toastMessages.success.updated('Hypothèses')
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useStrategicProjections(planId: string, scenarioId: string) {
  return useQuery({
    queryKey: strategicKeys.projections(planId, scenarioId),
    queryFn: () => strategicService.getProjections(planId, scenarioId),
    enabled: !!planId && !!scenarioId,
  })
}

export function useDeleteStrategicPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (planId: string) => strategicService.deletePlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategicKeys.plans() })
      toastMessages.success.deleted(entityNames.strategicPlan)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}
