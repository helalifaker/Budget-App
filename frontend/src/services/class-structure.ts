import { apiRequest } from '@/lib/api-client'
import { ClassStructure, PaginatedResponse } from '@/types/api'

export const classStructureApi = {
  getAll: async (versionId: string, params?: { page?: number; page_size?: number }) => {
    return apiRequest<PaginatedResponse<ClassStructure>>({
      method: 'GET',
      url: `/planning/class-structure/${versionId}`,
      params,
    })
  },

  getById: async (id: string) => {
    return apiRequest<ClassStructure>({
      method: 'GET',
      url: `/planning/class-structure/entry/${id}`,
    })
  },

  create: async (data: {
    budget_version_id: string
    level_id: string
    number_of_classes: number
    avg_class_size: number
  }) => {
    return apiRequest<ClassStructure>({
      method: 'POST',
      url: '/planning/class-structure',
      data,
    })
  },

  update: async (id: string, data: { number_of_classes?: number; avg_class_size?: number }) => {
    return apiRequest<ClassStructure>({
      method: 'PUT',
      url: `/planning/class-structure/${id}`,
      data,
    })
  },

  delete: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/class-structure/${id}`,
    })
  },

  calculateFromEnrollment: async (versionId: string) => {
    return apiRequest<{ success: boolean; message: string }>({
      method: 'POST',
      url: `/planning/class-structure/${versionId}/calculate`,
    })
  },
}
