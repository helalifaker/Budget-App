/**
 * Workforce - DHG Planning
 *
 * Dotation Horaire Globale (Global Hours Allocation) planning:
 * - Subject hours per level configuration
 * - Total hours calculation
 * - Teaching hours overview
 *
 * @module /workforce/dhg/planning
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Calculator, Clock, BookOpen, GraduationCap } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/dhg/planning')({
  beforeLoad: requireAuth,
  component: DHGPlanningPage,
})

function DHGPlanningPage() {
  return (
    <PageContainer
      title="DHG Planning"
      description="Dotation Horaire Globale - Global hours allocation and teaching load calculation"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Hours/Week</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Clock className="h-5 w-5 text-gold-600" />
                <span>-- h</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">All subjects combined</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Subjects</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-sage-600" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Configured subjects</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Levels</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-text-secondary" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Academic levels</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Classes</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Calculator className="h-5 w-5 text-terracotta-600" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">From class structure</p>
            </CardContent>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <Calculator className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">DHG Planning</h3>
            <p className="text-sm text-text-secondary text-center max-w-md">
              Calculate teaching hours based on class structure and subject hours configuration.
              This data flows from the Enrollment module&apos;s class structure.
            </p>
            <div className="mt-4 text-xs text-text-tertiary">
              Formula: Total Hours = Classes × Hours per Subject per Level
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
