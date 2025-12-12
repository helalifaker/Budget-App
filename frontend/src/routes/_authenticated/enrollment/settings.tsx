/**
 * Enrollment Settings Page - /enrollment/settings
 *
 * Step 1 of the enrollment planning workflow. Configure:
 * - Class size parameters (Min/Target/Max per level)
 * - Lateral entry calibration (auto-derived from historical data)
 * - Scenario multipliers
 *
 * Features:
 * - Tabbed interface for Class Sizes and Calibration Settings
 * - Auto-calibration from rolling 4-year historical window
 * - Override capability for manual rate adjustments
 * - Scenario multipliers for sensitivity analysis
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { PageContainer } from '@/components/layout/PageContainer'
import { ExcelDataTableLazy, type ClearedCell } from '@/components/ExcelDataTableLazy'
import { AlertCircle, Save, Settings, BarChart3, CheckCircle, Sliders, History } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import {
  useClassSizeParams,
  useCreateClassSizeParam,
  useLevels,
  useCycles,
} from '@/hooks/api/useConfiguration'
import {
  useEnrollmentSettings,
  useCalibrateParameters,
  useUpdateParameterOverride,
  useUpdateScenarioMultiplier,
  useResetScenarioMultipliers,
} from '@/hooks/api/useEnrollmentSettings'
import { CalibrationStatusBar } from '@/components/enrollment/CalibrationStatusBar'
import { EntryPointRatesTable } from '@/components/enrollment/EntryPointRatesTable'
import { IncidentalLateralTable } from '@/components/enrollment/IncidentalLateralTable'
import { ScenarioMultipliersTable } from '@/components/enrollment/ScenarioMultipliersTable'
import { toastMessages } from '@/lib/toast-messages'
import { toast } from 'sonner'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useOrganization } from '@/hooks/api/useOrganization'
import type { ParameterOverrideUpdate, ScenarioMultiplierUpdate } from '@/types/enrollmentSettings'

export const Route = createFileRoute('/_authenticated/enrollment/settings')({
  beforeLoad: requireAuth,
  component: EnrollmentSettingsPage,
})

// ============================================================================
// Types for local state
// ============================================================================

interface LocalLevelConfig {
  level_id: string
  level_code: string
  level_name: string
  cycle_id: string
  cycle_code: string
  min_class_size: number
  target_class_size: number
  max_class_size: number
  notes: string | null
  isValid: boolean
  hasExistingConfig: boolean
  isDirty: boolean
}

// Default values for class sizes
const DEFAULT_MIN_SIZE = 15
const DEFAULT_TARGET_SIZE = 25
const DEFAULT_MAX_SIZE = 30

// ============================================================================
// Validation helper
// ============================================================================

function validateClassSizeRow(min: number, target: number, max: number): boolean {
  return min > 0 && target > 0 && max > 0 && min < target && target <= max
}

// ============================================================================
// Main Page Component
// ============================================================================

function EnrollmentSettingsPage() {
  const { selectedVersionId } = useBudgetVersion()
  const { organizationId, isLoading: orgLoading } = useOrganization()
  const [activeTab, setActiveTab] = useState('class-sizes')

  // Local state for class size editing
  const [localConfigs, setLocalConfigs] = useState<LocalLevelConfig[]>([])
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Class Size Queries
  const {
    data: classSizeParamsData,
    isLoading: paramsLoading,
    error: paramsError,
  } = useClassSizeParams(selectedVersionId)
  const { data: levelsData, isLoading: levelsLoading } = useLevels()
  const { data: cyclesData } = useCycles()

  // Calibration Queries & Mutations
  const {
    data: settingsData,
    isLoading: settingsLoading,
    error: settingsError,
  } = useEnrollmentSettings(organizationId)

  const calibrateMutation = useCalibrateParameters()
  const updateOverrideMutation = useUpdateParameterOverride()
  const updateMultiplierMutation = useUpdateScenarioMultiplier()
  const resetMultipliersMutation = useResetScenarioMultipliers()

  // Class Size Mutations
  const createMutation = useCreateClassSizeParam()

  // Get cycle code from cycle_id
  const getCycleCode = useCallback(
    (cycleId: string): string => {
      return cyclesData?.find((c) => c.id === cycleId)?.code || ''
    },
    [cyclesData]
  )

  // Initialize local state from API data + all levels with defaults
  useEffect(() => {
    if (levelsData && cyclesData) {
      const configs = levelsData.map((level): LocalLevelConfig => {
        const existingConfig = classSizeParamsData?.find((c) => c.level_id === level.id)
        const min = existingConfig?.min_class_size ?? DEFAULT_MIN_SIZE
        const target = existingConfig?.target_class_size ?? DEFAULT_TARGET_SIZE
        const max = existingConfig?.max_class_size ?? DEFAULT_MAX_SIZE

        return {
          level_id: level.id,
          level_code: level.code,
          level_name: level.name_en || level.name_fr,
          cycle_id: level.cycle_id,
          cycle_code: getCycleCode(level.cycle_id),
          min_class_size: min,
          target_class_size: target,
          max_class_size: max,
          notes: existingConfig?.notes ?? null,
          isValid: validateClassSizeRow(min, target, max),
          hasExistingConfig: !!existingConfig,
          isDirty: false,
        }
      })

      // Sort by cycle order then level order
      configs.sort((a, b) => {
        const cycleA = cyclesData.find((c) => c.id === a.cycle_id)?.sort_order ?? 0
        const cycleB = cyclesData.find((c) => c.id === b.cycle_id)?.sort_order ?? 0
        if (cycleA !== cycleB) return cycleA - cycleB
        const levelA = levelsData.find((l) => l.id === a.level_id)?.sort_order ?? 0
        const levelB = levelsData.find((l) => l.id === b.level_id)?.sort_order ?? 0
        return levelA - levelB
      })

      setLocalConfigs(configs)
      setHasUnsavedChanges(false)
    }
  }, [levelsData, cyclesData, classSizeParamsData, getCycleCode])

  // Calculate summary statistics for class sizes
  const statistics = useMemo(() => {
    if (localConfigs.length === 0) {
      return {
        levelsConfigured: 0,
        totalLevels: 0,
        averageTargetSize: 0,
        sizeRange: { min: 0, max: 0 },
        allValid: true,
        isComplete: false,
      }
    }

    const configuredCount = localConfigs.filter((c) => c.hasExistingConfig || c.isDirty).length
    const targetSizes = localConfigs.map((c) => c.target_class_size)
    const minSizes = localConfigs.map((c) => c.min_class_size)
    const maxSizes = localConfigs.map((c) => c.max_class_size)

    return {
      levelsConfigured: configuredCount,
      totalLevels: localConfigs.length,
      averageTargetSize: Math.round(
        targetSizes.reduce((sum, t) => sum + t, 0) / targetSizes.length
      ),
      sizeRange: {
        min: Math.min(...minSizes),
        max: Math.max(...maxSizes),
      },
      allValid: localConfigs.every((c) => c.isValid),
      isComplete: configuredCount === localConfigs.length,
    }
  }, [localConfigs])

  // Handle cell value changes for class sizes
  const onCellValueChanged = useCallback((event: CellValueChangedEvent<LocalLevelConfig>) => {
    const { data, colDef, newValue } = event
    if (!data || !colDef.field) return

    setLocalConfigs((prev) =>
      prev.map((config) => {
        if (config.level_id !== data.level_id) return config

        const updated = { ...config, [colDef.field!]: newValue, isDirty: true }

        // Recalculate validation
        updated.isValid = validateClassSizeRow(
          updated.min_class_size,
          updated.target_class_size,
          updated.max_class_size
        )

        return updated
      })
    )
    setHasUnsavedChanges(true)
  }, [])

  /**
   * Handle paste from clipboard (Ctrl+V)
   * Updates local state with pasted values
   */
  const handlePaste = useCallback(
    async (
      updates: Array<{ rowId: string; field: string; newValue: string; originalData: unknown }>
    ) => {
      setLocalConfigs((prev) =>
        prev.map((config) => {
          const update = updates.find((u) => u.rowId === config.level_id)
          if (!update) return config

          const numericValue = parseFloat(update.newValue)
          if (isNaN(numericValue)) return config

          const updated = { ...config, [update.field]: numericValue, isDirty: true }

          // Recalculate validation
          updated.isValid = validateClassSizeRow(
            updated.min_class_size,
            updated.target_class_size,
            updated.max_class_size
          )

          return updated
        })
      )
      setHasUnsavedChanges(true)
    },
    []
  )

  /**
   * Handle cell clear (Delete key)
   * Resets cleared cells to defaults
   */
  const handleCellsCleared = useCallback((cells: ClearedCell[]) => {
    setLocalConfigs((prev) =>
      prev.map((config) => {
        const clearedCell = cells.find((c) => c.rowId === config.level_id)
        if (!clearedCell) return config

        // Reset to default values based on field
        let defaultValue = 0
        if (clearedCell.field === 'min_class_size') defaultValue = DEFAULT_MIN_SIZE
        if (clearedCell.field === 'target_class_size') defaultValue = DEFAULT_TARGET_SIZE
        if (clearedCell.field === 'max_class_size') defaultValue = DEFAULT_MAX_SIZE

        const updated = { ...config, [clearedCell.field]: defaultValue, isDirty: true }

        // Recalculate validation
        updated.isValid = validateClassSizeRow(
          updated.min_class_size,
          updated.target_class_size,
          updated.max_class_size
        )

        return updated
      })
    )
    setHasUnsavedChanges(true)
  }, [])

  // Handle save for class sizes
  const handleSaveClassSizes = async () => {
    if (!selectedVersionId || !statistics.allValid) return

    const dirtyConfigs = localConfigs.filter((c) => c.isDirty)

    if (dirtyConfigs.length === 0) {
      toast.info('No changes to save')
      return
    }

    // Prevent double-click by checking if already saving
    if (isSaving) {
      console.log('[Settings] Save already in progress, ignoring')
      return
    }

    setIsSaving(true)

    try {
      // Save each dirty config
      let savedCount = 0
      for (const config of dirtyConfigs) {
        await createMutation.mutateAsync({
          budget_version_id: selectedVersionId,
          level_id: config.level_id,
          cycle_id: null,
          min_class_size: config.min_class_size,
          target_class_size: config.target_class_size,
          max_class_size: config.max_class_size,
          notes: config.notes,
        })
        savedCount++
      }

      console.log(`[Settings] Successfully saved ${savedCount} class size configurations`)

      // Mark all as saved
      setLocalConfigs((prev) =>
        prev.map((c) => ({
          ...c,
          isDirty: false,
          hasExistingConfig: c.hasExistingConfig || c.isDirty,
        }))
      )
      setHasUnsavedChanges(false)
      toastMessages.success.updated('Class size parameters')
    } catch (error) {
      console.error('[Settings] Failed to save class size parameters:', error)
      toastMessages.error.custom('Failed to save class size parameters')
    } finally {
      // Always reset isSaving regardless of success or failure
      console.log('[Settings] Resetting isSaving to false')
      setIsSaving(false)
    }
  }

  // Calibration handlers
  const handleRecalibrate = useCallback(() => {
    if (!organizationId) return
    calibrateMutation.mutate({ organizationId, request: { force: true } })
  }, [organizationId, calibrateMutation])

  const handleUpdateOverride = useCallback(
    (update: ParameterOverrideUpdate) => {
      if (!organizationId) return
      updateOverrideMutation.mutate({
        organizationId,
        gradeCode: update.grade_code,
        override: update,
      })
    },
    [organizationId, updateOverrideMutation]
  )

  const handleUpdateMultiplier = useCallback(
    (update: ScenarioMultiplierUpdate) => {
      if (!organizationId) return
      updateMultiplierMutation.mutate({
        organizationId,
        scenarioCode: update.scenario_code,
        multiplier: update,
      })
    },
    [organizationId, updateMultiplierMutation]
  )

  const handleResetMultipliers = useCallback(() => {
    if (!organizationId) return
    resetMultipliersMutation.mutate({ organizationId })
  }, [organizationId, resetMultipliersMutation])

  // Column definitions for class sizes
  const columnDefs: ColDef<LocalLevelConfig>[] = useMemo(
    () => [
      {
        field: 'cycle_code',
        headerName: 'Cycle',
        width: 90,
        editable: false,
        cellClass: 'font-medium text-text-secondary',
      },
      {
        field: 'level_code',
        headerName: 'Level',
        width: 90,
        editable: false,
        cellClass: 'font-medium',
      },
      {
        field: 'level_name',
        headerName: 'Name',
        flex: 1,
        minWidth: 150,
        editable: false,
      },
      {
        field: 'min_class_size',
        headerName: 'Min Size',
        width: 110,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        cellStyle: (params) => {
          if (!params.data?.isValid) {
            return { backgroundColor: 'var(--color-status-error-bg)' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: 'var(--color-status-warning-bg)' }
          }
          return null
        },
      },
      {
        field: 'target_class_size',
        headerName: 'Target Size',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        cellStyle: (params) => {
          if (!params.data?.isValid) {
            return { backgroundColor: 'var(--color-status-error-bg)' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: 'var(--color-status-warning-bg)' }
          }
          return null
        },
      },
      {
        field: 'max_class_size',
        headerName: 'Max Size',
        width: 110,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        cellStyle: (params) => {
          if (!params.data?.isValid) {
            return { backgroundColor: 'var(--color-status-error-bg)' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: 'var(--color-status-warning-bg)' }
          }
          return null
        },
      },
      {
        field: 'notes',
        headerName: 'Notes',
        flex: 1,
        minWidth: 150,
        editable: true,
        cellStyle: (params) => {
          if (params.data?.isDirty) {
            return { backgroundColor: 'var(--color-status-warning-bg)' }
          }
          return null
        },
      },
      {
        headerName: 'Valid',
        width: 80,
        editable: false,
        cellRenderer: (params: { data?: LocalLevelConfig }) => {
          if (!params.data) return null
          return params.data.isValid ? (
            <span className="text-success-600 font-bold">✓</span>
          ) : (
            <span className="text-error-600 font-bold">⚠</span>
          )
        },
        cellClass: 'text-center',
      },
    ],
    []
  )

  const isClassSizesLoading = paramsLoading || levelsLoading
  const isCalibrationLoading = settingsLoading || orgLoading

  return (
    <PageContainer
      title="Enrollment Settings"
      description="Configure class sizes and lateral entry parameters (Step 1 of enrollment planning)"
    >
      <div className="space-y-6">
        {/* Version Selection Warning */}
        {!selectedVersionId && (
          <div className="flex items-center gap-2 p-4 bg-subtle border border-border-light rounded-lg">
            <AlertCircle className="h-4 w-4 text-sand-600" />
            <p className="text-sm text-sand-800">
              Please select a budget version to view and edit enrollment settings.
            </p>
          </div>
        )}

        {selectedVersionId && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="class-sizes" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Class Sizes
              </TabsTrigger>
              <TabsTrigger value="calibration" className="flex items-center gap-2">
                <Sliders className="h-4 w-4" />
                Lateral Entry
              </TabsTrigger>
            </TabsList>

            {/* Class Sizes Tab */}
            <TabsContent value="class-sizes" className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <SummaryCard
                  title="Levels Configured"
                  value={`${statistics.levelsConfigured} / ${statistics.totalLevels}`}
                  subtitle={
                    statistics.isComplete ? 'All levels configured' : 'Some levels using defaults'
                  }
                  icon={<Settings className="h-4 w-4" />}
                />
                <SummaryCard
                  title="Average Target Size"
                  value={statistics.averageTargetSize}
                  subtitle="Students per class"
                  icon={<BarChart3 className="h-4 w-4" />}
                />
                <SummaryCard
                  title="Size Range"
                  value={`${statistics.sizeRange.min} - ${statistics.sizeRange.max}`}
                  subtitle="Min to Max across levels"
                  icon={<BarChart3 className="h-4 w-4" />}
                />
                <SummaryCard
                  title="Configuration Status"
                  value={statistics.allValid ? 'Valid' : 'Has Errors'}
                  subtitle={
                    statistics.allValid ? 'All validations pass' : 'Please fix validation errors'
                  }
                  trend={statistics.allValid ? 'up' : 'down'}
                  icon={<CheckCircle className="h-4 w-4" />}
                />
              </div>

              {/* Action Bar */}
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Edit cells directly. Changes are saved when you click "Save Changes". Validation:
                  Min &lt; Target ≤ Max
                </p>
                <Button
                  onClick={handleSaveClassSizes}
                  disabled={!hasUnsavedChanges || !statistics.allValid || isSaving}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                  {hasUnsavedChanges && (
                    <Badge variant="secondary" className="ml-2 bg-amber-100 text-amber-800">
                      Unsaved
                    </Badge>
                  )}
                </Button>
              </div>

              {/* Validation Error Banner */}
              {!statistics.allValid && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <p className="text-sm text-red-700">
                    Some rows have invalid values. Min must be less than Target, and Target must be
                    ≤ Max.
                  </p>
                </div>
              )}

              {/* Data Grid */}
              <ExcelDataTableLazy<LocalLevelConfig>
                rowData={localConfigs}
                columnDefs={columnDefs}
                loading={isClassSizesLoading}
                error={paramsError}
                pagination={false}
                onCellValueChanged={onCellValueChanged}
                domLayout="autoHeight"
                defaultColDef={{
                  sortable: true,
                  resizable: true,
                }}
                getRowId={(params) => params.data.level_id}
                // Excel-like clipboard support
                onPaste={handlePaste}
                onCellsCleared={handleCellsCleared}
                rowIdGetter={(data) => data.level_id}
                tableLabel="Class Size Parameters"
                showStatusBar={true}
              />
            </TabsContent>

            {/* Calibration Tab */}
            <TabsContent value="calibration" className="space-y-6">
              {!organizationId ? (
                <div className="flex items-center gap-2 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <p className="text-sm text-amber-800">
                    Organization information not available. Please ensure a valid budget version is
                    selected.
                  </p>
                </div>
              ) : isCalibrationLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
              ) : settingsError ? (
                <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <p className="text-sm text-red-700">
                    Failed to load calibration settings. Please try refreshing the page.
                  </p>
                </div>
              ) : settingsData ? (
                <>
                  {/* Calibration Stats Bar - Full Width */}
                  <CalibrationStatusBar
                    status={settingsData.calibration_status}
                    onRecalibrate={handleRecalibrate}
                    isRecalibrating={calibrateMutation.isPending}
                  />

                  {/* Data Sufficiency Warning */}
                  {!settingsData.calibration_status.has_sufficient_data && (
                    <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5" />
                      <div className="text-sm text-amber-800">
                        <p className="font-medium">Insufficient Historical Data</p>
                        <p className="text-amber-700">
                          At least 2 years of enrollment data are needed for reliable calibration.
                          Using document defaults instead.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Sub-Tabs for Configuration Sections */}
                  <Tabs defaultValue="entry-points" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="entry-points" className="gap-2">
                        <History className="h-4 w-4" />
                        <span className="hidden sm:inline">Entry Point Rates</span>
                        <span className="sm:hidden">Entry Points</span>
                      </TabsTrigger>
                      <TabsTrigger value="incidental" className="gap-2">
                        <BarChart3 className="h-4 w-4" />
                        <span className="hidden sm:inline">Incidental Lateral</span>
                        <span className="sm:hidden">Incidental</span>
                      </TabsTrigger>
                      <TabsTrigger value="scenarios" className="gap-2">
                        <Sliders className="h-4 w-4" />
                        <span className="hidden sm:inline">Scenario Multipliers</span>
                        <span className="sm:hidden">Scenarios</span>
                      </TabsTrigger>
                    </TabsList>

                    {/* Entry Point Rates Tab */}
                    <TabsContent value="entry-points">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <History className="h-5 w-5 text-purple-600" />
                            Entry Point Rates
                          </CardTitle>
                          <CardDescription>
                            Percentage-based lateral entry for major intake grades (MS, GS, CP,
                            6ème, 2nde)
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <EntryPointRatesTable
                            rates={settingsData.entry_point_rates}
                            onUpdate={handleUpdateOverride}
                            disabled={
                              updateOverrideMutation.isPending || calibrateMutation.isPending
                            }
                          />
                        </CardContent>
                      </Card>
                    </TabsContent>

                    {/* Incidental Lateral Tab */}
                    <TabsContent value="incidental">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <BarChart3 className="h-5 w-5 text-blue-600" />
                            Incidental Lateral Entry
                          </CardTitle>
                          <CardDescription>
                            Fixed lateral entry values for intermediate grades
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <IncidentalLateralTable
                            entries={settingsData.incidental_lateral}
                            onUpdate={handleUpdateOverride}
                            disabled={
                              updateOverrideMutation.isPending || calibrateMutation.isPending
                            }
                          />
                        </CardContent>
                      </Card>
                    </TabsContent>

                    {/* Scenario Multipliers Tab */}
                    <TabsContent value="scenarios">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <Sliders className="h-5 w-5 text-green-600" />
                            Scenario Multipliers
                          </CardTitle>
                          <CardDescription>
                            Adjust lateral entry rates by scenario for sensitivity analysis
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <ScenarioMultipliersTable
                            multipliers={settingsData.scenario_multipliers}
                            onUpdate={handleUpdateMultiplier}
                            onReset={handleResetMultipliers}
                            disabled={
                              updateMultiplierMutation.isPending ||
                              resetMultipliersMutation.isPending ||
                              calibrateMutation.isPending
                            }
                          />
                        </CardContent>
                      </Card>
                    </TabsContent>
                  </Tabs>
                </>
              ) : null}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </PageContainer>
  )
}
