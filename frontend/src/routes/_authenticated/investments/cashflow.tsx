/**
 * Cash Flow Impact Page - /investments/cashflow
 *
 * Analyzes the cash flow impact of capital investments.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Download, TrendingUp, TrendingDown, Wallet, ArrowRight } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/investments/cashflow')({
  component: CashFlowPage,
})

function CashFlowPage() {
  const { selectedVersionId } = useVersion()

  const cashFlowCategories = [
    {
      title: 'Investment Outflows',
      icon: <TrendingDown className="w-5 h-5" />,
      description: 'Capital expenditure cash payments',
      color: 'text-red-600',
    },
    {
      title: 'Depreciation (Non-cash)',
      icon: <Wallet className="w-5 h-5" />,
      description: 'P&L expense, no cash impact',
      color: 'text-gray-600',
    },
    {
      title: 'Asset Sales',
      icon: <TrendingUp className="w-5 h-5" />,
      description: 'Proceeds from disposed assets',
      color: 'text-green-600',
    },
    {
      title: 'Net Impact',
      icon: <ArrowRight className="w-5 h-5" />,
      description: 'Total cash flow effect',
      color: 'text-blue-600',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Cash Flow Categories */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {cashFlowCategories.map((category) => (
              <Card key={category.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{category.title}</CardTitle>
                  <div className={`p-2 bg-teal-lighter rounded-lg ${category.color}`}>
                    {category.icon}
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{category.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Investment Cash Flow Analysis</CardTitle>
              <p className="text-sm text-gray-600">
                Analyze the timing and magnitude of cash flows from capital investments.
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Wallet className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Cash Flow Analysis</p>
                <p className="text-sm">
                  This page will display cash flow projections based on CapEx planning.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Cash Flow Concepts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">CapEx vs OpEx</h4>
                  <p className="text-gray-600">
                    Capital expenditure affects cash immediately but is recognized in the P&L over
                    time through depreciation. Operating expenses impact both cash and P&L in the
                    same period.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Free Cash Flow</h4>
                  <p className="text-gray-600">
                    Free Cash Flow = Operating Cash Flow - Capital Expenditures. This metric shows
                    available cash after maintaining/growing the asset base.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Payment Terms</h4>
                  <p className="text-gray-600">
                    Large purchases may have staged payments (e.g., 30% deposit, 40% on delivery,
                    30% after acceptance). Model timing accurately.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Working Capital Impact</h4>
                  <p className="text-gray-600">
                    Major investments may require additional working capital for operations. Include
                    in cash flow projections.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view cash flow analysis
        </div>
      )}
    </div>
  )
}
