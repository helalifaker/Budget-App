import { apiRequest } from '@/lib/api-client'
import { CostLineItem, PaginatedResponse } from '@/types/api'

export const costsApi = {
  getAll: async (versionId: string, category?: 'PERSONNEL' | 'OPERATING') => {
    return apiRequest<PaginatedResponse<CostLineItem>>({
      method: 'GET',
      url: `/planning/costs/${versionId}`,
      params: { category },
    })
  },

  getById: async (id: string) => {
    return apiRequest<CostLineItem>({
      method: 'GET',
      url: `/planning/costs/item/${id}`,
    })
  },

  create: async (data: {
    budget_version_id: string
    account_code: string
    description: string
    category: 'PERSONNEL' | 'OPERATING'
    cost_type: string
    p1_amount: number
    summer_amount: number
    p2_amount: number
    notes?: string
  }) => {
    return apiRequest<CostLineItem>({
      method: 'POST',
      url: '/planning/costs',
      data,
    })
  },

  update: async (
    id: string,
    data: {
      p1_amount?: number
      summer_amount?: number
      p2_amount?: number
      notes?: string
    }
  ) => {
    return apiRequest<CostLineItem>({
      method: 'PUT',
      url: `/planning/costs/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/costs/${id}`,
    })
  },

  calculatePersonnelCosts: async (versionId: string) => {
    return apiRequest<{ success: boolean; message: string }>({
      method: 'POST',
      url: `/planning/costs/${versionId}/calculate-personnel`,
    })
  },

  bulkUpdate: async (
    versionId: string,
    updates: Array<{ id: string; p1_amount?: number; summer_amount?: number; p2_amount?: number }>
  ) => {
    return apiRequest<{ success: boolean; count: number }>({
      method: 'POST',
      url: `/planning/costs/${versionId}/bulk-update`,
      data: { updates },
    })
  },
}
