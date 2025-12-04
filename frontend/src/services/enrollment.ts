import { apiRequest } from '@/lib/api-client'
import { Enrollment, PaginatedResponse } from '@/types/api'
import { withServiceErrorHandling } from './utils'

export const enrollmentApi = {
  getAll: async (versionId: string, params?: { page?: number; page_size?: number }) => {
    return withServiceErrorHandling(
      apiRequest<PaginatedResponse<Enrollment>>({
        method: 'GET',
        url: `/planning/enrollments/${versionId}`,
        params,
      }),
      'enrollment: get all'
    )
  },

  getById: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment>({
        method: 'GET',
        url: `/planning/enrollments/entry/${id}`,
      }),
      'enrollment: get by id'
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
        url: '/planning/enrollments',
        data,
      }),
      'enrollment: create'
    )
  },

  update: async (id: string, data: { student_count: number }) => {
    return withServiceErrorHandling(
      apiRequest<Enrollment>({
        method: 'PUT',
        url: `/planning/enrollments/${id}`,
        data,
      }),
      'enrollment: update'
    )
  },

  delete: async (id: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/planning/enrollments/${id}`,
      }),
      'enrollment: delete'
    )
  },

  calculateProjections: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; message: string }>({
        method: 'POST',
        url: `/planning/enrollments/${versionId}/calculate-projections`,
      }),
      'enrollment: calculate projections'
    )
  },

  bulkUpdate: async (
    versionId: string,
    enrollments: Array<{
      level_id: string
      nationality_type_id: string
      student_count: number
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; count: number }>({
        method: 'POST',
        url: `/planning/enrollments/${versionId}/bulk-update`,
        data: { enrollments },
      }),
      'enrollment: bulk update'
    )
  },
}
