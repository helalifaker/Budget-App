/**
 * Class Structure Page - /enrollment/class-structure
 *
 * Manages number of classes per level with average class sizes.
 * Navigation handled by ModuleLayout (WorkflowTabs + ModuleHeader).
 *
 * Phase 6 Migration: Removed PlanningPageWrapper, uses ModuleLayout
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useEffect, useMemo, useCallback, useState } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { DataTableLazy } from '@/components/DataTableLazy'
import { Button } from '@/components/ui/button'
import { Calculator } from 'lucide-react'
import {
  useClassStructures,
  useUpdateClassStructure,
  useCalculateClassStructure,
} from '@/hooks/api/useClassStructure'
import { useLevels } from '@/hooks/api/useConfiguration'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { ClassStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { HistoricalToggle } from '@/components/planning/HistoricalToggle'
import { createHistoricalColumns } from '@/components/grid/HistoricalColumns'
import { useClassesWithHistory } from '@/hooks/api/useHistorical'

export const Route = createFileRoute('/_authenticated/enrollment/class-structure')({
  beforeLoad: requireAuth,
  component: ClassStructurePage,
})

function ClassStructurePage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<ClassStructure[]>([])
  const [showHistorical, setShowHistorical] = useState(false)

  const {
    data: classStructuresData,
    isLoading: classStructuresLoading,
    error: classStructuresError,
  } = useClassStructures(selectedVersionId)
  const { data: levelsData } = useLevels()
  const { data: budgetVersions } = useBudgetVersions()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useClassesWithHistory(
    selectedVersionId,
    {
      enabled: showHistorical,
    }
  )

  // Get current fiscal year from selected budget version
  const currentFiscalYear = useMemo(() => {
    if (!selectedVersionId || !budgetVersions?.items) return new Date().getFullYear()
    const version = budgetVersions.items.find((v) => v.id === selectedVersionId)
    return version?.fiscal_year ?? new Date().getFullYear()
  }, [selectedVersionId, budgetVersions])

  const updateMutation = useUpdateClassStructure()
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
  const mergedRowData = useMemo(() => {
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

  // Historical columns for class count comparison
  const historicalColumns = useMemo(() => {
    if (!showHistorical) return []
    return createHistoricalColumns({
      historyField: 'history',
      currentFiscalYear,
      isCurrency: false,
      columnWidth: 110,
    })
  }, [showHistorical, currentFiscalYear])

  const columnDefs: ColDef<ClassStructure>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Level',
        flex: 1,
        valueFormatter: (params) => getLevelName(params.value),
      },
      {
        field: 'number_of_classes',
        headerName: 'Number of Classes',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 50,
        },
      },
      {
        field: 'avg_class_size',
        headerName: 'Avg Class Size',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 100,
        },
      },
      {
        headerName: 'Total Students',
        flex: 1,
        valueGetter: (params) => {
          const data = params.data as ClassStructure
          return data.number_of_classes * data.avg_class_size
        },
      },
      // Spread historical columns when enabled
      ...(showHistorical ? historicalColumns : []),
    ],
    [getLevelName, showHistorical, historicalColumns]
  )

  const onCellValueChanged = async (params: CellValueChangedEvent) => {
    const classStructure = params.data
    const field = params.column?.getColId()

    try {
      await updateMutation.mutateAsync({
        id: classStructure.id,
        data: {
          [field]: params.newValue,
        },
      })
    } catch {
      // Error toast is handled by the mutation
      // Revert the change
      params.node.setDataValue(params.column, params.oldValue)
    }
  }

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
        <Button
          data-testid="calculate-button"
          variant="outline"
          onClick={handleCalculateFromEnrollment}
          disabled={!selectedVersionId || calculateMutation.isPending}
        >
          <Calculator className="h-4 w-4 mr-2" />
          Calculate from Enrollment
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <DataTableLazy
          rowData={mergedRowData}
          columnDefs={columnDefs}
          loading={classStructuresLoading || (showHistorical && historicalLoading)}
          error={classStructuresError}
          pagination={true}
          paginationPageSize={50}
          onCellValueChanged={onCellValueChanged}
        />
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view class structure data
        </div>
      )}
    </div>
  )
}
