/**
 * Command Center - Executive Cockpit Landing Page
 *
 * Compact, viewport-fit design with:
 * - KPI grid showing key metrics
 * - Compact module cards with progress bars
 * - Quick actions row
 *
 * Note: Navigation (SmartHeader + ModuleDock) is provided by _authenticated.tsx layout
 * This page only renders content - NO CockpitLayout wrapper here!
 *
 * Theme: EFIR Premium with enhanced shadow depth
 */

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { motion } from 'framer-motion'
import { MODULES, MODULE_ORDER, type ModuleId, type ModuleStatus } from '@/contexts/ModuleContext'
import { cn } from '@/lib/utils'
import {
  Users,
  GraduationCap,
  BarChart3,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  Plus,
  RefreshCw,
  FileText,
} from 'lucide-react'

export const Route = createFileRoute('/_authenticated/command-center')({
  component: CommandCenterPage,
})

/**
 * Module metrics data
 */
interface ModuleMetrics {
  status: ModuleStatus
  progress: number
  primaryMetric: {
    label: string
    value: string
    trend?: 'up' | 'down' | 'neutral'
    trendValue?: string
  }
  secondaryMetrics?: Array<{
    label: string
    value: string
  }>
  attentionCount: number
}

const mockModuleMetrics: Record<ModuleId, ModuleMetrics> = {
  'command-center': {
    status: 'healthy',
    progress: 100,
    primaryMetric: { label: 'Overview', value: 'Active' },
    attentionCount: 0,
  },
  enrollment: {
    status: 'healthy',
    progress: 100,
    primaryMetric: {
      label: 'Total Students',
      value: '1,245',
      trend: 'up',
      trendValue: '+3.2%',
    },
    secondaryMetrics: [
      { label: 'Classes', value: '48' },
      { label: 'Avg Size', value: '24.8' },
    ],
    attentionCount: 0,
  },
  workforce: {
    status: 'attention',
    progress: 75,
    primaryMetric: {
      label: 'Total Staff',
      value: '123',
      trend: 'up',
      trendValue: '+5',
    },
    secondaryMetrics: [
      { label: 'AEFE Filled', value: '22/28' },
      { label: 'Teachers', value: '98 FTE' },
    ],
    attentionCount: 2,
  },
  revenue: {
    status: 'healthy',
    progress: 85,
    primaryMetric: {
      label: 'Total Revenue',
      value: '45.2M',
      trend: 'up',
      trendValue: '+2.1%',
    },
    secondaryMetrics: [
      { label: 'Tuition', value: '42.8M' },
      { label: 'Other', value: '2.4M' },
    ],
    attentionCount: 0,
  },
  costs: {
    status: 'warning',
    progress: 60,
    primaryMetric: {
      label: 'Total Costs',
      value: '45.3M',
      trend: 'up',
      trendValue: '+3.5%',
    },
    secondaryMetrics: [
      { label: 'Personnel', value: '38.2M' },
      { label: 'Operating', value: '7.1M' },
    ],
    attentionCount: 2,
  },
  investments: {
    status: 'healthy',
    progress: 70,
    primaryMetric: {
      label: 'CapEx',
      value: '2.5M',
      trend: 'neutral',
    },
    secondaryMetrics: [
      { label: 'Projects', value: '5' },
      { label: 'Approved', value: '3' },
    ],
    attentionCount: 0,
  },
  consolidation: {
    status: 'warning',
    progress: 50,
    primaryMetric: {
      label: 'Budget Balance',
      value: '-120K',
      trend: 'down',
      trendValue: 'Deficit',
    },
    secondaryMetrics: [
      { label: 'Revenue', value: '45.2M' },
      { label: 'Costs', value: '45.3M' },
    ],
    attentionCount: 3,
  },
  insights: {
    status: 'healthy',
    progress: 100,
    primaryMetric: {
      label: 'H/E Ratio',
      value: '1.42',
      trend: 'neutral',
    },
    secondaryMetrics: [
      { label: 'E/D', value: '24.8' },
      { label: 'Cost/Student', value: '36.4K' },
    ],
    attentionCount: 0,
  },
  strategic: {
    status: 'healthy',
    progress: 40,
    primaryMetric: {
      label: 'Scenarios',
      value: '3',
      trend: 'neutral',
    },
    secondaryMetrics: [
      { label: 'Active', value: '1' },
      { label: 'Draft', value: '2' },
    ],
    attentionCount: 0,
  },
  settings: {
    status: 'healthy',
    progress: 100,
    primaryMetric: {
      label: 'Configuration',
      value: 'Active',
    },
    secondaryMetrics: [
      { label: 'Versions', value: '3' },
      { label: 'Updated', value: 'Today' },
    ],
    attentionCount: 0,
  },
  admin: {
    status: 'healthy',
    progress: 100,
    primaryMetric: {
      label: 'System',
      value: 'Healthy',
    },
    secondaryMetrics: [
      { label: 'Users', value: '5' },
      { label: 'Imports', value: '0 pending' },
    ],
    attentionCount: 0,
  },
}

