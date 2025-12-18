import { apiRequest } from '@/lib/api-client'
import { withServiceErrorHandling } from './utils'

/**
 * Module completion status
 */
export interface ModulesCompleteStatus {
  enrollment: boolean
  classes: boolean
  dhg: boolean
  revenue: boolean
  costs: boolean
  capex: boolean
}

/**
 * Consolidation status response from the backend
 */
export interface ConsolidationStatus {
  version_id: string
  is_complete: boolean
  modules_complete: ModulesCompleteStatus
}

/**
 * Consolidation line item from the backend
 */
export interface ConsolidationLineItem {
  id: string
  account_code: string
  account_name: string
  consolidation_category: string
  is_revenue: boolean
  amount_sar: number
  source_table: string
  source_count: number
  is_calculated: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

/**
 * Full consolidated budget response from the backend
 */
export interface BudgetConsolidation {
  version_id: string
  version_name: string
  fiscal_year: number
  academic_year: string
  status: string
  revenue_items: ConsolidationLineItem[]
  personnel_items: ConsolidationLineItem[]
  operating_items: ConsolidationLineItem[]
  capex_items: ConsolidationLineItem[]
  total_revenue: number
  total_personnel_costs: number
  total_operating_costs: number
  total_capex: number
  operating_result: number
  net_result: number
}

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
  version_id: string
  version_name: string
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
  last_consolidated_at: string | null
}

/**
 * Workflow action response from the backend (for submit/approve)
 */
export interface WorkflowActionResponse {
  version_id: string
  previous_status: string
  new_status: string
  action_by: string
  action_at: string
  message: string
}

/**
 * Financial statement line item
 */
export interface FinancialStatementLine {
  id: string
  line_number: number
  line_type: string
  indent_level: number
  line_code: string | null
  line_description: string
  amount_sar: number | null
  is_bold: boolean
  is_underlined: boolean
  source_consolidation_category: string | null
}

/**
 * Income statement response
 */
export interface IncomeStatementResponse {
  id: string
  version_id: string
  statement_type: string
  statement_format: string
  statement_name: string
  fiscal_year: number
  total_amount_sar: number
  is_calculated: boolean
  notes: string | null
  lines: FinancialStatementLine[]
  created_at: string
  updated_at: string
}

/**
 * Balance sheet response
 */
export interface BalanceSheetResponse {
  version_id: string
  fiscal_year: number
  assets: IncomeStatementResponse
  liabilities: IncomeStatementResponse
  is_balanced: boolean
}

/**
 * Period financial totals
 */
export interface FinancialPeriodTotals {
  version_id: string
  period: string
  total_revenue: number
  total_expenses: number
  operating_result: number
  net_result: number
}

export const consolidationService = {
  /**
   * Get consolidation status for a version (module completion)
   */
  getStatus: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<ConsolidationStatus>({
        method: 'GET',
        url: `/consolidation/${versionId}/status`,
      }),
      'consolidation: get status'
    )
  },

  /**
   * Get full consolidated budget with all line items
   */
  getConsolidatedBudget: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetConsolidation>({
        method: 'GET',
        url: `/consolidation/${versionId}`,
      }),
      'consolidation: get consolidated budget'
    )
  },

  /**
   * Trigger budget consolidation (aggregates all planning modules)
   */
  consolidate: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<BudgetConsolidation>({
        method: 'POST',
        url: `/consolidation/${versionId}/consolidate`,
      }),
      'consolidation: run consolidation'
    )
  },

  /**
   * Submit budget for approval (WORKING → SUBMITTED)
   */
  submitForApproval: async (versionId: string, notes?: string) => {
    return withServiceErrorHandling(
      apiRequest<WorkflowActionResponse>({
        method: 'POST',
        url: `/consolidation/${versionId}/submit`,
        data: notes ? { notes } : undefined,
      }),
      'consolidation: submit for approval'
    )
  },

  /**
   * Approve budget (SUBMITTED → APPROVED) - requires manager role
   */
  approve: async (versionId: string, notes?: string) => {
    return withServiceErrorHandling(
      apiRequest<WorkflowActionResponse>({
        method: 'POST',
        url: `/consolidation/${versionId}/approve`,
        data: notes ? { notes } : undefined,
      }),
      'consolidation: approve budget'
    )
  },

  /**
   * Get validation results for budget completeness
   */
  getValidation: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<ConsolidationValidation>({
        method: 'GET',
        url: `/consolidation/${versionId}/validation`,
      }),
      'consolidation: get validation'
    )
  },

  /**
   * Get consolidation summary (totals and counts without line items)
   */
  getSummary: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<ConsolidationSummary>({
        method: 'GET',
        url: `/consolidation/${versionId}/summary`,
      }),
      'consolidation: get summary'
    )
  },

  /**
   * Get income statement
   */
  getIncomeStatement: async (versionId: string, format: 'pcg' | 'ifrs' = 'pcg') => {
    return withServiceErrorHandling(
      apiRequest<IncomeStatementResponse>({
        method: 'GET',
        url: `/consolidation/${versionId}/statements/income`,
        params: { format },
      }),
      'consolidation: get income statement'
    )
  },

  /**
   * Get balance sheet
   */
  getBalanceSheet: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<BalanceSheetResponse>({
        method: 'GET',
        url: `/consolidation/${versionId}/statements/balance`,
      }),
      'consolidation: get balance sheet'
    )
  },

  /**
   * Get financial totals for all periods (P1, Summer, P2, Annual)
   */
  getAllPeriodTotals: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<FinancialPeriodTotals[]>({
        method: 'GET',
        url: `/consolidation/${versionId}/statements/periods`,
      }),
      'consolidation: get all period totals'
    )
  },

  /**
   * Get financial totals for a specific period
   */
  getPeriodTotals: async (versionId: string, period: 'p1' | 'summer' | 'p2' | 'annual') => {
    return withServiceErrorHandling(
      apiRequest<FinancialPeriodTotals>({
        method: 'GET',
        url: `/consolidation/${versionId}/statements/periods/${period}`,
      }),
      'consolidation: get period totals'
    )
  },

  /**
   * Generic financial statement endpoint (for INCOME, BALANCE, or CASHFLOW)
   */
  getStatement: async (
    versionId: string,
    type: 'INCOME' | 'BALANCE' | 'CASHFLOW',
    format: 'PCG' | 'IFRS' = 'PCG',
    period: 'ANNUAL' | 'P1' | 'P2' | 'SUMMER' = 'ANNUAL'
  ) => {
    return withServiceErrorHandling(
      apiRequest<IncomeStatementResponse | BalanceSheetResponse>({
        method: 'GET',
        url: `/consolidation/${versionId}/statements/${type}`,
        params: { format, period },
      }),
      'consolidation: get financial statement'
    )
  },
}
