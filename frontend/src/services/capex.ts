import { apiRequest } from '@/lib/api-client'
import { CapExItem, PaginatedResponse } from '@/types/api'

export const capexApi = {
  getAll: async (versionId: string) => {
    return apiRequest<PaginatedResponse<CapExItem>>({
      method: 'GET',
      url: `/planning/capex/${versionId}`,
    })
  },

  getById: async (id: string) => {
    return apiRequest<CapExItem>({
      method: 'GET',
      url: `/planning/capex/item/${id}`,
    })
  },

  create: async (data: {
    budget_version_id: string
    description: string
    asset_type: 'EQUIPMENT' | 'IT' | 'FURNITURE' | 'BUILDING_IMPROVEMENTS' | 'SOFTWARE'
    account_code: string
    purchase_date: string
    cost: number
    useful_life_years: number
    depreciation_method: 'STRAIGHT_LINE' | 'DECLINING_BALANCE'
    notes?: string
  }) => {
    return apiRequest<CapExItem>({
      method: 'POST',
      url: '/planning/capex',
      data,
    })
  },

  update: async (
    id: string,
    data: {
      description?: string
      asset_type?: 'EQUIPMENT' | 'IT' | 'FURNITURE' | 'BUILDING_IMPROVEMENTS' | 'SOFTWARE'
      account_code?: string
      purchase_date?: string
      cost?: number
      useful_life_years?: number
      depreciation_method?: 'STRAIGHT_LINE' | 'DECLINING_BALANCE'
      notes?: string
    }
  ) => {
    return apiRequest<CapExItem>({
      method: 'PUT',
      url: `/planning/capex/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/capex/${id}`,
    })
  },

  getDepreciationSchedule: async (id: string) => {
    return apiRequest<Array<{ year: number; depreciation: number; book_value: number }>>({
      method: 'GET',
      url: `/planning/capex/${id}/depreciation-schedule`,
    })
  },
}
