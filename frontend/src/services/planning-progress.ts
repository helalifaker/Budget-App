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
   * Get comprehensive planning progress for a version
   *
   * @param versionId - Version UUID
   * @returns Planning progress with validation for all 6 steps
   */
  getProgress: async (versionId: string): Promise<PlanningProgressResponse> => {
    return withServiceErrorHandling(
      apiRequest<PlanningProgressResponse>({
        method: 'GET',
        url: `/orchestration/progress/${versionId}`,
      }),
      'planning progress: get progress'
    )
  },
}
