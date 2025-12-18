/**
 * Cascade API Service
 *
 * Handles cascade recalculation requests to the backend.
 * When a planning step changes, this service can trigger
 * recalculation of all downstream dependent steps.
 */

import { apiClient } from '@/lib/api-client'

/**
 * Response from cascade recalculation endpoint
 */
export interface CascadeResult {
  /** Steps that were recalculated */
  recalculated_steps: string[]
  /** Steps that failed recalculation */
  failed_steps: string[]
  /** Summary message */
  message: string
}

/**
 * Cascade API endpoints
 */
export const cascadeApi = {
  /**
   * Recalculate all steps downstream from a given step
   *
   * @param versionId - Version UUID
   * @param fromStepId - The step that changed (will recalculate all downstream)
   */
  recalculateFromStep: async (versionId: string, fromStepId: string): Promise<CascadeResult> => {
    const response = await apiClient.post<CascadeResult>(`/orchestration/cascade/${versionId}`, {
      from_step_id: fromStepId,
    })
    return response.data
  },

  /**
   * Recalculate specific steps
   *
   * @param versionId - Version UUID
   * @param stepIds - Array of step IDs to recalculate
   */
  recalculateSteps: async (versionId: string, stepIds: string[]): Promise<CascadeResult> => {
    const response = await apiClient.post<CascadeResult>(`/orchestration/cascade/${versionId}`, {
      step_ids: stepIds,
    })
    return response.data
  },
}
