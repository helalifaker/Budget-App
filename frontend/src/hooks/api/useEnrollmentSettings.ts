import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { enrollmentSettingsApi } from '@/services/enrollment-settings'
import { handleAPIErrorToast, toastMessages } from '@/lib/toast-messages'
import type {
  CalibrationRequest,
  ParameterOverrideUpdate,
  ScenarioMultiplierUpdate,
} from '@/types/enrollment-settings'

export const settingsKeys = {
  all: ['enrollment-settings'] as const,
  settings: (orgId: string, scenarioCode: string) =>
    [...settingsKeys.all, 'settings', orgId, scenarioCode] as const,
  status: (orgId: string) => [...settingsKeys.all, 'status', orgId] as const,
  history: (orgId: string) => [...settingsKeys.all, 'history', orgId] as const,
}

/**
 * Hook to get complete enrollment settings for the Settings tab.
 */
export function useEnrollmentSettings(organizationId: string | undefined, scenarioCode = 'base') {
  return useQuery({
    queryKey: settingsKeys.settings(organizationId ?? '', scenarioCode),
    queryFn: () => enrollmentSettingsApi.getSettings(organizationId!, scenarioCode),
    enabled: !!organizationId,
    staleTime: 30_000, // 30s staleTime for performance
  })
}

/**
 * Hook to get calibration status only.
 */
export function useCalibrationStatus(organizationId: string | undefined) {
  return useQuery({
    queryKey: settingsKeys.status(organizationId ?? ''),
    queryFn: () => enrollmentSettingsApi.getCalibrationStatus(organizationId!),
    enabled: !!organizationId,
    staleTime: 60_000, // Status can be stale longer
  })
}

/**
 * Hook to get historical data summary for calibration.
 */
export function useHistoricalDataSummary(organizationId: string | undefined) {
  return useQuery({
    queryKey: settingsKeys.history(organizationId ?? ''),
    queryFn: () => enrollmentSettingsApi.getHistoricalDataSummary(organizationId!),
    enabled: !!organizationId,
    staleTime: 60_000,
  })
}

/**
 * Hook to trigger calibration of derived parameters.
 */
export function useCalibrateParameters() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      request,
    }: {
      organizationId: string
      request?: CalibrationRequest
    }) => enrollmentSettingsApi.calibrate(organizationId, request),
    onSuccess: (data, variables) => {
      // Invalidate all settings queries for this org
      queryClient.invalidateQueries({
        queryKey: settingsKeys.all,
        predicate: (query) =>
          query.queryKey.includes(variables.organizationId) ||
          query.queryKey.includes('enrollment-settings'),
      })

      if (data.success) {
        toastMessages.success.custom(
          `Calibration complete: ${data.parameters_updated} parameters updated`
        )
      } else {
        toast.info(data.message)
      }
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to update a single parameter override.
 */
export function useUpdateParameterOverride() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      gradeCode,
      override,
      scenarioCode = 'base',
    }: {
      organizationId: string
      gradeCode: string
      override: ParameterOverrideUpdate
      scenarioCode?: string
    }) => enrollmentSettingsApi.updateOverride(organizationId, gradeCode, override, scenarioCode),
    onSuccess: (data, variables) => {
      // Update the cache with the returned settings
      queryClient.setQueryData(
        settingsKeys.settings(variables.organizationId, variables.scenarioCode ?? 'base'),
        data
      )
      toastMessages.success.updated(`Override for ${variables.gradeCode}`)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to bulk update parameter overrides.
 */
export function useUpdateParameterOverridesBulk() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      overrides,
      scenarioCode = 'base',
    }: {
      organizationId: string
      overrides: ParameterOverrideUpdate[]
      scenarioCode?: string
    }) => enrollmentSettingsApi.updateOverridesBulk(organizationId, overrides, scenarioCode),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        settingsKeys.settings(variables.organizationId, variables.scenarioCode ?? 'base'),
        data
      )
      toastMessages.success.updated(`${variables.overrides.length} parameter overrides`)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to update a scenario multiplier.
 */
export function useUpdateScenarioMultiplier() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      scenarioCode,
      multiplier,
    }: {
      organizationId: string
      scenarioCode: string
      multiplier: ScenarioMultiplierUpdate
    }) => enrollmentSettingsApi.updateMultiplier(organizationId, scenarioCode, multiplier),
    onSuccess: (_data, variables) => {
      // Invalidate all scenario settings since multiplier affects effective rates
      queryClient.invalidateQueries({ queryKey: settingsKeys.all })
      toastMessages.success.updated(`${variables.scenarioCode} multiplier`)
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to bulk update scenario multipliers.
 */
export function useUpdateScenarioMultipliersBulk() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      multipliers,
      scenarioCode = 'base',
    }: {
      organizationId: string
      multipliers: ScenarioMultiplierUpdate[]
      scenarioCode?: string
    }) => enrollmentSettingsApi.updateMultipliersBulk(organizationId, multipliers, scenarioCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.all })
      toastMessages.success.updated('Scenario multipliers')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to reset all parameter overrides.
 */
export function useResetParameterOverrides() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      scenarioCode = 'base',
    }: {
      organizationId: string
      scenarioCode?: string
    }) => enrollmentSettingsApi.resetOverrides(organizationId, scenarioCode),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        settingsKeys.settings(variables.organizationId, variables.scenarioCode ?? 'base'),
        data
      )
      toastMessages.success.custom('All overrides reset to derived/default values')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}

/**
 * Hook to reset scenario multipliers to defaults.
 */
export function useResetScenarioMultipliers() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      organizationId,
      scenarioCode = 'base',
    }: {
      organizationId: string
      scenarioCode?: string
    }) => enrollmentSettingsApi.resetMultipliers(organizationId, scenarioCode),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        settingsKeys.settings(variables.organizationId, variables.scenarioCode ?? 'base'),
        data
      )
      toastMessages.success.custom('Scenario multipliers reset to defaults')
    },
    onError: (error) => handleAPIErrorToast(error),
  })
}