/**
 * Get status color classes using EFIR palette
 */
function getStatusColor(status: ModuleStatus): {
  badge: string
  progress: string
  dot: string
} {
  switch (status) {
    case 'healthy':
      return {
        badge: 'bg-[var(--efir-accent-sage-light)] text-[var(--efir-accent-sage)]',
        progress: 'bg-[var(--efir-accent-sage)]',
        dot: 'bg-[var(--efir-accent-sage)]',
      }
    case 'attention':
      return {
        badge: 'bg-[var(--efir-accent-gold-light)] text-[var(--efir-accent-gold)]',
        progress: 'bg-[var(--efir-accent-gold)]',
        dot: 'bg-[var(--efir-accent-gold)]',
      }
    case 'warning':
      return {
        badge: 'bg-[var(--efir-accent-terracotta-light)] text-[var(--efir-accent-terracotta)]',
        progress: 'bg-[var(--efir-accent-terracotta)]',
        dot: 'bg-[var(--efir-accent-terracotta)]',
      }
    case 'error':
      return {
        badge: 'bg-[var(--efir-accent-wine-light)] text-[var(--efir-accent-wine)]',
        progress: 'bg-[var(--efir-accent-wine)]',
        dot: 'bg-[var(--efir-accent-wine)]',
      }
    default:
      return {
        badge: 'bg-[var(--efir-accent-slate)]/10 text-[var(--efir-accent-slate)]',
        progress: 'bg-[var(--efir-accent-slate)]',
        dot: 'bg-[var(--efir-accent-slate)]',
      }
  }
}

/**
 * KPI Card Component - EFIR Theme
 */
interface KPICardProps {
  label: string
  value: string
  unit: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  accentColor?: string
}

function KPICard({
  label,
  value,
  unit,
  trend,
  trendValue,
  accentColor = 'var(--efir-accent-gold)',
}: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative overflow-hidden',
        'bg-[var(--efir-bg-paper)] rounded-xl',
        'border border-[var(--efir-border-light)]',
        'p-4',
        'shadow-[var(--shadow-depth-2)]',
        'hover:shadow-[var(--shadow-depth-3)]',
        'transition-shadow duration-200'
      )}
    >
      {/* Accent bar */}
      <div
        className="absolute top-0 left-0 right-0 h-[3px]"
        style={{ background: `linear-gradient(90deg, ${accentColor}, ${accentColor}80)` }}
      />

      <div className="text-sm uppercase tracking-wider text-[var(--efir-text-tertiary)] font-medium mb-2">
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-display font-bold text-[var(--efir-text-primary)]">
          {value}
        </span>
        <span className="text-base text-[var(--efir-text-muted)]">{unit}</span>
      </div>
      {trend && trendValue && (
        <div
          className={cn(
            'flex items-center gap-1.5 text-sm mt-3 font-medium',
            trend === 'up' && 'text-[var(--efir-accent-sage)]',
            trend === 'down' && 'text-[var(--efir-accent-terracotta)]',
            trend === 'neutral' && 'text-[var(--efir-text-tertiary)]'
          )}
        >
          {trend === 'up' && <TrendingUp className="w-4 h-4" />}
          {trend === 'down' && <TrendingDown className="w-4 h-4" />}
          {trendValue}
        </div>
      )}
    </motion.div>
  )
}

/**
 * Compact Module Card Component - EFIR Theme
 */
