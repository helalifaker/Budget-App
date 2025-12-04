import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { AlertCircle } from 'lucide-react'
import {
  useSubjectHours,
  useUpdateSubjectHours,
  useLevels,
  useSubjects,
} from '@/hooks/api/useConfiguration'
import { SubjectHours } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/configuration/subject-hours')({
  beforeLoad: requireAuth,
  component: SubjectHoursPage,
})

function SubjectHoursPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')
  const [rowData, setRowData] = useState<SubjectHours[]>([])

  const {
    data: subjectHoursData,
    isLoading: hoursLoading,
    error: hoursError,
  } = useSubjectHours(selectedVersionId)
  const { data: levelsData } = useLevels()
  const { data: subjectsData } = useSubjects()

  const updateMutation = useUpdateSubjectHours()

  useEffect(() => {
    if (subjectHoursData) {
      setRowData(subjectHoursData)
    }
  }, [subjectHoursData])

  const getLevelName = useCallback(
    (levelId: string) => {
      return levelsData?.find((l) => l.id === levelId)?.name || levelId
    },
    [levelsData]
  )

  const getSubjectName = useCallback(
    (subjectId: string) => {
      return subjectsData?.find((s) => s.id === subjectId)?.name || subjectId
    },
    [subjectsData]
  )

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<SubjectHours>) => {
      const updatedRow = event.data
      if (!updatedRow) return

      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      // Skip if value didn't change
      if (newValue === oldValue) return

      // Validate hours_per_week range
      if (field === 'hours_per_week') {
        if (newValue < 0 || newValue > 12) {
          toastMessages.error.validation('Les heures par semaine doivent être entre 0 et 12')
          // Revert the change in the grid
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      // Prepare update data with all required fields
      const updateData = {
        budget_version_id: updatedRow.budget_version_id,
        subject_id: updatedRow.subject_id,
        level_id: updatedRow.level_id,
        hours_per_week: field === 'hours_per_week' ? newValue : updatedRow.hours_per_week,
        is_split: field === 'is_split' ? newValue : updatedRow.is_split,
        notes: field === 'notes' ? newValue : updatedRow.notes,
      }

      try {
        await updateMutation.mutateAsync(updateData)
      } catch {
        // Revert on error (error is already handled by mutation's onError)
        event.node.setDataValue(field, oldValue)
      }
    },
    [updateMutation]
  )

  const columnDefs: ColDef<SubjectHours>[] = useMemo(
    () => [
      {
        field: 'subject_id',
        headerName: 'Matière',
        flex: 2,
        valueFormatter: (params) => getSubjectName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'level_id',
        headerName: 'Niveau',
        flex: 2,
        valueFormatter: (params) => getLevelName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'hours_per_week',
        headerName: 'Heures/Semaine',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 12,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => {
          if (params.value == null) return ''
          return params.value.toFixed(2)
        },
      },
      {
        field: 'is_split',
        headerName: 'Classe divisée?',
        flex: 1,
        editable: true,
        cellEditor: 'agCheckboxCellEditor',
        cellRenderer: 'agCheckboxCellRenderer',
        filter: 'agSetColumnFilter',
        valueFormatter: (params) => (params.value ? 'Oui' : 'Non'),
      },
      {
        field: 'notes',
        headerName: 'Notes',
        flex: 2,
        editable: true,
        filter: 'agTextColumnFilter',
      },
    ],
    [getLevelName, getSubjectName]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Heures par matière"
        description="Configuration du nombre d'heures hebdomadaires par matière et par niveau"
      >
        <div className="space-y-4">
          <BudgetVersionSelector value={selectedVersionId} onChange={setSelectedVersionId} />

          {!selectedVersionId && (
            <div className="flex items-center gap-2 p-4 bg-sand-50 border border-sand-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-sand-600" />
              <p className="text-sm text-sand-800">
                Veuillez sélectionner une version budgétaire pour voir la matrice des heures par
                matière.
              </p>
            </div>
          )}

          {selectedVersionId && (
            <>
              <div className="flex items-center gap-2 p-4 bg-info-50 border border-info-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-info-600" />
                <p className="text-sm text-info-800">
                  Les cellules sont modifiables. Cliquez pour éditer les valeurs. Les changements
                  sont automatiquement sauvegardés. Validation: 0 ≤ Heures ≤ 12.
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={hoursLoading}
                error={hoursError}
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
