import { apiRequest } from '@/lib/api-client'
import type { ConsolidationStatus, BudgetLineItem, FinancialStatement } from '@/types/api'

export const consolidationService = {
  /**
   * Get consolidation status for a budget version
   */
  getStatus: async (versionId: string): Promise<ConsolidationStatus> => {
    return apiRequest<ConsolidationStatus>({
      method: 'GET',
      url: `/consolidation/${versionId}/status`,
    })
  },

  /**
   * Get consolidated budget line items
   */
  getLineItems: async (versionId: string): Promise<BudgetLineItem[]> => {
    return apiRequest<BudgetLineItem[]>({
      method: 'GET',
      url: `/consolidation/${versionId}/line-items`,
    })
  },

  /**
   * Trigger budget consolidation
   */
  consolidate: async (versionId: string): Promise<ConsolidationStatus> => {
    return apiRequest<ConsolidationStatus>({
      method: 'POST',
      url: `/consolidation/${versionId}/consolidate`,
    })
  },

  /**
   * Submit budget for approval
   */
  submitForApproval: async (versionId: string): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>({
      method: 'POST',
      url: `/consolidation/${versionId}/submit`,
    })
  },

  /**
   * Approve budget
   */
  approve: async (versionId: string): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>({
      method: 'POST',
      url: `/consolidation/${versionId}/approve`,
    })
  },

  /**
   * Get financial statement
   */
  getStatement: async (
    versionId: string,
    type: 'INCOME' | 'BALANCE' | 'CASHFLOW',
    format: 'PCG' | 'IFRS',
    period: 'ANNUAL' | 'P1' | 'P2' | 'SUMMER'
  ): Promise<FinancialStatement> => {
    return apiRequest<FinancialStatement>({
      method: 'GET',
      url: `/consolidation/${versionId}/statements/${type}`,
      params: { format, period },
    })
  },
}
