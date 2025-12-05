import { apiRequest } from '@/lib/api-client'
import { withServiceErrorHandling } from './utils'

// Types matching backend schemas
interface ClassStructure {
  id: string
  budget_version_id: string
  level_id: string
  total_students: number
  number_of_classes: number
  avg_class_size: number
  requires_atsem: boolean
  atsem_count: number
  calculation_method: string
  notes?: string | null
  created_at: string
  updated_at: string
}

export const classStructureApi = {
  getAll: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<ClassStructure[]>({
        method: 'GET',
        url: `/planning/class-structure/${versionId}`,
      }),
      'class-structure: get all'
    )
  },

  calculate: async (
    versionId: string,
    data: {
      method?: string
      override_by_level?: Record<string, { number_of_classes?: number; avg_class_size?: number }>
    } = {}
  ) => {
    return withServiceErrorHandling(
      apiRequest<ClassStructure[]>({
        method: 'POST',
        url: `/planning/class-structure/${versionId}/calculate`,
        data,
      }),
      'class-structure: calculate'
    )
  },

  update: async (
    classStructureId: string,
    data: {
      total_students?: number
      number_of_classes?: number
      avg_class_size?: number
      requires_atsem?: boolean
      atsem_count?: number
      calculation_method?: string
      notes?: string | null
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<ClassStructure>({
        method: 'PUT',
        url: `/planning/class-structure/${classStructureId}`,
        data,
      }),
      'class-structure: update'
    )
  },
}
