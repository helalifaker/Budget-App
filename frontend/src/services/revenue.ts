import { apiRequest } from '@/lib/api-client'
import type { RevenueLineItem, RevenueLineItemPivoted } from '@/types/api'
import { withServiceErrorHandling } from './utils'

/**
 * Pivot flat revenue items into UI-friendly rows with trimester columns.
 * Groups by account_code and maps trimester 1/2/3/null to t1/t2/t3/annual amounts.
 */
export function pivotRevenueItems(items: RevenueLineItem[]): RevenueLineItemPivoted[] {
  const byAccount = new Map<string, RevenueLineItemPivoted>()

  for (const item of items) {
    if (!byAccount.has(item.account_code)) {
      byAccount.set(item.account_code, {
        account_code: item.account_code,
        description: item.description,
        category: item.category,
        t1_amount: null,
        t2_amount: null,
        t3_amount: null,
        annual_amount: 0,
        is_calculated: item.is_calculated,
        notes: item.notes,
      })
    }

    const row = byAccount.get(item.account_code)!
    if (item.trimester === 1) {
      row.t1_amount = item.amount_sar
    } else if (item.trimester === 2) {
      row.t2_amount = item.amount_sar
    } else if (item.trimester === 3) {
      row.t3_amount = item.amount_sar
    } else {
      // trimester is null - this is the annual total
      row.annual_amount = item.amount_sar
    }
  }

  return Array.from(byAccount.values())
}

export const revenueApi = {
  /**
   * Get all revenue items for a version (flat list from backend)
   */
  getAll: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem[]>({
        method: 'GET',
        url: `/revenue/${versionId}`,
      }),
      'revenue: get all'
    )
  },

  /**
   * Get all revenue items pivoted for UI display (one row per account with trimester columns)
   */
  getAllPivoted: async (versionId: string) => {
    const items = await withServiceErrorHandling(
      apiRequest<RevenueLineItem[]>({
        method: 'GET',
        url: `/revenue/${versionId}`,
      }),
      'revenue: get all pivoted'
    )
    return pivotRevenueItems(items)
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'GET',
        url: `/revenue/item/${id}`,
      }),
      'revenue: get by id'
    )
  },

  create: async (data: {
    version_id: string
    account_code: string
    description: string
    category: string
    amount_sar: number
    is_calculated?: boolean
    calculation_driver?: string | null
    trimester?: number | null // 1-3 or null for annual
    notes?: string
  }) => {
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'POST',
        url: `/revenue/${data.version_id}`,
        data,
      }),
      'revenue: create'
    )
  },

  update: async (
    id: string,
    data: {
      account_code?: string
      description?: string
      category?: string
      amount_sar?: number
      is_calculated?: boolean
      calculation_driver?: string | null
      trimester?: number | null
      notes?: string
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<RevenueLineItem>({
        method: 'PUT',
        url: `/revenue/${id}`,
        data,
      }),
      'revenue: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/revenue/${id}`,
      }),
      'revenue: delete'
    )
  },

  calculateRevenue: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; message: string }>({
        method: 'POST',
        url: `/revenue/${versionId}/calculate`,
      }),
      'revenue: calculate'
    )
  },

  getSummary: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{
        total_revenue: number
        revenue_by_category: Record<string, number>
        revenue_by_account: Record<string, number>
      }>({
        method: 'GET',
        url: `/revenue/${versionId}/summary`,
      }),
      'revenue: get summary'
    )
  },

  bulkUpdate: async (
    versionId: string,
    updates: Array<{
      id: string
      amount_sar?: number
      notes?: string
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; count: number }>({
        method: 'POST',
        url: `/revenue/${versionId}/bulk-update`,
        data: { updates },
      }),
      'revenue: bulk update'
    )
  },
}
