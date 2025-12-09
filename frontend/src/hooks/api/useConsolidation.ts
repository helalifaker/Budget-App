import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { consolidationService } from '@/services/consolidation'
import type { FinancialStatement } from '@/types/api'
import { toastMessages, handleAPIErrorToast } from '@/lib/toast-messages'

export const consolidationKeys = {
  all: ['consolidation'] as const,
  status: (versionId: string) => [...consolidationKeys.all, 'status', versionId] as const,
  summary: (versionId: string) => [...consolidationKeys.all, 'summary', versionId] as const,
  validation: (versionId: string) => [...consolidationKeys.all, 'validation', versionId] as const,
  lineItems: (versionId: string) => [...consolidationKeys.all, 'line-items', versionId] as const,
  statements: (versionId: string, format: string) =>
    [...consolidationKeys.all, 'statements', versionId, format] as const,
  statement: (versionId: string, type: string, format: string, period: string) =>
    [...consolidationKeys.all, 'statement', versionId, type, format, period] as const,
}

export function useConsolidationStatus(versionId: string | undefined) {
  return useQuery({
    queryKey: consolidationKeys.status(versionId ?? ''),
    queryFn: () => consolidationService.getStatus(versionId!),
    enabled: !!versionId,
  })
}

export function useBudgetLineItems(versionId: string | undefined) {
  return useQuery({
    queryKey: consolidationKeys.lineItems(versionId ?? ''),
    queryFn: () => consolidationService.getLineItems(versionId!),
    enabled: !!versionId,
  })
}

export function useConsolidate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (versionId: string) => consolidationService.consolidate(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.lineItems(versionId) })
      toastMessages.success.calculated()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useSubmitForApproval() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (versionId: string) => consolidationService.submitForApproval(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: ['budget-versions'] })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      toastMessages.success.submitted()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useApproveBudget() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (versionId: string) => consolidationService.approve(versionId),
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: ['budget-versions'] })
      queryClient.invalidateQueries({ queryKey: consolidationKeys.status(versionId) })
      toastMessages.success.approved()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useFinancialStatement(
  versionId: string | undefined,
  type: FinancialStatement['statement_type'],
  format: FinancialStatement['format'],
  period: FinancialStatement['period']
) {
  return useQuery({
    queryKey: consolidationKeys.statement(versionId ?? '', type, format, period),
    queryFn: () => consolidationService.getStatement(versionId!, type, format, period),
    enabled: !!versionId,
  })
}

/**
 * Hook to fetch validation results for a budget version
 *
 * Returns completeness status, missing modules, and warnings.
 */
export function useConsolidationValidation(versionId: string | undefined) {
  return useQuery({
    queryKey: consolidationKeys.validation(versionId ?? ''),
    queryFn: () => consolidationService.getValidation(versionId!),
    enabled: !!versionId,
    staleTime: 10000, // Consider data stale after 10 seconds
  })
}

/**
 * Hook to fetch consolidation summary for a budget version
 *
 * Returns totals and key metrics without detailed line items.
 */
export function useConsolidationSummary(versionId: string | undefined) {
  return useQuery({
    queryKey: consolidationKeys.summary(versionId ?? ''),
    queryFn: () => consolidationService.getSummary(versionId!),
    enabled: !!versionId,
  })
}
