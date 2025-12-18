/**
 * Workforce - FTE Requirements
 *
 * Teacher FTE requirements calculated from DHG:
 * - FTE = Total Hours / Standard Teaching Hours (18h secondary, 24h primary)
 * - Subject-by-subject breakdown
 * - HSA (overtime) allocation
 *
 * @module /teachers/dhg/requirements
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ClipboardList, Users, Clock } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/requirements')({
  beforeLoad: requireAuth,
  component: FTERequirementsPage,
})

function FTERequirementsPage() {
  return (
    <PageContainer
      title="FTE Requirements"
      description="Teacher Full-Time Equivalent requirements calculated from DHG hours"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total FTE Required</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Users className="h-5 w-5 text-gold-600" />
                <span>-- FTE</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">All subjects</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Secondary (18h)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-sage-600" />
                <span>-- FTE</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Collège + Lycée</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Primary (24h)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-text-secondary" />
                <span>-- FTE</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Maternelle + Élémentaire</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>HSA Hours</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Clock className="h-5 w-5 text-terracotta-600" />
                <span>-- h</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Overtime allocation</p>
            </CardContent>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <ClipboardList className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">FTE Requirements</h3>
            <p className="text-sm text-text-secondary text-center max-w-md mb-4">
              Calculate teacher FTE requirements from DHG hours:
            </p>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• Secondary: 18 hours/week standard teaching load</li>
              <li>• Primary: 24 hours/week standard teaching load</li>
              <li>• HSA: Maximum 4 hours/week overtime per teacher</li>
              <li>• Formula: FTE = Total Hours ÷ Standard Hours</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
