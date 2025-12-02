import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { StatementSection } from '@/components/StatementSection'
import { useFinancialStatement } from '@/hooks/api/useConsolidation'
import { Download, Printer } from 'lucide-react'
import type { FinancialStatement } from '@/types/api'

export const Route = createFileRoute('/consolidation/statements')({
  component: FinancialStatementsPage,
})

function FinancialStatementsPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')
  const [format, setFormat] = useState<FinancialStatement['format']>('PCG')
  const [period, setPeriod] = useState<FinancialStatement['period']>('ANNUAL')
  const [activeTab, setActiveTab] = useState<FinancialStatement['statement_type']>('INCOME')

  const { data: statement, isLoading } = useFinancialStatement(
    selectedVersionId,
    activeTab,
    format,
    period
  )

  const handlePrint = () => {
    window.print()
  }

  const handleExport = () => {
    // Placeholder for PDF export
    alert('PDF export will be implemented')
  }

  return (
    <MainLayout>
      <PageContainer
        title="Financial Statements"
        description="View income statement, balance sheet, and cash flow"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Consolidation', href: '/consolidation/budget' },
          { label: 'Financial Statements' },
        ]}
      >
        <div className="space-y-6">
          {/* Version Selector */}
          <BudgetVersionSelector
            value={selectedVersionId}
            onChange={setSelectedVersionId}
            showCreateButton={false}
          />

          {selectedVersionId && (
            <>
              {/* Controls */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex gap-3">
                  <Select value={format} onValueChange={(v) => setFormat(v as typeof format)}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Format" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PCG">PCG</SelectItem>
                      <SelectItem value="IFRS">IFRS</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Period" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ANNUAL">Annual</SelectItem>
                      <SelectItem value="P1">Period 1</SelectItem>
                      <SelectItem value="P2">Period 2</SelectItem>
                      <SelectItem value="SUMMER">Summer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handlePrint}>
                    <Printer className="w-4 h-4 mr-2" />
                    Print
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleExport}>
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </Button>
                </div>
              </div>

              {/* Statement Tabs */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {activeTab === 'INCOME'
                      ? 'Income Statement'
                      : activeTab === 'BALANCE'
                        ? 'Balance Sheet'
                        : 'Cash Flow Statement'}
                  </CardTitle>
                  <div className="text-sm text-gray-600">
                    Format: {format} | Period: {period}
                    {statement?.generated_at && (
                      <span className="ml-4">
                        Generated: {new Date(statement.generated_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs
                    value={activeTab}
                    onValueChange={(v) => setActiveTab(v as typeof activeTab)}
                  >
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="INCOME">Income Statement</TabsTrigger>
                      <TabsTrigger value="BALANCE">Balance Sheet</TabsTrigger>
                      <TabsTrigger value="CASHFLOW">Cash Flow</TabsTrigger>
                    </TabsList>

                    <TabsContent value="INCOME" className="mt-6">
                      {isLoading ? (
                        <div className="text-center py-8">Loading statement...</div>
                      ) : statement && statement.lines.length > 0 ? (
                        <StatementSection lines={statement.lines} />
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No statement data available
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="BALANCE" className="mt-6">
                      {isLoading ? (
                        <div className="text-center py-8">Loading statement...</div>
                      ) : statement && statement.lines.length > 0 ? (
                        <StatementSection lines={statement.lines} />
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No statement data available
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="CASHFLOW" className="mt-6">
                      {isLoading ? (
                        <div className="text-center py-8">Loading statement...</div>
                      ) : statement && statement.lines.length > 0 ? (
                        <StatementSection lines={statement.lines} />
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No statement data available
                        </div>
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
