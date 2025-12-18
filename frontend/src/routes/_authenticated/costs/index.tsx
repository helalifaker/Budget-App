/**
 * Cost Planning Module Dashboard - /costs
 *
 * Overview of all cost planning activities including personnel costs,
 * operating expenses, and overhead allocation.
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import { useVersion } from '@/contexts/VersionContext'
import { usePersonnelCosts, useOperatingCosts } from '@/hooks/api/useCosts'
import { DollarSign, Users, ShoppingCart, Building2, ArrowRight } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/costs/')({
  component: CostsIndexPage,
})

function CostsIndexPage() {
  const { selectedVersionId } = useVersion()
  const { data: personnelCosts, isLoading: loadingPersonnel } = usePersonnelCosts(
    selectedVersionId!
  )
  const { data: operatingCosts, isLoading: loadingOperating } = useOperatingCosts(
    selectedVersionId!
  )

  // Calculate summary metrics
  const personnelItems = personnelCosts || []
  const operatingItems = operatingCosts || []

  const totalPersonnel = personnelItems.reduce(
    (sum: number, item: { total_cost_sar?: number }) => sum + (item.total_cost_sar || 0),
    0
  )
  const totalOperating = operatingItems.reduce(
    (sum: number, item: { amount_sar?: number }) => sum + (item.amount_sar || 0),
    0
  )
  const totalCosts = totalPersonnel + totalOperating

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const isLoading = loadingPersonnel || loadingOperating

  const workflowItems = [
    {
      title: 'Personnel Costs',
      description: 'Salaries, benefits, GOSI, EOS calculated from DHG',
      href: '/costs/personnel',
      icon: <Users className="w-5 h-5" />,
      status: totalPersonnel > 0 ? 'complete' : 'pending',
    },
    {
      title: 'Operating Costs',
      description: 'Day-to-day operating expenses',
      href: '/costs/operating',
      icon: <ShoppingCart className="w-5 h-5" />,
      status: totalOperating > 0 ? 'complete' : 'pending',
    },
    {
      title: 'Overhead Allocation',
      description: 'Shared cost distribution across departments',
      href: '/costs/overhead',
      icon: <Building2 className="w-5 h-5" />,
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
              title="Total Costs"
              value={isLoading ? '...' : formatCurrency(totalCosts)}
              subtitle="Annual projected"
              icon={<DollarSign className="w-5 h-5" />}
              valueClassName="text-red-600"
            />
            <SummaryCard
              title="Personnel Costs"
              value={isLoading ? '...' : formatCurrency(totalPersonnel)}
              subtitle={
                totalCosts > 0
                  ? `${((totalPersonnel / totalCosts) * 100).toFixed(1)}% of total`
                  : '—'
              }
              icon={<Users className="w-5 h-5" />}
            />
            <SummaryCard
              title="Operating Costs"
              value={isLoading ? '...' : formatCurrency(totalOperating)}
              subtitle={
                totalCosts > 0
                  ? `${((totalOperating / totalCosts) * 100).toFixed(1)}% of total`
                  : '—'
              }
              icon={<ShoppingCart className="w-5 h-5" />}
            />
            <SummaryCard
              title="Personnel Ratio"
              value={totalCosts > 0 ? `${((totalPersonnel / totalCosts) * 100).toFixed(1)}%` : '—'}
              subtitle="Typical: 60-70%"
              icon={<Users className="w-5 h-5" />}
            />
          </div>

          {/* Workflow Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {workflowItems.map((item) => (
              <Link key={item.href} to={item.href}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-orange-lighter rounded-lg text-orange">
                        {item.icon}
                      </div>
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
              <CardTitle>Cost Planning Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Data Flow</h4>
                  <p className="text-gray-600">
                    Personnel costs are auto-calculated from DHG workforce planning. Changes to FTE
                    counts or salary parameters will automatically update cost projections.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Period Allocation</h4>
                  <p className="text-gray-600">
                    Costs are distributed across periods: P1 (Jan-Jun), Summer (Jul-Aug), P2
                    (Sep-Dec). Summer costs are typically lower for variable expenses.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view cost planning
        </div>
      )}
    </div>
  )
}
