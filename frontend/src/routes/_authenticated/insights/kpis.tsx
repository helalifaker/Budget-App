import { createFileRoute } from '@tanstack/react-router'
import { PageContainer } from '@/components/layout/PageContainer'
import { KPICard } from '@/components/KPICard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useKPIs } from '@/hooks/api/useAnalysis'
import { useVersion } from '@/contexts/VersionContext'
import {
  BarChartLazy,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from '@/components/charts/ChartsLazy'

export const Route = createFileRoute('/_authenticated/insights/kpis')({
  component: KPIsPage,
})

function KPIsPage() {
  const { selectedVersionId } = useVersion()

  const { data: kpis, isLoading } = useKPIs(selectedVersionId)

  // Prepare benchmark comparison chart data
  const benchmarkData = kpis?.map((kpi) => ({
    name: kpi.title,
    value: kpi.value,
    min: kpi.benchmark_min || 0,
    max: kpi.benchmark_max || 0,
  }))

  return (
    <PageContainer
      title="Key Performance Indicators"
      description="Monitor budget performance metrics and benchmarks"
      compactHeader
    >
      <div className="space-y-5">
        {selectedVersionId && (
          <>
            {/* KPI Grid - Premium Layout */}
            {isLoading ? (
              <div className="text-center py-12 text-text-secondary">Loading KPIs...</div>
            ) : kpis && kpis.length > 0 ? (
              <>
                <div data-testid="kpi-grid" className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                  {kpis.map((kpi) => (
                    <div
                      key={kpi.id}
                      data-testid={`kpi-${kpi.title.toLowerCase().replace(/[^a-z0-9]/g, `-`)}`}
                    >
                      <KPICard
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
                        compact
                      />
                    </div>
                  ))}
                </div>

                {/* Benchmark Comparison Chart - Premium Styling */}
                <Card>
                  <CardHeader>
                    <CardTitle>Benchmark Comparison</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChartLazy
                        data={benchmarkData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                        <XAxis
                          dataKey="name"
                          angle={-45}
                          textAnchor="end"
                          height={100}
                          stroke="var(--color-text-tertiary)"
                        />
                        <YAxis stroke="var(--color-text-tertiary)" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'var(--color-paper)',
                            border: '1px solid var(--color-border-light)',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <Bar
                          dataKey="value"
                          fill="var(--color-gold)"
                          name="Actual Value"
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="min"
                          fill="var(--color-sage)"
                          name="Min Benchmark"
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="max"
                          fill="var(--color-terracotta)"
                          name="Max Benchmark"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChartLazy>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* KPI Definitions - Premium Card */}
                <Card accent>
                  <CardHeader>
                    <CardTitle>KPI Definitions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div className="p-3 rounded-lg bg-subtle/50">
                        <h4 className="font-semibold text-text-primary">
                          H/E Ratio (Hours/Student)
                        </h4>
                        <p className="text-text-secondary mt-1">
                          Total teaching hours divided by total students. Benchmark: 1.1-1.3 for
                          primary, 1.3-1.5 for secondary.
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-subtle/50">
                        <h4 className="font-semibold text-text-primary">
                          E/D Ratio (Students/Class)
                        </h4>
                        <p className="text-text-secondary mt-1">
                          Average class size. Target: 20-25 students per class.
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-subtle/50">
                        <h4 className="font-semibold text-text-primary">Cost per Student</h4>
                        <p className="text-text-secondary mt-1">
                          Total costs divided by total students. Monitor for efficiency.
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-subtle/50">
                        <h4 className="font-semibold text-text-primary">Operating Margin</h4>
                        <p className="text-text-secondary mt-1">
                          (Revenue - Costs) / Revenue. Target: 5-10% for sustainability.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-12 text-text-secondary">
                  No KPI data available. Please consolidate the budget first.
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </PageContainer>
  )
}
