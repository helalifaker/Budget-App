/**
 * Budget Consolidation Page - /finance/consolidation
 *
 * Reviews and consolidates budget versions.
 * Navigation (SmartHeader + ModuleDock) provided by _authenticated.tsx layout.
 *
 * Migrated from /consolidation/budget
 */

import { createFileRoute } from '@tanstack/react-router'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SummaryCard } from '@/components/SummaryCard'
import {
  useConsolidationStatus,
  useBudgetLineItems,
  useConsolidate,
  useSubmitForApproval,
  useApproveBudget,
} from '@/hooks/api/useConsolidation'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { CheckCircle2, XCircle, FileCheck, Send, CheckSquare, DollarSign } from 'lucide-react'
import { toastMessages } from '@/lib/toast-messages'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export const Route = createFileRoute('/_authenticated/finance/consolidation')({
  component: BudgetConsolidationPage,
})

function BudgetConsolidationPage() {
  const { selectedVersionId } = useBudgetVersion()

  const { data: status, isLoading: statusLoading } = useConsolidationStatus(selectedVersionId)
  const { data: lineItems, isLoading: lineItemsLoading } = useBudgetLineItems(selectedVersionId)

  const consolidateMutation = useConsolidate()
  const submitMutation = useSubmitForApproval()
  const approveMutation = useApproveBudget()

  const handleConsolidate = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await consolidateMutation.mutateAsync(selectedVersionId)
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleSubmit = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await submitMutation.mutateAsync(selectedVersionId)
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleApprove = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await approveMutation.mutateAsync(selectedVersionId)
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

  // Group line items by category
  const groupedItems = lineItems?.reduce(
    (acc, item) => {
      const category = item.category
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(item)
      return acc
    },
    {} as Record<string, typeof lineItems>
  )

  // Prepare chart data
  const chartData = [
    {
      name: 'Revenue vs Costs',
      Revenue: status?.total_revenue || 0,
      Costs: status?.total_costs || 0,
    },
  ]

  return (
    <PageContainer
      title="Budget Consolidation"
      description="Review and consolidate budget version"
      breadcrumbs={[
        { label: 'Home', href: '/' },
        { label: 'Finance', href: '/finance' },
        { label: 'Consolidation' },
      ]}
    >
      <div className="space-y-6">
        {selectedVersionId && (
          <>
            {/* Consolidation Status */}
            <Card>
              <CardHeader>
                <CardTitle>Consolidation Status</CardTitle>
              </CardHeader>
              <CardContent>
                {statusLoading ? (
                  <div className="text-center py-4">Loading status...</div>
                ) : status ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Overall Status:</span>
                      <Badge variant={status.is_complete ? 'default' : 'secondary'}>
                        {status.is_complete ? 'Complete' : 'Incomplete'}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {Object.entries(status.modules_complete).map(([module, complete]) => (
                        <div
                          key={module}
                          className="flex items-center gap-2 p-2 rounded bg-gray-50"
                        >
                          {complete ? (
                            <CheckCircle2 className="w-5 h-5 text-green-600" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-400" />
                          )}
                          <span className="text-sm capitalize">{module}</span>
                        </div>
                      ))}
                    </div>

                    {status.last_consolidated_at && (
                      <div className="text-sm text-gray-600">
                        Last consolidated: {new Date(status.last_consolidated_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">No status available</div>
                )}
              </CardContent>
            </Card>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div data-testid="total-revenue">
                <SummaryCard
                  title="Total Revenue"
                  value={formatCurrency(status?.total_revenue || 0)}
                  icon={<DollarSign className="w-5 h-5" />}
                  valueClassName="text-green-600"
                />
              </div>
              <div data-testid="total-expenses">
                <SummaryCard
                  title="Total Costs"
                  value={formatCurrency(status?.total_costs || 0)}
                  icon={<DollarSign className="w-5 h-5" />}
                  valueClassName="text-red-600"
                />
              </div>
              <div data-testid="net-result">
                <SummaryCard
                  title="Net Income"
                  value={formatCurrency(status?.net_income || 0)}
                  icon={<DollarSign className="w-5 h-5" />}
                  valueClassName={
                    (status?.net_income || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }
                />
              </div>
              <SummaryCard
                title="Operating Margin"
                value={`${(status?.operating_margin || 0).toFixed(1)}%`}
                icon={<DollarSign className="w-5 h-5" />}
              />
            </div>

            {/* Revenue vs Costs Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue vs Costs</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Legend />
                    <Bar dataKey="Revenue" fill="#10B981" />
                    <Bar dataKey="Costs" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Line Items Table */}
            <Card>
              <CardHeader>
                <CardTitle>Budget Line Items</CardTitle>
              </CardHeader>
              <CardContent>
                {lineItemsLoading ? (
                  <div className="text-center py-8">Loading line items...</div>
                ) : lineItems && lineItems.length > 0 ? (
                  <div className="space-y-6">
                    {['REVENUE', 'PERSONNEL', 'OPERATING', 'CAPEX'].map((category) => {
                      const items = groupedItems?.[category] || []
                      if (items.length === 0) return null

                      const categoryTotal = items.reduce((sum, item) => sum + item.annual_amount, 0)

                      return (
                        <div key={category}>
                          <h3 className="font-semibold text-lg mb-3 text-gray-800">{category}</h3>
                          <div className="space-y-1">
                            {items.map((item) => (
                              <div
                                key={item.id}
                                className="grid grid-cols-[120px,1fr,150px] gap-4 py-2 px-3 hover:bg-gray-50 rounded"
                              >
                                <span className="text-sm font-mono text-gray-600">
                                  {item.account_code}
                                </span>
                                <span className="text-sm">{item.description}</span>
                                <span className="text-sm text-right font-semibold">
                                  {formatCurrency(item.annual_amount)}
                                </span>
                              </div>
                            ))}
                            <div className="grid grid-cols-[120px,1fr,150px] gap-4 py-2 px-3 bg-gray-100 rounded font-bold">
                              <span></span>
                              <span className="text-sm">Subtotal</span>
                              <span className="text-sm text-right">
                                {formatCurrency(categoryTotal)}
                              </span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No line items available. Please consolidate the budget first.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                data-testid="consolidate-button"
                onClick={handleConsolidate}
                disabled={consolidateMutation.isPending}
                className="flex items-center gap-2"
              >
                <FileCheck className="w-4 h-4" />
                {consolidateMutation.isPending ? 'Consolidating...' : 'Consolidate'}
              </Button>
              <Button
                data-testid="submit-button"
                onClick={handleSubmit}
                disabled={!status?.is_complete || submitMutation.isPending}
                variant="secondary"
                className="flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                {submitMutation.isPending ? 'Submitting...' : 'Submit for Approval'}
              </Button>
              <Button
                data-testid="approve-button"
                onClick={handleApprove}
                disabled={approveMutation.isPending}
                variant="outline"
                className="flex items-center gap-2"
              >
                <CheckSquare className="w-4 h-4" />
                {approveMutation.isPending ? 'Approving...' : 'Approve'}
              </Button>
            </div>
          </>
        )}
      </div>
    </PageContainer>
  )
}
