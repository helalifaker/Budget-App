import { apiRequest } from '@/lib/api-client'
import type { KPI, VarianceReport, DashboardSummary, Activity, SystemAlert } from '@/types/api'

export const analysisService = {
  /**
   * Get KPIs for a budget version
   */
  getKPIs: async (versionId: string): Promise<KPI[]> => {
    return apiRequest<KPI[]>({
      method: 'GET',
      url: `/analysis/${versionId}/kpis`,
    })
  },

  /**
   * Get variance report
   */
  getVarianceReport: async (
    versionId: string,
    period: 'T1' | 'T2' | 'T3' | 'ANNUAL'
  ): Promise<VarianceReport> => {
    return apiRequest<VarianceReport>({
      method: 'GET',
      url: `/analysis/${versionId}/variance`,
      params: { period },
    })
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

    return apiRequest<{ success: boolean; imported_count: number }>({
      method: 'POST',
      url: `/analysis/${versionId}/import-actuals`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * Create forecast revision
   */
  createForecastRevision: async (versionId: string): Promise<{ new_version_id: string }> => {
    return apiRequest<{ new_version_id: string }>({
      method: 'POST',
      url: `/analysis/${versionId}/create-forecast`,
    })
  },

  /**
   * Get dashboard summary
   */
  getDashboardSummary: async (versionId: string): Promise<DashboardSummary> => {
    return apiRequest<DashboardSummary>({
      method: 'GET',
      url: `/analysis/${versionId}/dashboard`,
    })
  },

  /**
   * Get recent activity
   */
  getRecentActivity: async (limit: number = 10): Promise<Activity[]> => {
    return apiRequest<Activity[]>({
      method: 'GET',
      url: '/analysis/activity',
      params: { limit },
    })
  },

  /**
   * Get system alerts
   */
  getSystemAlerts: async (versionId: string): Promise<SystemAlert[]> => {
    return apiRequest<SystemAlert[]>({
      method: 'GET',
      url: `/analysis/${versionId}/alerts`,
    })
  },
}
