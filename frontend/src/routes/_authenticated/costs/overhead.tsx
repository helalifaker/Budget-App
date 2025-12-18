/**
 * Overhead Allocation Page - /costs/overhead
 *
 * Manages shared cost distribution across departments and cost centers.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, Building2, PieChart, Calculator, Settings } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/costs/overhead')({
  component: OverheadPage,
})

function OverheadPage() {
  const { selectedVersionId } = useVersion()

  const allocationMethods = [
    {
      title: 'Direct Allocation',
      icon: <Building2 className="w-5 h-5" />,
      description: 'Costs directly assigned to departments',
    },
    {
      title: 'Square Meter',
      icon: <PieChart className="w-5 h-5" />,
      description: 'Allocated based on floor space',
    },
    {
      title: 'Headcount',
      icon: <Calculator className="w-5 h-5" />,
      description: 'Allocated based on FTE count',
    },
    {
      title: 'Custom Formula',
      icon: <Settings className="w-5 h-5" />,
      description: 'User-defined allocation rules',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          Add Allocation Rule
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Allocation Methods */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {allocationMethods.map((method) => (
              <Card key={method.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{method.title}</CardTitle>
                  <div className="p-2 bg-orange-lighter rounded-lg text-orange">{method.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{method.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Overhead Allocation Rules</CardTitle>
              <p className="text-sm text-gray-600">
                Define how shared costs are distributed across departments and cost centers.
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Overhead Allocation</p>
                <p className="text-sm">
                  This page will display overhead allocation rules once configured.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Allocation Methods Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Direct Allocation</h4>
                  <p className="text-gray-600">
                    Used when costs can be directly traced to specific departments or activities. No
                    allocation formula needed.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Square Meter Basis</h4>
                  <p className="text-gray-600">
                    Ideal for facility costs (rent, utilities, maintenance). Costs distributed
                    proportionally to floor space occupied.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Headcount Basis</h4>
                  <p className="text-gray-600">
                    Best for HR-related costs, IT support, and general administration. Based on
                    number of employees in each department.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Custom Formula</h4>
                  <p className="text-gray-600">
                    For complex allocations requiring multiple drivers or weighted combinations of
                    different allocation bases.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view overhead allocation
        </div>
      )}
    </div>
  )
}
