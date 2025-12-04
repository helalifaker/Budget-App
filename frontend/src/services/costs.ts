import { apiRequest } from '@/lib/api-client'
import { CostLineItem, PaginatedResponse } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const costsApi = {
  getAll: async (versionId: string, category?: 'PERSONNEL' | 'OPERATING') => {
    return withServiceErrorHandling(
      apiRequest<PaginatedResponse<CostLineItem>>({
        method: 'GET',
        url: `/planning/costs/${versionId}`,
        params: { category },
      }),
      'costs: get all'
    )
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<CostLineItem>({
        method: 'GET',
        url: `/planning/costs/item/${id}`,
      }),
      'costs: get by id'
    )
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
    return withServiceErrorHandling(
      apiRequest<CostLineItem>({
        method: 'POST',
        url: '/planning/costs',
        data,
      }),
      'costs: create'
    )
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
    return withServiceErrorHandling(
      apiRequest<CostLineItem>({
        method: 'PUT',
        url: `/planning/costs/${id}`,
        data,
      }),
      'costs: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/planning/costs/${id}`,
      }),
      'costs: delete'
    )
  },

  calculatePersonnelCosts: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; message: string }>({
        method: 'POST',
        url: `/planning/costs/${versionId}/calculate-personnel`,
      }),
      'costs: calculate personnel'
    )
  },

  bulkUpdate: async (
    versionId: string,
    updates: Array<{ id: string; p1_amount?: number; summer_amount?: number; p2_amount?: number }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; count: number }>({
        method: 'POST',
        url: `/planning/costs/${versionId}/bulk-update`,
        data: { updates },
      }),
      'costs: bulk update'
    )
  },
}
