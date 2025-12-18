/**
 * Custom Reports Page - /insights/reports
 *
 * Create and run custom ad-hoc reports.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, FileText, Table, BarChart, PieChart } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/insights/reports')({
  component: ReportsPage,
})

function ReportsPage() {
  const { selectedVersionId } = useVersion()

  const reportTypes = [
    {
      title: 'Table Report',
      icon: <Table className="w-5 h-5" />,
      description: 'Tabular data with filters and grouping',
    },
    {
      title: 'Chart Report',
      icon: <BarChart className="w-5 h-5" />,
      description: 'Visual charts and graphs',
    },
    {
      title: 'Summary Report',
      icon: <PieChart className="w-5 h-5" />,
      description: 'Executive summary with KPIs',
    },
    {
      title: 'Custom Report',
      icon: <FileText className="w-5 h-5" />,
      description: 'Build your own report layout',
    },
  ]

  const savedReports = [
    { name: 'Monthly Enrollment Summary', type: 'Table', lastRun: '2024-12-15' },
    { name: 'Revenue by Grade Level', type: 'Chart', lastRun: '2024-12-14' },
    { name: 'Cost Center Analysis', type: 'Table', lastRun: '2024-12-10' },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          New Report
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Report Types */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {reportTypes.map((report) => (
              <Card key={report.title} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{report.title}</CardTitle>
                  <div className="p-2 bg-slate-lighter rounded-lg text-slate">{report.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{report.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Saved Reports */}
          <Card>
            <CardHeader>
              <CardTitle>Saved Reports</CardTitle>
              <p className="text-sm text-gray-600">Previously created reports you can run again</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {savedReports.map((report) => (
                  <div
                    key={report.name}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <FileText className="w-5 h-5 text-slate" />
                      <div>
                        <h4 className="font-medium">{report.name}</h4>
                        <p className="text-sm text-gray-600">
                          {report.type} • Last run: {report.lastRun}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">
                        Run
                      </Button>
                      <Button size="sm" variant="outline">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Report Builder Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Data Sources</h4>
                  <p className="text-gray-600">
                    Reports can pull data from enrollment, workforce, revenue, costs, and
                    investments. Select the modules relevant to your analysis.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Filters</h4>
                  <p className="text-gray-600">
                    Filter by fiscal year, period, grade level, department, cost center, or account
                    code to focus your analysis.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Grouping & Aggregation</h4>
                  <p className="text-gray-600">
                    Group data by dimensions and apply aggregations (sum, average, count) to create
                    meaningful summaries.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Scheduling</h4>
                  <p className="text-gray-600">
                    Save reports and schedule them to run automatically on a recurring basis with
                    email delivery.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to create reports
        </div>
      )}
    </div>
  )
}
