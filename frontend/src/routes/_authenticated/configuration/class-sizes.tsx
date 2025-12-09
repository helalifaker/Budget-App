import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle, Save, Settings, BarChart3, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SummaryCard } from '@/components/SummaryCard'
import {
  useClassSizeParams,
  useCreateClassSizeParam,
  useLevels,
  useCycles,
} from '@/hooks/api/useConfiguration'
import { toastMessages } from '@/lib/toast-messages'
import { toast } from 'sonner'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/_authenticated/configuration/class-sizes')({
  beforeLoad: requireAuth,
  component: ClassSizesPage,
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

function ClassSizesPage() {
  const { selectedVersionId } = useBudgetVersion()

  // Local state for editing
  const [localConfigs, setLocalConfigs] = useState<LocalLevelConfig[]>([])
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Queries
  const {
    data: classSizeParamsData,
    isLoading: paramsLoading,
    error: paramsError,
  } = useClassSizeParams(selectedVersionId)
  const { data: levelsData, isLoading: levelsLoading } = useLevels()
  const { data: cyclesData } = useCycles()

  // Mutations
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

  // Calculate summary statistics
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

  // Handle cell value changes
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

  // Handle save
  const handleSave = async () => {
    if (!selectedVersionId || !statistics.allValid) return

    const dirtyConfigs = localConfigs.filter((c) => c.isDirty)

    if (dirtyConfigs.length === 0) {
      toast.info('No changes to save')
      return
    }

    setIsSaving(true)

    try {
      // Save each dirty config
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
      }

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
    } catch {
      toastMessages.error.custom('Failed to save class size parameters')
    } finally {
      setIsSaving(false)
    }
  }

  // Column definitions
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
            return { backgroundColor: '#FEE2E2' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: '#FEF3C7' }
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
            return { backgroundColor: '#FEE2E2' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: '#FEF3C7' }
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
            return { backgroundColor: '#FEE2E2' }
          }
          if (params.data?.isDirty) {
            return { backgroundColor: '#FEF3C7' }
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
            return { backgroundColor: '#FEF3C7' }
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

  const isLoading = paramsLoading || levelsLoading

  return (
    <PageContainer
      title="Class Size Parameters"
      description="Configure minimum, target, and maximum class sizes for each academic level"
    >
      <div className="space-y-6">
        {/* Version Selection Warning */}
        {!selectedVersionId && (
          <div className="flex items-center gap-2 p-4 bg-subtle border border-border-light rounded-lg">
            <AlertCircle className="h-4 w-4 text-sand-600" />
            <p className="text-sm text-sand-800">
              Please select a budget version to view and edit class size parameters.
            </p>
          </div>
        )}

        {selectedVersionId && (
          <>
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
                onClick={handleSave}
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
                  Some rows have invalid values. Min must be less than Target, and Target must be ≤
                  Max.
                </p>
              </div>
            )}

            {/* Data Grid */}
            <DataTableLazy
              rowData={localConfigs}
              columnDefs={columnDefs}
              loading={isLoading}
              error={paramsError}
              pagination={false}
              onCellValueChanged={onCellValueChanged}
              domLayout="autoHeight"
              defaultColDef={{
                sortable: true,
                resizable: true,
              }}
              getRowId={(params) => params.data.level_id}
            />
          </>
        )}
      </div>
    </PageContainer>
  )
}
