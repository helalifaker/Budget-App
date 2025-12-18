/**
 * Strategic Targets Page - /strategic/targets
 *
 * Define and track strategic KPI targets.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, Target, Users, DollarSign, Percent } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/strategic/targets')({
  component: TargetsPage,
})

function TargetsPage() {
  const { selectedVersionId } = useVersion()

  const targetCategories = [
    {
      title: 'Enrollment Targets',
      icon: <Users className="w-5 h-5" />,
      description: 'Student growth and retention goals',
      metrics: ['Total Students', 'Growth Rate', 'Retention Rate'],
    },
    {
      title: 'Financial Targets',
      icon: <DollarSign className="w-5 h-5" />,
      description: 'Revenue and margin objectives',
      metrics: ['Revenue Growth', 'Operating Margin', 'Reserve Ratio'],
    },
    {
      title: 'Quality Targets',
      icon: <Target className="w-5 h-5" />,
      description: 'Educational quality indicators',
      metrics: ['Student:Teacher Ratio', 'Satisfaction Score', 'Pass Rate'],
    },
    {
      title: 'Efficiency Targets',
      icon: <Percent className="w-5 h-5" />,
      description: 'Operational efficiency goals',
      metrics: ['Cost per Student', 'Personnel %', 'Capacity Utilization'],
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          Add Target
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Target Categories */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {targetCategories.map((category) => (
              <Card key={category.title}>
                <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-2">
                  <div className="p-2 bg-purple-lighter rounded-lg text-purple">
                    {category.icon}
                  </div>
                  <div>
                    <CardTitle className="text-base">{category.title}</CardTitle>
                    <p className="text-xs text-gray-500">{category.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.metrics.map((metric) => (
                      <li key={metric} className="text-sm text-gray-600 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-purple rounded-full" />
                        {metric}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Target Performance</CardTitle>
              <p className="text-sm text-gray-600">Track progress toward strategic targets</p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Strategic Targets</p>
                <p className="text-sm">
                  This page will display target tracking once targets are configured.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Target Setting Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">SMART Targets</h4>
                  <p className="text-gray-600">
                    Targets should be Specific, Measurable, Achievable, Relevant, and Time-bound.
                    Avoid vague or unrealistic goals.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Cascading Goals</h4>
                  <p className="text-gray-600">
                    Strategic targets should cascade down to department-level objectives and
                    individual performance metrics.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Balanced Scorecard</h4>
                  <p className="text-gray-600">
                    Include targets across multiple dimensions: financial, customer/student,
                    internal processes, and learning/growth.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Review Cadence</h4>
                  <p className="text-gray-600">
                    Review target progress quarterly. Annual targets should be set during the
                    strategic planning cycle.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view strategic targets
        </div>
      )}
    </div>
  )
}
