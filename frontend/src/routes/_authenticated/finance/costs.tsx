/**
 * Cost Planning Page - /finance/costs
 *
 * Manages personnel and operating costs planning.
 * Navigation (SmartHeader + ModuleDock) provided by _authenticated.tsx layout.
 *
 * Migrated from /planning/costs
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, themeQuartz } from 'ag-grid-community'
import { PlanningPageWrapper } from '@/components/planning/PlanningPageWrapper'
import { SummaryCard } from '@/components/SummaryCard'
import { CostChart } from '@/components/charts/CostChart'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AccountCodeRenderer } from '@/components/grid/AccountCodeRenderer'
import { CurrencyRenderer } from '@/components/grid/CurrencyRenderer'
import {
  usePersonnelCosts,
  useOperatingCosts,
  useCalculatePersonnelCosts,
} from '@/hooks/api/useCosts'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { DollarSign, Users, ShoppingCart, Calculator, Download, Plus } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useCostsWithHistory } from '@/hooks/api/useHistorical'

export const Route = createFileRoute('/_authenticated/finance/costs')({
  component: CostsPage,
})

function CostsPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [activeTab, setActiveTab] = useState<'personnel' | 'operating'>('personnel')
  const [showHistorical, setShowHistorical] = useState(false)

  const { data: personnelCosts, isLoading: loadingPersonnel } = usePersonnelCosts(
    selectedVersionId!
  )
  const { data: operatingCosts, isLoading: loadingOperating } = useOperatingCosts(
    selectedVersionId!
  )
  const { data: budgetVersions } = useBudgetVersions()
  const calculatePersonnel = useCalculatePersonnelCosts()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useCostsWithHistory(
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

  const handleCalculatePersonnel = () => {
    if (selectedVersionId) {
      calculatePersonnel.mutate({ versionId: selectedVersionId })
    }
  }

  // Calculate summary metrics - API returns arrays directly
  const personnelItems = personnelCosts || []
  const operatingItems = operatingCosts || []

  const totalPersonnel = personnelItems.reduce(
    (sum: number, item: { total_cost_sar?: number }) => sum + (item.total_cost_sar || 0),
    0
  )
  const totalOperating = operatingItems.reduce(
    (sum: number, item: { amount_sar?: number }) => sum + (item.amount_sar || 0),
    0
  )
  const totalCosts = totalPersonnel + totalOperating

  // Note: period amounts may not exist in current API - using annual amounts split
  const personnelP1 = totalPersonnel * 0.5 // Jan-Jun estimate
  const personnelSummer = totalPersonnel * 0.17 // Jul-Aug estimate
  const personnelP2 = totalPersonnel * 0.33 // Sep-Dec estimate

  const operatingP1 = totalOperating * 0.5
  const operatingSummer = totalOperating * 0.17
  const operatingP2 = totalOperating * 0.33

  // Chart data
  const chartData = [
    { period: 'P1 (Jan-Jun)', personnel: personnelP1, operating: operatingP1 },
    { period: 'Summer', personnel: personnelSummer, operating: operatingSummer },
    { period: 'P2 (Sep-Dec)', personnel: personnelP2, operating: operatingP2 },
  ]

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <PlanningPageWrapper
      stepId="costs"
      actions={
        <>
          <HistoricalToggle
            showHistorical={showHistorical}
            onToggle={setShowHistorical}
            disabled={!selectedVersionId}
            isLoading={historicalLoading}
            currentFiscalYear={currentFiscalYear}
          />
          <Button
            data-testid="calculate-button"
            onClick={handleCalculatePersonnel}
            disabled={!selectedVersionId || calculatePersonnel.isPending}
          >
            <Calculator className="w-4 h-4 mr-2" />
            Recalculate Personnel Costs
          </Button>
          <Button data-testid="export-button" variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </>
      }
    >
      <div className="p-6 space-y-6">
        {selectedVersionId ? (
          <>
            {/* Historical Summary for Costs */}
            {showHistorical && historicalData?.totals && (
              <div className="flex gap-4 mb-4">
                <HistoricalSummary
                  currentValue={totalCosts}
                  priorYearValue={historicalData.totals.n_minus_1?.value ?? null}
                  changePercent={historicalData.totals.vs_n_minus_1_pct ?? null}
                  label="Total Costs vs Prior Year"
                  isCurrency={true}
                />
                {historicalData.personnel_totals && (
                  <HistoricalSummary
                    currentValue={totalPersonnel}
                    priorYearValue={historicalData.personnel_totals.n_minus_1?.value ?? null}
                    changePercent={historicalData.personnel_totals.vs_n_minus_1_pct ?? null}
                    label="Personnel vs Prior Year"
                    isCurrency={true}
                  />
                )}
                {historicalData.operating_totals && (
                  <HistoricalSummary
                    currentValue={totalOperating}
                    priorYearValue={historicalData.operating_totals.n_minus_1?.value ?? null}
                    changePercent={historicalData.operating_totals.vs_n_minus_1_pct ?? null}
                    label="Operating vs Prior Year"
                    isCurrency={true}
                  />
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <SummaryCard
                title="Total Costs"
                value={formatCurrency(totalCosts)}
                subtitle="Annual total"
                icon={<DollarSign className="w-5 h-5" />}
                valueClassName="text-red-600"
              />
              <SummaryCard
                title="Personnel Costs"
                value={formatCurrency(totalPersonnel)}
                subtitle={`${((totalPersonnel / totalCosts) * 100).toFixed(1)}% of total`}
                icon={<Users className="w-5 h-5" />}
              />
              <SummaryCard
                title="Operating Costs"
                value={formatCurrency(totalOperating)}
                subtitle={`${((totalOperating / totalCosts) * 100).toFixed(1)}% of total`}
                icon={<ShoppingCart className="w-5 h-5" />}
              />
              <SummaryCard
                title="Personnel %"
                value={`${((totalPersonnel / totalCosts) * 100).toFixed(1)}%`}
                subtitle="Typical: 60-70%"
                icon={<Users className="w-5 h-5" />}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger data-testid="personnel-tab" value="personnel">
                      Personnel Costs
                    </TabsTrigger>
                    <TabsTrigger data-testid="operating-tab" value="operating">
                      Operating Costs
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="personnel" className="mt-6">
                    <PersonnelCostsTab data={personnelItems} isLoading={loadingPersonnel} />
                  </TabsContent>

                  <TabsContent value="operating" className="mt-6">
                    <OperatingCostsTab data={operatingItems} isLoading={loadingOperating} />
                  </TabsContent>
                </Tabs>
              </div>

              <div>
                <CostChart data={chartData} title="Cost Breakdown by Period" />

                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle>Cost Planning Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 text-sm">
                      <div>
                        <h4 className="font-medium mb-1">Personnel Costs (641xx, 645xx)</h4>
                        <p className="text-gray-600">
                          Auto-calculated from DHG FTE. Includes teacher salaries, social charges
                          (42%), and benefits.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">AEFE Contributions</h4>
                        <p className="text-gray-600">
                          PRRD: ~41,863 EUR per teacher. Converted to SAR at current rate.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Operating Costs (606xx-625xx)</h4>
                        <p className="text-gray-600">
                          Supplies, utilities, maintenance, insurance, and other operating expenses.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Period Allocation</h4>
                        <p className="text-gray-600">
                          P1 (Jan-Jun), Summer (Jul-Aug), P2 (Sep-Dec). Summer costs typically
                          lower.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-text-secondary">
            Please select a budget version to view cost planning
          </div>
        )}
      </div>
    </PlanningPageWrapper>
  )
}

