/**
 * Historical Comparison API Service
 *
 * Frontend service for fetching planning data with historical actuals
 * for comparison (N-2, N-1, Current).
 */

import { apiRequest } from '@/lib/api-client'
import type {
  EnrollmentWithHistoryResponse,
  ClassStructureWithHistoryResponse,
  DHGWithHistoryResponse,
  RevenueWithHistoryResponse,
  CostsWithHistoryResponse,
  CapExWithHistoryResponse,
} from '@/types/historical'

/**
 * Query parameters for historical endpoints
 */
interface HistoricalQueryParams {
  /** Number of historical years to include (default: 2) */
  history_years?: number
}

export const historicalService = {
  /**
   * Get enrollment data with historical comparison
   *
   * Returns enrollment by level with N-2 and N-1 actuals.
   */
  getEnrollmentWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<EnrollmentWithHistoryResponse> => {
    return apiRequest<EnrollmentWithHistoryResponse>({
      method: 'GET',
      url: `/historical/enrollment/${versionId}`,
      params,
    })
  },

  /**
   * Get class structure data with historical comparison
   *
   * Returns class counts by level with N-2 and N-1 actuals.
   */
  getClassesWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<ClassStructureWithHistoryResponse> => {
    return apiRequest<ClassStructureWithHistoryResponse>({
      method: 'GET',
      url: `/historical/classes/${versionId}`,
      params,
    })
  },

  /**
   * Get DHG data with historical comparison
   *
   * Returns teacher hours and FTE by subject with N-2 and N-1 actuals.
   */
  getDHGWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<DHGWithHistoryResponse> => {
    return apiRequest<DHGWithHistoryResponse>({
      method: 'GET',
      url: `/historical/dhg/${versionId}`,
      params,
    })
  },

  /**
   * Get revenue data with historical comparison
   *
   * Returns revenue by account code with N-2 and N-1 actuals.
   */
  getRevenueWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<RevenueWithHistoryResponse> => {
    return apiRequest<RevenueWithHistoryResponse>({
      method: 'GET',
      url: `/historical/revenue/${versionId}`,
      params,
    })
  },

  /**
   * Get costs data with historical comparison
   *
   * Returns personnel and operating costs by account code with N-2 and N-1 actuals.
   */
  getCostsWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<CostsWithHistoryResponse> => {
    return apiRequest<CostsWithHistoryResponse>({
      method: 'GET',
      url: `/historical/costs/${versionId}`,
      params,
    })
  },

  /**
   * Get CapEx data with historical comparison
   *
   * Returns capital expenditures by account code with N-2 and N-1 actuals.
   */
  getCapExWithHistory: async (
    versionId: string,
    params?: HistoricalQueryParams
  ): Promise<CapExWithHistoryResponse> => {
    return apiRequest<CapExWithHistoryResponse>({
      method: 'GET',
      url: `/historical/capex/${versionId}`,
      params,
    })
  },
}
