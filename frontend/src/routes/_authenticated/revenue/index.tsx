/**
 * Revenue Module Dashboard - /revenue
 *
 * Overview of all revenue planning activities including tuition,
 * other revenue streams, and AEFE subsidies.
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import { useVersion } from '@/contexts/VersionContext'
import { useRevenuePivoted } from '@/hooks/api/useRevenue'
import { DollarSign, TrendingUp, GraduationCap, Building2, ArrowRight } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/revenue/')({
  component: RevenueIndexPage,
})

function RevenueIndexPage() {
  const { selectedVersionId } = useVersion()
  const { data: revenueItems = [], isLoading } = useRevenuePivoted(selectedVersionId!)

  // Calculate summary metrics
  const tuitionRevenue = revenueItems
    .filter((item) => item.account_code.startsWith('7011') || item.account_code.startsWith('7012'))
    .reduce((sum, item) => sum + item.annual_amount, 0)

  const enrollmentFees = revenueItems
    .filter((item) => item.account_code.startsWith('702'))
    .reduce((sum, item) => sum + item.annual_amount, 0)

  const otherRevenue = revenueItems
    .filter(
      (item) =>
        item.account_code.startsWith('75') ||
        item.account_code.startsWith('76') ||
        item.account_code.startsWith('77')
    )
    .reduce((sum, item) => sum + item.annual_amount, 0)

  const totalRevenue = tuitionRevenue + enrollmentFees + otherRevenue

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
      title: 'Tuition Revenue',
      description: 'Auto-calculated from enrollment × fee structure',
      href: '/revenue/tuition',
      icon: <GraduationCap className="w-5 h-5" />,
      status: tuitionRevenue > 0 ? 'complete' : 'pending',
    },
    {
      title: 'Other Revenue',
      description: 'Transportation, cafeteria, activities',
      href: '/revenue/other',
      icon: <TrendingUp className="w-5 h-5" />,
      status: otherRevenue > 0 ? 'complete' : 'pending',
    },
    {
      title: 'AEFE Subsidies',
      description: 'Government grants and contributions',
      href: '/revenue/subsidies',
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
              title="Total Revenue"
              value={isLoading ? '...' : formatCurrency(totalRevenue)}
              subtitle="Annual projected"
              icon={<DollarSign className="w-5 h-5" />}
              valueClassName="text-green-600"
            />
            <SummaryCard
              title="Tuition Revenue"
              value={isLoading ? '...' : formatCurrency(tuitionRevenue)}
              subtitle={
                totalRevenue > 0
                  ? `${((tuitionRevenue / totalRevenue) * 100).toFixed(1)}% of total`
                  : '—'
              }
              icon={<GraduationCap className="w-5 h-5" />}
            />
            <SummaryCard
              title="Enrollment Fees"
              value={isLoading ? '...' : formatCurrency(enrollmentFees)}
              subtitle={
                totalRevenue > 0
                  ? `${((enrollmentFees / totalRevenue) * 100).toFixed(1)}% of total`
                  : '—'
              }
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <SummaryCard
              title="Other Revenue"
              value={isLoading ? '...' : formatCurrency(otherRevenue)}
              subtitle={
                totalRevenue > 0
                  ? `${((otherRevenue / totalRevenue) * 100).toFixed(1)}% of total`
                  : '—'
              }
              icon={<Building2 className="w-5 h-5" />}
            />
          </div>

          {/* Workflow Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {workflowItems.map((item) => (
              <Link key={item.href} to={item.href}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gold-lighter rounded-lg text-gold">{item.icon}</div>
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
              <CardTitle>Revenue Planning Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Data Flow</h4>
                  <p className="text-gray-600">
                    Tuition revenue is auto-calculated from Enrollment Planning × Fee Structure.
                    Changes to enrollment or fees will automatically update revenue projections.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Trimester Split</h4>
                  <p className="text-gray-600">
                    Revenue is distributed across trimesters: T1 (40%), T2 (30%), T3 (30%). This
                    follows the school year payment schedule.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view revenue planning
        </div>
      )}
    </div>
  )
}
