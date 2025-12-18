/**
 * Enrollment Settings Page - /students/settings
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
import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { PageContainer } from '@/components/layout/PageContainer'
import { ExcelEditableTableLazy } from '@/components/grid/tanstack/ExcelEditableTableLazy'
import type { CellValueChangedEvent } from '@/components/grid/tanstack/EditableTable'
import { AlertCircle, Save, Settings, BarChart3, CheckCircle, Sliders, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import {
  useClassSizeParams,
  useBatchSaveClassSizeParams,
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
import { UnifiedLateralTable } from '@/components/enrollment/UnifiedLateralTable'
import { ScenarioMultipliersTable } from '@/components/enrollment/ScenarioMultipliersTable'
import { toastMessages } from '@/lib/toast-messages'
import { toast } from 'sonner'
import { useVersion } from '@/contexts/VersionContext'
import { useOrganization } from '@/hooks/api/useOrganization'
import type { ParameterOverrideUpdate, ScenarioMultiplierUpdate } from '@/types/enrollment-settings'

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
  updated_at: string | null // For optimistic locking
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
  const { selectedVersionId, selectedVersion } = useVersion()
  const { organizationId, isLoading: orgLoading } = useOrganization()
  const [activeTab, setActiveTab] = useState('class-sizes')

  // Class sizes are read-only when viewing an "actual" version
  const isActualVersion = selectedVersion?.scenario_type === 'ACTUAL'

  // Local state for class size editing
  const [localConfigs, setLocalConfigs] = useState<LocalLevelConfig[]>([])
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Ref to prevent useEffect from resetting state during save operations
  // This fixes the race condition where query invalidation during save
  // would reset isDirty flags before all configs are saved
  const savingInProgressRef = useRef(false)

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
  const batchSaveMutation = useBatchSaveClassSizeParams()

  // Get cycle code from cycle_id
  const getCycleCode = useCallback(
    (cycleId: string): string => {
      return cyclesData?.find((c) => c.id === cycleId)?.code || ''
    },
    [cyclesData]
  )

  // Initialize local state from API data + all levels with defaults
  useEffect(() => {
    // CRITICAL: Skip state reset if saving is in progress
    // This prevents the race condition where query invalidation during save
    // would reset isDirty flags before all configs are saved
    if (savingInProgressRef.current) {
      console.log('[Settings] Skipping state reset - save in progress')
      return
    }

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
          updated_at: existingConfig?.updated_at ?? null,
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
    const { data, field, newValue } = event
    if (!data || !field) return

    setLocalConfigs((prev) =>
      prev.map((config) => {
        if (config.level_id !== data.level_id) return config

        const updated = { ...config, [field]: newValue, isDirty: true }

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
   * Handle cell clear (Delete key)
   * Resets cleared cells to defaults
   */
  const handleCellsCleared = useCallback(
    (cells: Array<{ rowId: string; field: string; oldValue: unknown }>) => {
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
    },
    []
  )

  // Handle save for class sizes - batch save with optimistic locking
  const handleSaveClassSizes = async () => {
    if (!selectedVersionId || !statistics.allValid || isActualVersion) return

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
    // CRITICAL: Set ref to prevent useEffect from resetting state during save
    // This fixes the race condition where query invalidation during save
    // would reset isDirty flags before all configs are saved
    savingInProgressRef.current = true
    console.log('[Settings] Starting batch save - blocking state reset')

    try {
      // Build batch request with optimistic locking
      const batchRequest = {
        version_id: selectedVersionId,
        entries: dirtyConfigs.map((config) => ({
          level_id: config.level_id,
          min_class_size: config.min_class_size,
          target_class_size: config.target_class_size,
          max_class_size: config.max_class_size,
          notes: config.notes,
          updated_at: config.updated_at, // For optimistic locking
        })),
      }

      const result = await batchSaveMutation.mutateAsync(batchRequest)

      console.log(
        `[Settings] Batch save complete: created=${result.created_count}, updated=${result.updated_count}, conflicts=${result.conflict_count}`
      )

      // Handle conflicts if any
      if (result.conflict_count > 0) {
        const conflictEntries = result.entries.filter((e) => e.status === 'conflict')
        console.warn('[Settings] Conflicts detected:', conflictEntries)

        // Update local state with new updated_at values for successful entries
        setLocalConfigs((prev) =>
          prev.map((config) => {
            const entry = result.entries.find((e) => e.level_id === config.level_id)
            if (!entry) return config

            if (entry.status === 'conflict') {
              // Keep dirty flag for conflicts so user can retry after refresh
              return config
            }

            return {
              ...config,
              isDirty: false,
              hasExistingConfig: true,
              updated_at: entry.updated_at ?? config.updated_at,
            }
          })
        )

        // Show conflict dialog
        toast.error(
          `${result.conflict_count} record(s) were modified by another user. Please refresh and try again.`,
          {
            duration: 5000,
            action: {
              label: 'Refresh',
              onClick: () => window.location.reload(),
            },
          }
        )
      } else {
        // All succeeded - update local state
        setLocalConfigs((prev) =>
          prev.map((config) => {
            const entry = result.entries.find((e) => e.level_id === config.level_id)
            if (!entry) return config

            return {
              ...config,
              isDirty: false,
              hasExistingConfig: true,
              updated_at: entry.updated_at ?? config.updated_at,
            }
          })
        )
        setHasUnsavedChanges(false)
      }
    } catch (error) {
      console.error('[Settings] Failed to batch save class size parameters:', error)
      toastMessages.error.custom('Failed to save class size parameters')
    } finally {
      // Always reset flags regardless of success or failure
      console.log('[Settings] Save complete - allowing state reset')
      savingInProgressRef.current = false
      setIsSaving(false)
    }
  }

  // Calibration handlers
  const handleRecalibrate = useCallback(() => {
    if (!organizationId || !selectedVersionId) {
      toast.error('Please select a budget version before calibrating')
      return
    }
    // Pass version_id to determine target academic year
    // For Budget 2026 (fiscal_year=2026), calibration targets 2026-2027
    calibrateMutation.mutate({
      organizationId,
      request: {
        version_id: selectedVersionId,
        force: true,
      },
    })
  }, [organizationId, selectedVersionId, calibrateMutation])

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

  // Helper to get cell class based on validation/dirty state
  const getCellClassName = useCallback(
    (data: LocalLevelConfig | undefined, isEditable: boolean): string => {
      if (!data) return ''
      const classes: string[] = []
      if (!data.isValid && isEditable) classes.push('bg-terracotta-50')
      else if (data.isDirty && isEditable) classes.push('bg-gold-50')
      return classes.join(' ')
    },
    []
  )

  // Column definitions for class sizes (TanStack Table format)
  // Improved column widths and styling for better readability
  const columnDefs: ColumnDef<LocalLevelConfig, unknown>[] = useMemo(
    () => [
      {
        id: 'cycle_code',
        accessorKey: 'cycle_code',
        header: 'Cycle',
        size: 80,
        meta: { editable: false },
        cell: (info) => (
          <span className="font-medium text-muted-foreground px-1">
            {info.getValue() as string}
          </span>
        ),
      },
      {
        id: 'level_code',
        accessorKey: 'level_code',
        header: 'Level',
        size: 80,
        meta: { editable: false },
        cell: (info) => (
          <span className="font-semibold text-foreground px-1">{info.getValue() as string}</span>
        ),
      },
      {
        id: 'level_name',
        accessorKey: 'level_name',
        header: 'Name',
        size: 250,
        minSize: 200,
        meta: { editable: false },
        cell: (info) => <span className="text-foreground px-1">{info.getValue() as string}</span>,
      },
      {
        id: 'min_class_size',
        accessorKey: 'min_class_size',
        header: () => <span className="block text-right w-full">Min</span>,
        size: 70,
        meta: {
          editable: !isActualVersion,
          editorType: 'number' as const,
          min: 1,
          max: 50,
          precision: 0,
          align: 'right',
        },
        cell: (info) => {
          const data = info.row.original
          return (
            <div
              className={`text-right tabular-nums px-2 ${getCellClassName(data, !isActualVersion)}`}
            >
              {info.getValue() as number}
            </div>
          )
        },
      },
      {
        id: 'target_class_size',
        accessorKey: 'target_class_size',
        header: () => <span className="block text-right w-full">Target</span>,
        size: 80,
        meta: {
          editable: !isActualVersion,
          editorType: 'number' as const,
          min: 1,
          max: 50,
          precision: 0,
          align: 'right',
        },
        cell: (info) => {
          const data = info.row.original
          return (
            <div
              className={`text-right tabular-nums font-medium px-2 ${getCellClassName(data, !isActualVersion)}`}
            >
              {info.getValue() as number}
            </div>
          )
        },
      },
      {
        id: 'max_class_size',
        accessorKey: 'max_class_size',
        header: () => <span className="block text-right w-full">Max</span>,
        size: 70,
        meta: {
          editable: !isActualVersion,
          editorType: 'number' as const,
          min: 1,
          max: 50,
          precision: 0,
          align: 'right',
        },
        cell: (info) => {
          const data = info.row.original
          return (
            <div
              className={`text-right tabular-nums px-2 ${getCellClassName(data, !isActualVersion)}`}
            >
              {info.getValue() as number}
            </div>
          )
        },
      },
      {
        id: 'notes',
        accessorKey: 'notes',
        header: 'Notes',
        size: 170,
        meta: {
          editable: !isActualVersion,
          editorType: 'text' as const,
        },
        cell: (info) => {
          const data = info.row.original
          const value = info.getValue() as string | null
          return (
            <div className={`px-2 ${getCellClassName(data, !isActualVersion)}`}>
              {value ? (
                <span className="text-foreground">{value}</span>
              ) : (
                <span className="text-muted-foreground/50">—</span>
              )}
            </div>
          )
        },
      },
      {
        id: 'valid',
        header: '',
        size: 50,
        meta: { editable: false },
        cell: (info) => {
          const data = info.row.original
          return (
            <div className="flex items-center justify-center">
              {data.isValid ? (
                <CheckCircle className="h-4 w-4 text-sage-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-terracotta-500" />
              )}
            </div>
          )
        },
      },
    ],
    [getCellClassName, isActualVersion]
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

              {/* Read-Only Banner for Actual Versions */}
              {isActualVersion && (
                <div className="flex items-center gap-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <Info className="h-4 w-4 text-blue-600" />
                  <p className="text-sm text-blue-800">
                    You are viewing an <strong>Actual</strong> version. Class size parameters are
                    read-only. To make changes, select a Budget or Forecast version.
                  </p>
                </div>
              )}

              {/* Action Bar */}
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  {isActualVersion
                    ? 'Viewing actual data (read-only). Select a budget version to edit.'
                    : 'Edit cells directly. Changes are saved when you click "Save Changes". Validation: Min < Target ≤ Max'}
                </p>
                <Button
                  onClick={handleSaveClassSizes}
                  disabled={
                    isActualVersion || !hasUnsavedChanges || !statistics.allValid || isSaving
                  }
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                  {hasUnsavedChanges && !isActualVersion && (
                    <Badge variant="secondary" className="ml-2 bg-gold-100 text-gold-800">
                      Unsaved
                    </Badge>
                  )}
                </Button>
              </div>

              {/* Validation Error Banner */}
              {!statistics.allValid && (
                <div className="flex items-center gap-2 p-3 bg-terracotta-50 border border-terracotta-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-terracotta-600" />
                  <p className="text-sm text-terracotta-700">
                    Some rows have invalid values. Min must be less than Target, and Target must be
                    ≤ Max.
                  </p>
                </div>
              )}

              {/* Data Grid - TanStack Table */}
              <ExcelEditableTableLazy<LocalLevelConfig>
                rowData={localConfigs}
                columnDefs={columnDefs}
                getRowId={(data) => data.level_id}
                loading={isClassSizesLoading}
                error={paramsError}
                onCellValueChanged={onCellValueChanged}
                onCellsCleared={handleCellsCleared}
                tableLabel="Class Size Parameters"
                showSelectionStats={true}
                enableClipboard={true}
                enableFillDown={!isActualVersion}
                enableClear={!isActualVersion}
                compact={false}
                moduleColor="sage"
              />
            </TabsContent>

            {/* Calibration Tab */}
            <TabsContent value="calibration" className="space-y-6">
              {!organizationId ? (
                <div className="flex items-center gap-2 p-4 bg-terracotta-50 border border-terracotta-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-terracotta-600" />
                  <p className="text-sm text-terracotta-800">
                    Organization information not available. Please ensure a valid budget version is
                    selected.
                  </p>
                </div>
              ) : isCalibrationLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
              ) : settingsError ? (
                <div className="flex items-center gap-2 p-4 bg-terracotta-50 border border-terracotta-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-terracotta-600" />
                  <p className="text-sm text-terracotta-700">
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
                    <div className="flex items-start gap-2 p-3 bg-terracotta-50 border border-terracotta-200 rounded-lg">
                      <AlertCircle className="h-4 w-4 text-terracotta-600 mt-0.5" />
                      <div className="text-sm text-terracotta-800">
                        <p className="font-medium">Insufficient Historical Data</p>
                        <p className="text-terracotta-700">
                          At least 2 years of enrollment data are needed for reliable calibration.
                          Using document defaults instead.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Sub-Tabs: Lateral Rates (unified) and Scenario Multipliers */}
                  <Tabs defaultValue="lateral-rates" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="lateral-rates" className="gap-2">
                        <BarChart3 className="h-4 w-4" />
                        <span className="hidden sm:inline">Lateral Entry Rates</span>
                        <span className="sm:hidden">Lateral Rates</span>
                      </TabsTrigger>
                      <TabsTrigger value="scenarios" className="gap-2">
                        <Sliders className="h-4 w-4" />
                        <span className="hidden sm:inline">Scenario Multipliers</span>
                        <span className="sm:hidden">Scenarios</span>
                      </TabsTrigger>
                    </TabsList>

                    {/* Unified Lateral Rates Tab */}
                    <TabsContent value="lateral-rates">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <BarChart3 className="h-5 w-5 text-blue-600" />
                            Lateral Entry Rates
                          </CardTitle>
                          <CardDescription>
                            Unified percentage-based lateral entry for all 14 grades. Rates derived
                            from weighted historical analysis (70% N-1 + 30% N-2).
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <UnifiedLateralTable
                            entryPointRates={settingsData.entry_point_rates}
                            incidentalLateral={settingsData.incidental_lateral}
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
