/* eslint-disable react-refresh/only-export-components */
/**
 * TaskDescription - Contextual Task Help Text
 *
 * New UI redesign component (Phase 2) providing contextual descriptions
 * for each workflow step/tab.
 *
 * Layout:
 * - Height: 32px (var(--description-line-height))
 * - Muted text (text-tertiary)
 * - 1-2 lines maximum, truncated if longer
 *
 * Features:
 * - Automatic description based on current route
 * - Can be overridden with prop
 * - Graceful fallback for unknown routes
 */

import { useLocation } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { getTypographyClasses } from '@/styles/typography'

/**
 * Tab descriptions mapping - provides contextual help for each page
 * Based on UI_REDESIGN_PLAN.md Phase 3.2 specifications
 */
export const TAB_DESCRIPTIONS: Record<string, string> = {
  // Command Center
  '/': 'Welcome to EFIR Budget Planning. Select a module to begin.',
  '/command-center': 'Your budget planning hub. Quick access to all modules and recent activity.',
  '/dashboard': 'Overview of your budget planning progress and key metrics.',

  // Students Module (Enrollment)
  '/students': 'Manage student enrollment projections and class structure.',
  '/students/planning': 'Enter enrollment projections by grade level for the budget year.',
  '/students/class-structure': 'Configure classes per level based on enrollment numbers.',
  '/students/validation': 'Review and validate your enrollment plan before proceeding.',
  '/students/settings': 'Configure class size parameters and enrollment rules.',

  // Teachers Module (Workforce)
  '/teachers': 'Manage employees, salaries, and teaching hour allocations.',
  '/teachers/employees': 'View and manage staff roster, contracts, and employment details.',
  '/teachers/salaries': 'Configure salary grids and compensation structures.',
  '/teachers/aefe-positions': 'Manage AEFE detached and funded positions.',
  '/teachers/dhg': 'Plan teaching hours by subject and level (DHG).',
  '/teachers/dhg/planning': 'Plan teaching hours by subject and level (DHG).',
  '/teachers/dhg/requirements': 'Calculate FTE requirements based on DHG hours.',
  '/teachers/dhg/gap-analysis': 'Compare available staff against requirements (TRMD).',
  '/teachers/settings': 'Configure subject hours and teacher cost parameters.',

  // Finance Module
  '/finance': 'Plan revenue, costs, and view financial consolidation.',
  '/finance/revenue': 'Plan tuition fees, registration fees, and other revenue streams.',
  '/finance/costs': 'Budget personnel, operations, and other expense categories.',
  '/finance/capex': 'Plan capital expenditure projects and investments.',
  '/finance/consolidation': 'Consolidate all budget inputs into a unified view.',
  '/finance/statements': 'View consolidated financial statements (PCG/IFRS formats).',
  '/finance/settings': 'Configure fee structures and financial parameters.',

  // Insights Module (Analysis)
  '/insights': 'Analyze KPIs, view dashboards, and compare variances.',
  '/insights/kpis': 'Monitor key performance indicators across all budget areas.',
  '/insights/dashboards': 'Visual dashboards showing budget health and trends.',
  '/insights/variance': 'Compare budget versus actual performance by period.',

  // Strategic Module
  '/strategic': 'Develop long-term financial projections and strategic plans.',

  // Settings Module (Configuration)
  '/settings': 'System-wide settings, version management, and data imports.',
  '/settings/versions': 'Manage versions and fiscal year configurations.',
  '/settings/class-sizes': 'Configure class size parameters by cycle.',
  '/settings/subject-hours': 'Define teaching hours by subject and level.',
  '/settings/teacher-costs': 'Configure teacher cost rates by category.',
  '/settings/fees': 'Configure fee structures and tuition rates.',
  '/settings/uploads': 'Import historical data and external files.',
  '/settings/system': 'Configure system-wide application settings.',

  // Admin (legacy route)
  '/admin/historical-import': 'Import historical data from Excel files.',
}

/**
 * Get the best matching description for a given pathname
 * Handles exact matches and prefix-based fallbacks
 */
function getDescriptionForPath(pathname: string): string {
  // Try exact match first
  if (TAB_DESCRIPTIONS[pathname]) {
    return TAB_DESCRIPTIONS[pathname]
  }

  // Try without trailing slash
  const withoutTrailingSlash = pathname.endsWith('/') ? pathname.slice(0, -1) : pathname
  if (TAB_DESCRIPTIONS[withoutTrailingSlash]) {
    return TAB_DESCRIPTIONS[withoutTrailingSlash]
  }

  // Try parent path (for dynamic routes)
  const parentPath = pathname.split('/').slice(0, -1).join('/')
  if (parentPath && TAB_DESCRIPTIONS[parentPath]) {
    return TAB_DESCRIPTIONS[parentPath]
  }

  // Try module root
  const moduleRoot = '/' + pathname.split('/')[1]
  if (TAB_DESCRIPTIONS[moduleRoot]) {
    return TAB_DESCRIPTIONS[moduleRoot]
  }

  // Default fallback
  return 'Configure and manage your budget data.'
}

interface TaskDescriptionProps {
  /** Override the automatic description */
  description?: string
  /** Additional CSS classes */
  className?: string
}

export function TaskDescription({ description, className }: TaskDescriptionProps) {
  const location = useLocation()

  // Use provided description or auto-detect from route
  const displayDescription = description ?? getDescriptionForPath(location.pathname)

  return (
    <div
      className={cn(
        // Height
        'h-[var(--description-line-height)]',
        // Layout
        'flex items-center',
        'px-4 lg:px-6',
        // Background - subtle, different from tabs
        'bg-subtle/30',
        // No bottom border - flows into content
        className
      )}
    >
      <p
        className={cn(
          getTypographyClasses('description'),
          // Truncation for long text
          'truncate',
          // Max width for readability
          'max-w-3xl'
        )}
      >
        {displayDescription}
      </p>
    </div>
  )
}

export default TaskDescription
