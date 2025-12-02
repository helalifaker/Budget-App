import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { KPICard } from '@/components/KPICard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useKPIs } from '@/hooks/api/useAnalysis'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export const Route = createFileRoute('/analysis/kpis')({
  component: KPIsPage,
})

function KPIsPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')

  const { data: kpis, isLoading } = useKPIs(selectedVersionId)

  // Prepare benchmark comparison chart data
  const benchmarkData = kpis?.map((kpi) => ({
    name: kpi.title,
    value: kpi.value,
    min: kpi.benchmark_min || 0,
    max: kpi.benchmark_max || 0,
  }))

  return (
    <MainLayout>
      <PageContainer
        title="Key Performance Indicators"
        description="Monitor budget performance metrics and benchmarks"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Analysis', href: '/analysis/kpis' },
          { label: 'KPIs' },
        ]}
      >
        <div className="space-y-6">
          {/* Version Selector */}
          <BudgetVersionSelector
            value={selectedVersionId}
            onChange={setSelectedVersionId}
            showCreateButton={false}
          />

          {selectedVersionId && (
            <>
              {/* KPI Grid */}
              {isLoading ? (
                <div className="text-center py-12">Loading KPIs...</div>
              ) : kpis && kpis.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {kpis.map((kpi) => (
                      <KPICard
                        key={kpi.id}
                        title={kpi.title}
                        value={kpi.value}
                        unit={kpi.unit}
                        benchmark={
                          kpi.benchmark_min && kpi.benchmark_max
                            ? { min: kpi.benchmark_min, max: kpi.benchmark_max }
                            : undefined
                        }
                        trend={
                          kpi.trend
                            ? (kpi.trend.toLowerCase() as 'up' | 'down' | 'stable')
                            : undefined
                        }
                        status={kpi.status.toLowerCase() as 'good' | 'warning' | 'alert'}
                        previousValue={kpi.previous_value || undefined}
                      />
                    ))}
                  </div>

                  {/* Benchmark Comparison Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Benchmark Comparison</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart
                          data={benchmarkData}
                          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="value" fill="#3B82F6" name="Actual Value" />
                          <Bar dataKey="min" fill="#10B981" name="Min Benchmark" />
                          <Bar dataKey="max" fill="#EF4444" name="Max Benchmark" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* KPI Definitions */}
                  <Card>
                    <CardHeader>
                      <CardTitle>KPI Definitions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4 text-sm">
                        <div>
                          <h4 className="font-semibold">H/E Ratio (Hours/Student)</h4>
                          <p className="text-gray-600">
                            Total teaching hours divided by total students. Benchmark: 1.1-1.3 for
                            primary, 1.3-1.5 for secondary.
                          </p>
                        </div>
                        <div>
                          <h4 className="font-semibold">E/D Ratio (Students/Class)</h4>
                          <p className="text-gray-600">
                            Average class size. Target: 20-25 students per class.
                          </p>
                        </div>
                        <div>
                          <h4 className="font-semibold">Cost per Student</h4>
                          <p className="text-gray-600">
                            Total costs divided by total students. Monitor for efficiency.
                          </p>
                        </div>
                        <div>
                          <h4 className="font-semibold">Operating Margin</h4>
                          <p className="text-gray-600">
                            (Revenue - Costs) / Revenue. Target: 5-10% for sustainability.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    No KPI data available. Please consolidate the budget first.
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
