/**
 * Operating Costs Page - /costs/operating
 *
 * Manages day-to-day operating expenses including supplies, services,
 * utilities, and other operational costs.
 *
 * Migrated from: /finance/costs (operating tab)
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'
import { SummaryCard } from '@/components/SummaryCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useOperatingCosts } from '@/hooks/api/useCosts'
import { useVersion } from '@/contexts/VersionContext'
import { useVersions } from '@/hooks/api/useVersions'
import { DollarSign, ShoppingCart, Plus, Download } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useCostsWithHistory } from '@/hooks/api/useHistorical'

// Account code category helper
const getAccountCategory = (code: string): { label: string; color: string } => {
  const codeNum = parseInt(code)
  if (codeNum >= 60000 && codeNum < 61000) {
    return { label: 'Supplies', color: 'bg-yellow-100 text-yellow-800' }
  }
  if (codeNum >= 61000 && codeNum < 62000) {
    return { label: 'Services', color: 'bg-blue-100 text-blue-800' }
  }
  if (codeNum >= 62000 && codeNum < 63000) {
    return { label: 'External', color: 'bg-purple-100 text-purple-800' }
  }
  if (codeNum >= 63000 && codeNum < 64000) {
    return { label: 'Taxes', color: 'bg-red-100 text-red-800' }
  }
  return { label: 'Other', color: 'bg-gray-100 text-gray-800' }
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

// Matches OperatingCostPlan from backend API
interface OperatingCostItem {
  id: string
  version_id: string
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

export const Route = createFileRoute('/_authenticated/costs/operating')({
  component: OperatingCostsPage,
})

function OperatingCostsPage() {
  const { selectedVersionId } = useVersion()
  const [showHistorical, setShowHistorical] = useState(false)

  const { data: operatingCosts, isLoading } = useOperatingCosts(selectedVersionId!)
  const { data: budgetVersions } = useVersions()

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

  const operatingItems = (operatingCosts || []) as OperatingCostItem[]

  const totalOperating = operatingItems.reduce(
    (sum: number, item: OperatingCostItem) => sum + (item.amount_sar || 0),
    0
  )

  // Category breakdown
  const suppliesCost = operatingItems
    .filter((item) => item.account_code.startsWith('60'))
    .reduce((sum, item) => sum + (item.amount_sar || 0), 0)

  const servicesCost = operatingItems
    .filter((item) => item.account_code.startsWith('61'))
    .reduce((sum, item) => sum + (item.amount_sar || 0), 0)

  const externalCost = operatingItems
    .filter((item) => item.account_code.startsWith('62'))
    .reduce((sum, item) => sum + (item.amount_sar || 0), 0)

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const columnDefs: ColumnDef<OperatingCostItem, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'account_code',
        header: 'Account Code',
        size: 150,
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
        accessorKey: 'description',
        header: 'Description',
        size: 250,
      },
      {
        accessorKey: 'category',
        header: 'Category',
        size: 150,
      },
      {
        accessorKey: 'amount_sar',
        header: 'Amount (SAR)',
        size: 160,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return (
            <div
              className={cn(
                'flex items-center justify-end font-bold',
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
        accessorKey: 'is_calculated',
        header: 'Auto',
        size: 80,
        cell: ({ getValue }) => {
          const value = getValue() as boolean
          return value ? '✓' : '✗'
        },
        meta: { align: 'center' },
      },
      {
        accessorKey: 'calculation_driver',
        header: 'Driver',
        size: 150,
        cell: ({ getValue }) => String(getValue() ?? '—'),
      },
      {
        accessorKey: 'notes',
        header: 'Notes',
        size: 200,
        cell: ({ getValue }) => String(getValue() ?? '—'),
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
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          Add Line Item
        </Button>
        <Button data-testid="export-button" variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Historical Summary */}
          {showHistorical && historicalData?.operating_totals && (
            <HistoricalSummary
              currentValue={totalOperating}
              priorYearValue={historicalData.operating_totals.n_minus_1?.value ?? null}
              changePercent={historicalData.operating_totals.vs_n_minus_1_pct ?? null}
              label="Operating Costs vs Prior Year"
              isCurrency={true}
              className="mb-4"
            />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Total Operating"
              value={formatCurrency(totalOperating)}
              subtitle="Annual total"
              icon={<DollarSign className="w-5 h-5" />}
              valueClassName="text-red-600"
            />
            <SummaryCard
              title="Supplies (60xxx)"
              value={formatCurrency(suppliesCost)}
              subtitle={
                totalOperating > 0 ? `${((suppliesCost / totalOperating) * 100).toFixed(1)}%` : '—'
              }
              icon={<ShoppingCart className="w-5 h-5" />}
            />
            <SummaryCard
              title="Services (61xxx)"
              value={formatCurrency(servicesCost)}
              subtitle={
                totalOperating > 0 ? `${((servicesCost / totalOperating) * 100).toFixed(1)}%` : '—'
              }
              icon={<ShoppingCart className="w-5 h-5" />}
            />
            <SummaryCard
              title="External (62xxx)"
              value={formatCurrency(externalCost)}
              subtitle={
                totalOperating > 0 ? `${((externalCost / totalOperating) * 100).toFixed(1)}%` : '—'
              }
              icon={<ShoppingCart className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Operating Costs</CardTitle>
                    <p className="text-sm text-gray-600">
                      Add, edit, or delete operating expense line items.
                    </p>
                  </div>
                </CardHeader>
                <CardContent>
                  <TanStackDataTable<OperatingCostItem>
                    rowData={operatingItems}
                    columnDefs={columnDefs}
                    getRowId={(row) => row.id}
                    loading={isLoading}
                    height={600}
                    tableLabel="Operating Costs Grid"
                    enableSorting={true}
                    nativeColumns={true}
                    moduleColor="orange"
                  />
                </CardContent>
              </Card>
            </div>

            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Operating Cost Categories</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 text-sm">
                    <div>
                      <h4 className="font-medium mb-1">Supplies (60xxx)</h4>
                      <p className="text-gray-600">
                        Educational materials, office supplies, cleaning supplies, and consumables.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Services (61xxx)</h4>
                      <p className="text-gray-600">
                        Utilities, maintenance, repairs, IT services, and contracted services.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">External Services (62xxx)</h4>
                      <p className="text-gray-600">
                        Professional fees, consulting, legal, audit, and external contractors.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Taxes & Fees (63xxx)</h4>
                      <p className="text-gray-600">
                        Government fees, licenses, permits, and other regulatory costs.
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
          Please select a budget version to view operating cost planning
        </div>
      )}
    </div>
  )
}
