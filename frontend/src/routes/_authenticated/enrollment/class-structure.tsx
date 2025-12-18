/**
 * Class Structure Page - /students/class-structure
 *
 * Manages number of classes per level with average class sizes.
 * Navigation handled by ModuleLayout (WorkflowTabs + ModuleHeader).
 *
 * Phase 6 Migration: Migrated from AG Grid to TanStack Table
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useEffect, useMemo, useCallback, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { ExcelEditableTableLazy } from '@/components/grid/tanstack/ExcelEditableTableLazy'
import type { CellValueChangedEvent } from '@/components/grid/tanstack/EditableTable'
import { Button } from '@/components/ui/button'
import { Calculator } from 'lucide-react'
import {
  useClassStructures,
  useUpdateClassStructure,
  useCalculateClassStructure,
  useBulkUpdateClassStructure,
} from '@/hooks/api/useClassStructure'
import { useEnrollmentSummary } from '@/hooks/api/useEnrollment'
import { useLevels } from '@/hooks/api/useConfiguration'
import { useVersions } from '@/hooks/api/useVersions'
import { ClassStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useVersion } from '@/contexts/VersionContext'
import { HistoricalToggle } from '@/components/planning/HistoricalToggle'
import { createHistoricalColumnsTanStack } from '@/components/grid/tanstack/HistoricalColumnsTanStack'
import { useClassesWithHistory } from '@/hooks/api/useHistorical'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'
import type { HistoricalComparison } from '@/types/historical'

export const Route = createFileRoute('/_authenticated/enrollment/class-structure')({
  beforeLoad: requireAuth,
  component: ClassStructurePage,
})

/**
 * Extended type for rows with historical data
 */
interface ClassStructureWithHistory extends ClassStructure {
  history?: HistoricalComparison | null
}

