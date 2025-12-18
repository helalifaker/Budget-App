import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  consolidationService,
  type BudgetConsolidation,
  type ConsolidationStatus,
  type ConsolidationValidation,
  type ConsolidationSummary,
  type IncomeStatementResponse,
  type BalanceSheetResponse,
  type WorkflowActionResponse,
} from '@/services/consolidation'
import { toastMessages, handleAPIErrorToast } from '@/lib/toast-messages'

export const consolidationKeys = {
  all: ['consolidation'] as const,
  status: (versionId: string) => [...consolidationKeys.all, 'status', versionId] as const,
  summary: (versionId: string) => [...consolidationKeys.all, 'summary', versionId] as const,
  validation: (versionId: string) => [...consolidationKeys.all, 'validation', versionId] as const,
  consolidated: (versionId: string) =>
    [...consolidationKeys.all, 'consolidated', versionId] as const,
  incomeStatement: (versionId: string, format: string) =>
    [...consolidationKeys.all, 'income', versionId, format] as const,
  balanceSheet: (versionId: string) => [...consolidationKeys.all, 'balance', versionId] as const,
  periodTotals: (versionId: string) => [...consolidationKeys.all, 'periods', versionId] as const,
  statement: (versionId: string, type: string, format: string, period: string) =>
    [...consolidationKeys.all, 'statement', versionId, type, format, period] as const,
}

/**
 * Get consolidation status (module completion)
 */
export function useConsolidationStatus(versionId: string | undefined) {
  return useQuery<ConsolidationStatus>({
    queryKey: consolidationKeys.status(versionId ?? ''),
    queryFn: () => consolidationService.getStatus(versionId!),
    enabled: !!versionId,
  })
}

/**
 * Get full consolidated budget with all line items
 * @deprecated Use useConsolidatedBudget instead for clarity
 */
export function useBudgetLineItems(versionId: string | undefined) {
  return useConsolidatedBudget(versionId)
}

/**
 * Get full consolidated budget with all line items
 */
export function useConsolidatedBudget(versionId: string | undefined) {
  return useQuery<BudgetConsolidation>({
    queryKey: consolidationKeys.consolidated(versionId ?? ''),
    queryFn: () => consolidationService.getConsolidatedBudget(versionId!),
    enabled: !!versionId,
  })
}

/**
 * Trigger budget consolidation
 */
export function useConsolidate() {
  const queryClient = useQueryClient()

  return useMutation<BudgetConsolidation, Error, string>({
    mutationFn: (versionId: string) => consolidationService.consolidate(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidated(versionId) })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.summary(versionId) })
      toastMessages.success.calculated()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

/**
 * Submit budget for approval (WORKING → SUBMITTED)
 */
export function useSubmitForApproval() {
  const queryClient = useQueryClient()

  return useMutation<WorkflowActionResponse, Error, string>({
    mutationFn: (versionId: string) => consolidationService.submitForApproval(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      toastMessages.success.submitted()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

/**
 * Approve budget (SUBMITTED → APPROVED)
 */
export function useApproveBudget() {
  const queryClient = useQueryClient()

  return useMutation<WorkflowActionResponse, Error, string>({
    mutationFn: (versionId: string) => consolidationService.approve(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      toastMessages.success.approved()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

/**
 * Get income statement
 */
export function useIncomeStatement(versionId: string | undefined, format: 'pcg' | 'ifrs' = 'pcg') {
  return useQuery<IncomeStatementResponse>({
    queryKey: consolidationKeys.incomeStatement(versionId ?? '', format),
    queryFn: () => consolidationService.getIncomeStatement(versionId!, format),
    enabled: !!versionId,
  })
}

/**
 * Get balance sheet
 */
export function useBalanceSheet(versionId: string | undefined) {
  return useQuery<BalanceSheetResponse>({
    queryKey: consolidationKeys.balanceSheet(versionId ?? ''),
    queryFn: () => consolidationService.getBalanceSheet(versionId!),
    enabled: !!versionId,
  })
}

/**
 * Generic financial statement hook (for backwards compatibility)
 */
export function useFinancialStatement(
  versionId: string | undefined,
  type: 'INCOME' | 'BALANCE' | 'CASHFLOW',
  format: 'PCG' | 'IFRS',
  period: 'ANNUAL' | 'P1' | 'P2' | 'SUMMER'
) {
  return useQuery<IncomeStatementResponse | BalanceSheetResponse>({
    queryKey: consolidationKeys.statement(versionId ?? '', type, format, period),
    queryFn: () => consolidationService.getStatement(versionId!, type, format, period),
    enabled: !!versionId,
  })
}

/**
 * Get validation results for a budget version
 */
export function useConsolidationValidation(versionId: string | undefined) {
  return useQuery<ConsolidationValidation>({
    queryKey: consolidationKeys.validation(versionId ?? ''),
    queryFn: () => consolidationService.getValidation(versionId!),
    enabled: !!versionId,
    staleTime: 10000, // Consider data stale after 10 seconds
  })
}

/**
 * Get consolidation summary (totals and counts without line items)
 */
export function useConsolidationSummary(versionId: string | undefined) {
  return useQuery<ConsolidationSummary>({
    queryKey: consolidationKeys.summary(versionId ?? ''),
    queryFn: () => consolidationService.getSummary(versionId!),
    enabled: !!versionId,
  })
}
