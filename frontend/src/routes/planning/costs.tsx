import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, themeQuartz } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { SummaryCard } from '@/components/SummaryCard'
import { CostChart } from '@/components/charts/CostChart'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AccountCodeRenderer } from '@/components/grid/AccountCodeRenderer'
import { CurrencyRenderer } from '@/components/grid/CurrencyRenderer'
import { useCosts, useCalculatePersonnelCosts } from '@/hooks/api/useCosts'
import { DollarSign, Users, ShoppingCart, Calculator, Download, Plus } from 'lucide-react'

export const Route = createFileRoute('/planning/costs')({
  component: CostsPage,
})

function CostsPage() {
  const [selectedVersion, setSelectedVersion] = useState<string>()
  const [activeTab, setActiveTab] = useState<'personnel' | 'operating'>('personnel')

  const { data: personnelCosts, isLoading: loadingPersonnel } = useCosts(
    selectedVersion!,
    'PERSONNEL'
  )
  const { data: operatingCosts, isLoading: loadingOperating } = useCosts(
    selectedVersion!,
    'OPERATING'
  )
  const calculatePersonnel = useCalculatePersonnelCosts()

  const handleCalculatePersonnel = () => {
    if (selectedVersion) {
      calculatePersonnel.mutate(selectedVersion)
    }
  }

  // Calculate summary metrics
  const personnelItems = personnelCosts?.items || []
  const operatingItems = operatingCosts?.items || []

  const totalPersonnel = personnelItems.reduce((sum, item) => sum + item.annual_amount, 0)
  const totalOperating = operatingItems.reduce((sum, item) => sum + item.annual_amount, 0)
  const totalCosts = totalPersonnel + totalOperating

  const personnelP1 = personnelItems.reduce((sum, item) => sum + item.p1_amount, 0)
  const personnelSummer = personnelItems.reduce((sum, item) => sum + item.summer_amount, 0)
  const personnelP2 = personnelItems.reduce((sum, item) => sum + item.p2_amount, 0)

  const operatingP1 = operatingItems.reduce((sum, item) => sum + item.p1_amount, 0)
  const operatingSummer = operatingItems.reduce((sum, item) => sum + item.summer_amount, 0)
  const operatingP2 = operatingItems.reduce((sum, item) => sum + item.p2_amount, 0)

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
    <MainLayout>
      <PageContainer
        title="Cost Planning"
        description="Manage personnel and operating costs by period"
      >
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <BudgetVersionSelector value={selectedVersion} onChange={setSelectedVersion} />
            <div className="flex gap-2">
              <Button
                onClick={handleCalculatePersonnel}
                disabled={!selectedVersion || calculatePersonnel.isPending}
              >
                <Calculator className="w-4 h-4 mr-2" />
                Recalculate Personnel Costs
              </Button>
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {selectedVersion && (
            <>
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
                  <Tabs
                    value={activeTab}
                    onValueChange={(v) => setActiveTab(v as typeof activeTab)}
                  >
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="personnel">Personnel Costs</TabsTrigger>
                      <TabsTrigger value="operating">Operating Costs</TabsTrigger>
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
                            Supplies, utilities, maintenance, insurance, and other operating
                            expenses.
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
          )}

          {!selectedVersion && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-gray-500">
                  <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>Select a budget version to view cost planning</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}

interface CostItem {
  account_code: string
  description: string
  cost_type: string
  p1_amount: number
  summer_amount: number
  p2_amount: number
  annual_amount: number
  is_auto_calculated: boolean
  notes?: string | null
}

function PersonnelCostsTab({ data, isLoading }: { data: CostItem[]; isLoading: boolean }) {
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
    },
    {
      headerName: 'Type',
      field: 'cost_type',
      width: 150,
    },
    {
      headerName: 'P1 (Jan-Jun)',
      field: 'p1_amount',
      width: 150,
      editable: (params) => !params.data.is_auto_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_auto_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'Summer',
      field: 'summer_amount',
      width: 150,
      editable: (params) => !params.data.is_auto_calculated,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
      cellStyle: (params) =>
        params.data.is_auto_calculated ? { backgroundColor: '#F3F4F6' } : undefined,
    },
    {
      headerName: 'P2 (Sep-Dec)',
      field: 'p2_amount',
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
      headerName: 'Auto',
      field: 'is_auto_calculated',
      width: 80,
      cellRenderer: (params: { value: boolean }) => (params.value ? '✓' : '✗'),
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 250,
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

function OperatingCostsTab({ data, isLoading }: { data: CostItem[]; isLoading: boolean }) {
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
      editable: true,
    },
    {
      headerName: 'Type',
      field: 'cost_type',
      width: 150,
    },
    {
      headerName: 'P1 (Jan-Jun)',
      field: 'p1_amount',
      width: 150,
      editable: true,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
    },
    {
      headerName: 'Summer',
      field: 'summer_amount',
      width: 150,
      editable: true,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
    },
    {
      headerName: 'P2 (Sep-Dec)',
      field: 'p2_amount',
      width: 150,
      editable: true,
      cellDataType: 'number',
      cellRenderer: CurrencyRenderer,
    },
    {
      headerName: 'Annual Total',
      field: 'annual_amount',
      width: 180,
      cellRenderer: CurrencyRenderer,
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 250,
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
