/**
 * Tuition Revenue Page - /revenue/tuition
 *
 * Manages tuition fee revenue projections including enrollment-based calculations.
 * Auto-calculated from enrollment × fee structure.
 *
 * Migrated from: /finance/revenue
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'
import { SummaryCard } from '@/components/SummaryCard'
import { RevenueChart } from '@/components/charts/RevenueChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useRevenuePivoted, useCalculateRevenue } from '@/hooks/api/useRevenue'
import { useVersion } from '@/contexts/VersionContext'
import { useVersions } from '@/hooks/api/useVersions'
import { DollarSign, TrendingUp, Calculator, Download } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useRevenueWithHistory } from '@/hooks/api/useHistorical'
import type { RevenueLineItemPivoted } from '@/types/api'

// Account code category helper
const getAccountCategory = (code: string): { label: string; color: string } => {
  const codeNum = parseInt(code)
  if (codeNum >= 70000 && codeNum < 71000) {
    return { label: 'Tuition', color: 'bg-green-100 text-green-800' }
  }
  if (codeNum >= 70100 && codeNum < 70300) {
    return { label: 'Enrollment Fees', color: 'bg-blue-100 text-blue-800' }
  }
  if (codeNum >= 75000 && codeNum < 78000) {
    return { label: 'Other Revenue', color: 'bg-purple-100 text-purple-800' }
  }
  if (codeNum >= 64000 && codeNum < 65000) {
    return { label: 'Salaries', color: 'bg-orange-100 text-orange-800' }
  }
  if (codeNum >= 60000 && codeNum < 63000) {
    return { label: 'Supplies', color: 'bg-yellow-100 text-yellow-800' }
  }
  if (codeNum >= 20000 && codeNum < 30000) {
    return { label: 'CapEx', color: 'bg-indigo-100 text-indigo-800' }
  }
  return { label: 'Other', color: 'bg-gray-100 text-gray-800' }
}

type RevenueGridItem = RevenueLineItemPivoted

export const Route = createFileRoute('/_authenticated/revenue/tuition')({
  component: TuitionRevenuePage,
})

function TuitionRevenuePage() {
  const { selectedVersionId } = useVersion()
  const [showHistorical, setShowHistorical] = useState(false)
  const { data: revenueItems = [], isLoading } = useRevenuePivoted(selectedVersionId!)
  const { data: budgetVersions } = useVersions()
  const calculateRevenue = useCalculateRevenue()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useRevenueWithHistory(
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

  const handleCalculateRevenue = () => {
    if (selectedVersionId) {
      calculateRevenue.mutate(selectedVersionId)
    }
  }

  // Calculate summary metrics
  const tuitionRevenue = revenueItems
    .filter((item) => item.account_code.startsWith('7011') || item.account_code.startsWith('7012'))
    .reduce((sum, item) => sum + item.annual_amount, 0)
  const enrollmentFees = revenueItems
    .filter((item) => item.account_code.startsWith('702'))
    .reduce((sum, item) => sum + item.annual_amount, 0)
  const otherRevenue = revenueItems
    .filter(
      (item) =>
        item.account_code.startsWith('75') ||
        item.account_code.startsWith('76') ||
        item.account_code.startsWith('77')
    )
    .reduce((sum, item) => sum + item.annual_amount, 0)
  const totalRevenue = tuitionRevenue + enrollmentFees + otherRevenue

  // Chart data - using theme colors
  const chartData = [
    { category: 'Tuition', amount: tuitionRevenue, color: 'var(--color-sage)' },
    { category: 'Enrollment Fees', amount: enrollmentFees, color: 'var(--color-slate)' },
    { category: 'Other Revenue', amount: otherRevenue, color: 'var(--color-wine)' },
  ]

  // Format currency helper
  const formatCurrencyCell = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '—'
    const formatted = new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
    return formatted
  }

  // TanStack Table column definitions
  const columnDefs: ColumnDef<RevenueGridItem, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'account_code',
        header: 'Account Code',
        size: 200,
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
        size: 300,
      },
      {
        accessorKey: 'category',
        header: 'Category',
        size: 150,
      },
      {
        accessorKey: 't1_amount',
        header: 'T1 (40%)',
        size: 150,
        cell: ({ getValue, row }) => {
          const value = getValue() as number | null
          const isAuto = row.original.is_calculated
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value !== null && value < 0 ? 'text-red-600' : 'text-gray-900',
                isAuto && 'bg-subtle'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 't2_amount',
        header: 'T2 (30%)',
        size: 150,
        cell: ({ getValue, row }) => {
          const value = getValue() as number | null
          const isAuto = row.original.is_calculated
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value !== null && value < 0 ? 'text-red-600' : 'text-gray-900',
                isAuto && 'bg-subtle'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 't3_amount',
        header: 'T3 (30%)',
        size: 150,
        cell: ({ getValue, row }) => {
          const value = getValue() as number | null
          const isAuto = row.original.is_calculated
          return (
            <div
              className={cn(
                'flex items-center justify-end font-medium',
                value !== null && value < 0 ? 'text-red-600' : 'text-gray-900',
                isAuto && 'bg-subtle'
              )}
            >
              {formatCurrencyCell(value)}
            </div>
          )
        },
        meta: { align: 'right' },
      },
      {
        accessorKey: 'annual_amount',
        header: 'Annual Total',
        size: 180,
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
        header: 'Auto-Calculated',
        size: 150,
        cell: ({ getValue }) => {
          const value = getValue() as boolean
          return value ? '✓ Yes' : '✗ No'
        },
        meta: { align: 'center' },
      },
      {
        accessorKey: 'notes',
        header: 'Notes',
        size: 250,
        cell: ({ getValue }) => String(getValue() ?? '—'),
      },
    ],
    []
  )

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

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
          data-testid="calculate-revenue"
          onClick={handleCalculateRevenue}
          disabled={!selectedVersionId || calculateRevenue.isPending}
        >
          <Calculator className="w-4 h-4 mr-2" />
          Recalculate Revenue
        </Button>
        <Button data-testid="export-button" variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Historical Summary for Revenue */}
          {showHistorical && historicalData?.totals && (
            <HistoricalSummary
              currentValue={totalRevenue}
              priorYearValue={historicalData.totals.n_minus_1?.value ?? null}
              changePercent={historicalData.totals.vs_n_minus_1_pct ?? null}
              label="Total Revenue vs Prior Year"
              isCurrency={true}
              className="mb-4"
            />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Total Revenue"
              value={formatCurrency(totalRevenue)}
              subtitle="Annual total"
              icon={<DollarSign className="w-5 h-5" />}
              valueClassName="text-green-600"
            />
            <SummaryCard
              title="Tuition Revenue"
              value={formatCurrency(tuitionRevenue)}
              subtitle={`${((tuitionRevenue / totalRevenue) * 100).toFixed(1)}% of total`}
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <SummaryCard
              title="Enrollment Fees"
              value={formatCurrency(enrollmentFees)}
              subtitle={`${((enrollmentFees / totalRevenue) * 100).toFixed(1)}% of total`}
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <SummaryCard
              title="Other Revenue"
              value={formatCurrency(otherRevenue)}
              subtitle={`${((otherRevenue / totalRevenue) * 100).toFixed(1)}% of total`}
              icon={<TrendingUp className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Line Items</CardTitle>
                  <p className="text-sm text-gray-600">
                    Gray cells are auto-calculated from enrollment. Edit trimester amounts for
                    manual entries.
                  </p>
                </CardHeader>
                <CardContent>
                  <TanStackDataTable<RevenueGridItem>
                    rowData={revenueItems}
                    columnDefs={columnDefs}
                    getRowId={(row) => row.account_code}
                    loading={isLoading}
                    height={600}
                    tableLabel="Revenue Line Items Grid"
                    enableSorting={true}
                    nativeColumns={true}
                    moduleColor="gold"
                  />
                </CardContent>
              </Card>
            </div>

            <div>
              <RevenueChart data={chartData} title="Revenue Breakdown" />

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Revenue Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 text-sm">
                    <div>
                      <h4 className="font-medium mb-1">Tuition (70110-70130)</h4>
                      <p className="text-gray-600">
                        Auto-calculated from enrollment × fee structure. Includes sibling discounts
                        (25% for 3rd+ child).
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Enrollment Fees (70200-70299)</h4>
                      <p className="text-gray-600">
                        Registration fees and DAI (annual enrollment fee). DAI is annual only, not
                        split by trimester.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Other Revenue (75xxx-77xxx)</h4>
                      <p className="text-gray-600">
                        Transportation, cafeteria, after-school activities, and other services.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Trimester Split</h4>
                      <p className="text-gray-600">
                        T1: 40% (Jan-Apr), T2: 30% (May-Aug), T3: 30% (Sep-Dec)
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
          Please select a budget version to view tuition revenue planning
        </div>
      )}
    </div>
  )
}
