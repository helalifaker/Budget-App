/**
 * Other Revenue Page - /revenue/other
 *
 * Manages non-tuition revenue streams including transportation,
 * cafeteria, activities, and other services.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, Bus, UtensilsCrossed, Music, Package } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/revenue/other')({
  component: OtherRevenuePage,
})

function OtherRevenuePage() {
  const { selectedVersionId } = useVersion()

  const revenueCategories = [
    {
      title: 'Transportation',
      icon: <Bus className="w-5 h-5" />,
      accountCodes: '75100-75199',
      description: 'School bus and transport services',
    },
    {
      title: 'Cafeteria',
      icon: <UtensilsCrossed className="w-5 h-5" />,
      accountCodes: '75200-75299',
      description: 'Food services and meal plans',
    },
    {
      title: 'Activities',
      icon: <Music className="w-5 h-5" />,
      accountCodes: '75300-75399',
      description: 'After-school programs and clubs',
    },
    {
      title: 'Other Services',
      icon: <Package className="w-5 h-5" />,
      accountCodes: '76000-77999',
      description: 'Uniforms, supplies, events',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          Add Revenue Line
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Revenue Categories */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {revenueCategories.map((category) => (
              <Card key={category.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{category.title}</CardTitle>
                  <div className="p-2 bg-gold-lighter rounded-lg text-gold">{category.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-500 mb-2">{category.accountCodes}</p>
                  <p className="text-sm text-gray-600">{category.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Other Revenue Line Items</CardTitle>
              <p className="text-sm text-gray-600">
                Non-tuition revenue streams. These are typically manually entered based on
                historical data and projected service usage.
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Other Revenue Planning</p>
                <p className="text-sm">
                  This page will display non-tuition revenue items once data is available.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Categories Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Transportation (75100)</h4>
                  <p className="text-gray-600">
                    School bus services billed monthly or by trimester. Includes routes, stops, and
                    fuel cost adjustments.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Cafeteria (75200)</h4>
                  <p className="text-gray-600">
                    Meal plans and food services. Can be daily, weekly, or trimester-based billing
                    options.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Activities (75300)</h4>
                  <p className="text-gray-600">
                    After-school programs, sports, music, arts, and other extracurricular activities
                    with separate fees.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Other Services (76000-77000)</h4>
                  <p className="text-gray-600">
                    Uniforms, school supplies, special events, field trips, and miscellaneous
                    service fees.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view other revenue planning
        </div>
      )}
    </div>
  )
}
