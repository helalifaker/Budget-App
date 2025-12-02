import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { consolidationService } from '@/services/consolidation'
import type { FinancialStatement } from '@/types/api'
import { toastMessages, handleAPIErrorToast } from '@/lib/toast-messages'

export const consolidationKeys = {
  all: ['consolidation'] as const,
  status: (versionId: string) => [...consolidationKeys.all, 'status', versionId] as const,
  summary: (versionId: string) => [...consolidationKeys.all, 'summary', versionId] as const,
  lineItems: (versionId: string) => [...consolidationKeys.all, 'line-items', versionId] as const,
  statements: (versionId: string, format: string) =>
    [...consolidationKeys.all, 'statements', versionId, format] as const,
  statement: (versionId: string, type: string, format: string, period: string) =>
    [...consolidationKeys.all, 'statement', versionId, type, format, period] as const,
}

export function useConsolidationStatus(versionId: string) {
  return useQuery({
    queryKey: consolidationKeys.status(versionId),
    queryFn: () => consolidationService.getStatus(versionId),
    enabled: !!versionId,
  })
}

export function useBudgetLineItems(versionId: string) {
  return useQuery({
    queryKey: consolidationKeys.lineItems(versionId),
    queryFn: () => consolidationService.getLineItems(versionId),
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
  versionId: string,
  type: FinancialStatement['statement_type'],
  format: FinancialStatement['format'],
  period: FinancialStatement['period']
) {
  return useQuery({
    queryKey: consolidationKeys.statement(versionId, type, format, period),
    queryFn: () => consolidationService.getStatement(versionId, type, format, period),
    enabled: !!versionId,
  })
}
