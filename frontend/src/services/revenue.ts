import { apiRequest } from '@/lib/api-client'
import { RevenueLineItem, PaginatedResponse } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const revenueApi = {
  getAll: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<PaginatedResponse<RevenueLineItem>>({
        method: 'GET',
        url: `/planning/revenue/${versionId}`,
      }),
      'revenue: get all'
    )
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'GET',
        url: `/planning/revenue/item/${id}`,
      }),
      'revenue: get by id'
    )
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
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'POST',
        url: '/planning/revenue',
        data,
      }),
      'revenue: create'
    )
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
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'PUT',
        url: `/planning/revenue/${id}`,
        data,
      }),
      'revenue: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/planning/revenue/${id}`,
      }),
      'revenue: delete'
    )
  },

  calculateRevenue: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; message: string }>({
        method: 'POST',
        url: `/planning/revenue/${versionId}/calculate`,
      }),
      'revenue: calculate'
    )
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
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; count: number }>({
        method: 'POST',
        url: `/planning/revenue/${versionId}/bulk-update`,
        data: { updates },
      }),
      'revenue: bulk update'
    )
  },
}
