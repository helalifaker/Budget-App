/**
 * Financial Statements Page - /consolidation/statements
 *
 * Views income statement, balance sheet, and cash flow.
 *
 * Migrated from: /finance/statements
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
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
import { useVersion } from '@/contexts/VersionContext'
import { Download, Printer } from 'lucide-react'
import type {
  IncomeStatementResponse,
  BalanceSheetResponse,
  FinancialStatementLine,
} from '@/services/consolidation'
import type { StatementLine } from '@/types/api'

// Type for statement type selection
type StatementType = 'INCOME' | 'BALANCE' | 'CASHFLOW'
type StatementFormat = 'PCG' | 'IFRS'
type StatementPeriod = 'ANNUAL' | 'P1' | 'P2' | 'SUMMER'

// Transform backend FinancialStatementLine to frontend StatementLine
function mapToStatementLine(line: FinancialStatementLine): StatementLine {
  return {
    label: line.line_description,
    amount: line.amount_sar ?? 0,
    indent: line.indent_level,
    is_bold: line.is_bold,
    is_underlined: line.is_underlined,
    account_code: line.line_code,
  }
}

export const Route = createFileRoute('/_authenticated/consolidation/statements')({
  component: FinancialStatementsPage,
})

function FinancialStatementsPage() {
  const { selectedVersionId } = useVersion()
  const [format, setFormat] = useState<StatementFormat>('PCG')
  const [period, setPeriod] = useState<StatementPeriod>('ANNUAL')
  const [activeTab, setActiveTab] = useState<StatementType>('INCOME')

  const { data: statement, isLoading } = useFinancialStatement(
    selectedVersionId,
    activeTab,
    format,
    period
  )

  // Helper to get lines from either income statement or balance sheet
  const getStatementLines = (
    stmt: IncomeStatementResponse | BalanceSheetResponse | undefined
  ): StatementLine[] => {
    if (!stmt) return []
    // Balance sheet has assets/liabilities, income statement has lines directly
    if ('assets' in stmt) {
      // Balance sheet - combine assets and liabilities lines
      const assetLines = (stmt.assets.lines || []).map(mapToStatementLine)
      const liabilityLines = (stmt.liabilities.lines || []).map(mapToStatementLine)
      return [...assetLines, ...liabilityLines]
    }
    return (stmt.lines || []).map(mapToStatementLine)
  }

  const statementLines = getStatementLines(statement)

  const handlePrint = () => {
    window.print()
  }

  const handleExport = () => {
    // Placeholder for PDF export
    alert('PDF export will be implemented')
  }

  return (
    <div className="p-6 space-y-6">
      {selectedVersionId ? (
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
              <Button data-testid="print-button" variant="outline" size="sm" onClick={handlePrint}>
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
                {statement && 'updated_at' in statement && statement.updated_at && (
                  <span className="ml-4">
                    Generated: {new Date(statement.updated_at).toLocaleString()}
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
                  ) : statementLines.length > 0 ? (
                    <StatementSection lines={statementLines} />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      No statement data available
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="BALANCE" className="mt-6">
                  {isLoading ? (
                    <div className="text-center py-8">Loading statement...</div>
                  ) : statementLines.length > 0 ? (
                    <StatementSection lines={statementLines} />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      No statement data available
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="CASHFLOW" className="mt-6">
                  {isLoading ? (
                    <div className="text-center py-8">Loading statement...</div>
                  ) : statementLines.length > 0 ? (
                    <StatementSection lines={statementLines} />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      No statement data available
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Statement Formats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">PCG Format</h4>
                  <p className="text-gray-600">
                    French Plan Comptable Général format. Uses French accounting structure with
                    specific account numbering (Class 1-7). Required for AEFE reporting.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">IFRS Format</h4>
                  <p className="text-gray-600">
                    International Financial Reporting Standards format. Standard presentation for
                    international stakeholders and comparative analysis.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view financial statements
        </div>
      )}
    </div>
  )
}
