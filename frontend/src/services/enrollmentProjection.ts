import { apiRequest } from '@/lib/api-client'
import type {
  EnrollmentScenario,
  ProjectionConfig,
  GlobalOverrides,
  LevelOverride,
  GradeOverride,
  ProjectionResults,
} from '@/types/enrollmentProjection'
import { withServiceErrorHandling } from './utils'

const BASE_PATH = '/planning/enrollment-projection'

export const enrollmentProjectionApi = {
  getScenarios: async (): Promise<EnrollmentScenario[]> => {
    return withServiceErrorHandling(
      apiRequest<{ scenarios: EnrollmentScenario[] }>({
        method: 'GET',
        url: `${BASE_PATH}/scenarios`,
      }).then((r) => r.scenarios),
      'enrollmentProjection: get scenarios'
    )
  },

  getConfig: async (versionId: string): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'GET',
        url: `${BASE_PATH}/${versionId}/config`,
      }),
      'enrollmentProjection: get config'
    )
  },

  updateConfig: async (
    versionId: string,
    updates: Partial<ProjectionConfig>
  ): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'PUT',
        url: `${BASE_PATH}/${versionId}/config`,
        data: updates,
      }),
      'enrollmentProjection: update config'
    )
  },

  updateGlobalOverrides: async (
    versionId: string,
    overrides: GlobalOverrides
  ): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'PUT',
        url: `${BASE_PATH}/${versionId}/global-overrides`,
        data: overrides,
      }),
      'enrollmentProjection: update global overrides'
    )
  },

  updateLevelOverrides: async (
    versionId: string,
    overrides: Array<Pick<LevelOverride, 'cycle_id' | 'class_size_ceiling' | 'max_divisions'>>
  ): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'PUT',
        url: `${BASE_PATH}/${versionId}/level-overrides`,
        data: { overrides },
      }),
      'enrollmentProjection: update level overrides'
    )
  },

  updateGradeOverrides: async (
    versionId: string,
    overrides: Array<
      Pick<
        GradeOverride,
        'level_id' | 'retention_rate' | 'lateral_entry' | 'max_divisions' | 'class_size_ceiling'
      >
    >
  ): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'PUT',
        url: `${BASE_PATH}/${versionId}/grade-overrides`,
        data: { overrides },
      }),
      'enrollmentProjection: update grade overrides'
    )
  },

  getResults: async (
    versionId: string,
    includeFiscalProration = true
  ): Promise<ProjectionResults> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionResults>({
        method: 'GET',
        url: `${BASE_PATH}/${versionId}/results`,
        params: { include_fiscal_proration: includeFiscalProration },
      }),
      'enrollmentProjection: get results'
    )
  },

  calculate: async (versionId: string): Promise<ProjectionResults> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionResults>({
        method: 'POST',
        url: `${BASE_PATH}/${versionId}/calculate`,
      }),
      'enrollmentProjection: calculate'
    )
  },

  validate: async (
    versionId: string,
    confirmation: boolean
  ): Promise<{ success: boolean; downstream_updated: string[] }> => {
    return withServiceErrorHandling(
      apiRequest<{ success: boolean; downstream_updated: string[] }>({
        method: 'POST',
        url: `${BASE_PATH}/${versionId}/validate`,
        data: { confirmation },
      }),
      'enrollmentProjection: validate'
    )
  },

  unvalidate: async (versionId: string): Promise<ProjectionConfig> => {
    return withServiceErrorHandling(
      apiRequest<ProjectionConfig>({
        method: 'POST',
        url: `${BASE_PATH}/${versionId}/unvalidate`,
      }),
      'enrollmentProjection: unvalidate'
    )
  },
}
