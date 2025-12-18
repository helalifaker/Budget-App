import { apiRequest } from '@/lib/api-client'
import { withServiceErrorHandling } from './utils'

// Types matching backend schemas
interface PersonnelCostPlan {
  id: string
  version_id: string
  account_code: string
  description: string
  fte_count: number
  unit_cost_sar: number
  total_cost_sar: number
  category_id: string
  cycle_id?: string | null
  is_calculated: boolean
  calculation_driver?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

interface OperatingCostPlan {
  id: string
  version_id: string
  account_code: string
  description: string
  category: string
  amount_sar: number
  is_calculated: boolean
  calculation_driver?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

interface CostSummary {
  total_personnel_cost: number
  total_operating_cost: number
  total_cost: number
  personnel_by_category: Record<string, number>
  operating_by_category: Record<string, number>
}

export const costsApi = {
  // Personnel Costs
  getPersonnelCosts: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<PersonnelCostPlan[]>({
        method: 'GET',
        url: `/costs/personnel/${versionId}`,
      }),
      'costs: get personnel costs'
    )
  },

  calculatePersonnelCosts: async (versionId: string, eurToSarRate: number = 4.0) => {
    return withServiceErrorHandling(
      apiRequest<PersonnelCostPlan[]>({
        method: 'POST',
        url: `/costs/personnel/${versionId}/calculate`,
        data: { eur_to_sar_rate: eurToSarRate },
      }),
      'costs: calculate personnel costs'
    )
  },

  createPersonnelCost: async (
    versionId: string,
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
  ) => {
    return withServiceErrorHandling(
      apiRequest<PersonnelCostPlan>({
        method: 'POST',
        url: `/costs/personnel/${versionId}`,
        data,
      }),
      'costs: create personnel cost'
    )
  },

  // Operating Costs
  getOperatingCosts: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<OperatingCostPlan[]>({
        method: 'GET',
        url: `/costs/operating/${versionId}`,
      }),
      'costs: get operating costs'
    )
  },

  calculateOperatingCosts: async (versionId: string, driverRates: Record<string, number>) => {
    return withServiceErrorHandling(
      apiRequest<OperatingCostPlan[]>({
        method: 'POST',
        url: `/costs/operating/${versionId}/calculate`,
        data: { driver_rates: driverRates },
      }),
      'costs: calculate operating costs'
    )
  },

  createOperatingCost: async (
    versionId: string,
    data: {
      account_code: string
      description: string
      category: string
      amount_sar: number
      is_calculated?: boolean
      calculation_driver?: string | null
      notes?: string | null
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<OperatingCostPlan>({
        method: 'POST',
        url: `/costs/operating/${versionId}`,
        data,
      }),
      'costs: create operating cost'
    )
  },

  // Summary
  getCostSummary: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<CostSummary>({
        method: 'GET',
        url: `/costs/${versionId}/summary`,
      }),
      'costs: get summary'
    )
  },
}
