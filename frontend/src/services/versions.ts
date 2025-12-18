import { apiRequest } from '@/lib/api-client'
import { BudgetVersion, PaginatedResponse, ScenarioType } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export type VersionsListParams = {
  page?: number
  page_size?: number
  fiscal_year?: number
  status?: string
  scenario_type?: ScenarioType
}

export type CreateVersionData = {
  name: string
  fiscal_year: number
  academic_year: string
  scenario_type?: ScenarioType
  notes?: string
}

export type CloneVersionData = {
  name: string
  fiscal_year: number
  academic_year: string
  scenario_type?: ScenarioType
  clone_configuration?: boolean
}

export const versionsApi = {
  getAll: async (params?: VersionsListParams) => {
    return withServiceErrorHandling(
      apiRequest<PaginatedResponse<BudgetVersion>>({
        method: 'GET',
        url: '/budget-versions',
        params,
      }),
      'versions: get all'
    )
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'GET',
        url: `/budget-versions/${id}`,
      }),
      'versions: get by id'
    )
  },

  create: async (data: CreateVersionData) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'POST',
        url: '/budget-versions',
        data,
      }),
      'versions: create'
    )
  },

  update: async (id: string, data: { name?: string; notes?: string }) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT',
        url: `/budget-versions/${id}`,
        data,
      }),
      'versions: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/budget-versions/${id}`,
      }),
      'versions: delete'
    )
  },

  submit: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT', // Changed from POST to match backend
        url: `/budget-versions/${id}/submit`,
      }),
      'versions: submit'
    )
  },

  approve: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT', // Changed from POST to match backend
        url: `/budget-versions/${id}/approve`,
      }),
      'versions: approve'
    )
  },

  clone: async (id: string, data: CloneVersionData) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'POST',
        url: `/budget-versions/${id}/clone`,
        data,
      }),
      'versions: clone'
    )
  },

  reject: async (id: string, reason?: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT',
        url: `/budget-versions/${id}/reject`,
        params: reason ? { reason } : undefined,
      }),
      'versions: reject'
    )
  },

  supersede: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetVersion>({
        method: 'PUT',
        url: `/budget-versions/${id}/supersede`,
      }),
      'versions: supersede'
    )
  },
}

// Backward compatibility alias
export const budgetVersionsApi = versionsApi
