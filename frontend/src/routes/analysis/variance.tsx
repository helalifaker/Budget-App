import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { SummaryCard } from '@/components/SummaryCard'
import { VarianceRow } from '@/components/VarianceRow'
import { WaterfallChart } from '@/components/charts/WaterfallChart'
import {
  useVarianceReport,
  useImportActuals,
  useCreateForecastRevision,
} from '@/hooks/api/useAnalysis'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { Upload, TrendingUp, AlertCircle } from 'lucide-react'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/analysis/variance')({
  component: BudgetVsActualPage,
})

function BudgetVsActualPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [period, setPeriod] = useState<'T1' | 'T2' | 'T3' | 'ANNUAL'>('ANNUAL')
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const { data: report, isLoading } = useVarianceReport(selectedVersionId, period)
  const importMutation = useImportActuals()
  const forecastMutation = useCreateForecastRevision()

  const handleImport = async () => {
    if (!selectedFile) {
      toastMessages.warning.unsavedChanges()
      return
    }
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }

    try {
      await importMutation.mutateAsync({
        versionId: selectedVersionId,
        period,
        file: selectedFile,
      })
      setImportDialogOpen(false)
      setSelectedFile(null)
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleCreateForecast = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }

    try {
      await forecastMutation.mutateAsync(selectedVersionId)
      // Navigate to new version
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Prepare waterfall chart data
  const waterfallData =
    report?.lines.slice(0, 10).map((line) => ({
      name: line.description.substring(0, 20),
      value: line.variance,
      type: line.is_favorable ? ('favorable' as const) : ('unfavorable' as const),
    })) || []

  // Group lines by category
  const groupedLines = report?.lines.reduce(
    (acc, line) => {
      if (!acc[line.category]) {
        acc[line.category] = []
      }
      acc[line.category].push(line)
      return acc
    },
    {} as Record<string, typeof report.lines>
  )

  return (
    <MainLayout>
      <PageContainer
        title="Budget vs Actual"
        description="Analyze variance between budget and actual performance"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Analysis', href: '/analysis/variance' },
          { label: 'Budget vs Actual' },
        ]}
      >
        <div className="space-y-6">
          {/* Controls */}
          <div className="flex items-center justify-between gap-4">
            <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="T1">Trimester 1</SelectItem>
                <SelectItem value="T2">Trimester 2</SelectItem>
                <SelectItem value="T3">Trimester 3</SelectItem>
                <SelectItem value="ANNUAL">Annual</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex gap-2">
              <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Upload className="w-4 h-4 mr-2" />
                    Import Actuals
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Import Actual Data</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>Period</Label>
                      <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="T1">Trimester 1</SelectItem>
                          <SelectItem value="T2">Trimester 2</SelectItem>
                          <SelectItem value="T3">Trimester 3</SelectItem>
                          <SelectItem value="ANNUAL">Annual</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>File (CSV/Excel)</Label>
                      <Input
                        type="file"
                        accept=".csv,.xlsx,.xls"
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      />
                    </div>
                    <Button
                      onClick={handleImport}
                      disabled={!selectedFile || importMutation.isPending}
                    >
                      {importMutation.isPending ? 'Importing...' : 'Import'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Button
                variant="outline"
                size="sm"
                onClick={handleCreateForecast}
                disabled={forecastMutation.isPending}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                {forecastMutation.isPending ? 'Creating...' : 'Create Forecast'}
              </Button>
            </div>
          </div>

          {selectedVersionId && (
            <>
              {isLoading ? (
                <div className="text-center py-12">Loading variance report...</div>
              ) : report ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <SummaryCard
                      title="Total Variance"
                      value={formatCurrency(report.total_variance)}
                      valueClassName={
                        report.total_variance >= 0 ? 'text-green-600' : 'text-red-600'
                      }
                    />
                    <SummaryCard
                      title="Favorable Variances"
                      value={report.favorable_count}
                      valueClassName="text-green-600"
                    />
                    <SummaryCard
                      title="Unfavorable Variances"
                      value={report.unfavorable_count}
                      valueClassName="text-red-600"
                    />
                  </div>

                  {/* Waterfall Chart */}
                  <WaterfallChart data={waterfallData} title="Top 10 Variances" />

                  {/* Variance Table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Variance Analysis</CardTitle>
                      <div className="text-sm text-gray-600">
                        Generated: {new Date(report.generated_at).toLocaleString()}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        {/* Table Header */}
                        <div className="grid grid-cols-[100px,1fr,120px,120px,120px,100px,120px] gap-4 py-2 px-3 bg-gray-100 font-semibold text-sm">
                          <div>Account</div>
                          <div>Description</div>
                          <div className="text-right">Budget</div>
                          <div className="text-right">Actual</div>
                          <div className="text-right">Variance</div>
                          <div className="text-right">Variance %</div>
                          <div className="text-right">Status</div>
                        </div>

                        {/* Grouped Rows */}
                        {['REVENUE', 'PERSONNEL', 'OPERATING'].map((category) => {
                          const lines = groupedLines?.[category] || []
                          if (lines.length === 0) return null

                          const categoryVariance = lines.reduce(
                            (sum, line) => sum + line.variance,
                            0
                          )

                          return (
                            <div key={category}>
                              <div className="font-semibold text-lg mb-2 px-3 text-gray-800">
                                {category}
                              </div>
                              {lines.map((line) => (
                                <VarianceRow
                                  key={line.account_code}
                                  account={line.account_code}
                                  description={line.description}
                                  budget={line.budget}
                                  actual={line.actual}
                                  variance={line.variance}
                                  variancePercent={line.variance_percent}
                                  isFavorable={line.is_favorable}
                                  isMaterial={line.is_material}
                                />
                              ))}
                              <div className="grid grid-cols-[100px,1fr,120px,120px,120px,100px,120px] gap-4 py-2 px-3 bg-gray-100 font-bold text-sm mt-1">
                                <div></div>
                                <div>Subtotal</div>
                                <div></div>
                                <div></div>
                                <div
                                  className={`text-right ${categoryVariance >= 0 ? 'text-green-600' : 'text-red-600'}`}
                                >
                                  {formatCurrency(categoryVariance)}
                                </div>
                                <div></div>
                                <div></div>
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      {/* Material Variance Note */}
                      <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm">
                          <strong>Material Variance:</strong> Variances marked as material exceed 5%
                          or 100,000 SAR and require management attention.
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    No variance data available. Import actuals to begin analysis.
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
