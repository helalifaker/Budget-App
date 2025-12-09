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
 * Query is enabled when session exists - we don't wait for loading to complete
 * because if session exists, the user is authenticated.
 */
export function useBudgetVersions(page = 1, pageSize = 50) {
  const { session } = useAuth()

  return useQuery({
    queryKey: budgetVersionKeys.list(`page=${page}&pageSize=${pageSize}`),
    queryFn: async () => {
      console.log('[useBudgetVersions] Fetching budget versions...')
      try {
        const result = await budgetVersionsApi.getAll({ page, page_size: pageSize })
        console.log('[useBudgetVersions] Success:', result)
        return result
      } catch (error) {
        console.error('[useBudgetVersions] Error:', error)
        throw error
      }
    },
    // Enable query when session exists - session presence means user is authenticated
    enabled: !!session,
    // Prevent excessive refetching - budget versions don't change frequently
    staleTime: 30_000, // 30 seconds
    refetchOnWindowFocus: false, // Don't refetch on tab focus
    // Disable retries to see actual errors immediately
    retry: false,
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
