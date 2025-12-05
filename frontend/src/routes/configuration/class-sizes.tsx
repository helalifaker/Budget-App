import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle } from 'lucide-react'
import {
  useClassSizeParams,
  useUpdateClassSizeParam,
  useLevels,
  useCycles,
} from '@/hooks/api/useConfiguration'
import { ClassSizeParam } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/configuration/class-sizes')({
  beforeLoad: requireAuth,
  component: ClassSizesPage,
})

function ClassSizesPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<ClassSizeParam[]>([])

  const {
    data: classSizeParamsData,
    isLoading: paramsLoading,
    error: paramsError,
  } = useClassSizeParams(selectedVersionId)
  const { data: levelsData } = useLevels()
  const { data: cyclesData } = useCycles()

  const updateMutation = useUpdateClassSizeParam()

  useEffect(() => {
    if (classSizeParamsData) {
      setRowData(classSizeParamsData)
    }
  }, [classSizeParamsData])

  const getLevelName = useCallback(
    (levelId: string | null) => {
      if (!levelId) return 'Cycle default'
      return levelsData?.find((l) => l.id === levelId)?.name_en || levelId
    },
    [levelsData]
  )

  const getCycleName = useCallback(
    (cycleId: string | null) => {
      if (!cycleId) return 'Level-specific'
      return cyclesData?.find((c) => c.id === cycleId)?.name_en || cycleId
    },
    [cyclesData]
  )

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<ClassSizeParam>) => {
      const updatedRow = event.data
      if (!updatedRow) return

      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      // Skip if value didn't change
      if (newValue === oldValue) return

      // Validate the field
      if (
        field === 'min_class_size' ||
        field === 'target_class_size' ||
        field === 'max_class_size'
      ) {
        const minSize = field === 'min_class_size' ? newValue : updatedRow.min_class_size
        const targetSize = field === 'target_class_size' ? newValue : updatedRow.target_class_size
        const maxSize = field === 'max_class_size' ? newValue : updatedRow.max_class_size

        // Validate business rules: min < target ≤ max
        if (targetSize <= minSize) {
          toastMessages.error.validation(
            'La taille cible doit être supérieure à la taille minimale'
          )
          // Revert the change in the grid
          event.node.setDataValue(field, oldValue)
          return
        }

        if (maxSize < targetSize) {
          toastMessages.error.validation(
            'La taille maximale doit être supérieure ou égale à la taille cible'
          )
          // Revert the change in the grid
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      // Optimistically update the UI
      const updatedData = {
        [field]: newValue,
      }

      try {
        await updateMutation.mutateAsync({
          id: updatedRow.id,
          data: updatedData,
        })
      } catch {
        // Revert on error (error is already handled by mutation's onError)
        event.node.setDataValue(field, oldValue)
      }
    },
    [updateMutation]
  )

  const columnDefs: ColDef<ClassSizeParam>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Level',
        flex: 2,
        valueFormatter: (params) => getLevelName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'cycle_id',
        headerName: 'Cycle',
        flex: 2,
        valueFormatter: (params) => getCycleName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'min_class_size',
        headerName: 'Min Size',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        filter: 'agNumberColumnFilter',
      },
      {
        field: 'target_class_size',
        headerName: 'Target Size',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        filter: 'agNumberColumnFilter',
      },
      {
        field: 'max_class_size',
        headerName: 'Max Size',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 1,
          max: 50,
          precision: 0,
        },
        filter: 'agNumberColumnFilter',
      },
      {
        field: 'notes',
        headerName: 'Notes',
        flex: 2,
        editable: true,
        filter: 'agTextColumnFilter',
      },
    ],
    [getLevelName, getCycleName]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Class Size Parameters"
        description="Configure minimum, target, and maximum class sizes for each academic level"
      >
        <div className="space-y-4">
          {!selectedVersionId && (
            <div className="flex items-center gap-2 p-4 bg-sand-50 border border-sand-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-sand-600" />
              <p className="text-sm text-sand-800">
                Veuillez sélectionner une version budgétaire pour voir les paramètres de taille de
                classe.
              </p>
            </div>
          )}

          {selectedVersionId && (
            <>
              <div className="flex items-center gap-2 p-4 bg-info-50 border border-info-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-info-600" />
                <p className="text-sm text-info-800">
                  Les cellules sont modifiables. Cliquez pour éditer les valeurs. Les changements
                  sont automatiquement sauvegardés. Validation: Min &lt; Target ≤ Max.
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={paramsLoading}
                error={paramsError}
                pagination={true}
                paginationPageSize={50}
                onCellValueChanged={handleCellValueChanged}
                defaultColDef={{
                  sortable: true,
                  filter: true,
                  resizable: true,
                }}
              />
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
