import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisService } from '@/services/analysis'
import { toastMessages, handleAPIErrorToast } from '@/lib/toast-messages'

export const analysisKeys = {
  all: ['analysis'] as const,
  kpis: (versionId: string) => [...analysisKeys.all, 'kpis', versionId] as const,
  variance: (versionId: string, period: string) =>
    [...analysisKeys.all, 'variance', versionId, period] as const,
  dashboard: (versionId: string) => [...analysisKeys.all, 'dashboard', versionId] as const,
  activity: () => [...analysisKeys.all, 'activity'] as const,
  alerts: (versionId: string) => [...analysisKeys.all, 'alerts', versionId] as const,
}

export function useKPIs(versionId: string) {
  return useQuery({
    queryKey: analysisKeys.kpis(versionId),
    queryFn: () => analysisService.getKPIs(versionId),
    enabled: !!versionId,
  })
}

export function useVarianceReport(versionId: string, period: 'T1' | 'T2' | 'T3' | 'ANNUAL') {
  return useQuery({
    queryKey: analysisKeys.variance(versionId, period),
    queryFn: () => analysisService.getVarianceReport(versionId, period),
    enabled: !!versionId,
  })
}

export function useImportActuals() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, period, file }: { versionId: string; period: string; file: File }) =>
      analysisService.importActuals(versionId, period, file),
    onSuccess: (data, { versionId, period }) => {
      queryClient.invalidateQueries({
        queryKey: analysisKeys.variance(versionId, period as 'T1' | 'T2' | 'T3' | 'ANNUAL'),
      })
      const count = (data as { imported_count?: number })?.imported_count ?? 0
      toastMessages.success.imported(count)
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useCreateForecastRevision() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (versionId: string) => analysisService.createForecastRevision(versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget-versions'] })
      toastMessages.success.created('Révision de prévision')
    },
    onError: (error) => {
      handleAPIErrorToast(error)
    },
  })
}

export function useDashboardSummary(versionId: string) {
  return useQuery({
    queryKey: analysisKeys.dashboard(versionId),
    queryFn: () => analysisService.getDashboardSummary(versionId),
    enabled: !!versionId,
  })
}

export function useRecentActivity(limit: number = 10) {
  return useQuery({
    queryKey: analysisKeys.activity(),
    queryFn: () => analysisService.getRecentActivity(limit),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

export function useSystemAlerts(versionId: string) {
  return useQuery({
    queryKey: analysisKeys.alerts(versionId),
    queryFn: () => analysisService.getSystemAlerts(versionId),
    enabled: !!versionId,
    refetchInterval: 60000, // Refresh every minute
  })
}
