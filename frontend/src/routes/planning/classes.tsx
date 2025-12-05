import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { Button } from '@/components/ui/button'
import { Calculator } from 'lucide-react'
import {
  useClassStructures,
  useUpdateClassStructure,
  useCalculateClassStructure,
} from '@/hooks/api/useClassStructure'
import { useLevels } from '@/hooks/api/useConfiguration'
import { ClassStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useState } from 'react'

export const Route = createFileRoute('/planning/classes')({
  beforeLoad: requireAuth,
  component: ClassStructurePage,
})

function ClassStructurePage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<ClassStructure[]>([])

  const {
    data: classStructuresData,
    isLoading: classStructuresLoading,
    error: classStructuresError,
  } = useClassStructures(selectedVersionId)
  const { data: levelsData } = useLevels()

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
    ],
    [getLevelName]
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
    <MainLayout>
      <PageContainer
        title="Class Structure"
        description="Define class structure and average class sizes. Use 'Calculate from Enrollment' to auto-generate based on enrollment data."
        actions={
          <Button
            data-testid="calculate-button"
            variant="outline"
            onClick={handleCalculateFromEnrollment}
            disabled={!selectedVersionId || calculateMutation.isPending}
          >
            <Calculator className="h-4 w-4 mr-2" />
            Calculate from Enrollment
          </Button>
        }
      >
        {selectedVersionId ? (
          <DataTableLazy
            rowData={rowData}
            columnDefs={columnDefs}
            loading={classStructuresLoading}
            error={classStructuresError}
            pagination={true}
            paginationPageSize={50}
            onCellValueChanged={onCellValueChanged}
          />
        ) : (
          <div className="text-center py-12 text-twilight-600">
            Please select a budget version to view class structure data
          </div>
        )}
      </PageContainer>
    </MainLayout>
  )
}
