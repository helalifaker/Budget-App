import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetVersionsApi } from '@/services/budget-versions'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'
import { useAuth } from '@/contexts/AuthContext'

export const budgetVersionKeys = {
  all: ['budget-versions'] as const,
  lists: () => [...budgetVersionKeys.all, 'list'] as const,
  list: (filters: string) => [...budgetVersionKeys.lists(), { filters }] as const,
  details: () => [...budgetVersionKeys.all, 'detail'] as const,
  detail: (id: string) => [...budgetVersionKeys.details(), id] as const,
}

/**
 * Fetch budget versions with authentication check.
 * Query is disabled until session is available to prevent race conditions.
 */
export function useBudgetVersions(page = 1, pageSize = 50) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: budgetVersionKeys.list(`page=${page}&pageSize=${pageSize}`),
    queryFn: () => budgetVersionsApi.getAll({ page, page_size: pageSize }),
    // Only enable query when session is confirmed and not loading
    enabled: !!session && !loading,
  })
}

export function useBudgetVersion(id: string) {
  return useQuery({
    queryKey: budgetVersionKeys.detail(id),
    queryFn: () => budgetVersionsApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: budgetVersionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.created(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useUpdateBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; notes?: string } }) =>
      budgetVersionsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: budgetVersionKeys.detail(variables.id),
      })
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.updated(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useDeleteBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: budgetVersionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.deleted(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useSubmitBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: budgetVersionsApi.submit,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: budgetVersionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.submitted()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useApproveBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: budgetVersionsApi.approve,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: budgetVersionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.approved()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useCloneBudgetVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      budgetVersionsApi.clone(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetVersionKeys.lists() })
      toastMessages.success.cloned()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}
