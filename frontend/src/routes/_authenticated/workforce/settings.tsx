/**
 * Workforce Settings - Overview
 *
 * Central hub for workforce configuration settings:
 * - Subject Hours: Teaching hours per subject per level
 * - Cost Parameters: Default salaries by category
 * - HSA Rates: Overtime configuration
 *
 * @module /workforce/settings
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Clock, DollarSign, BookOpen, ArrowRight } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/workforce/settings')({
  beforeLoad: requireAuth,
  component: WorkforceSettingsPage,
})

function WorkforceSettingsPage() {
  const settingsCards = [
    {
      title: 'Subject Hours',
      description: 'Configure teaching hours per subject per level for DHG calculation',
      icon: BookOpen,
      href: '/workforce/settings/subject-hours',
      color: 'gold',
      details: ['Hours per subject/level', 'Group size configs', 'Language sections'],
    },
    {
      title: 'Cost Parameters',
      description: 'Default salary parameters by employee category for placeholder positions',
      icon: DollarSign,
      href: '/workforce/settings/cost-parameters',
      color: 'sage',
      details: ['PRRD rates (EUR)', 'EUR/SAR exchange', 'Category averages'],
    },
    {
      title: 'HSA Rates',
      description: 'Overtime hours allocation and rates for teachers',
      icon: Clock,
      href: '/workforce/settings/hsa-rates',
      color: 'twilight',
      details: ['Max HSA hours', 'Hourly rates', 'HSA strategy'],
    },
  ]

  const colorClasses = {
    gold: {
      bg: 'bg-gold-100',
      text: 'text-gold-600',
      border: 'border-gold-200',
      hover: 'hover:border-gold-400',
    },
    sage: {
      bg: 'bg-sage-100',
      text: 'text-sage-600',
      border: 'border-sage-200',
      hover: 'hover:border-sage-400',
    },
    twilight: {
      bg: 'bg-twilight-100',
      text: 'text-text-secondary',
      border: 'border-twilight-200',
      hover: 'hover:border-twilight-400',
    },
  }

  return (
    <PageContainer
      title="Workforce Settings"
      description="Configure parameters for workforce planning and cost calculations"
    >
      <div className="space-y-6">
        {/* Header Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-gold-600" />
              Configuration Overview
            </CardTitle>
            <CardDescription>
              These settings control how DHG calculations, FTE requirements, and cost estimates are
              computed. Changes here affect placeholder position creation and gap analysis.
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Settings Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {settingsCards.map((card) => {
            const Icon = card.icon
            const colors = colorClasses[card.color as keyof typeof colorClasses]

            return (
              <Card
                key={card.href}
                className={`transition-all duration-200 ${colors.border} ${colors.hover}`}
              >
                <CardHeader>
                  <div
                    className={`w-12 h-12 rounded-lg ${colors.bg} flex items-center justify-center mb-3`}
                  >
                    <Icon className={`h-6 w-6 ${colors.text}`} />
                  </div>
                  <CardTitle className="text-lg">{card.title}</CardTitle>
                  <CardDescription>{card.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-text-secondary space-y-1 mb-4">
                    {card.details.map((detail, idx) => (
                      <li key={idx} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-twilight-400" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                  <Button asChild variant="outline" className="w-full gap-2">
                    <Link to={card.href}>
                      Configure
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Info Card */}
        <Card className="bg-subtle/50 border-border-light">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-gold-100 flex items-center justify-center flex-shrink-0">
                <Settings className="h-5 w-5 text-gold-600" />
              </div>
              <div>
                <h4 className="font-semibold text-text-primary mb-1">Settings Impact</h4>
                <p className="text-sm text-text-secondary">
                  These configuration values are used throughout the workforce module. Subject hours
                  feed into DHG calculations, cost parameters determine placeholder position
                  estimates, and HSA rates affect deficit resolution strategies.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