// Matches PersonnelCostPlan from backend API
interface PersonnelCostItem {
  id: string
  budget_version_id: string
  account_code: string
  description: string
  fte_count: number
  unit_cost_sar: number
  total_cost_sar: number
  category_id: string
  cycle_id?: string | null
  is_calculated: boolean
  calculation_driver?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

// Matches OperatingCostPlan from backend API
interface OperatingCostItem {
  id: string
  budget_version_id: string
  account_code: string
  description: string
  category: string
  amount_sar: number
  is_calculated: boolean
  calculation_driver?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

function PersonnelCostsTab({ data, isLoading }: { data: PersonnelCostItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    {
      headerName: 'Account Code',
      field: 'account_code',
      width: 150,
      pinned: 'left',
      cellRenderer: AccountCodeRenderer,
    },
    {
      headerName: 'Description',
      field: 'description',
      width: 250,
    },
    {
      headerName: 'Category',
      field: 'category_id',
      width: 150,
    },
    {
      headerName: 'FTE Count',
      field: 'fte_count',
      width: 120,
      editable: (params) => !params.data.is_calculated,
      cellDataType: 'number',
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
      cellStyle: (params) =>
        params.data.is_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'Unit Cost (SAR)',
      field: 'unit_cost_sar',
      width: 150,
      editable: (params) => !params.data.is_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'Total Cost (SAR)',
      field: 'total_cost_sar',
      width: 160,
      cellRenderer: CurrencyRenderer,
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'Auto',
      field: 'is_calculated',
      width: 80,
      cellRenderer: (params: { value: boolean }) => (params.value ? '✓' : '✗'),
    },
    {
      headerName: 'Driver',
      field: 'calculation_driver',
      width: 150,
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 200,
      editable: true,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Personnel Costs</CardTitle>
        <p className="text-sm text-gray-600">
          Gray cells are auto-calculated from DHG. Manual adjustments allowed with notes.
        </p>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
          />
        </div>
      </CardContent>
    </Card>
  )
}

function OperatingCostsTab({ data, isLoading }: { data: OperatingCostItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    {
      headerName: 'Account Code',
      field: 'account_code',
      width: 150,
      pinned: 'left',
      cellRenderer: AccountCodeRenderer,
    },
    {
      headerName: 'Description',
      field: 'description',
      width: 250,
      editable: true,
    },
    {
      headerName: 'Category',
      field: 'category',
      width: 150,
    },
    {
      headerName: 'Amount (SAR)',
      field: 'amount_sar',
      width: 160,
      editable: (params) => !params.data.is_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'Auto',
      field: 'is_calculated',
      width: 80,
      cellRenderer: (params: { value: boolean }) => (params.value ? '✓' : '✗'),
    },
    {
      headerName: 'Driver',
      field: 'calculation_driver',
      width: 150,
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 200,
      editable: true,
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Operating Costs</CardTitle>
          <p className="text-sm text-gray-600">
            Add, edit, or delete operating expense line items.
          </p>
        </div>
        <Button size="sm">
          <Plus className="w-4 h-4 mr-2" />
          Add Line Item
        </Button>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
          />
        </div>
      </CardContent>
    </Card>
  )
}
