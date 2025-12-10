/**
 * Finance Settings Page - /finance/settings
 *
 * Configure fee structure for revenue planning.
 * Migrated from /configuration/fees
 *
 * Features:
 * - Fee amounts by level, nationality, and category
 * - Trimester-based or annual fees
 * - Inline editing with auto-save
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, DollarSign, Globe, GraduationCap, Settings } from 'lucide-react'
import {
  useFeeStructure,
  useFeeCategories,
  useNationalityTypes,
  useLevels,
  useUpdateFeeStructure,
} from '@/hooks/api/useConfiguration'
import { FeeStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/_authenticated/finance/settings')({
  beforeLoad: requireAuth,
  component: FinanceSettingsPage,
})

function FinanceSettingsPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<FeeStructure[]>([])

  const { data: feeRows, isLoading, error } = useFeeStructure(selectedVersionId!)
  const { data: feeCategories } = useFeeCategories()
  const { data: nationalityTypes } = useNationalityTypes()
  const { data: levels } = useLevels()
  const updateMutation = useUpdateFeeStructure()

  useEffect(() => {
    if (feeRows) {
      setRowData(feeRows)
    }
  }, [feeRows])

  // Calculate statistics
  const statistics = useMemo(() => {
    if (!rowData.length) {
      return {
        totalFeeCategories: 0,
        totalConfigurations: 0,
        averageFee: 0,
        uniqueLevels: 0,
      }
    }

    const feesWithAmount = rowData.filter((r) => r.amount_sar != null && Number(r.amount_sar) > 0)
    const avgFee =
      feesWithAmount.length > 0
        ? feesWithAmount.reduce((sum, r) => sum + Number(r.amount_sar), 0) / feesWithAmount.length
        : 0

    return {
      totalFeeCategories: new Set(rowData.map((r) => r.fee_category_id)).size,
      totalConfigurations: rowData.length,
      averageFee: Math.round(avgFee),
      uniqueLevels: new Set(rowData.map((r) => r.level_id)).size,
    }
  }, [rowData])

  const getFeeCategoryName = useCallback(
    (id: string) =>
      feeCategories?.find((c) => c.id === id)?.name_en ||
      feeCategories?.find((c) => c.id === id)?.name_fr ||
      id,
    [feeCategories]
  )

  const getNationalityName = useCallback(
    (id: string) => nationalityTypes?.find((n) => n.id === id)?.name_en || id,
    [nationalityTypes]
  )

  const getLevelName = useCallback(
    (id: string) => levels?.find((l) => l.id === id)?.name_en || id,
    [levels]
  )

  const columnDefs: ColDef<FeeStructure>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Level',
        valueFormatter: (params) => getLevelName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'nationality_type_id',
        headerName: 'Nationality',
        valueFormatter: (params) => getNationalityName(params.value),
        flex: 1.1,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'fee_category_id',
        headerName: 'Category',
        valueFormatter: (params) => getFeeCategoryName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'trimester',
        headerName: 'Trimester',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 1, max: 3, precision: 0 },
        valueFormatter: (params) => params.value ?? 'Annual',
        flex: 0.8,
      },
      {
        field: 'amount_sar',
        headerName: 'Amount (SAR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 500000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('en-US', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'notes',
        headerName: 'Notes',
        editable: true,
        flex: 1.2,
      },
    ],
    [getFeeCategoryName, getNationalityName, getLevelName]
  )

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<FeeStructure>) => {
      const updatedRow = event.data
      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      if (!updatedRow || newValue === oldValue) return

      if (field === 'amount_sar' && (newValue == null || Number(newValue) < 0)) {
        toastMessages.error.validation('Amount must be positive')
        event.node.setDataValue(field, oldValue)
        return
      }

      if (field === 'trimester' && newValue != null) {
        const parsed = Number(newValue)
        if (parsed < 1 || parsed > 3) {
          toastMessages.error.validation('Trimester must be 1, 2, or 3 (or empty for annual)')
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      const payload = {
        budget_version_id: updatedRow.budget_version_id,
        level_id: updatedRow.level_id,
        nationality_type_id: updatedRow.nationality_type_id,
        fee_category_id: updatedRow.fee_category_id,
        amount_sar: field === 'amount_sar' ? Number(newValue) : updatedRow.amount_sar,
        trimester:
          field === 'trimester'
            ? newValue == null
              ? null
              : Number(newValue)
            : updatedRow.trimester,
        notes: field === 'notes' ? newValue : updatedRow.notes,
      }

      try {
        await updateMutation.mutateAsync(payload)
      } catch {
        event.node.setDataValue(field, oldValue)
      }
    },
    [updateMutation]
  )

  return (
    <PageContainer
      title="Finance Settings"
      description="Configure tuition and fee amounts by level, nationality, and category"
    >
      <div className="space-y-6">
        {!selectedVersionId && (
          <div className="flex items-center gap-2 p-4 bg-subtle border border-border-light rounded-lg">
            <AlertCircle className="h-4 w-4 text-sand-600" />
            <p className="text-sm text-sand-800">
              Please select a budget version to view the fee structure.
            </p>
          </div>
        )}

        {selectedVersionId && (
          <>
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Fee Categories
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{statistics.totalFeeCategories}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <GraduationCap className="h-4 w-4" />
                    Levels Configured
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{statistics.uniqueLevels}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Total Configurations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{statistics.totalConfigurations}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Average Fee (SAR)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {statistics.averageFee.toLocaleString('en-US')}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Info Banner */}
            <Card className="bg-info-50 border-info-200">
              <CardContent className="py-3">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-info-600" />
                  <p className="text-sm text-info-800">
                    Amounts are in SAR. Leave trimester empty for annual fees, or enter 1-3 for
                    trimester-based tuition.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Data Grid */}
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
  )
}
