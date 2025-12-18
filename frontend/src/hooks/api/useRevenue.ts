import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { revenueApi, pivotRevenueItems } from '@/services/revenue'
import { toastMessages, handleAPIErrorToast, entityNames } from '@/lib/toast-messages'
import { useMemo } from 'react'

// PERFORMANCE: 10 minutes staleTime for revenue data
// Revenue changes rarely during a session
const REVENUE_STALE_TIME = 10 * 60 * 1000 // 10 minutes

export const revenueKeys = {
  all: ['revenue'] as const,
  lists: () => [...revenueKeys.all, 'list'] as const,
  list: (versionId: string) => [...revenueKeys.lists(), versionId] as const,
  summary: (versionId: string) => [...revenueKeys.all, 'summary', versionId] as const,
  details: () => [...revenueKeys.all, 'detail'] as const,
  detail: (id: string) => [...revenueKeys.details(), id] as const,
}

/**
 * Get raw revenue items from backend (flat list)
 */
export function useRevenue(versionId: string) {
  return useQuery({
    queryKey: revenueKeys.list(versionId),
    queryFn: () => revenueApi.getAll(versionId),
    enabled: !!versionId,
    staleTime: REVENUE_STALE_TIME,
  })
}

/**
 * Get revenue items pivoted for UI display (one row per account with trimester columns).
 * This is a convenience hook that transforms the flat backend response.
 */
export function useRevenuePivoted(versionId: string) {
  const query = useRevenue(versionId)

  const pivotedData = useMemo(() => {
    if (!query.data) return []
    return pivotRevenueItems(query.data)
  }, [query.data])

  return {
    ...query,
    data: pivotedData,
    // Keep raw data available if needed
    rawData: query.data,
  }
}

/**
 * Get revenue summary statistics
 */
export function useRevenueSummary(versionId: string) {
  return useQuery({
    queryKey: revenueKeys.summary(versionId),
    queryFn: () => revenueApi.getSummary(versionId),
    enabled: !!versionId,
    staleTime: REVENUE_STALE_TIME,
  })
}

export function useRevenueItem(id: string) {
  return useQuery({
    queryKey: revenueKeys.detail(id),
    queryFn: () => revenueApi.getById(id),
    enabled: !!id,
    staleTime: REVENUE_STALE_TIME,
  })
}

export function useCreateRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(data.version_id) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.summary(data.version_id) })
      toastMessages.success.created(entityNames.revenue)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useUpdateRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
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
    }) => revenueApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(data.version_id) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.summary(data.version_id) })
      toastMessages.success.updated(entityNames.revenue)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useDeleteRevenueItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.lists() })
      toastMessages.success.deleted(entityNames.revenue)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useCalculateRevenue() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: revenueApi.calculateRevenue,
    onSuccess: (_, versionId) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(versionId) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.summary(versionId) })
      toastMessages.success.calculated()
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

export function useBulkUpdateRevenue() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      versionId,
      updates,
    }: {
      versionId: string
      updates: Array<{
        id: string
        amount_sar?: number
        notes?: string
      }>
    }) => revenueApi.bulkUpdate(versionId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: revenueKeys.list(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: revenueKeys.summary(variables.versionId) })
      toastMessages.success.updated(entityNames.revenue)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}
