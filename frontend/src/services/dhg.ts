import { apiRequest } from '@/lib/api-client'
import { withServiceErrorHandling } from './utils'

// Types matching backend schemas
interface DHGSubjectHours {
  id: string
  version_id: string
  subject_id: string
  level_id: string
  class_count: number
  hours_per_week: number
  total_weekly_hours: number
  total_annual_hours: number
  is_split: boolean
  notes?: string | null
  created_at: string
  updated_at: string
}

interface DHGTeacherRequirement {
  id: string
  version_id: string
  subject_id: string
  cycle_id: string
  required_hours: number
  standard_hours: number
  fte_required: number
  notes?: string | null
  created_at: string
  updated_at: string
}

interface TeacherAllocation {
  id: string
  version_id: string
  subject_id: string
  cycle_id: string
  category_id: string
  fte_count: number
  notes?: string | null
  created_at: string
  updated_at: string
}

interface TRMDGapAnalysis {
  version_id: string
  analysis_date: string
  gaps: Array<{
    subject_id: string
    cycle_id: string
    required_fte: number
    aefe_allocated: number
    local_allocated: number
    total_allocated: number
    deficit: number
    hsa_needed: number
  }>
  total_deficit: number
  total_hsa_needed: number
}

export const dhgApi = {
  // DHG Subject Hours
  getSubjectHours: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<DHGSubjectHours[]>({
        method: 'GET',
        url: `/dhg/subject-hours/${versionId}`,
      }),
      'dhg: get subject hours'
    )
  },

  calculateSubjectHours: async (versionId: string, recalculateAll: boolean = false) => {
    return withServiceErrorHandling(
      apiRequest<DHGSubjectHours[]>({
        method: 'POST',
        url: `/dhg/subject-hours/${versionId}/calculate`,
        data: { recalculate_all: recalculateAll },
      }),
      'dhg: calculate subject hours'
    )
  },

  // DHG Teacher Requirements
  getTeacherRequirements: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<DHGTeacherRequirement[]>({
        method: 'GET',
        url: `/dhg/teacher-requirements/${versionId}`,
      }),
      'dhg: get teacher requirements'
    )
  },

  calculateTeacherRequirements: async (versionId: string, recalculateAll: boolean = false) => {
    return withServiceErrorHandling(
      apiRequest<DHGTeacherRequirement[]>({
        method: 'POST',
        url: `/dhg/teacher-requirements/${versionId}/calculate`,
        data: { recalculate_all: recalculateAll },
      }),
      'dhg: calculate teacher requirements'
    )
  },

  // Teacher Allocations
  getAllocations: async (versionId: string) => {
    return withServiceErrorHandling(
      apiRequest<TeacherAllocation[]>({
        method: 'GET',
        url: `/dhg/allocations/${versionId}`,
      }),
      'dhg: get allocations'
    )
  },

  createAllocation: async (
    versionId: string,
    data: {
      subject_id: string
      cycle_id: string
      category_id: string
      fte_count: number
      notes?: string | null
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<TeacherAllocation>({
        method: 'POST',
        url: `/dhg/allocations/${versionId}`,
        data,
      }),
      'dhg: create allocation'
    )
  },

  updateAllocation: async (
    allocationId: string,
    data: {
      fte_count: number
      notes?: string | null
    }
  ) => {
    return withServiceErrorHandling(
      apiRequest<TeacherAllocation>({
        method: 'PUT',
        url: `/dhg/allocations/${allocationId}`,
        data,
      }),
      'dhg: update allocation'
    )
  },

  deleteAllocation: async (allocationId: string) => {
    return withServiceErrorHandling(
      apiRequest<void>({
        method: 'DELETE',
        url: `/dhg/allocations/${allocationId}`,
      }),
      'dhg: delete allocation'
    )
  },

  bulkUpdateAllocations: async (
    versionId: string,
    allocations: Array<{
      subject_id: string
      cycle_id: string
      category_id: string
      fte_count: number
      notes?: string | null
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<TeacherAllocation[]>({
        method: 'POST',
        url: `/dhg/allocations/${versionId}/bulk`,
        data: { allocations },
      }),
      'dhg: bulk update allocations'
    )
  },

  // TRMD Gap Analysis
  // Note: 422 errors are expected when prerequisites are missing
  getTRMDGapAnalysis: async (versionId: string) => {
    try {
      return await apiRequest<TRMDGapAnalysis>({
        method: 'GET',
        url: `/dhg/trmd/${versionId}`,
      })
    } catch (error) {
      // Silently handle 422 validation errors (expected when prerequisites missing)
      // Other errors will still be thrown
      if (error && typeof error === 'object' && 'status' in error && error.status === 422) {
        // Return null for missing prerequisites - React Query will handle this
        return null as unknown as TRMDGapAnalysis
      }
      // Log and re-throw unexpected errors
      console.error('[Service:dhg: get TRMD gap analysis]', error)
      throw error
    }
  },

  // =============================================================================
  // PERFORMANCE: Draft + Apply Pattern (BFF Endpoints)
  // =============================================================================

  /**
   * Save allocation changes as a draft without triggering FTE recalculation.
   * Use this for debounced auto-save as user edits allocation cells.
   */
  saveDraft: async (
    versionId: string,
    allocations: Array<{
      subject_id: string
      cycle_id: string
      category_id: string
      fte_count: number
      notes?: string | null
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<TeacherAllocation[]>({
        method: 'POST',
        url: `/dhg/${versionId}/draft`,
        data: { allocations },
      }),
      'dhg: save draft'
    )
  },

  /**
   * Apply allocation changes and run full FTE calculation.
   * This is the "Apply & Calculate" action that combines save + calculate.
   */
  applyAndCalculate: async (
    versionId: string,
    allocations?: Array<{
      subject_id: string
      cycle_id: string
      category_id: string
      fte_count: number
      notes?: string | null
    }>
  ) => {
    return withServiceErrorHandling(
      apiRequest<TRMDGapAnalysis>({
        method: 'POST',
        url: `/dhg/${versionId}/apply`,
        data: allocations ? { allocations } : {},
      }),
      'dhg: apply and calculate'
    )
  },
}
