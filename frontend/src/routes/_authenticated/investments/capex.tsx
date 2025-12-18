/**
 * CapEx Planning Page - /investments/capex
 *
 * Manages capital expenditure and depreciation planning.
 *
 * Migrated from: /finance/capex
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'
import { SummaryCard } from '@/components/SummaryCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { useCapEx, useDepreciationSchedule } from '@/hooks/api/useCapEx'
import { useVersion } from '@/contexts/VersionContext'
import { useVersions } from '@/hooks/api/useVersions'
import { Building2, Laptop, Wrench, TrendingDown, Plus, Download, Eye } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useCapExWithHistory } from '@/hooks/api/useHistorical'

// Define typed interface for capex items
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

// Account code category helper
const getAccountCategory = (code: string): { label: string; color: string } => {
  const codeNum = parseInt(code)
  if (codeNum >= 20000 && codeNum < 30000) {
    return { label: 'CapEx', color: 'bg-teal-100 text-teal-800' }
  }
  return { label: 'Other', color: 'bg-gray-100 text-gray-800' }
}

// Asset type badge colors
const ASSET_TYPE_COLORS: Record<string, 'info' | 'success' | 'warning' | 'default'> = {
  EQUIPMENT: 'info',
  IT: 'success',
  FURNITURE: 'warning',
  BUILDING_IMPROVEMENTS: 'default',
  SOFTWARE: 'info',
}

export const Route = createFileRoute('/_authenticated/investments/capex')({
  component: CapExPage,
})

function CapExPage() {
  const { selectedVersionId } = useVersion()
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const [showDepreciation, setShowDepreciation] = useState(false)
  const [showHistorical, setShowHistorical] = useState(false)

  const { data: capexData, isLoading } = useCapEx(selectedVersionId!)
  const { data: depreciationSchedule } = useDepreciationSchedule(selectedItemId!)
  const { data: budgetVersions } = useVersions()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useCapExWithHistory(
    selectedVersionId,
    {
      enabled: showHistorical,
    }
  )

  // Get current fiscal year from selected version
  const currentFiscalYear = useMemo(() => {
    if (!selectedVersionId || !budgetVersions?.items) return new Date().getFullYear()
    const version = budgetVersions.items.find((v) => v.id === selectedVersionId)
    return version?.fiscal_year ?? new Date().getFullYear()
  }, [selectedVersionId, budgetVersions])

  // API returns array directly
  const capexItems = (capexData || []) as CapExItem[]

  // Calculate summary metrics
  const totalCapEx = capexItems.reduce((sum, item) => sum + item.total_cost_sar, 0)
  const equipmentCost = capexItems
    .filter((item) => item.category === 'EQUIPMENT')
    .reduce((sum, item) => sum + item.total_cost_sar, 0)
  const itCost = capexItems
    .filter((item) => item.category === 'IT')
    .reduce((sum, item) => sum + item.total_cost_sar, 0)

  const avgUsefulLife =
    capexItems.length > 0
      ? capexItems.reduce((sum, item) => sum + item.useful_life_years, 0) / capexItems.length
      : 0

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  // Currency formatter
  const formatCurrencyCell = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '—'
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // TanStack Table column definitions
  const columnDefs: ColumnDef<CapExItem, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'description',
        header: 'Description',
        size: 300,
      },
      {
        accessorKey: 'category',
        header: 'Asset Type',
        size: 180,
        cell: ({ getValue }) => {
          const value = getValue() as string
          const variant = ASSET_TYPE_COLORS[value] || 'default'
          const label = value?.replace(/_/g, ' ') || '—'
          return <Badge variant={variant}>{label}</Badge>
        },
      },
      {
        accessorKey: 'account_code',
        header: 'Account Code',
        size: 180,
        cell: ({ getValue }) => {
          const value = getValue() as string
          if (!value) return null
          const category = getAccountCategory(value)
          return (
            <div className="flex items-center gap-2">
              <span className="font-mono font-medium">{value}</span>
              <span className={cn('text-xs px-2 py-0.5 rounded-full', category.color)}>
                {category.label}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: 'acquisition_date',
        header: 'Acquisition Date',
        size: 150,
        cell: ({ getValue }) => {
          const value = getValue() as string
          return value ? new Date(value).toLocaleDateString() : '—'
        },
      },
      {
        accessorKey: 'total_cost_sar',
        header: 'Cost',
        size: 150,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value < 0 ? 'text-red-600' : 'text-gray-900'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 'useful_life_years',
        header: 'Useful Life (Years)',
        size: 170,
        cell: ({ getValue }) => String(getValue() ?? '—'),
        meta: { align: 'right' },
      },
      {
        accessorKey: 'annual_depreciation_sar',
        header: 'Annual Depreciation',
        size: 180,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value < 0 ? 'text-red-600' : 'text-gray-900'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        id: 'actions',
        header: 'Actions',
        size: 100,
        cell: ({ row }) => (
          <div className="flex gap-2 items-center justify-center">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedItemId(row.original.id)
                setShowDepreciation(true)
              }}
            >
              <Eye className="w-4 h-4" />
            </Button>
          </div>
        ),
      },
    ],
    []
  )

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
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
      </div>

      {/* Content */}
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
              valueClassName="text-teal-600"
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
                  <TanStackDataTable<CapExItem>
                    rowData={capexItems}
                    columnDefs={columnDefs}
                    getRowId={(row) => row.id}
                    loading={isLoading}
                    height={600}
                    tableLabel="Capital Expenditure Items Grid"
                    enableSorting={true}
                    nativeColumns={true}
                    moduleColor="teal"
                  />
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
                      const count = capexItems.filter((item) => item.category === type).length
                      const cost = capexItems
                        .filter((item) => item.category === type)
                        .reduce((sum, item) => sum + item.total_cost_sar, 0)
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
          Please select a version to view capital expenditure planning
        </div>
      )}

      {/* Depreciation Dialog */}
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
    </div>
  )
}
