import { apiRequest } from '@/lib/api-client'
import { withServiceErrorHandling } from './utils'

// Types matching backend schemas
interface CapExPlan {
  id: string
  budget_version_id: string
  account_code: string
  description: string
  category: string
  quantity: number
  unit_cost_sar: number
  total_cost_sar: number
  acquisition_date: string
  useful_life_years: number
  annual_depreciation_sar: number
  notes?: string | null
  created_at: string
  updated_at: string
}

interface DepreciationCalculation {
  capex_id: string
  year: number
  annual_depreciation: number
  accumulated_depreciation: number
  book_value: number
  is_fully_depreciated: boolean
}

interface CapExSummary {
  total_acquisition_cost: number
  total_annual_depreciation: number
  count_by_category: Record<string, number>
  cost_by_category: Record<string, number>
}

export const capexApi = {
  getAll: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<CapExPlan[]>({
        method: 'GET',
        url: `/planning/capex/${versionId}`,
      }),
      'capex: get all'
    )
  },

  create: async (
    versionId: string,
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
  ) => {
    return withServiceErrorHandling(
      apiRequest<CapExPlan>({
        method: 'POST',
        url: `/planning/capex/${versionId}`,
        data,
      }),
      'capex: create'
    )
  },

  update: async (
    versionId: string,
    capexId: string,
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
  ) => {
    return withServiceErrorHandling(
      apiRequest<CapExPlan>({
        method: 'PUT',
        url: `/planning/capex/${versionId}/${capexId}`,
        data,
      }),
      'capex: update'
    )
  },

  delete: async (versionId: string, capexId: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/planning/capex/${versionId}/${capexId}`,
      }),
      'capex: delete'
    )
  },

  calculateDepreciation: async (capexId: string, calculationYear: number) => {
    return withServiceErrorHandling(
      apiRequest<DepreciationCalculation>({
        method: 'POST',
        url: `/planning/capex/${capexId}/depreciation`,
        data: { calculation_year: calculationYear },
      }),
      'capex: calculate depreciation'
    )
  },

  getDepreciationSchedule: async (capexId: string, yearsAhead: number = 10) => {
    return withServiceErrorHandling(
      apiRequest<DepreciationCalculation[]>({
        method: 'GET',
        url: `/planning/capex/${capexId}/depreciation-schedule`,
        params: { years_ahead: yearsAhead },
      }),
      'capex: get depreciation schedule'
    )
  },

  getSummary: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<CapExSummary>({
        method: 'GET',
        url: `/planning/capex/${versionId}/summary`,
      }),
      'capex: get summary'
    )
  },

  getAnnualDepreciation: async (versionId: string, year: number) => {
    return withServiceErrorHandling(
      apiRequest<{
        year: number
        total_depreciation: number
        depreciation_by_category: Record<string, number>
      }>({
        method: 'GET',
        url: `/planning/capex/${versionId}/depreciation/${year}`,
      }),
      'capex: get annual depreciation'
    )
  },
}
