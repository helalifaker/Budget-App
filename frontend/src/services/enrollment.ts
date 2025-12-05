import { apiRequest } from '@/lib/api-client'
import { Enrollment, EnrollmentWithDistribution, NationalityDistribution } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const enrollmentApi = {
  getAll: async (versionId: string, params?: { page?: number; page_size?: number }) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment[]>({
        method: 'GET',
        url: `/planning/enrollment/${versionId}`,
        params,
      }),
      'enrollment: get all'
    )
  },

  create: async (data: {
    budget_version_id: string
    level_id: string
    nationality_type_id: string
    student_count: number
  }) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment>({
        method: 'POST',
        url: `/planning/enrollment/${data.budget_version_id}`,
        data,
      }),
      'enrollment: create'
    )
  },

  update: async (id: string, data: { student_count: number; notes?: string | null }) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment>({
        method: 'PUT',
        url: `/planning/enrollment/${id}`,
        data,
      }),
      'enrollment: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/planning/enrollment/${id}`,
      }),
      'enrollment: delete'
    )
  },

  getSummary: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{
        total_students: number
        by_cycle: Record<string, number>
        by_nationality: Record<string, number>
      }>({
        method: 'GET',
        url: `/planning/enrollment/${versionId}/summary`,
      }),
      'enrollment: get summary'
    )
  },

  project: async (
    versionId: string,
    data: {
      years_to_project: number
      growth_scenario: string
      custom_growth_rates?: Record<string, number>
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<Array<{ year: number; projected_enrollment: number }>>({
        method: 'POST',
        url: `/planning/enrollment/${versionId}/project`,
        data,
      }),
      'enrollment: project'
    )
  },

  // ============================================================================
  // Enrollment with Distribution API
  // ============================================================================

  /**
   * Get complete enrollment data with nationality distributions and calculated breakdown
   */
  getWithDistribution: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentWithDistribution>({
        method: 'GET',
        url: `/planning/enrollment/${versionId}/with-distribution`,
      }),
      'enrollment: get with distribution'
    )
  },

  /**
   * Bulk upsert enrollment totals by level.
   * Distributes students according to nationality percentages.
   */
  bulkUpsertTotals: async (
    versionId: string,
    totals: Array<{ level_id: string; total_students: number }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment[]>({
        method: 'PUT',
        url: `/planning/enrollment/${versionId}/bulk`,
        data: { totals },
      }),
      'enrollment: bulk upsert totals'
    )
  },

  // ============================================================================
  // Nationality Distribution API
  // ============================================================================

  /**
   * Get nationality distributions for all levels in a budget version
   */
  getDistributions: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<NationalityDistribution[]>({
        method: 'GET',
        url: `/planning/distributions/${versionId}`,
      }),
      'enrollment: get distributions'
    )
  },

  /**
   * Bulk upsert nationality distributions.
   * Each distribution must have percentages summing to 100%.
   */
  bulkUpsertDistributions: async (
    versionId: string,
    distributions: Array<{
      level_id: string
      french_pct: number
      saudi_pct: number
      other_pct: number
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<NationalityDistribution[]>({
        method: 'PUT',
        url: `/planning/distributions/${versionId}`,
        data: { distributions },
      }),
      'enrollment: bulk upsert distributions'
    )
  },
}
