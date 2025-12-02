import { apiRequest } from '@/lib/api-client'
import { SubjectHours, TeacherFTE, TRMDGap, HSAPlanning, PaginatedResponse } from '@/types/api'

export const dhgApi = {
  // Subject Hours
  getSubjectHours: async (versionId: string) => {
    return apiRequest<PaginatedResponse<SubjectHours>>({
      method: 'GET',
      url: `/planning/dhg/${versionId}/subject-hours`,
    })
  },

  updateSubjectHours: async (
    id: string,
    data: { hours_per_week: number; split_class: boolean }
  ) => {
    return apiRequest<SubjectHours>({
      method: 'PUT',
      url: `/planning/dhg/subject-hours/${id}`,
      data,
    })
  },

  bulkUpdateSubjectHours: async (
    versionId: string,
    updates: Array<{ id: string; hours_per_week: number; split_class: boolean }>
  ) => {
    return apiRequest<{ success: boolean; count: number }>({
      method: 'POST',
      url: `/planning/dhg/${versionId}/subject-hours/bulk-update`,
      data: { updates },
    })
  },

  // Teacher FTE
  getTeacherFTE: async (versionId: string) => {
    return apiRequest<PaginatedResponse<TeacherFTE>>({
      method: 'GET',
      url: `/planning/dhg/${versionId}/teacher-fte`,
    })
  },

  calculateFTE: async (versionId: string) => {
    return apiRequest<{ success: boolean; message: string }>({
      method: 'POST',
      url: `/planning/dhg/${versionId}/calculate-fte`,
    })
  },

  // TRMD Gap Analysis
  getTRMDGaps: async (versionId: string) => {
    return apiRequest<PaginatedResponse<TRMDGap>>({
      method: 'GET',
      url: `/planning/dhg/${versionId}/trmd-gaps`,
    })
  },

  updateTRMDGap: async (id: string, data: { aefe_positions: number; local_positions: number }) => {
    return apiRequest<TRMDGap>({
      method: 'PUT',
      url: `/planning/dhg/trmd-gaps/${id}`,
      data,
    })
  },

  // HSA Planning
  getHSAPlanning: async (versionId: string) => {
    return apiRequest<PaginatedResponse<HSAPlanning>>({
      method: 'GET',
      url: `/planning/dhg/${versionId}/hsa-planning`,
    })
  },

  createHSAPlanning: async (data: {
    budget_version_id: string
    teacher_id: string
    subject_id: string
    hsa_hours: number
    notes?: string
  }) => {
    return apiRequest<HSAPlanning>({
      method: 'POST',
      url: '/planning/dhg/hsa-planning',
      data,
    })
  },

  updateHSAPlanning: async (id: string, data: { hsa_hours: number; notes?: string }) => {
    return apiRequest<HSAPlanning>({
      method: 'PUT',
      url: `/planning/dhg/hsa-planning/${id}`,
      data,
    })
  },

  deleteHSAPlanning: async (id: string) => {
    return apiRequest<void>({
      method: 'DELETE',
      url: `/planning/dhg/hsa-planning/${id}`,
    })
  },
}
