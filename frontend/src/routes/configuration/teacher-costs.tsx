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
  useTeacherCosts,
  useUpdateTeacherCost,
  useTeacherCategories,
  useCycles,
} from '@/hooks/api/useConfiguration'
import { TeacherCostParam } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/configuration/teacher-costs')({
  beforeLoad: requireAuth,
  component: TeacherCostsPage,
})

function TeacherCostsPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')
  const [rowData, setRowData] = useState<TeacherCostParam[]>([])

  const {
    data: teacherCostsData,
    isLoading: costsLoading,
    error: costsError,
  } = useTeacherCosts(selectedVersionId)
  const { data: categoriesData } = useTeacherCategories()
  const { data: cyclesData } = useCycles()

  const updateMutation = useUpdateTeacherCost()

  useEffect(() => {
    if (teacherCostsData) {
      setRowData(teacherCostsData)
    }
  }, [teacherCostsData])

  const getCategoryName = useCallback(
    (categoryId: string) => {
      return categoriesData?.find((c) => c.id === categoryId)?.name_fr || categoryId
    },
    [categoriesData]
  )

  const getCycleName = useCallback(
    (cycleId: string | null) => {
      if (!cycleId) return 'Tous'
      return cyclesData?.find((c) => c.id === cycleId)?.name || cycleId
    },
    [cyclesData]
  )

  const formatCurrency = useCallback((value: number | null | undefined): string => {
    if (value == null) return ''
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }, [])

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<TeacherCostParam>) => {
      const updatedRow = event.data
      if (!updatedRow) return

      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      // Skip if value didn't change
      if (newValue === oldValue) return

      // Validation rules
      if (field === 'social_charges_rate') {
        const rate = newValue / 100 // Convert from percentage display to decimal
        if (rate < 0 || rate > 1) {
          toastMessages.error.validation('Le taux de charges sociales doit être entre 0% et 100%')
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      if (field === 'max_hsa_hours') {
        if (newValue < 0 || newValue > 10) {
          toastMessages.error.validation('Les heures HSA maximum doivent être entre 0 et 10')
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      if (
        field === 'prrd_contribution_eur' ||
        field === 'avg_salary_sar' ||
        field === 'benefits_allowance_sar' ||
        field === 'hsa_hourly_rate_sar'
      ) {
        if (newValue != null && newValue < 0) {
          toastMessages.error.validation('Les montants ne peuvent pas être négatifs')
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      // Prepare update data with all required fields
      const updateData = {
        budget_version_id: updatedRow.budget_version_id,
        category_id: updatedRow.category_id,
        cycle_id: updatedRow.cycle_id,
        prrd_contribution_eur:
          field === 'prrd_contribution_eur' ? newValue : updatedRow.prrd_contribution_eur,
        avg_salary_sar: field === 'avg_salary_sar' ? newValue : updatedRow.avg_salary_sar,
        social_charges_rate:
          field === 'social_charges_rate' ? newValue / 100 : updatedRow.social_charges_rate,
        benefits_allowance_sar:
          field === 'benefits_allowance_sar' ? newValue : updatedRow.benefits_allowance_sar,
        hsa_hourly_rate_sar:
          field === 'hsa_hourly_rate_sar' ? newValue : updatedRow.hsa_hourly_rate_sar,
        max_hsa_hours: field === 'max_hsa_hours' ? newValue : updatedRow.max_hsa_hours,
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

  const columnDefs: ColDef<TeacherCostParam>[] = useMemo(
    () => [
      {
        field: 'category_id',
        headerName: 'Catégorie',
        flex: 2,
        valueFormatter: (params) => getCategoryName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'cycle_id',
        headerName: 'Cycle',
        flex: 1.5,
        valueFormatter: (params) => getCycleName(params.value),
        filter: 'agTextColumnFilter',
      },
      {
        field: 'prrd_contribution_eur',
        headerName: 'PRRD (EUR)',
        flex: 1.5,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => formatCurrency(params.value),
      },
      {
        field: 'avg_salary_sar',
        headerName: 'Salaire Moyen (SAR)',
        flex: 2,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => formatCurrency(params.value),
      },
      {
        field: 'social_charges_rate',
        headerName: 'Charges Sociales (%)',
        flex: 1.8,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 100,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueGetter: (params) => {
          if (params.data?.social_charges_rate == null) return null
          return params.data.social_charges_rate * 100
        },
        valueSetter: (params) => {
          if (params.data) {
            params.data.social_charges_rate = params.newValue / 100
          }
          return true
        },
        valueFormatter: (params) => {
          if (params.value == null) return ''
          return `${params.value.toFixed(2)}%`
        },
      },
      {
        field: 'benefits_allowance_sar',
        headerName: 'Indemnités (SAR)',
        flex: 1.8,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => formatCurrency(params.value),
      },
      {
        field: 'hsa_hourly_rate_sar',
        headerName: 'Taux Horaire HSA (SAR)',
        flex: 2.2,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => formatCurrency(params.value),
      },
      {
        field: 'max_hsa_hours',
        headerName: 'HSA Max (heures)',
        flex: 1.8,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 10,
          precision: 1,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => {
          if (params.value == null) return ''
          return params.value.toFixed(1)
        },
      },
      {
        field: 'notes',
        headerName: 'Notes',
        flex: 2,
        editable: true,
        filter: 'agTextColumnFilter',
      },
    ],
    [getCategoryName, getCycleName, formatCurrency]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Coûts des Enseignants"
        description="Configuration des coûts par catégorie d'enseignants (AEFE/Local)"
      >
        <div className="space-y-4">
          <BudgetVersionSelector value={selectedVersionId} onChange={setSelectedVersionId} />

          {!selectedVersionId && (
            <div className="flex items-center gap-2 p-4 bg-sand-50 border border-sand-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-sand-600" />
              <p className="text-sm text-sand-800">
                Veuillez sélectionner une version budgétaire pour voir les paramètres de coûts des
                enseignants.
              </p>
            </div>
          )}

          {selectedVersionId && (
            <>
              <div className="flex items-center gap-2 p-4 bg-info-50 border border-info-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-info-600" />
                <p className="text-sm text-info-800">
                  Les cellules sont modifiables. Cliquez pour éditer les valeurs. Les changements
                  sont automatiquement sauvegardés. Les charges sociales sont affichées en
                  pourcentage (ex: 21% = 0.21).
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={costsLoading}
                error={costsError}
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
