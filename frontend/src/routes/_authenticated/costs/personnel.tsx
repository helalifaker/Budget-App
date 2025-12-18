/**
 * Personnel Costs Page - /costs/personnel
 *
 * Manages personnel cost planning including salaries, benefits, GOSI, and EOS.
 * Auto-calculated from DHG workforce planning.
 *
 * Migrated from: /finance/costs (personnel tab)
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'
import { SummaryCard } from '@/components/SummaryCard'
import { CostChart } from '@/components/charts/CostChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { usePersonnelCosts, useCalculatePersonnelCosts } from '@/hooks/api/useCosts'
import { useVersion } from '@/contexts/VersionContext'
import { useVersions } from '@/hooks/api/useVersions'
import { DollarSign, Users, Calculator, Download } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useCostsWithHistory } from '@/hooks/api/useHistorical'

// Account code category helper
const getAccountCategory = (code: string): { label: string; color: string } => {
  const codeNum = parseInt(code)
  if (codeNum >= 64000 && codeNum < 65000) {
    return { label: 'Salaries', color: 'bg-orange-100 text-orange-800' }
  }
  if (codeNum >= 60000 && codeNum < 63000) {
    return { label: 'Supplies', color: 'bg-yellow-100 text-yellow-800' }
  }
  if (codeNum >= 61000 && codeNum < 62000) {
    return { label: 'Services', color: 'bg-blue-100 text-blue-800' }
  }
  if (codeNum >= 62000 && codeNum < 63000) {
    return { label: 'External', color: 'bg-purple-100 text-purple-800' }
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

// Matches PersonnelCostPlan from backend API
interface PersonnelCostItem {
  id: string
  version_id: string
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

export const Route = createFileRoute('/_authenticated/costs/personnel')({
  component: PersonnelCostsPage,
})

function PersonnelCostsPage() {
  const { selectedVersionId } = useVersion()
  const [showHistorical, setShowHistorical] = useState(false)

  const { data: personnelCosts, isLoading } = usePersonnelCosts(selectedVersionId!)
  const { data: budgetVersions } = useVersions()
  const calculatePersonnel = useCalculatePersonnelCosts()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useCostsWithHistory(
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

  const handleCalculatePersonnel = () => {
    if (selectedVersionId) {
      calculatePersonnel.mutate({ versionId: selectedVersionId })
    }
  }

  const personnelItems = (personnelCosts || []) as PersonnelCostItem[]

  const totalPersonnel = personnelItems.reduce(
    (sum: number, item: PersonnelCostItem) => sum + (item.total_cost_sar || 0),
    0
  )

  // Period estimates
  const personnelP1 = totalPersonnel * 0.5
  const personnelSummer = totalPersonnel * 0.17
  const personnelP2 = totalPersonnel * 0.33

  // Chart data
  const chartData = [
    { period: 'P1 (Jan-Jun)', personnel: personnelP1, operating: 0 },
    { period: 'Summer', personnel: personnelSummer, operating: 0 },
    { period: 'P2 (Sep-Dec)', personnel: personnelP2, operating: 0 },
  ]

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  // Total FTE
  const totalFTE = personnelItems.reduce(
    (sum: number, item: PersonnelCostItem) => sum + (item.fte_count || 0),
    0
  )

  // Average cost per FTE
  const avgCostPerFTE = totalFTE > 0 ? totalPersonnel / totalFTE : 0

  const columnDefs: ColumnDef<PersonnelCostItem, unknown>[] = useMemo(
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
        accessorKey: 'category_id',
        header: 'Category',
        size: 150,
      },
      {
        accessorKey: 'fte_count',
        header: 'FTE Count',
        size: 120,
        cell: ({ getValue, row }) => {
          const value = getValue() as number
          const isCalc = row.original.is_calculated
          return (
            <div className={cn('text-right', isCalc && 'bg-subtle')}>
              {value?.toFixed(2) ?? '0.00'}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 'unit_cost_sar',
        header: 'Unit Cost (SAR)',
        size: 150,
        cell: ({ getValue, row }) => {
          const value = getValue() as number
          const isCalc = row.original.is_calculated
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value < 0 ? 'text-red-600' : 'text-gray-900',
                isCalc && 'bg-subtle'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 'total_cost_sar',
        header: 'Total Cost (SAR)',
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
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Historical Summary */}
          {showHistorical && historicalData?.personnel_totals && (
            <HistoricalSummary
              currentValue={totalPersonnel}
              priorYearValue={historicalData.personnel_totals.n_minus_1?.value ?? null}
              changePercent={historicalData.personnel_totals.vs_n_minus_1_pct ?? null}
              label="Personnel Costs vs Prior Year"
              isCurrency={true}
              className="mb-4"
            />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Total Personnel"
              value={formatCurrency(totalPersonnel)}
              subtitle="Annual total"
              icon={<DollarSign className="w-5 h-5" />}
              valueClassName="text-red-600"
            />
            <SummaryCard
              title="Total FTE"
              value={totalFTE.toFixed(1)}
              subtitle="Full-time equivalents"
              icon={<Users className="w-5 h-5" />}
            />
            <SummaryCard
              title="Avg Cost/FTE"
              value={formatCurrency(avgCostPerFTE)}
              subtitle="Including benefits"
              icon={<Users className="w-5 h-5" />}
            />
            <SummaryCard
              title="Line Items"
              value={personnelItems.length.toString()}
              subtitle="Cost categories"
              icon={<Users className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Personnel Costs</CardTitle>
                  <p className="text-sm text-gray-600">
                    Gray cells are auto-calculated from DHG. Manual adjustments allowed with notes.
                  </p>
                </CardHeader>
                <CardContent>
                  <TanStackDataTable<PersonnelCostItem>
                    rowData={personnelItems}
                    columnDefs={columnDefs}
                    getRowId={(row) => row.id}
                    loading={isLoading}
                    height={600}
                    tableLabel="Personnel Costs Grid"
                    enableSorting={true}
                    nativeColumns={true}
                    moduleColor="orange"
                  />
                </CardContent>
              </Card>
            </div>

            <div>
              <CostChart data={chartData} title="Personnel Costs by Period" />

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Personnel Cost Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 text-sm">
                    <div>
                      <h4 className="font-medium mb-1">Salaries (641xx)</h4>
                      <p className="text-gray-600">
                        Auto-calculated from DHG FTE counts × salary scales.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">GOSI (12% + 10%)</h4>
                      <p className="text-gray-600">
                        Saudi social insurance: 12% employer + 10% employee (capped).
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">EOS (End of Service)</h4>
                      <p className="text-gray-600">
                        Gratuity accrual based on tenure and final salary.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">AEFE (PRRD)</h4>
                      <p className="text-gray-600">
                        ~41,863 EUR per seconded teacher contribution.
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
          Please select a version to view personnel cost planning
        </div>
      )}
    </div>
  )
}
