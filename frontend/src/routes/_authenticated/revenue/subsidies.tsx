/**
 * AEFE Subsidies Page - /revenue/subsidies
 *
 * Manages government grants, AEFE contributions, and other subsidies.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, Building2, Euro, FileText, Calculator } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/revenue/subsidies')({
  component: SubsidiesPage,
})

function SubsidiesPage() {
  const { selectedVersionId } = useVersion()

  const subsidyTypes = [
    {
      title: 'AEFE Operating Grant',
      icon: <Building2 className="w-5 h-5" />,
      description: 'Annual operating contribution from AEFE',
      accountCode: '74100',
    },
    {
      title: 'Teacher Subsidies (PRRD)',
      icon: <Euro className="w-5 h-5" />,
      description: '~41,863 EUR per seconded teacher',
      accountCode: '74200',
    },
    {
      title: 'Capital Grants',
      icon: <FileText className="w-5 h-5" />,
      description: 'Grants for construction and equipment',
      accountCode: '74300',
    },
    {
      title: 'Other Contributions',
      icon: <Calculator className="w-5 h-5" />,
      description: 'Ministry of Education, local grants',
      accountCode: '74900',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          Add Subsidy
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Subsidy Types */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {subsidyTypes.map((subsidy) => (
              <Card key={subsidy.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{subsidy.title}</CardTitle>
                  <div className="p-2 bg-gold-lighter rounded-lg text-gold">{subsidy.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-500 mb-2">Account: {subsidy.accountCode}</p>
                  <p className="text-sm text-gray-600">{subsidy.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>AEFE & Government Subsidies</CardTitle>
              <p className="text-sm text-gray-600">
                Track government grants, AEFE contributions, and other institutional funding.
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Subsidies & Grants</p>
                <p className="text-sm">
                  This page will display subsidy data once configured in the system.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>AEFE Funding Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">PRRD (Teacher Contribution)</h4>
                  <p className="text-gray-600">
                    AEFE provides approximately €41,863 per year for each seconded French teacher
                    (détaché). This covers the difference between local and French salary scales.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Operating Grant</h4>
                  <p className="text-gray-600">
                    Annual operating grant based on student enrollment and school classification.
                    Amount varies by school type and agreement with AEFE.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Capital Support</h4>
                  <p className="text-gray-600">
                    Available for major construction, renovation, or equipment purchases. Requires
                    formal application and approval process.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Currency Conversion</h4>
                  <p className="text-gray-600">
                    AEFE grants paid in EUR must be converted to SAR. Use the configured exchange
                    rate in Settings for consistent projections.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view subsidies planning
        </div>
      )}
    </div>
  )
}
