import { createFileRoute } from '@tanstack/react-router'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, themeQuartz } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { SummaryCard } from '@/components/SummaryCard'
import { RevenueChart } from '@/components/charts/RevenueChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AccountCodeRenderer } from '@/components/grid/AccountCodeRenderer'
import { CurrencyRenderer } from '@/components/grid/CurrencyRenderer'
import { useRevenue, useCalculateRevenue } from '@/hooks/api/useRevenue'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { DollarSign, TrendingUp, Calculator, Download } from 'lucide-react'

export const Route = createFileRoute('/planning/revenue')({
  component: RevenuePage,
})

function RevenuePage() {
  const { selectedVersionId } = useBudgetVersion()
  const { data: revenue, isLoading } = useRevenue(selectedVersionId!)
  const calculateRevenue = useCalculateRevenue()

  const handleCalculateRevenue = () => {
    if (selectedVersionId) {
      calculateRevenue.mutate(selectedVersionId)
    }
  }

  // Calculate summary metrics
  const revenueItems = revenue?.items || []
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

  // Chart data
  const chartData = [
    { category: 'Tuition', amount: tuitionRevenue, color: '#10B981' },
    { category: 'Enrollment Fees', amount: enrollmentFees, color: '#3B82F6' },
    { category: 'Other Revenue', amount: otherRevenue, color: '#8B5CF6' },
  ]

  const columnDefs: ColDef[] = [
    {
      headerName: 'Account Code',
      field: 'account_code',
      width: 200,
      pinned: 'left',
      cellRenderer: AccountCodeRenderer,
    },
    {
      headerName: 'Description',
      field: 'description',
      width: 300,
      editable: false,
    },
    {
      headerName: 'Category',
      field: 'category',
      width: 150,
    },
    {
      headerName: 'T1 (40%)',
      field: 't1_amount',
      width: 150,
      editable: (params) => !params.data.is_auto_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_auto_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'T2 (30%)',
      field: 't2_amount',
      width: 150,
      editable: (params) => !params.data.is_auto_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_auto_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'T3 (30%)',
      field: 't3_amount',
      width: 150,
      editable: (params) => !params.data.is_auto_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_auto_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'Annual Total',
      field: 'annual_amount',
      width: 180,
      cellRenderer: CurrencyRenderer,
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'Auto-Calculated',
      field: 'is_auto_calculated',
      width: 150,
      cellRenderer: (params: { value: boolean }) => (params.value ? '✓ Yes' : '✗ No'),
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 250,
      editable: true,
    },
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
    <MainLayout>
      <PageContainer
        title="Revenue Planning"
        description="Manage revenue projections by category and trimester"
      >
        <div className="space-y-6">
          <div className="flex items-center justify-end gap-2">
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

          {selectedVersionId && (
            <>
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
                      <div style={{ height: 600 }}>
                        <AgGridReact
                          rowData={revenueItems}
                          columnDefs={columnDefs}
                          defaultColDef={{
                            sortable: true,
                            filter: true,
                            resizable: true,
                          }}
                          loading={isLoading}
                          groupDisplayType="groupRows"
                          groupDefaultExpanded={-1}
                          theme={themeQuartz}
                        />
                      </div>
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
                            Auto-calculated from enrollment × fee structure. Includes sibling
                            discounts (25% for 3rd+ child).
                          </p>
                        </div>
                        <div>
                          <h4 className="font-medium mb-1">Enrollment Fees (70200-70299)</h4>
                          <p className="text-gray-600">
                            Registration fees and DAI (annual enrollment fee). DAI is annual only,
                            not split by trimester.
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
          )}

          {!selectedVersionId && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-gray-500">
                  <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>Select a budget version to view revenue planning</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
