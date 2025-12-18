/**
 * Long-Term Planning Page - /strategic/long-term
 *
 * Multi-year strategic planning and projections.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, Calendar, TrendingUp, Target, LineChart } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/strategic/long-term')({
  component: LongTermPage,
})

function LongTermPage() {
  const { selectedVersionId } = useVersion()

  const planningHorizons = [
    {
      title: '3-Year Plan',
      icon: <Calendar className="w-5 h-5" />,
      description: 'Near-term operational planning',
      years: '2025-2027',
    },
    {
      title: '5-Year Plan',
      icon: <TrendingUp className="w-5 h-5" />,
      description: 'Medium-term strategic planning',
      years: '2025-2029',
    },
    {
      title: '10-Year Vision',
      icon: <Target className="w-5 h-5" />,
      description: 'Long-term institutional vision',
      years: '2025-2034',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          New Plan
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Planning Horizons */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {planningHorizons.map((horizon) => (
              <Card
                key={horizon.title}
                className="cursor-pointer hover:shadow-md transition-shadow"
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-lg">{horizon.title}</CardTitle>
                  <div className="p-2 bg-purple-lighter rounded-lg text-purple">{horizon.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-2">{horizon.description}</p>
                  <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-800">
                    {horizon.years}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Multi-Year Projections</CardTitle>
              <p className="text-sm text-gray-600">
                Develop long-term enrollment, revenue, and cost projections
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <LineChart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Long-Term Planning</p>
                <p className="text-sm">
                  This page will display multi-year projections once configured.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Planning Methodology</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Base Year Assumptions</h4>
                  <p className="text-gray-600">
                    Long-term projections extend from the current budget year using growth rates,
                    inflation factors, and strategic assumptions.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Enrollment Growth</h4>
                  <p className="text-gray-600">
                    Model student population growth considering capacity constraints, market demand,
                    and strategic enrollment targets.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Infrastructure Needs</h4>
                  <p className="text-gray-600">
                    Link enrollment growth to facility requirements, teacher hiring, and capital
                    investment needs.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Financial Sustainability</h4>
                  <p className="text-gray-600">
                    Ensure revenue projections support cost growth while maintaining target
                    operating margins and reserve levels.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view long-term planning
        </div>
      )}
    </div>
  )
}
