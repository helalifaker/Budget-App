import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { SummaryCard } from '@/components/SummaryCard'
import { ActivityFeed } from '@/components/ActivityFeed'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useDashboardSummary, useRecentActivity, useSystemAlerts } from '@/hooks/api/useAnalysis'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import {
  Users,
  School,
  GraduationCap,
  DollarSign,
  AlertCircle,
  Info,
  TrendingUp,
} from 'lucide-react'

export const Route = createFileRoute('/analysis/dashboards')({
  beforeLoad: requireAuth,
  component: AnalysisDashboardPage,
})

function AnalysisDashboardPage() {
  const { selectedVersionId } = useBudgetVersion()

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary(selectedVersionId)
  const { data: activity } = useRecentActivity(8)
  const { data: alerts } = useSystemAlerts(selectedVersionId)

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value)

  const alertColors = {
    INFO: 'bg-blue-100 text-blue-800 border-blue-200',
    WARNING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    ERROR: 'bg-red-100 text-red-800 border-red-200',
  }

  const alertIcons = {
    INFO: <Info className="w-4 h-4" />,
    WARNING: <AlertCircle className="w-4 h-4" />,
    ERROR: <AlertCircle className="w-4 h-4" />,
  }

  return (
    <MainLayout>
      <PageContainer
        title="Dashboards"
        description="Visualize consolidated metrics, alerts, and recent activity for the selected version"
        breadcrumbs={[{ label: 'Analysis', href: '/analysis/kpis' }, { label: 'Dashboards' }]}
      >
        <div className="space-y-6">
          {selectedVersionId && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {summaryLoading ? (
                  <div className="col-span-5 text-center py-6 text-sand-700">
                    Chargement du résumé...
                  </div>
                ) : summary ? (
                  <>
                    <SummaryCard
                      title="Étudiants"
                      value={summary.total_students?.toLocaleString() || '0'}
                      icon={<Users className="w-5 h-5" />}
                      subtitle="Effectifs consolidés"
                    />
                    <SummaryCard
                      title="Classes"
                      value={summary.total_classes?.toLocaleString() || '0'}
                      icon={<School className="w-5 h-5" />}
                      subtitle="Ouvertes"
                    />
                    <SummaryCard
                      title="Enseignants"
                      value={summary.total_teachers_fte?.toLocaleString() || '0'}
                      icon={<GraduationCap className="w-5 h-5" />}
                      subtitle="FTE"
                    />
                    <SummaryCard
                      title="Revenus"
                      value={formatCurrency(summary.total_revenue_sar)}
                      icon={<DollarSign className="w-5 h-5" />}
                      valueClassName="text-green-700"
                    />
                    <SummaryCard
                      title="Coûts"
                      value={formatCurrency(summary.total_costs_sar)}
                      icon={<DollarSign className="w-5 h-5" />}
                      valueClassName="text-red-600"
                    />
                  </>
                ) : null}
              </div>

              {alerts && alerts.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Alertes système</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border ${alertColors[alert.type]}`}
                      >
                        {alertIcons[alert.type]}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{alert.message}</p>
                          <p className="text-xs mt-1 opacity-75">
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  {activity && activity.length > 0 ? (
                    <ActivityFeed activities={activity} />
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-sand-700">
                        Aucune activité récente.
                      </CardContent>
                    </Card>
                  )}
                </div>
                <Card>
                  <CardHeader className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <CardTitle>Marges</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {summary ? (
                      <>
                        <div className="flex items-center justify-between text-sm">
                          <span>Résultat net</span>
                          <span
                            className={
                              summary.net_result_sar >= 0
                                ? 'text-green-700 font-semibold'
                                : 'text-red-600 font-semibold'
                            }
                          >
                            {formatCurrency(summary.net_result_sar)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>Marge opérationnelle</span>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">
                              {summary.operating_margin_pct.toFixed(1)}%
                            </span>
                            <Badge
                              variant={
                                summary.operating_margin_pct >= 5 ? 'default' : 'destructive'
                              }
                            >
                              {summary.operating_margin_pct >= 5 ? 'Saine' : 'Sous cible'}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>Coût par étudiant</span>
                          <span className="font-semibold">
                            {formatCurrency(
                              summary.total_students > 0
                                ? summary.total_costs_sar / summary.total_students
                                : 0
                            )}
                          </span>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-sand-700">
                        Sélectionnez une version pour voir les marges.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
