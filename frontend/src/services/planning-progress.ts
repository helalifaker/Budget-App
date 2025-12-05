import { apiRequest } from '@/lib/api-client'
import { PlanningProgressResponse } from '@/types/planning-progress'
import { withServiceErrorHandling } from './utils'

/**
 * Planning Progress API Service
 *
 * Service for fetching planning progress and validation status.
 */
export const planningProgressApi = {
  /**
   * Get comprehensive planning progress for a budget version
   *
   * @param versionId - Budget version UUID
   * @returns Planning progress with validation for all 6 steps
   */
  getProgress: async (versionId: string): Promise<PlanningProgressResponse> => {
    return withServiceErrorHandling(
      apiRequest<PlanningProgressResponse>({
        method: 'GET',
        url: `/planning/progress/${versionId}`,
      }),
      'planning progress: get progress'
    )
  },
}
