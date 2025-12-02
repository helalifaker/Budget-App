import { apiRequest } from '@/lib/api-client'
import { BudgetVersion, PaginatedResponse } from '@/types/api'

export const budgetVersionsApi = {
  getAll: async (params?: { page?: number; page_size?: number }) => {
    return apiRequest<PaginatedResponse<BudgetVersion>>({
      method: 'GET',
      url: '/configuration/budget-versions',
      params,
    })
  },

  getById: async (id: string) => {
    return apiRequest<BudgetVersion>({
      method: 'GET',
      url: `/configuration/budget-versions/${id}`,
    })
  },

  create: async (data: {
    name: string
    fiscal_year: number
    academic_year: string
    notes?: string
  }) => {
    return apiRequest<BudgetVersion>({
      method: 'POST',
      url: '/configuration/budget-versions',
      data,
    })
  },

  update: async (id: string, data: { name?: string; notes?: string }) => {
    return apiRequest<BudgetVersion>({
      method: 'PUT',
      url: `/configuration/budget-versions/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/configuration/budget-versions/${id}`,
    })
  },

  submit: async (id: string) => {
    return apiRequest<BudgetVersion>({
      method: 'POST',
      url: `/configuration/budget-versions/${id}/submit`,
    })
  },

  approve: async (id: string) => {
    return apiRequest<BudgetVersion>({
      method: 'POST',
      url: `/configuration/budget-versions/${id}/approve`,
    })
  },

  clone: async (id: string, data: { name: string }) => {
    return apiRequest<BudgetVersion>({
      method: 'POST',
      url: `/configuration/budget-versions/${id}/clone`,
      data,
    })
  },
}