function ClassStructurePage() {
  const { selectedVersionId } = useVersion()
  const [rowData, setRowData] = useState<ClassStructure[]>([])
  const [showHistorical, setShowHistorical] = useState(false)

  const {
    data: classStructuresData,
    isLoading: classStructuresLoading,
    error: classStructuresError,
  } = useClassStructures(selectedVersionId)
  const { data: levelsData } = useLevels()
  const { data: budgetVersions } = useVersions()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useClassesWithHistory(
    selectedVersionId,
    {
      enabled: showHistorical,
    }
  )

  // Check if enrollment data exists for the selected version
  const { data: enrollmentSummary, isLoading: enrollmentSummaryLoading } =
    useEnrollmentSummary(selectedVersionId)

  // Derived state: does enrollment data exist?
  const hasEnrollmentData = (enrollmentSummary?.total_students ?? 0) > 0

  // Get current fiscal year from selected budget version
  const currentFiscalYear = useMemo(() => {
    if (!selectedVersionId || !budgetVersions?.items) return new Date().getFullYear()
    const version = budgetVersions.items.find((v) => v.id === selectedVersionId)
    return version?.fiscal_year ?? new Date().getFullYear()
  }, [selectedVersionId, budgetVersions])

  const updateMutation = useUpdateClassStructure()
  const bulkUpdateMutation = useBulkUpdateClassStructure()
  const calculateMutation = useCalculateClassStructure()

  useEffect(() => {
    // API returns array directly
    if (classStructuresData) {
      setRowData(classStructuresData)
    }
  }, [classStructuresData])

  const handleCalculateFromEnrollment = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await calculateMutation.mutateAsync({
        versionId: selectedVersionId,
        data: {},
      })
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const getLevelName = useCallback(
    (levelId: string) => {
      return levelsData?.find((l) => l.id === levelId)?.name_en || levelId
    },
    [levelsData]
  )

  // Merge row data with historical data when available
  const mergedRowData = useMemo((): ClassStructureWithHistory[] => {
    if (!showHistorical || !historicalData?.rows) {
      return rowData
    }
    // Merge historical data into row data by level_id
    return rowData.map((row) => {
      const histRow = historicalData.rows.find((h) => h.level_id === row.level_id)
      return {
        ...row,
        history: histRow?.history ?? null,
      }
    })
  }, [rowData, showHistorical, historicalData])

  // Historical columns for class count comparison (TanStack format)
  const historicalColumns = useMemo(() => {
    if (!showHistorical) return []
    return createHistoricalColumnsTanStack<ClassStructureWithHistory>({
      historyField: 'history',
      currentFiscalYear,
      isCurrency: false,
      columnWidth: 110,
    })
  }, [showHistorical, currentFiscalYear])

  // TanStack Table column definitions
  const columnDefs: ColumnDef<ClassStructureWithHistory, unknown>[] = useMemo(
    () => [
      {
        id: 'level_id',
        accessorKey: 'level_id',
        header: 'Level',
        size: 150,
        meta: {
          editable: false,
        },
        cell: (info) => getLevelName(info.getValue() as string),
      },
      {
        id: 'number_of_classes',
        accessorKey: 'number_of_classes',
        header: 'Number of Classes',
        size: 150,
        meta: {
          editable: true,
          editorType: 'number' as const,
          min: 0,
          max: 50,
          precision: 0,
        },
      },
      {
        id: 'avg_class_size',
        accessorKey: 'avg_class_size',
        header: 'Avg Class Size',
        size: 150,
        meta: {
          editable: true,
          editorType: 'number' as const,
          min: 1,
          max: 100,
          precision: 0,
        },
      },
      {
        id: 'total_students',
        header: 'Total Students',
        size: 150,
        meta: {
          editable: false,
        },
        accessorFn: (row) => row.number_of_classes * row.avg_class_size,
        cell: (info) => {
          const value = info.getValue() as number
          return <span className="font-medium">{value.toLocaleString()}</span>
        },
      },
      // Spread historical columns when enabled
      ...historicalColumns,
    ],
    [getLevelName, historicalColumns]
  )

  /**
   * Handle cell value changes
   * Updates backend and handles revert on error
   */
  const onCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<ClassStructureWithHistory>) => {
      const { data, field, newValue, revertValue } = event

      try {
        await updateMutation.mutateAsync({
          id: data.id,
          data: {
            [field]: newValue,
          },
        })
      } catch {
        // Error toast is handled by the mutation
        // Revert the change
        revertValue()
      }
    },
    [updateMutation]
  )

  /**
   * Handle cell clear (Delete key)
   * Resets cleared cells to 0
   */
  const handleCellsCleared = useCallback(
    async (cells: Array<{ rowId: string; field: string; oldValue: unknown }>) => {
      if (!selectedVersionId || cells.length === 0) return

      // Group updates by rowId to merge multiple field clears for same row
      const updatesMap = new Map<string, Record<string, unknown>>()

      for (const cell of cells) {
        if (!updatesMap.has(cell.rowId)) {
          updatesMap.set(cell.rowId, { id: cell.rowId })
        }
        const update = updatesMap.get(cell.rowId)!
        // Reset to 0 for numeric fields
        // Note: We assume all editable fields here are numeric based on columnDefs
        update[cell.field] = 0
      }

      const updates = Array.from(updatesMap.values()) as Array<
        { id: string } & Record<string, unknown>
      >

      try {
        await bulkUpdateMutation.mutateAsync({
          versionId: selectedVersionId,
          updates,
        })
      } catch {
        // Error toast handled by mutation
      }
    },
    [bulkUpdateMutation, selectedVersionId]
  )

  return (
    <div className="p-6 space-y-4">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <HistoricalToggle
          showHistorical={showHistorical}
          onToggle={setShowHistorical}
          disabled={!selectedVersionId}
          isLoading={historicalLoading}
          currentFiscalYear={currentFiscalYear}
        />
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={!hasEnrollmentData && selectedVersionId ? 0 : undefined}>
                <Button
                  data-testid="calculate-button"
                  variant="outline"
                  onClick={handleCalculateFromEnrollment}
                  disabled={
                    !selectedVersionId ||
                    calculateMutation.isPending ||
                    !hasEnrollmentData ||
                    enrollmentSummaryLoading
                  }
                >
                  <Calculator className="h-4 w-4 mr-2" />
                  Calculate from Enrollment
                </Button>
              </span>
            </TooltipTrigger>
            {!hasEnrollmentData && selectedVersionId && !enrollmentSummaryLoading && (
              <TooltipContent>
                <p>Veuillez d'abord saisir les effectifs dans la page Planification</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <ExcelEditableTableLazy<ClassStructureWithHistory>
          rowData={mergedRowData}
          columnDefs={columnDefs}
          getRowId={(row) => row.id}
          loading={classStructuresLoading || (showHistorical && historicalLoading)}
          error={classStructuresError}
          onCellValueChanged={onCellValueChanged}
          onCellsCleared={handleCellsCleared}
          tableLabel="Class Structure Grid"
          showSelectionStats={true}
          enableRowSelection={true}
          showCheckboxColumn={true}
        />
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view class structure data
        </div>
      )}
    </div>
  )
}
