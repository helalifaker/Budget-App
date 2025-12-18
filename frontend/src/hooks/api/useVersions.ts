import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { versionsApi, VersionsListParams, CloneVersionData } from '@/services/versions'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'
import { useAuth } from '@/contexts/AuthContext'
import { ScenarioType } from '@/types/api'

export const versionKeys = {
  all: ['versions'] as const,
  lists: () => [...versionKeys.all, 'list'] as const,
  list: (filters: string) => [...versionKeys.lists(), { filters }] as const,
  details: () => [...versionKeys.all, 'detail'] as const,
  detail: (id: string) => [...versionKeys.details(), id] as const,
}

// Backward compatibility alias
export const budgetVersionKeys = versionKeys

export type UseVersionsParams = {
  page?: number
  pageSize?: number
  scenarioType?: ScenarioType
  fiscalYear?: number
  status?: string
}

/**
 * Fetch versions with authentication check and optional filters.
 * Query is enabled when session exists - we don't wait for loading to complete
 * because if session exists, the user is authenticated.
 */
export function useVersions(params: UseVersionsParams = {}) {
  const { session } = useAuth()
  const { page = 1, pageSize = 50, scenarioType, fiscalYear, status } = params

  // Build filter key for query caching
  const filterKey = JSON.stringify({ page, pageSize, scenarioType, fiscalYear, status })

  return useQuery({
    queryKey: versionKeys.list(filterKey),
    queryFn: async () => {
      console.log('[useVersions] Fetching versions...')
      try {
        const apiParams: VersionsListParams = {
          page,
          page_size: pageSize,
        }
        if (scenarioType) apiParams.scenario_type = scenarioType
        if (fiscalYear) apiParams.fiscal_year = fiscalYear
        if (status) apiParams.status = status

        const result = await versionsApi.getAll(apiParams)
        console.log('[useVersions] Success:', result)
        return result
      } catch (error) {
        console.error('[useVersions] Error:', error)
        throw error
      }
    },
    // Enable query when session exists - session presence means user is authenticated
    enabled: !!session,
    // Prevent excessive refetching - versions don't change frequently
    staleTime: 30_000, // 30 seconds
    refetchOnWindowFocus: false, // Don't refetch on tab focus
    // Disable retries to see actual errors immediately
    retry: false,
  })
}

// Backward compatibility alias
export const useBudgetVersions = useVersions

export function useVersionById(id: string) {
  return useQuery({
    queryKey: versionKeys.detail(id),
    queryFn: () => versionsApi.getById(id),
    enabled: !!id,
  })
}

// Backward compatibility alias
export const useBudgetVersion = useVersionById

export function useCreateVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: versionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.created(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useCreateBudgetVersion = useCreateVersion

export function useUpdateVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; notes?: string } }) =>
      versionsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: versionKeys.detail(variables.id),
      })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.updated(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useUpdateBudgetVersion = useUpdateVersion

export function useDeleteVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: versionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.deleted(entityNames.budgetVersion)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useDeleteBudgetVersion = useDeleteVersion

export function useSubmitVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: versionsApi.submit,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: versionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.submitted()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useSubmitBudgetVersion = useSubmitVersion

export function useApproveVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: versionsApi.approve,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: versionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.approved()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useApproveBudgetVersion = useApproveVersion

export function useCloneVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CloneVersionData }) =>
      versionsApi.clone(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.cloned()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useCloneBudgetVersion = useCloneVersion

export function useRejectVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => versionsApi.reject(id, reason),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: versionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.unlocked()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useRejectBudgetVersion = useRejectVersion

export function useSupersedeVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => versionsApi.supersede(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: versionKeys.detail(data.id),
      })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      toastMessages.success.superseded()
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

// Backward compatibility alias
export const useSupersedeBudgetVersion = useSupersedeVersion
