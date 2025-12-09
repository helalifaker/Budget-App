import { apiRequest } from '@/lib/api-client'
import type { ConsolidationStatus, BudgetLineItem, FinancialStatement } from '@/types/api'

/**
 * Consolidation validation response from the backend
 */
export interface ConsolidationValidation {
  is_complete: boolean
  missing_modules: string[]
  warnings: string[]
  module_counts: Record<string, number>
}

/**
 * Consolidation summary response from the backend
 */
export interface ConsolidationSummary {
  budget_version_id: string
  budget_version_name: string
  fiscal_year: number
  status: string
  total_revenue: number
  total_expenses: number
  total_capex: number
  operating_result: number
  net_result: number
  revenue_count: number
  expense_count: number
  capex_count: number
  last_consolidated_at: string
}

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

  /**
   * Get validation results for budget completeness
   */
  getValidation: async (versionId: string): Promise<ConsolidationValidation> => {
    return apiRequest<ConsolidationValidation>({
      method: 'GET',
      url: `/consolidation/${versionId}/validation`,
    })
  },

  /**
   * Get consolidation summary (totals and counts)
   */
  getSummary: async (versionId: string): Promise<ConsolidationSummary> => {
    return apiRequest<ConsolidationSummary>({
      method: 'GET',
      url: `/consolidation/${versionId}/summary`,
    })
  },
}
