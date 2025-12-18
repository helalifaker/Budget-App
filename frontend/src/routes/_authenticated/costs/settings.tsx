/**
 * Cost Settings Page - /costs/settings
 *
 * Module-specific configuration for cost planning including
 * calculation rules, allocation parameters, and period distributions.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Save, Settings, Percent, Calendar, Calculator } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/costs/settings')({
  component: CostSettingsPage,
})

function CostSettingsPage() {
  const { selectedVersionId } = useVersion()

  const settingsCategories = [
    {
      title: 'Period Distribution',
      icon: <Calendar className="w-5 h-5" />,
      description: 'Cost allocation across periods',
      items: ['P1 (Jan-Jun): 50%', 'Summer (Jul-Aug): 17%', 'P2 (Sep-Dec): 33%'],
    },
    {
      title: 'GOSI Parameters',
      icon: <Percent className="w-5 h-5" />,
      description: 'Social insurance rates',
      items: ['Employer: 12%', 'Employee: 10%', 'Max salary: SAR 45,000'],
    },
    {
      title: 'EOS Calculation',
      icon: <Calculator className="w-5 h-5" />,
      description: 'End of service gratuity rules',
      items: ['0-5 years: 0.5 month/year', '5+ years: 1 month/year'],
    },
    {
      title: 'Recalculation Rules',
      icon: <Settings className="w-5 h-5" />,
      description: 'Auto-calculation triggers',
      items: ['On DHG FTE change', 'On salary update'],
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Settings Categories */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {settingsCategories.map((category) => (
              <Card key={category.title}>
                <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-2">
                  <div className="p-2 bg-orange-lighter rounded-lg text-orange">
                    {category.icon}
                  </div>
                  <div>
                    <CardTitle className="text-base">{category.title}</CardTitle>
                    <p className="text-xs text-gray-500">{category.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.items.map((item) => (
                      <li key={item} className="text-sm text-gray-600 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-orange rounded-full" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Configuration Note */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Calculation Flow</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Personnel Cost Calculation</h4>
                  <p className="text-gray-600">
                    1. FTE counts from DHG Workforce Planning
                    <br />
                    2. × Salary scales from Teacher Cost Parameters
                    <br />
                    3. + GOSI employer contribution (12%)
                    <br />
                    4. + EOS accrual (based on tenure)
                    <br />
                    5. + AEFE contribution (for seconded teachers)
                    <br />
                    6. = Total personnel costs
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Operating Cost Planning</h4>
                  <p className="text-gray-600">
                    Operating costs are typically based on historical data with inflation
                    adjustments. Use prior year actuals as baseline and apply growth rates for
                    projections.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to configure cost settings
        </div>
      )}
    </div>
  )
}
