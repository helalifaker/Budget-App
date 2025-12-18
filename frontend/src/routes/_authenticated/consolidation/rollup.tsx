/**
 * Budget Rollup Page - /consolidation/rollup
 *
 * Consolidates all budget inputs from different modules into
 * a unified budget view.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Play, RefreshCw, CheckCircle, AlertCircle, Layers } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/consolidation/rollup')({
  component: RollupPage,
})

function RollupPage() {
  const { selectedVersionId } = useVersion()

  const rollupSources = [
    {
      title: 'Enrollment',
      description: 'Student projections and class structure',
      status: 'ready',
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
    },
    {
      title: 'Workforce',
      description: 'DHG and FTE requirements',
      status: 'ready',
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
    },
    {
      title: 'Revenue',
      description: 'Tuition and other revenue',
      status: 'ready',
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
    },
    {
      title: 'Costs',
      description: 'Personnel and operating costs',
      status: 'pending',
      icon: <AlertCircle className="w-5 h-5 text-amber-600" />,
    },
    {
      title: 'Investments',
      description: 'CapEx and depreciation',
      status: 'pending',
      icon: <AlertCircle className="w-5 h-5 text-amber-600" />,
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button variant="outline" disabled={!selectedVersionId}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Sources
        </Button>
        <Button disabled={!selectedVersionId}>
          <Play className="w-4 h-4 mr-2" />
          Run Consolidation
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Source Status */}
          <Card>
            <CardHeader>
              <CardTitle>Data Sources</CardTitle>
              <p className="text-sm text-gray-600">
                Status of input data from each planning module
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {rollupSources.map((source) => (
                  <div
                    key={source.title}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      {source.icon}
                      <div>
                        <h4 className="font-medium">{source.title}</h4>
                        <p className="text-sm text-gray-600">{source.description}</p>
                      </div>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        source.status === 'ready'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {source.status === 'ready' ? 'Ready' : 'Pending'}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Rollup Status */}
          <Card>
            <CardHeader>
              <CardTitle>Consolidation Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Layers className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Budget Rollup</p>
                <p className="text-sm mb-4">
                  Consolidate data from all modules to create unified budget
                </p>
                <Button disabled={!selectedVersionId}>
                  <Play className="w-4 h-4 mr-2" />
                  Start Consolidation
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Consolidation Process</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Data Collection</h4>
                  <p className="text-gray-600">
                    The consolidation process collects data from all planning modules: enrollment
                    counts, workforce FTEs, revenue projections, cost plans, and investment
                    schedules.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Validation</h4>
                  <p className="text-gray-600">
                    Before rollup, data is validated for consistency. Any discrepancies between
                    modules are flagged for review.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Account Mapping</h4>
                  <p className="text-gray-600">
                    Each line item is mapped to the chart of accounts for proper classification in
                    financial statements.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Period Allocation</h4>
                  <p className="text-gray-600">
                    Annual amounts are distributed across periods based on configured allocation
                    rules (trimester or monthly).
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view budget rollup
        </div>
      )}
    </div>
  )
}
