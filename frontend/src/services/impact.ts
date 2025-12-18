/**
 * Impact Calculation API Service
 *
 * Frontend service for calculating real-time impact of budget changes.
 */

import { apiRequest } from '@/lib/api-client'

/**
 * Request parameters for impact calculation
 */
export interface ImpactCalculationRequest {
  step_id: 'enrollment' | 'class_structure' | 'dhg' | 'revenue' | 'costs' | 'capex'
  dimension_type: 'level' | 'subject' | 'account_code'
  dimension_id?: string | null
  dimension_code?: string | null
  field_name: string
  new_value: string | number | null
}

/**
 * Response from impact calculation
 */
export interface ImpactCalculationResponse {
  fte_change: number
  fte_current: number
  fte_proposed: number
  cost_impact_sar: number
  cost_current_sar: number
  cost_proposed_sar: number
  revenue_impact_sar: number
  revenue_current_sar: number
  revenue_proposed_sar: number
  margin_impact_pct: number
  margin_current_pct: number
  margin_proposed_pct: number
  affected_steps: string[]
}

export const impactService = {
  /**
   * Calculate impact of a proposed budget change
   *
   * This is a preview calculation - no changes are made to the database.
   * Use this to show users the cascading effects of their edits.
   */
  calculateImpact: async (
    versionId: string,
    request: ImpactCalculationRequest
  ): Promise<ImpactCalculationResponse> => {
    return apiRequest<ImpactCalculationResponse>({
      method: 'POST',
      url: `/impact/${versionId}`,
      data: request,
    })
  },
}