function CompactModuleCard({ moduleId }: { moduleId: ModuleId }) {
  const module = MODULES[moduleId]
  const metrics = mockModuleMetrics[moduleId]
  const colors = getStatusColor(metrics.status)

  // Use module icons directly from the MODULES definition
  const Icon = module.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: MODULE_ORDER.indexOf(moduleId) * 0.05 }}
    >
      <Link to={module.basePath}>
        <div
          className={cn(
            'relative overflow-hidden',
            'bg-[var(--efir-bg-paper)] rounded-xl',
            'border border-[var(--efir-border-light)]',
            'p-4',
            'shadow-[var(--shadow-depth-2)]',
            'hover:shadow-[var(--shadow-depth-3)]',
            'hover:border-[var(--efir-border-medium)]',
            'transition-all duration-200',
            'cursor-pointer group'
          )}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div
                className={cn('w-9 h-9 rounded-lg flex items-center justify-center', colors.badge)}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-[var(--efir-text-primary)]">
                  {module.label}
                </h3>
                <div className="text-xs text-[var(--efir-text-tertiary)]">
                  {metrics.progress}% complete
                </div>
              </div>
            </div>

            {/* Status indicator */}
            <div className={cn('w-2.5 h-2.5 rounded-full', colors.dot)} />
          </div>

          {/* Progress bar */}
          <div className="h-1.5 bg-[var(--efir-bg-subtle)] rounded-full overflow-hidden mb-3">
            <div
              className={cn('h-full rounded-full transition-all duration-500', colors.progress)}
              style={{ width: `${metrics.progress}%` }}
            />
          </div>

          {/* Primary metric */}
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-sm text-[var(--efir-text-tertiary)]">
              {metrics.primaryMetric.label}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-display font-bold text-[var(--efir-text-primary)]">
                {metrics.primaryMetric.value}
              </span>
              {metrics.primaryMetric.trend && (
                <span
                  className={cn(
                    'text-xs font-medium',
                    metrics.primaryMetric.trend === 'up' && 'text-[var(--efir-accent-sage)]',
                    metrics.primaryMetric.trend === 'down' &&
                      'text-[var(--efir-accent-terracotta)]',
                    metrics.primaryMetric.trend === 'neutral' && 'text-[var(--efir-text-tertiary)]'
                  )}
                >
                  {metrics.primaryMetric.trendValue}
                </span>
              )}
            </div>
          </div>

          {/* Secondary metrics */}
          {metrics.secondaryMetrics && (
            <div className="flex gap-4 pt-3 border-t border-[var(--efir-border-light)]">
              {metrics.secondaryMetrics.map((metric) => (
                <div key={metric.label} className="flex-1">
                  <div className="text-xs text-[var(--efir-text-muted)]">{metric.label}</div>
                  <div className="text-sm font-semibold text-[var(--efir-text-secondary)]">
                    {metric.value}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Hover arrow */}
          <div
            className={cn(
              'absolute bottom-3 right-3',
              'opacity-0 group-hover:opacity-100',
              'transition-opacity duration-150'
            )}
          >
            <ChevronRight className="w-4 h-4 text-[var(--efir-accent-gold)]" />
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

/**
 * Quick Action Button - EFIR Theme
 */
interface QuickActionProps {
  icon: typeof Users
  label: string
  onClick?: () => void
}

function QuickActionButton({ icon: Icon, label, onClick }: QuickActionProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2.5 px-5 py-2.5',
        'bg-[var(--efir-bg-paper)] rounded-lg',
        'border border-[var(--efir-border-light)]',
        'text-sm font-medium text-[var(--efir-text-secondary)]',
        'shadow-[var(--shadow-depth-1)]',
        'hover:shadow-[var(--shadow-depth-2)]',
        'hover:border-[var(--efir-border-medium)]',
        'hover:text-[var(--efir-text-primary)]',
        'transition-all duration-150'
      )}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  )
}

/**
 * Main Command Center Page - Content Only
 * NO CockpitLayout wrapper - navigation is provided by _authenticated.tsx
 */
function CommandCenterPage() {
  const navigate = useNavigate()
  const displayModules = MODULE_ORDER.filter((id) => id !== 'command-center')

  return (
    <div className="p-6 space-y-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      {/* KPI Grid */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--efir-text-tertiary)] mb-4">
          Key Performance Indicators
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Total Budget"
            value="48.5M"
            unit="SAR"
            trend="up"
            trendValue="+2.3% YoY"
            accentColor="var(--efir-accent-gold)"
          />
          <KPICard
            label="Net Result"
            value="-120K"
            unit="SAR"
            trend="down"
            trendValue="Deficit"
            accentColor="var(--efir-accent-terracotta)"
          />
          <KPICard
            label="Enrollment"
            value="1,245"
            unit="Students"
            trend="up"
            trendValue="+3.2%"
            accentColor="var(--efir-accent-sage)"
          />
          <KPICard
            label="Staff Count"
            value="123"
            unit="FTE"
            trend="neutral"
            trendValue="Stable"
            accentColor="var(--efir-accent-slate)"
          />
        </div>
      </section>

      {/* Planning Modules */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--efir-text-tertiary)] mb-4">
          Planning Modules
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {displayModules.map((moduleId) => (
            <CompactModuleCard key={moduleId} moduleId={moduleId} />
          ))}
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--efir-text-tertiary)] mb-4">
          Quick Actions
        </h3>
        <div className="flex flex-wrap gap-3">
          <QuickActionButton
            icon={Plus}
            label="Add Employee"
            onClick={() => navigate({ to: '/workforce/employees' })}
          />
          <QuickActionButton
            icon={GraduationCap}
            label="Update Enrollment"
            onClick={() => navigate({ to: '/enrollment/projections' })}
          />
          <QuickActionButton
            icon={RefreshCw}
            label="Run DHG"
            onClick={() => navigate({ to: '/workforce/dhg' })}
          />
          <QuickActionButton
            icon={FileText}
            label="View Reports"
            onClick={() => navigate({ to: '/consolidation/statements' })}
          />
          <QuickActionButton
            icon={BarChart3}
            label="KPI Dashboard"
            onClick={() => navigate({ to: '/insights/kpis' })}
          />
        </div>
      </section>
    </div>
  )
}
