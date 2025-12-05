import { apiRequest } from '@/lib/api-client'
import { BudgetVersion, PaginatedResponse } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const budgetVersionsApi = {
  getAll: async (params?: { page?: number; page_size?: number }) => {
    return withServiceErrorHandling(
      apiRequest<PaginatedResponse<BudgetVersion>>({
        method: 'GET',
        url: '/budget-versions',
        params,
      }),
      'budget-versions: get all'
    )
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'GET',
        url: `/budget-versions/${id}`,
      }),
      'budget-versions: get by id'
    )
  },

  create: async (data: {
    name: string
    fiscal_year: number
    academic_year: string
    notes?: string
  }) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'POST',
        url: '/budget-versions',
        data,
      }),
      'budget-versions: create'
    )
  },

  update: async (id: string, data: { name?: string; notes?: string }) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT',
        url: `/budget-versions/${id}`,
        data,
      }),
      'budget-versions: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/budget-versions/${id}`,
      }),
      'budget-versions: delete'
    )
  },

  submit: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT', // Changed from POST to match backend
        url: `/budget-versions/${id}/submit`,
      }),
      'budget-versions: submit'
    )
  },

  approve: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT', // Changed from POST to match backend
        url: `/budget-versions/${id}/approve`,
      }),
      'budget-versions: approve'
    )
  },

  clone: async (id: string, data: { name: string }) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'POST',
        url: `/budget-versions/${id}/clone`,
        data,
      }),
      'budget-versions: clone'
    )
  },
}
