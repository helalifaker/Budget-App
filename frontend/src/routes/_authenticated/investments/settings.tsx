/**
 * Investment Settings Page - /investments/settings
 *
 * Module-specific configuration for investment planning including
 * depreciation methods, useful life defaults, and capitalization thresholds.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Save, Settings, Calendar, DollarSign, Percent } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/investments/settings')({
  component: InvestmentSettingsPage,
})

function InvestmentSettingsPage() {
  const { selectedVersionId } = useVersion()

  const settingsCategories = [
    {
      title: 'Depreciation Methods',
      icon: <Calendar className="w-5 h-5" />,
      description: 'Default depreciation calculations',
      items: ['Straight Line (default)', 'Declining Balance (20%)', 'Units of Production'],
    },
    {
      title: 'Capitalization Threshold',
      icon: <DollarSign className="w-5 h-5" />,
      description: 'Minimum amount for CapEx treatment',
      items: ['Min. SAR 5,000', 'Min. useful life: 1 year'],
    },
    {
      title: 'Default Useful Lives',
      icon: <Percent className="w-5 h-5" />,
      description: 'Asset category defaults',
      items: [
        'Equipment: 7 years',
        'IT Hardware: 4 years',
        'Furniture: 10 years',
        'Software: 3 years',
      ],
    },
    {
      title: 'Approval Rules',
      icon: <Settings className="w-5 h-5" />,
      description: 'Authorization thresholds',
      items: ['< SAR 50K: Manager', '< SAR 200K: Director', '> SAR 200K: Board'],
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
                  <div className="p-2 bg-teal-lighter rounded-lg text-teal">{category.icon}</div>
                  <div>
                    <CardTitle className="text-base">{category.title}</CardTitle>
                    <p className="text-xs text-gray-500">{category.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.items.map((item) => (
                      <li key={item} className="text-sm text-gray-600 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-teal rounded-full" />
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
              <CardTitle>Investment Accounting Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Capitalization Rules</h4>
                  <p className="text-gray-600">
                    Items meeting the capitalization threshold are recorded as assets on the balance
                    sheet and depreciated over their useful life. Items below threshold are expensed
                    immediately as operating costs.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Depreciation Start Date</h4>
                  <p className="text-gray-600">
                    Depreciation begins when asset is placed in service (ready for use), not on
                    purchase date. Pro-rate first year based on months in service.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Impairment Review</h4>
                  <p className="text-gray-600">
                    Review asset values annually for impairment. Write down book value if
                    recoverable amount is less than carrying amount.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to configure investment settings
        </div>
      )}
    </div>
  )
}
