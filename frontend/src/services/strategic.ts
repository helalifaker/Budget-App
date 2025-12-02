import { apiRequest } from '@/lib/api-client'
import type { StrategicPlan, StrategicScenario, StrategicProjection } from '@/types/api'

interface CreatePlanRequest {
  name: string
  base_version_id: string
  years_count: number
}

interface UpdateAssumptionsRequest {
  scenario_id: string
  enrollment_growth_rate: number
  fee_increase_rate: number
  salary_inflation_rate: number
  operating_growth_rate: number
}

export const strategicService = {
  /**
   * Get all strategic plans
   */
  getPlans: async (): Promise<StrategicPlan[]> => {
    return apiRequest<StrategicPlan[]>({
      method: 'GET',
      url: '/strategic/plans',
    })
  },

  /**
   * Get a specific strategic plan
   */
  getPlan: async (planId: string): Promise<StrategicPlan> => {
    return apiRequest<StrategicPlan>({
      method: 'GET',
      url: `/strategic/plans/${planId}`,
    })
  },

  /**
   * Create new strategic plan
   */
  createPlan: async (data: CreatePlanRequest): Promise<StrategicPlan> => {
    return apiRequest<StrategicPlan>({
      method: 'POST',
      url: '/strategic/plans',
      data,
    })
  },

  /**
   * Update scenario assumptions
   */
  updateAssumptions: async (
    planId: string,
    data: UpdateAssumptionsRequest
  ): Promise<StrategicScenario> => {
    return apiRequest<StrategicScenario>({
      method: 'PUT',
      url: `/strategic/plans/${planId}/scenarios/${data.scenario_id}`,
      data,
    })
  },

  /**
   * Get projections for a scenario
   */
  getProjections: async (planId: string, scenarioId: string): Promise<StrategicProjection[]> => {
    return apiRequest<StrategicProjection[]>({
      method: 'GET',
      url: `/strategic/plans/${planId}/scenarios/${scenarioId}/projections`,
    })
  },

  /**
   * Delete strategic plan
   */
  deletePlan: async (planId: string): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>({
      method: 'DELETE',
      url: `/strategic/plans/${planId}`,
    })
  },
}
