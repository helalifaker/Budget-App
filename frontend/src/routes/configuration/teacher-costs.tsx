import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { requireAuth } from '@/lib/auth-guard'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle } from 'lucide-react'
import {
  useTeacherCosts,
  useTeacherCategories,
  useCycles,
  useUpdateTeacherCost,
} from '@/hooks/api/useConfiguration'
import { TeacherCostParam } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/configuration/teacher-costs')({
  beforeLoad: requireAuth,
  component: TeacherCostsPage,
})

function TeacherCostsPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<TeacherCostParam[]>([])

  const { data: teacherCosts, isLoading, error } = useTeacherCosts(selectedVersionId!)
  const { data: categories } = useTeacherCategories()
  const { data: cycles } = useCycles()
  const updateMutation = useUpdateTeacherCost()

  useEffect(() => {
    if (teacherCosts) {
      setRowData(teacherCosts)
    }
  }, [teacherCosts])

  const getCategoryName = useCallback(
    (id: string) => categories?.find((c) => c.id === id)?.name_en || id,
    [categories]
  )

  const getCycleName = useCallback(
    (id: string | null) => {
      if (!id) return 'All cycles'
      return cycles?.find((c) => c.id === id)?.name_en || id
    },
    [cycles]
  )

  const columnDefs: ColDef<TeacherCostParam>[] = useMemo(
    () => [
      {
        field: 'category_id',
        headerName: 'Category',
        valueFormatter: (params) => getCategoryName(params.value),
        flex: 1.5,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'cycle_id',
        headerName: 'Cycle',
        valueFormatter: (params) => getCycleName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'prrd_contribution_eur',
        headerName: 'PRRD (EUR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 100000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'avg_salary_sar',
        headerName: 'Salary (SAR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 1000000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 0 }),
        flex: 1,
      },
      {
        field: 'social_charges_rate',
        headerName: 'Charges (%)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 1, precision: 4 },
        valueFormatter: (params) =>
          params.value == null ? '' : `${(Number(params.value) * 100).toFixed(2)}%`,
        flex: 1,
      },
      {
        field: 'benefits_allowance_sar',
        headerName: 'Allowances (SAR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 200000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 0 }),
        flex: 1,
      },
      {
        field: 'hsa_hourly_rate_sar',
        headerName: 'HSA Rate (SAR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 2000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'max_hsa_hours',
        headerName: 'Max HSA Hours',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 10, precision: 2 },
        flex: 1,
      },
      {
        field: 'notes',
        headerName: 'Notes',
        editable: true,
        flex: 1.2,
      },
    ],
    [getCategoryName, getCycleName]
  )

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<TeacherCostParam>) => {
      const updatedRow = event.data
      if (!updatedRow || !selectedVersionId) return

      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      if (newValue === oldValue) return

      if (field !== 'notes' && (newValue == null || Number(newValue) < 0)) {
        toastMessages.error.validation('La valeur doit être positive')
        event.node.setDataValue(field, oldValue)
        return
      }

      const payload = {
        budget_version_id: updatedRow.budget_version_id,
        category_id: updatedRow.category_id,
        cycle_id: updatedRow.cycle_id,
        prrd_contribution_eur:
          field === 'prrd_contribution_eur' ? Number(newValue) : updatedRow.prrd_contribution_eur,
        avg_salary_sar: field === 'avg_salary_sar' ? Number(newValue) : updatedRow.avg_salary_sar,
        social_charges_rate:
          field === 'social_charges_rate' ? Number(newValue) : updatedRow.social_charges_rate,
        benefits_allowance_sar:
          field === 'benefits_allowance_sar' ? Number(newValue) : updatedRow.benefits_allowance_sar,
        hsa_hourly_rate_sar:
          field === 'hsa_hourly_rate_sar' ? Number(newValue) : updatedRow.hsa_hourly_rate_sar,
        max_hsa_hours: field === 'max_hsa_hours' ? Number(newValue) : updatedRow.max_hsa_hours,
        notes: field === 'notes' ? newValue : updatedRow.notes,
      }

      try {
        await updateMutation.mutateAsync(payload)
      } catch {
        event.node.setDataValue(field, oldValue)
      }
    },
    [selectedVersionId, updateMutation]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Teacher Costs"
        description="Configure teacher salary, charges and overtime assumptions by category"
      >
        <div className="space-y-4">
          {!selectedVersionId && (
            <div className="flex items-center gap-2 p-4 bg-sand-50 border border-sand-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-sand-600" />
              <p className="text-sm text-sand-800">
                Veuillez sélectionner une version budgétaire pour voir les coûts enseignants.
              </p>
            </div>
          )}

          {selectedVersionId && (
            <>
              <div className="flex items-center gap-2 p-4 bg-info-50 border border-info-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-info-600" />
                <p className="text-sm text-info-800">
                  Modifiez directement les cellules pour mettre à jour les paramètres de coûts. Les
                  valeurs doivent être positives. Les montants PRRD sont en EUR, les autres en SAR.
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={isLoading}
                error={error}
                pagination
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
