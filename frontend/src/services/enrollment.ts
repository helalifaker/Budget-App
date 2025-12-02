import { apiRequest } from '@/lib/api-client'
import { Enrollment, PaginatedResponse } from '@/types/api'

export const enrollmentApi = {
  getAll: async (versionId: string, params?: { page?: number; page_size?: number }) => {
    return apiRequest<PaginatedResponse<Enrollment>>({
      method: 'GET',
      url: `/planning/enrollments/${versionId}`,
      params,
    })
  },

  getById: async (id: string) => {
    return apiRequest<Enrollment>({
      method: 'GET',
      url: `/planning/enrollments/entry/${id}`,
    })
  },

  create: async (data: {
    budget_version_id: string
    level_id: string
    nationality_type_id: string
    student_count: number
  }) => {
    return apiRequest<Enrollment>({
      method: 'POST',
      url: '/planning/enrollments',
      data,
    })
  },

  update: async (id: string, data: { student_count: number }) => {
    return apiRequest<Enrollment>({
      method: 'PUT',
      url: `/planning/enrollments/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/enrollments/${id}`,
    })
  },

  calculateProjections: async (versionId: string) => {
    return apiRequest<{ success: boolean; message: string }>({
      method: 'POST',
      url: `/planning/enrollments/${versionId}/calculate-projections`,
    })
  },

  bulkUpdate: async (
    versionId: string,
    enrollments: Array<{
      level_id: string
      nationality_type_id: string
      student_count: number
    }>
  ) => {
    return apiRequest<{ success: boolean; count: number }>({
      method: 'POST',
      url: `/planning/enrollments/${versionId}/bulk-update`,
      data: { enrollments },
    })
  },
}
