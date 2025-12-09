/**
 * Workforce Settings - HSA (Overtime) Configuration
 *
 * Configure HSA (Heures Supplémentaires Annuelles) overtime rules:
 * - Maximum hours per teacher (typically 2-4 hours/week)
 * - HSA hourly rates by category
 * - HSA usage strategy (before/after hiring)
 *
 * @module /workforce/settings/hsa-rates
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, DollarSign, Users, TrendingUp } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/settings/hsa-rates')({
  beforeLoad: requireAuth,
  component: HSARatesPage,
})

function HSARatesPage() {
  return (
    <PageContainer
      title="HSA (Overtime) Configuration"
      description="Configure overtime hours allocation and rates for teachers"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Max HSA Hours</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Clock className="h-5 w-5 text-gold-600" />
                <span>4h/week</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Per teacher maximum</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>AEFE HSA Rate</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-sage-600" />
                <span>-- EUR</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Per hour</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Local HSA Rate</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-text-secondary" />
                <span>-- SAR</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Per hour</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Teachers with HSA</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Users className="h-5 w-5 text-terracotta-600" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Eligible teachers</p>
            </CardContent>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <TrendingUp className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              HSA (Overtime) Configuration
            </h3>
            <p className="text-sm text-text-secondary text-center max-w-md mb-4">
              Heures Supplémentaires Annuelles (Annual Overtime Hours) configuration for handling
              DHG deficits:
            </p>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• Maximum HSA hours per teacher (typically 2-4h/week)</li>
              <li>• HSA hourly rates by employee category</li>
              <li>• Strategy: Use HSA before or after hiring decision</li>
              <li>• Total HSA budget allocation</li>
            </ul>

            {/* HSA Formula Reference */}
            <div className="mt-6 p-4 bg-white rounded-xl border border-border-light max-w-md">
              <p className="text-sm font-medium text-text-primary mb-2">HSA Cost Calculation:</p>
              <div className="text-xs text-text-secondary space-y-1 font-mono bg-subtle p-3 rounded-lg">
                <p>Total HSA Cost = Hours × Rate × 36 weeks</p>
                <p className="mt-2">Example (AEFE):</p>
                <p>2h/week × 45 EUR × 36 = 3,240 EUR/year</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
