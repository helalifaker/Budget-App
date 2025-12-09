/**
 * Workforce Settings - Subject Hours Configuration
 *
 * Configure hours per subject per level for DHG calculation:
 * - Secondary: 18h/week standard teaching load
 * - Primary: 24h/week standard teaching load
 * - Subject-specific hours by level
 *
 * @module /workforce/settings/subject-hours
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, BookOpen, GraduationCap, Settings } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/settings/subject-hours')({
  beforeLoad: requireAuth,
  component: SubjectHoursSettingsPage,
})

function SubjectHoursSettingsPage() {
  return (
    <PageContainer
      title="Subject Hours Configuration"
      description="Configure teaching hours per subject per level for DHG calculation"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Subjects Configured</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-gold-600" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Active subjects</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Secondary Standard</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Clock className="h-5 w-5 text-sage-600" />
                <span>18h/week</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Collège + Lycée</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Primary Standard</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Clock className="h-5 w-5 text-text-secondary" />
                <span>24h/week</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Maternelle + Élémentaire</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Levels</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-terracotta-600" />
                <span>--</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Academic levels</p>
            </CardContent>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <Settings className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Subject Hours Configuration
            </h3>
            <p className="text-sm text-text-secondary text-center max-w-md mb-4">
              Configure teaching hours per subject per level. This data feeds into DHG calculations
              for teacher FTE requirements.
            </p>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• Hours per subject per academic level</li>
              <li>• Group size configurations (full class, half class, etc.)</li>
              <li>• Special education hours allocation</li>
              <li>• Language section hours (anglophone, etc.)</li>
            </ul>
            <p className="mt-4 text-xs text-text-tertiary">
              Note: This will migrate from /configuration/subject-hours
            </p>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
