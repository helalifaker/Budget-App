/**
 * Workforce Settings - Cost Parameters
 *
 * Configure default cost parameters by employee category:
 * - AEFE Detached: PRRD rate (~41,863 EUR)
 * - AEFE Funded: Zero cost
 * - Local Teachers: Average salary by category
 * - Administrative: Average salary by role
 * - Support Staff: Average salary by role
 *
 * @module /teachers/settings/cost-parameters
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DollarSign, BadgeEuro, Users, Briefcase } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/settings/cost-parameters')({
  beforeLoad: requireAuth,
  component: CostParametersPage,
})

function CostParametersPage() {
  return (
    <PageContainer
      title="Cost Parameters"
      description="Default salary parameters by employee category for placeholder positions"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>PRRD Rate (EUR)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BadgeEuro className="h-5 w-5 text-gold-600" />
                <span>41,863</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Per detached position</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>EUR/SAR Rate</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-sage-600" />
                <span>4.05</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Exchange rate</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Teacher Salary</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Users className="h-5 w-5 text-text-secondary" />
                <span>-- SAR</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Local teachers</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Admin Salary</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-terracotta-600" />
                <span>-- SAR</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Administrative staff</p>
            </CardContent>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <DollarSign className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Cost Parameters Configuration
            </h3>
            <p className="text-sm text-text-secondary text-center max-w-md mb-4">
              Configure default salary parameters used when creating placeholder positions from DHG
              gap analysis:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-text-secondary">
              <div className="p-3 bg-white rounded-lg border border-border-light">
                <p className="font-semibold mb-1">AEFE Positions</p>
                <ul className="space-y-1 text-xs">
                  <li>• PRRD rate (EUR)</li>
                  <li>• EUR/SAR exchange rate</li>
                </ul>
              </div>
              <div className="p-3 bg-white rounded-lg border border-border-light">
                <p className="font-semibold mb-1">Local Staff</p>
                <ul className="space-y-1 text-xs">
                  <li>• Category averages</li>
                  <li>• Allowance percentages</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
