/**
 * Trends Analysis Page - /insights/trends
 *
 * Historical trend analysis across key metrics.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Download, TrendingUp, Users, DollarSign, LineChart } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/insights/trends')({
  component: TrendsPage,
})

function TrendsPage() {
  const { selectedVersionId } = useVersion()

  const trendCategories = [
    {
      title: 'Enrollment Trends',
      icon: <Users className="w-5 h-5" />,
      description: 'Student count over time',
      metrics: ['Total Enrollment', 'New Students', 'Attrition Rate'],
    },
    {
      title: 'Financial Trends',
      icon: <DollarSign className="w-5 h-5" />,
      description: 'Revenue and cost evolution',
      metrics: ['Total Revenue', 'Total Costs', 'Operating Margin'],
    },
    {
      title: 'Efficiency Trends',
      icon: <TrendingUp className="w-5 h-5" />,
      description: 'Operational metrics over time',
      metrics: ['Cost per Student', 'Revenue per Student', 'Student:Teacher'],
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Analysis
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Trend Categories */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {trendCategories.map((category) => (
              <Card key={category.title}>
                <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-2">
                  <div className="p-2 bg-slate-lighter rounded-lg text-slate">{category.icon}</div>
                  <div>
                    <CardTitle className="text-base">{category.title}</CardTitle>
                    <p className="text-xs text-gray-500">{category.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.metrics.map((metric) => (
                      <li key={metric} className="text-sm text-gray-600 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-slate rounded-full" />
                        {metric}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Chart Area */}
          <Card>
            <CardHeader>
              <CardTitle>Historical Trends</CardTitle>
              <p className="text-sm text-gray-600">
                View multi-year trends for key performance indicators
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <LineChart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Trend Analysis</p>
                <p className="text-sm">
                  This page will display historical trend charts once data is available.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Trend Analysis Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Time Periods</h4>
                  <p className="text-gray-600">
                    Analyze trends across multiple fiscal years. Compare current budget to
                    historical actuals for context.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Growth Rates</h4>
                  <p className="text-gray-600">
                    View year-over-year and compound annual growth rates (CAGR) for enrollment,
                    revenue, and cost metrics.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Seasonality</h4>
                  <p className="text-gray-600">
                    Understand seasonal patterns in enrollment, revenue collection, and cost timing
                    throughout the fiscal year.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Forecasting</h4>
                  <p className="text-gray-600">
                    Use historical trends to inform future budget assumptions and validate
                    projection reasonableness.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view trend analysis
        </div>
      )}
    </div>
  )
}
