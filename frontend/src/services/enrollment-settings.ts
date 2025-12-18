import { apiRequest } from '@/lib/api-client'
import type {
  EnrollmentSettingsResponse,
  CalibrationStatus,
  CalibrationResult,
  CalibrationRequest,
  HistoricalDataSummary,
  ParameterOverrideUpdate,
  ScenarioMultiplierUpdate,
} from '@/types/enrollment-settings'
import { withServiceErrorHandling } from './utils'

const BASE_PATH = '/enrollment/settings'

export const enrollmentSettingsApi = {
  /**
   * Get complete enrollment settings for the Settings tab.
   */
  getSettings: async (
    organizationId: string,
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'GET',
        url: BASE_PATH,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
      }),
      'enrollmentSettings: get settings'
    )
  },

  /**
   * Get calibration status.
   */
  getCalibrationStatus: async (organizationId: string): Promise<CalibrationStatus> => {
    return withServiceErrorHandling(
      apiRequest<CalibrationStatus>({
        method: 'GET',
        url: `${BASE_PATH}/status`,
        params: { organization_id: organizationId },
      }),
      'enrollmentSettings: get calibration status'
    )
  },

  /**
   * Trigger recalibration of derived parameters.
   */
  calibrate: async (
    organizationId: string,
    request?: CalibrationRequest
  ): Promise<CalibrationResult> => {
    return withServiceErrorHandling(
      apiRequest<CalibrationResult>({
        method: 'POST',
        url: `${BASE_PATH}/calibrate`,
        params: { organization_id: organizationId },
        data: request ?? { force: false },
      }),
      'enrollmentSettings: calibrate'
    )
  },

  /**
   * Get historical data summary for calibration.
   */
  getHistoricalDataSummary: async (organizationId: string): Promise<HistoricalDataSummary> => {
    return withServiceErrorHandling(
      apiRequest<HistoricalDataSummary>({
        method: 'GET',
        url: `${BASE_PATH}/history`,
        params: { organization_id: organizationId },
      }),
      'enrollmentSettings: get historical summary'
    )
  },

  /**
   * Update parameter override for a specific grade.
   */
  updateOverride: async (
    organizationId: string,
    gradeCode: string,
    override: ParameterOverrideUpdate,
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'PUT',
        url: `${BASE_PATH}/overrides/${gradeCode}`,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
        data: override,
      }),
      'enrollmentSettings: update override'
    )
  },

  /**
   * Bulk update parameter overrides for multiple grades.
   */
  updateOverridesBulk: async (
    organizationId: string,
    overrides: ParameterOverrideUpdate[],
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'PUT',
        url: `${BASE_PATH}/overrides`,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
        data: { overrides },
      }),
      'enrollmentSettings: update overrides bulk'
    )
  },

  /**
   * Update scenario multiplier.
   */
  updateMultiplier: async (
    organizationId: string,
    scenarioCode: string,
    multiplier: ScenarioMultiplierUpdate
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'PUT',
        url: `${BASE_PATH}/multipliers/${scenarioCode}`,
        params: { organization_id: organizationId },
        data: multiplier,
      }),
      'enrollmentSettings: update multiplier'
    )
  },

  /**
   * Bulk update scenario multipliers.
   */
  updateMultipliersBulk: async (
    organizationId: string,
    multipliers: ScenarioMultiplierUpdate[],
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'PUT',
        url: `${BASE_PATH}/multipliers`,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
        data: { multipliers },
      }),
      'enrollmentSettings: update multipliers bulk'
    )
  },

  /**
   * Reset all parameter overrides to use derived/default values.
   */
  resetOverrides: async (
    organizationId: string,
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'POST',
        url: `${BASE_PATH}/reset-overrides`,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
      }),
      'enrollmentSettings: reset overrides'
    )
  },

  /**
   * Reset scenario multipliers to default values.
   */
  resetMultipliers: async (
    organizationId: string,
    scenarioCode = 'base'
  ): Promise<EnrollmentSettingsResponse> => {
    return withServiceErrorHandling(
      apiRequest<EnrollmentSettingsResponse>({
        method: 'POST',
        url: `${BASE_PATH}/reset-multipliers`,
        params: { organization_id: organizationId, scenario_code: scenarioCode },
      }),
      'enrollmentSettings: reset multipliers'
    )
  },
}
