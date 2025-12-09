/**
 * CapEx Planning Page - /finance/capex
 *
 * Manages capital expenditure and depreciation.
 * Navigation (SmartHeader + ModuleDock) provided by _authenticated.tsx layout.
 *
 * Migrated from /planning/capex
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ICellRendererParams, themeQuartz } from 'ag-grid-community'
import { PlanningPageWrapper } from '@/components/planning/PlanningPageWrapper'
import { SummaryCard } from '@/components/SummaryCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { CurrencyRenderer } from '@/components/grid/CurrencyRenderer'
import { AccountCodeRenderer } from '@/components/grid/AccountCodeRenderer'
import { useCapEx, useDepreciationSchedule } from '@/hooks/api/useCapEx'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { Building2, Laptop, Wrench, TrendingDown, Plus, Download, Eye } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useCapExWithHistory } from '@/hooks/api/useHistorical'

export const Route = createFileRoute('/_authenticated/finance/capex')({
  component: CapExPage,
})

function CapExPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const [showDepreciation, setShowDepreciation] = useState(false)
  const [showHistorical, setShowHistorical] = useState(false)

  const { data: capexData, isLoading } = useCapEx(selectedVersionId!)
  const { data: depreciationSchedule } = useDepreciationSchedule(selectedItemId!)
  const { data: budgetVersions } = useBudgetVersions()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useCapExWithHistory(
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

  // API returns array directly
  const capexItems = capexData || []

  // Define typed interface for capex items to fix type errors
  interface CapExItem {
    id: string
    description: string
    category: string
    account_code: string
    acquisition_date: string
    total_cost_sar: number
    useful_life_years: number
    annual_depreciation_sar: number
    notes?: string | null
  }

  // Calculate summary metrics
  const totalCapEx = capexItems.reduce(
    (sum: number, item: CapExItem) => sum + item.total_cost_sar,
    0
  )
  const equipmentCost = capexItems
    .filter((item: CapExItem) => item.category === 'EQUIPMENT')
    .reduce((sum: number, item: CapExItem) => sum + item.total_cost_sar, 0)
  const itCost = capexItems
    .filter((item: CapExItem) => item.category === 'IT')
    .reduce((sum: number, item: CapExItem) => sum + item.total_cost_sar, 0)

  const avgUsefulLife =
    capexItems.length > 0
      ? capexItems.reduce((sum: number, item: CapExItem) => sum + item.useful_life_years, 0) /
        capexItems.length
      : 0

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const assetTypeColors: Record<string, string> = {
    EQUIPMENT: 'info',
    IT: 'success',
    FURNITURE: 'warning',
    BUILDING_IMPROVEMENTS: 'default',
    SOFTWARE: 'info',
  }

  const AssetTypeBadge = ({ value }: { value: string }) => {
    const variant = assetTypeColors[value] as 'info' | 'success' | 'warning' | 'default'
    const label = value.replace(/_/g, ' ')
    return <Badge variant={variant}>{label}</Badge>
  }

  const ActionsCellRenderer = (params: ICellRendererParams) => {
    return (
      <div className="flex gap-2 h-full items-center">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setSelectedItemId(params.data.id)
            setShowDepreciation(true)
          }}
        >
          <Eye className="w-4 h-4" />
        </Button>
      </div>
    )
  }

  const columnDefs: ColDef[] = [
    {
      headerName: 'Description',
      field: 'description',
      width: 300,
      pinned: 'left',
      editable: true,
    },
    {
      headerName: 'Asset Type',
      field: 'category',
      width: 180,
      cellRenderer: (params: { value: string }) => <AssetTypeBadge value={params.value} />,
    },
    {
      headerName: 'Account Code',
      field: 'account_code',
      width: 180,
      cellRenderer: AccountCodeRenderer,
    },
    {
      headerName: 'Acquisition Date',
      field: 'acquisition_date',
      width: 150,
      valueFormatter: (params) => new Date(params.value).toLocaleDateString(),
      editable: true,
    },
    {
      headerName: 'Cost',
      field: 'total_cost_sar',
      width: 150,
      cellRenderer: CurrencyRenderer,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Useful Life (Years)',
      field: 'useful_life_years',
      width: 170,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Annual Depreciation',
      field: 'annual_depreciation_sar',
      width: 180,
      cellRenderer: CurrencyRenderer,
    },
    {
      headerName: 'Actions',
      width: 100,
      cellRenderer: ActionsCellRenderer,
      pinned: 'right',
    },
  ]

  return (
    <PlanningPageWrapper
      stepId="capex"
      actions={
        <>
          <HistoricalToggle
            showHistorical={showHistorical}
            onToggle={setShowHistorical}
            disabled={!selectedVersionId}
            isLoading={historicalLoading}
            currentFiscalYear={currentFiscalYear}
          />
          <Button data-testid="add-capex-button" disabled={!selectedVersionId}>
            <Plus className="w-4 h-4 mr-2" />
            Add CapEx Item
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
            {/* Historical Summary for CapEx */}
            {showHistorical && historicalData?.totals && (
              <HistoricalSummary
                currentValue={totalCapEx}
                priorYearValue={historicalData.totals.n_minus_1?.value ?? null}
                changePercent={historicalData.totals.vs_n_minus_1_pct ?? null}
                label="Total CapEx vs Prior Year"
                isCurrency={true}
                className="mb-4"
              />
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <SummaryCard
                title="Total CapEx"
                value={formatCurrency(totalCapEx)}
                subtitle={`${capexItems.length} items`}
                icon={<Building2 className="w-5 h-5" />}
                valueClassName="text-blue-600"
              />
              <SummaryCard
                title="Equipment"
                value={formatCurrency(equipmentCost)}
                subtitle={`${((equipmentCost / totalCapEx) * 100).toFixed(1)}% of total`}
                icon={<Wrench className="w-5 h-5" />}
              />
              <SummaryCard
                title="IT & Software"
                value={formatCurrency(itCost)}
                subtitle={`${((itCost / totalCapEx) * 100).toFixed(1)}% of total`}
                icon={<Laptop className="w-5 h-5" />}
              />
              <SummaryCard
                title="Avg. Useful Life"
                value={`${avgUsefulLife.toFixed(1)} years`}
                subtitle="Average across all assets"
                icon={<TrendingDown className="w-5 h-5" />}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Capital Expenditure Items</CardTitle>
                    <p className="text-sm text-gray-600">
                      Add and manage capital expenditure items. Click the eye icon to view
                      depreciation schedule.
                    </p>
                  </CardHeader>
                  <CardContent>
                    <div style={{ height: 600 }}>
                      <AgGridReact
                        rowData={capexItems}
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
              </div>

              <div>
                <Card>
                  <CardHeader>
                    <CardTitle>Asset Categories</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        {
                          type: 'EQUIPMENT',
                          icon: <Wrench className="w-4 h-4" />,
                          label: 'Equipment',
                        },
                        {
                          type: 'IT',
                          icon: <Laptop className="w-4 h-4" />,
                          label: 'IT Hardware',
                        },
                        {
                          type: 'FURNITURE',
                          icon: <Building2 className="w-4 h-4" />,
                          label: 'Furniture',
                        },
                        {
                          type: 'BUILDING_IMPROVEMENTS',
                          icon: <Building2 className="w-4 h-4" />,
                          label: 'Building Improvements',
                        },
                        {
                          type: 'SOFTWARE',
                          icon: <Laptop className="w-4 h-4" />,
                          label: 'Software',
                        },
                      ].map(({ type, icon, label }) => {
                        const count = capexItems.filter(
                          (item: CapExItem) => item.category === type
                        ).length
                        const cost = capexItems
                          .filter((item: CapExItem) => item.category === type)
                          .reduce((sum: number, item: CapExItem) => sum + item.total_cost_sar, 0)
                        return (
                          <div
                            key={type}
                            className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                          >
                            <div className="flex items-center gap-2">
                              {icon}
                              <span className="text-sm font-medium">{label}</span>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-bold">{formatCurrency(cost)}</div>
                              <div className="text-xs text-gray-500">{count} items</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>

                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle>Depreciation Info</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 text-sm">
                      <div>
                        <h4 className="font-medium mb-1">Straight Line</h4>
                        <p className="text-gray-600">
                          Equal depreciation each year. Annual = Cost ÷ Useful Life
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Declining Balance</h4>
                        <p className="text-gray-600">
                          Accelerated depreciation. Higher in early years, typically 20% per year.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Account Codes (2xxx)</h4>
                        <p className="text-gray-600">
                          All capital assets are recorded in the 2000 series of accounts.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Purchase Date</h4>
                        <p className="text-gray-600">
                          Must be within the budget fiscal year for proper allocation.
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
            Please select a budget version to view capital expenditure planning
          </div>
        )}
      </div>

      <Dialog open={showDepreciation} onOpenChange={setShowDepreciation}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Depreciation Schedule</DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {depreciationSchedule && depreciationSchedule.length > 0 ? (
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-4 font-medium text-sm border-b pb-2">
                  <div>Year</div>
                  <div className="text-right">Depreciation</div>
                  <div className="text-right">Book Value</div>
                </div>
                {depreciationSchedule.map((item, index) => (
                  <div key={index} className="grid grid-cols-3 gap-4 text-sm py-1">
                    <div>Year {item.year}</div>
                    <div className="text-right">{formatCurrency(item.annual_depreciation)}</div>
                    <div className="text-right font-medium">{formatCurrency(item.book_value)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">Loading depreciation schedule...</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </PlanningPageWrapper>
  )
}
