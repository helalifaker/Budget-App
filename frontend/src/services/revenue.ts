import { apiRequest } from '@/lib/api-client'
import { RevenueLineItem, PaginatedResponse } from '@/types/api'

export const revenueApi = {
  getAll: async (versionId: string) => {
    return apiRequest<PaginatedResponse<RevenueLineItem>>({
      method: 'GET',
      url: `/planning/revenue/${versionId}`,
    })
  },

  getById: async (id: string) => {
    return apiRequest<RevenueLineItem>({
      method: 'GET',
      url: `/planning/revenue/item/${id}`,
    })
  },

  create: async (data: {
    budget_version_id: string
    account_code: string
    description: string
    category: string
    t1_amount?: number
    t2_amount?: number
    t3_amount?: number
    annual_amount: number
    notes?: string
  }) => {
    return apiRequest<RevenueLineItem>({
      method: 'POST',
      url: '/planning/revenue',
      data,
    })
  },

  update: async (
    id: string,
    data: {
      t1_amount?: number
      t2_amount?: number
      t3_amount?: number
      annual_amount?: number
      notes?: string
    }
  ) => {
    return apiRequest<RevenueLineItem>({
      method: 'PUT',
      url: `/planning/revenue/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/revenue/${id}`,
    })
  },

  calculateRevenue: async (versionId: string) => {
    return apiRequest<{ success: boolean; message: string }>({
      method: 'POST',
      url: `/planning/revenue/${versionId}/calculate`,
    })
  },

  bulkUpdate: async (
    versionId: string,
    updates: Array<{
      id: string
      t1_amount?: number
      t2_amount?: number
      t3_amount?: number
      annual_amount?: number
    }>
  ) => {
    return apiRequest<{ success: boolean; count: number }>({
      method: 'POST',
      url: `/planning/revenue/${versionId}/bulk-update`,
      data: { updates },
    })
  },
}
