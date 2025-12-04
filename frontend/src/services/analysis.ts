import { apiRequest } from '@/lib/api-client'
import type { KPI, VarianceReport, DashboardSummary, Activity, SystemAlert } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const analysisService = {
  /**
   * Get KPIs for a budget version
   */
  getKPIs: async (versionId: string): Promise<KPI[]> => {
    return withServiceErrorHandling(
      apiRequest<KPI[]>({
        method: 'GET',
        url: `/analysis/${versionId}/kpis`,
      }),
      'analysis: get KPIs'
    )
  },

  /**
   * Get variance report
   */
  getVarianceReport: async (
    versionId: string,
    period: 'T1' | 'T2' | 'T3' | 'ANNUAL'
  ): Promise<VarianceReport> => {
    return withServiceErrorHandling(
      apiRequest<VarianceReport>({
        method: 'GET',
        url: `/analysis/${versionId}/variance`,
        params: { period },
      }),
      'analysis: get variance report'
    )
  },

  /**
   * Import actual data
   */
  importActuals: async (
    versionId: string,
    period: string,
    file: File
  ): Promise<{ success: boolean; imported_count: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('period', period)

    return withServiceErrorHandling(
      apiRequest<{ success: boolean; imported_count: number }>({
        method: 'POST',
        url: `/analysis/${versionId}/import-actuals`,
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }),
      'analysis: import actuals'
    )
  },

  /**
   * Create forecast revision
   */
  createForecastRevision: async (versionId: string): Promise<{ new_version_id: string }> => {
    return withServiceErrorHandling(
      apiRequest<{ new_version_id: string }>({
        method: 'POST',
        url: `/analysis/${versionId}/create-forecast`,
      }),
      'analysis: create forecast revision'
    )
  },

  /**
   * Get dashboard summary
   */
  getDashboardSummary: async (versionId: string): Promise<DashboardSummary> => {
    return withServiceErrorHandling(
      apiRequest<DashboardSummary>({
        method: 'GET',
        url: `/analysis/${versionId}/dashboard`,
      }),
      'analysis: get dashboard summary'
    )
  },

  /**
   * Get recent activity
   */
  getRecentActivity: async (limit: number = 10): Promise<Activity[]> => {
    return withServiceErrorHandling(
      apiRequest<Activity[]>({
        method: 'GET',
        url: '/analysis/activity',
        params: { limit },
      }),
      'analysis: get activity'
    )
  },

  /**
   * Get system alerts
   */
  getSystemAlerts: async (versionId: string): Promise<SystemAlert[]> => {
    return withServiceErrorHandling(
      apiRequest<SystemAlert[]>({
        method: 'GET',
        url: `/analysis/${versionId}/alerts`,
      }),
      'analysis: get alerts'
    )
  },
}
