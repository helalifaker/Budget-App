/**
 * Scenario Modeling Page - /strategic/scenarios
 *
 * What-if scenario modeling and sensitivity analysis.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, GitBranch, TrendingUp, TrendingDown, Minus } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/strategic/scenarios')({
  component: ScenariosPage,
})

function ScenariosPage() {
  const { selectedVersionId } = useVersion()

  const scenarioTypes = [
    {
      title: 'Best Case',
      icon: <TrendingUp className="w-5 h-5 text-green-600" />,
      description: 'Optimistic growth assumptions',
      color: 'bg-green-100 text-green-800',
    },
    {
      title: 'Base Case',
      icon: <Minus className="w-5 h-5 text-blue-600" />,
      description: 'Most likely scenario',
      color: 'bg-blue-100 text-blue-800',
    },
    {
      title: 'Worst Case',
      icon: <TrendingDown className="w-5 h-5 text-red-600" />,
      description: 'Conservative/stress scenario',
      color: 'bg-red-100 text-red-800',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          New Scenario
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Comparison
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Scenario Types */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {scenarioTypes.map((scenario) => (
              <Card
                key={scenario.title}
                className="cursor-pointer hover:shadow-md transition-shadow"
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-lg">{scenario.title}</CardTitle>
                  <div className="p-2 bg-purple-lighter rounded-lg">{scenario.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-2">{scenario.description}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${scenario.color}`}>
                    View Scenario
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Scenario Comparison</CardTitle>
              <p className="text-sm text-gray-600">
                Compare key metrics across different scenarios
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <GitBranch className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Scenario Modeling</p>
                <p className="text-sm">This page will display scenario comparisons once created.</p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Scenario Planning Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Key Variables</h4>
                  <p className="text-gray-600">
                    Scenarios typically vary: enrollment growth rate, fee increases, salary
                    inflation, exchange rates, and major project timing.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Sensitivity Analysis</h4>
                  <p className="text-gray-600">
                    Test how sensitive results are to individual assumptions. Identify which
                    variables have the biggest impact on outcomes.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Monte Carlo Simulation</h4>
                  <p className="text-gray-600">
                    For advanced analysis, run multiple simulations with randomized inputs to
                    understand probability distributions of outcomes.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Stress Testing</h4>
                  <p className="text-gray-600">
                    Model extreme scenarios (enrollment decline, major cost increase) to ensure
                    financial resilience and adequate reserves.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view scenario modeling
        </div>
      )}
    </div>
  )
}
