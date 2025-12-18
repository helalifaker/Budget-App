/**
 * Investments Module Dashboard - /investments
 *
 * Overview of capital expenditure and investment planning activities.
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import { useVersion } from '@/contexts/VersionContext'
import { useCapEx } from '@/hooks/api/useCapEx'
import { Building2, Laptop, Wrench, TrendingDown, ArrowRight } from 'lucide-react'

// Define typed interface for capex items
interface CapExItem {
  id: string
  description: string
  category: string
  account_code: string
  acquisition_date: string
  total_cost_sar: number
  useful_life_years: number
  annual_depreciation_sar: number
  notes?: string | null
}

export const Route = createFileRoute('/_authenticated/investments/')({
  component: InvestmentsIndexPage,
})

function InvestmentsIndexPage() {
  const { selectedVersionId } = useVersion()
  const { data: capexData, isLoading } = useCapEx(selectedVersionId!)

  const capexItems = (capexData || []) as CapExItem[]

  // Calculate summary metrics
  const totalCapEx = capexItems.reduce((sum, item) => sum + item.total_cost_sar, 0)
  const totalDepreciation = capexItems.reduce((sum, item) => sum + item.annual_depreciation_sar, 0)
  const equipmentCost = capexItems
    .filter((item) => item.category === 'EQUIPMENT')
    .reduce((sum, item) => sum + item.total_cost_sar, 0)
  const itCost = capexItems
    .filter((item) => item.category === 'IT')
    .reduce((sum, item) => sum + item.total_cost_sar, 0)

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const workflowItems = [
    {
      title: 'Capital Expenditure',
      description: 'Equipment, IT, furniture, and building improvements',
      href: '/investments/capex',
      icon: <Building2 className="w-5 h-5" />,
      status: capexItems.length > 0 ? 'complete' : 'pending',
    },
    {
      title: 'Project Budgets',
      description: 'Major project planning and budgeting',
      href: '/investments/projects',
      icon: <Wrench className="w-5 h-5" />,
      status: 'pending',
    },
    {
      title: 'Cash Flow Impact',
      description: 'Investment cash flow analysis',
      href: '/investments/cashflow',
      icon: <TrendingDown className="w-5 h-5" />,
      status: 'pending',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {selectedVersionId ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Total CapEx"
              value={isLoading ? '...' : formatCurrency(totalCapEx)}
              subtitle={`${capexItems.length} items`}
              icon={<Building2 className="w-5 h-5" />}
              valueClassName="text-teal-600"
            />
            <SummaryCard
              title="Annual Depreciation"
              value={isLoading ? '...' : formatCurrency(totalDepreciation)}
              subtitle="P&L impact"
              icon={<TrendingDown className="w-5 h-5" />}
            />
            <SummaryCard
              title="Equipment"
              value={isLoading ? '...' : formatCurrency(equipmentCost)}
              subtitle={
                totalCapEx > 0 ? `${((equipmentCost / totalCapEx) * 100).toFixed(1)}%` : '—'
              }
              icon={<Wrench className="w-5 h-5" />}
            />
            <SummaryCard
              title="IT & Software"
              value={isLoading ? '...' : formatCurrency(itCost)}
              subtitle={totalCapEx > 0 ? `${((itCost / totalCapEx) * 100).toFixed(1)}%` : '—'}
              icon={<Laptop className="w-5 h-5" />}
            />
          </div>

          {/* Workflow Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {workflowItems.map((item) => (
              <Link key={item.href} to={item.href}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-teal-lighter rounded-lg text-teal">{item.icon}</div>
                      <CardTitle className="text-lg">{item.title}</CardTitle>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">{item.description}</p>
                    <div className="mt-3">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          item.status === 'complete'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {item.status === 'complete' ? 'Data Available' : 'Not Started'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {/* Quick Info */}
          <Card>
            <CardHeader>
              <CardTitle>Investment Planning Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Depreciation Methods</h4>
                  <p className="text-gray-600">
                    Straight-line depreciation is used by default. Assets are depreciated over their
                    useful life, with annual expense recognized in the P&L.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Budget Impact</h4>
                  <p className="text-gray-600">
                    Capital expenditure affects cash flow immediately but impacts the P&L through
                    depreciation expense over the asset's useful life.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view investment planning
        </div>
      )}
    </div>
  )
}
