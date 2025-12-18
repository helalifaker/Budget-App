/**
 * Reports & Exports Page - /consolidation/exports
 *
 * Generate and download budget reports and exports.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Download, FileText, FileSpreadsheet, Printer, Mail } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/consolidation/exports')({
  component: ExportsPage,
})

function ExportsPage() {
  const { selectedVersionId } = useVersion()

  const exportTypes = [
    {
      title: 'Budget Summary (PDF)',
      description: 'Executive summary with charts and key metrics',
      icon: <FileText className="w-5 h-5" />,
      format: 'PDF',
    },
    {
      title: 'Detailed Budget (Excel)',
      description: 'Complete budget with all line items',
      icon: <FileSpreadsheet className="w-5 h-5" />,
      format: 'XLSX',
    },
    {
      title: 'Financial Statements (PDF)',
      description: 'P&L, Balance Sheet, Cash Flow',
      icon: <FileText className="w-5 h-5" />,
      format: 'PDF',
    },
    {
      title: 'Board Presentation',
      description: 'Formatted for board review',
      icon: <Printer className="w-5 h-5" />,
      format: 'PDF',
    },
  ]

  const scheduledReports = [
    {
      title: 'Monthly Budget Report',
      frequency: 'Monthly',
      recipients: 'Finance Team',
      status: 'active',
    },
    {
      title: 'Quarterly Review',
      frequency: 'Quarterly',
      recipients: 'Executive Team',
      status: 'active',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Export Options */}
          <Card>
            <CardHeader>
              <CardTitle>Generate Reports</CardTitle>
              <p className="text-sm text-gray-600">Download budget reports in various formats</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exportTypes.map((export_type) => (
                  <div
                    key={export_type.title}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-blue-lighter rounded-lg text-blue">
                        {export_type.icon}
                      </div>
                      <div>
                        <h4 className="font-medium">{export_type.title}</h4>
                        <p className="text-sm text-gray-600">{export_type.description}</p>
                      </div>
                    </div>
                    <Button size="sm" variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      {export_type.format}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Scheduled Reports */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Scheduled Reports</CardTitle>
                <p className="text-sm text-gray-600">Automated report delivery</p>
              </div>
              <Button size="sm" variant="outline">
                <Mail className="w-4 h-4 mr-2" />
                New Schedule
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {scheduledReports.map((report) => (
                  <div
                    key={report.title}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div>
                      <h4 className="font-medium">{report.title}</h4>
                      <p className="text-sm text-gray-600">
                        {report.frequency} • {report.recipients}
                      </p>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        report.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {report.status === 'active' ? 'Active' : 'Paused'}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Export Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">PDF Reports</h4>
                  <p className="text-gray-600">
                    Formatted for presentation and printing. Includes charts, tables, and executive
                    summaries. Ideal for board meetings and stakeholder communication.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Excel Exports</h4>
                  <p className="text-gray-600">
                    Full data export with formulas preserved. Suitable for further analysis, custom
                    reporting, or import into other systems.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Scheduled Delivery</h4>
                  <p className="text-gray-600">
                    Set up automated report delivery via email. Reports are generated on schedule
                    and sent to designated recipients.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Data Privacy</h4>
                  <p className="text-gray-600">
                    Exported reports may contain sensitive financial data. Ensure proper handling
                    and distribution controls.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to generate reports
        </div>
      )}
    </div>
  )
}
