/**
 * Revenue Settings Page - /revenue/settings
 *
 * Module-specific configuration for revenue planning including
 * trimester splits, discount rules, and calculation parameters.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Save, Settings, Percent, Calendar, Euro } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/revenue/settings')({
  component: RevenueSettingsPage,
})

function RevenueSettingsPage() {
  const { selectedVersionId } = useVersion()

  const settingsCategories = [
    {
      title: 'Trimester Distribution',
      icon: <Calendar className="w-5 h-5" />,
      description: 'Configure payment split across trimesters',
      items: ['T1: 40%', 'T2: 30%', 'T3: 30%'],
    },
    {
      title: 'Sibling Discounts',
      icon: <Percent className="w-5 h-5" />,
      description: 'Family discount rules',
      items: ['2nd child: 10%', '3rd+ child: 25%'],
    },
    {
      title: 'Exchange Rates',
      icon: <Euro className="w-5 h-5" />,
      description: 'Currency conversion for AEFE grants',
      items: ['EUR/SAR: 4.05 (default)'],
    },
    {
      title: 'Calculation Rules',
      icon: <Settings className="w-5 h-5" />,
      description: 'Revenue calculation parameters',
      items: ['Auto-recalculate on enrollment change'],
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
                  <div className="p-2 bg-gold-lighter rounded-lg text-gold">{category.icon}</div>
                  <div>
                    <CardTitle className="text-base">{category.title}</CardTitle>
                    <p className="text-xs text-gray-500">{category.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.items.map((item) => (
                      <li key={item} className="text-sm text-gray-600 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-gold rounded-full" />
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
              <CardTitle>Configuration Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Revenue Calculation Flow</h4>
                  <p className="text-gray-600">
                    1. Enrollment counts from Enrollment Planning
                    <br />
                    2. × Fee rates from Global Settings → Fee Structure
                    <br />
                    3. − Sibling discounts (configured here)
                    <br />
                    4. = Tuition revenue by trimester
                    <br />
                    5. + Other revenue (manual entries)
                    <br />
                    6. = Total revenue projection
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">When to Recalculate</h4>
                  <p className="text-gray-600">
                    Revenue is automatically recalculated when enrollment projections change. Manual
                    recalculation is available if you've updated fee structures or discount rules.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to configure revenue settings
        </div>
      )}
    </div>
  )
}
