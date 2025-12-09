/**
 * Financial Statements Page - /finance/statements
 *
 * Views income statement, balance sheet, and cash flow.
 * Navigation (SmartHeader + ModuleDock) provided by _authenticated.tsx layout.
 *
 * Migrated from /consolidation/statements
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
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
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { Download, Printer } from 'lucide-react'
import type { FinancialStatement } from '@/types/api'

export const Route = createFileRoute('/_authenticated/finance/statements')({
  component: FinancialStatementsPage,
})

function FinancialStatementsPage() {
  const { selectedVersionId } = useBudgetVersion()
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
    <PageContainer
      title="Financial Statements"
      description="View income statement, balance sheet, and cash flow"
      breadcrumbs={[
        { label: 'Home', href: '/' },
        { label: 'Finance', href: '/finance' },
        { label: 'Financial Statements' },
      ]}
    >
      <div className="space-y-6">
        {selectedVersionId && (
          <>
            {/* Controls */}
            <div className="flex items-center justify-between gap-4">
              <div className="flex gap-3">
                <Select value={format} onValueChange={(v) => setFormat(v as typeof format)}>
                  <SelectTrigger data-testid="format-selector" className="w-40">
                    <SelectValue placeholder="Format" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem data-testid="format-pcg" value="PCG">
                      PCG
                    </SelectItem>
                    <SelectItem data-testid="format-ifrs" value="IFRS">
                      IFRS
                    </SelectItem>
                  </SelectContent>
                </Select>

                <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
                  <SelectTrigger data-testid="period-selector" className="w-40">
                    <SelectValue placeholder="Period" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem data-testid="period-annual" value="ANNUAL">
                      Annual
                    </SelectItem>
                    <SelectItem data-testid="period-p1" value="P1">
                      Period 1
                    </SelectItem>
                    <SelectItem data-testid="period-p2" value="P2">
                      Period 2
                    </SelectItem>
                    <SelectItem data-testid="period-summer" value="SUMMER">
                      Summer
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  data-testid="print-button"
                  variant="outline"
                  size="sm"
                  onClick={handlePrint}
                >
                  <Printer className="w-4 h-4 mr-2" />
                  Print
                </Button>
                <Button
                  data-testid="export-button"
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                >
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
                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger data-testid="income-tab" value="INCOME">
                      Income Statement
                    </TabsTrigger>
                    <TabsTrigger data-testid="balance-tab" value="BALANCE">
                      Balance Sheet
                    </TabsTrigger>
                    <TabsTrigger data-testid="cashflow-tab" value="CASHFLOW">
                      Cash Flow
                    </TabsTrigger>
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
  )
}
