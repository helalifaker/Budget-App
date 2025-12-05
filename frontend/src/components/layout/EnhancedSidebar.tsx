/**
 * EnhancedSidebar
 *
 * A luxuriously styled sidebar with:
 * - Live quick stats for each module
 * - Collapsible sections with smooth animations
 * - Premium "Sahara Luxe" light theme styling
 * - Active state indicators with gold accents
 * - Hover effects and micro-interactions
 */

import { useState, useCallback } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { usePrefetchRoute } from '@/hooks/usePrefetchRoute'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useModuleStats } from '@/hooks/useSidebarStats'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  GraduationCap,
  Users,
  Wallet,
  Building2,
  PieChart,
  Settings,
  Target,
  ChevronDown,
  FileText,
  Clock,
  DollarSign,
  Calculator,
  Truck,
  BarChart3,
  LineChart,
  GitCompare,
  CalendarCog,
  BookOpen,
  UserCog,
  Receipt,
} from 'lucide-react'

/**
 * Navigation structure with new information architecture
 */
const navigation = [
  {
    id: 'dashboard',
    name: 'Command Center',
    href: '/dashboard',
    icon: LayoutDashboard,
    statKey: null,
    description: 'Overview & Quick Actions',
  },
  {
    id: 'enrollment',
    name: 'Enrollment',
    icon: GraduationCap,
    statKey: 'enrollment',
    description: 'Student planning',
    children: [
      { name: 'Planning', href: '/planning/enrollment', icon: Users },
      { name: 'Class Structure', href: '/planning/classes', icon: BookOpen },
    ],
  },
  {
    id: 'workforce',
    name: 'Workforce',
    icon: Users,
    statKey: 'workforce',
    description: 'DHG & Teacher FTE',
    children: [
      { name: 'DHG Planning', href: '/planning/dhg', icon: Calculator },
      { name: 'Planning Guide', href: '/planning/guide', icon: FileText },
    ],
  },
  {
    id: 'costs',
    name: 'Costs',
    icon: Wallet,
    statKey: 'costs',
    description: 'Personnel & Operating',
    children: [
      { name: 'Cost Planning', href: '/planning/costs', icon: Receipt },
      { name: 'Revenue', href: '/planning/revenue', icon: DollarSign },
    ],
  },
  {
    id: 'investment',
    name: 'Investment',
    icon: Building2,
    statKey: 'investment',
    description: 'Capital Expenditure',
    children: [{ name: 'CapEx Planning', href: '/planning/capex', icon: Truck }],
  },
  {
    id: 'financial',
    name: 'Financial',
    icon: PieChart,
    statKey: 'financial',
    description: 'Budget & Statements',
    children: [
      { name: 'Budget Review', href: '/consolidation/budget', icon: BarChart3 },
      { name: 'Statements', href: '/consolidation/statements', icon: FileText },
      { name: 'KPIs', href: '/analysis/kpis', icon: LineChart },
      { name: 'Dashboards', href: '/analysis/dashboards', icon: LayoutDashboard },
      { name: 'Variance', href: '/analysis/variance', icon: GitCompare },
    ],
  },
  {
    id: 'configuration',
    name: 'Configuration',
    icon: Settings,
    statKey: null,
    description: 'System settings',
    collapsed: true, // Start collapsed
    children: [
      { name: 'Budget Versions', href: '/configuration/versions', icon: Clock },
      { name: 'Class Sizes', href: '/configuration/class-sizes', icon: Users },
      { name: 'Subject Hours', href: '/configuration/subject-hours', icon: Clock },
      { name: 'Teacher Costs', href: '/configuration/teacher-costs', icon: UserCog },
      { name: 'Fee Structure', href: '/configuration/fees', icon: DollarSign },
      { name: 'Timetable', href: '/configuration/timetable', icon: CalendarCog },
    ],
  },
  {
    id: 'strategic',
    name: 'Strategic',
    href: '/strategic',
    icon: Target,
    statKey: null,
    description: '5-Year Planning',
    badge: '5-Yr',
  },
]

interface NavItemProps {
  item: (typeof navigation)[0]
  isExpanded: boolean
  onToggle: () => void
  activePath: string
  prefetchRoute: (href: string, versionId?: string) => void
  selectedVersionId: string | undefined
  stat: { label: string; value: string; loading: boolean; trend?: string } | null
}

function NavItem({
  item,
  isExpanded,
  onToggle,
  activePath,
  prefetchRoute,
  selectedVersionId,
  stat,
}: NavItemProps) {
  const Icon = item.icon
  const hasChildren = item.children && item.children.length > 0
  const isActive = item.href
    ? activePath === item.href
    : item.children?.some((child) => activePath === child.href)

  // Direct link item (no children)
  if (item.href && !hasChildren) {
    return (
      <Link
        to={item.href}
        className={cn(
          'group flex items-center justify-between px-3 py-2.5 rounded-xl',
          'transition-all duration-200 ease-out',
          'hover:bg-sand-100 hover:translate-x-1',
          isActive && [
            'bg-gradient-to-r from-gold-50 to-sand-50',
            'border-l-3 border-gold-500',
            'shadow-sm',
          ]
        )}
        onMouseEnter={() => prefetchRoute(item.href!, selectedVersionId)}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'p-1.5 rounded-lg transition-colors duration-200',
              isActive
                ? 'bg-gold-100 text-gold-700'
                : 'bg-sand-100 text-twilight-500 group-hover:bg-gold-50 group-hover:text-gold-600'
            )}
          >
            <Icon className="w-4 h-4" />
          </div>
          <span
            className={cn(
              'text-sm font-medium',
              isActive ? 'text-brown-900' : 'text-brown-700 group-hover:text-brown-900'
            )}
          >
            {item.name}
          </span>
        </div>

        {/* Badge or Stat */}
        {item.badge && (
          <span className="text-[10px] font-semibold text-twilight-500 bg-sand-100 px-1.5 py-0.5 rounded">
            {item.badge}
          </span>
        )}
      </Link>
    )
  }

  // Expandable section
  return (
    <div className="space-y-0.5">
      {/* Section header */}
      <button
        onClick={onToggle}
        className={cn(
          'w-full group flex items-center justify-between px-3 py-2.5 rounded-xl',
          'transition-all duration-200 ease-out',
          'hover:bg-sand-100',
          isActive && 'bg-sand-50'
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'p-1.5 rounded-lg transition-colors duration-200',
              isActive
                ? 'bg-gold-100 text-gold-700'
                : 'bg-sand-100 text-twilight-500 group-hover:bg-gold-50 group-hover:text-gold-600'
            )}
          >
            <Icon className="w-4 h-4" />
          </div>
          <span
            className={cn(
              'text-sm font-medium',
              isActive ? 'text-brown-900' : 'text-brown-700 group-hover:text-brown-900'
            )}
          >
            {item.name}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick stat */}
          {stat && !stat.loading && (
            <span
              className={cn(
                'text-xs font-mono font-medium px-1.5 py-0.5 rounded',
                stat.trend === 'up' && 'text-sage-700 bg-sage-50',
                stat.trend === 'down' && 'text-terracotta-600 bg-terracotta-50',
                !stat.trend && 'text-twilight-600 bg-sand-100'
              )}
            >
              {stat.value}
            </span>
          )}

          {/* Expand/collapse chevron */}
          <div className={cn('transition-transform duration-200', isExpanded && 'rotate-180')}>
            <ChevronDown className="w-4 h-4 text-twilight-400" />
          </div>
        </div>
      </button>

      {/* Children */}
      <div
        className={cn(
          'overflow-hidden transition-all duration-300 ease-out',
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="ml-5 pl-3 border-l border-sand-200 space-y-0.5 py-1">
          {item.children?.map((child) => {
            const ChildIcon = child.icon
            const childActive = activePath === child.href

            return (
              <Link
                key={child.href}
                to={child.href}
                className={cn(
                  'group flex items-center gap-2.5 px-3 py-2 rounded-lg',
                  'transition-all duration-200 ease-out',
                  'hover:bg-sand-100 hover:translate-x-0.5',
                  childActive && ['bg-gold-50', 'text-brown-900', 'shadow-sm']
                )}
                onMouseEnter={() => prefetchRoute(child.href, selectedVersionId)}
              >
                <ChildIcon
                  className={cn(
                    'w-3.5 h-3.5 transition-colors',
                    childActive ? 'text-gold-600' : 'text-twilight-400 group-hover:text-gold-500'
                  )}
                />
                <span
                  className={cn(
                    'text-sm',
                    childActive
                      ? 'font-medium text-brown-900'
                      : 'text-brown-600 group-hover:text-brown-800'
                  )}
                >
                  {child.name}
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export function EnhancedSidebar() {
  const { prefetchRoute } = usePrefetchRoute()
  const { selectedVersionId, selectedVersion } = useBudgetVersion()
  const moduleStats = useModuleStats()
  const routerState = useRouterState()
  const activePath = routerState.location.pathname

  // Track which sections are expanded
  const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
    // Initialize: expand sections that have an active child, collapse "configuration" by default
    const expanded = new Set<string>()
    navigation.forEach((item) => {
      if (item.children) {
        const hasActiveChild = item.children.some((child) => activePath === child.href)
        if (hasActiveChild || !item.collapsed) {
          expanded.add(item.id)
        }
      }
    })
    return expanded
  })

  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }, [])

  return (
    <aside
      className={cn(
        'w-72 flex flex-col',
        'bg-gradient-to-b from-cream-50 to-sand-50',
        'border-r border-sand-200',
        'shadow-sm'
      )}
    >
      {/* Logo Section */}
      <div className="h-16 flex items-center px-5 border-b border-sand-200">
        <div className="flex items-center gap-3">
          {/* Logo mark */}
          <div
            className={cn(
              'w-9 h-9 rounded-xl flex items-center justify-center',
              'bg-gradient-to-br from-gold-400 to-gold-600',
              'shadow-md shadow-gold-200'
            )}
          >
            <span className="text-white font-display font-bold text-lg">E</span>
          </div>
          {/* Brand text */}
          <div>
            <h1 className="text-lg font-display font-bold text-brown-900 tracking-tight">
              EFIR Budget
            </h1>
            {selectedVersion && (
              <p className="text-[10px] text-twilight-500 -mt-0.5">
                FY{selectedVersion.fiscal_year} • {selectedVersion.status}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavItem
            key={item.id}
            item={item}
            isExpanded={expandedSections.has(item.id)}
            onToggle={() => toggleSection(item.id)}
            activePath={activePath}
            prefetchRoute={prefetchRoute}
            selectedVersionId={selectedVersionId}
            stat={item.statKey ? moduleStats[item.statKey] : null}
          />
        ))}
      </nav>

      {/* Footer - Version info */}
      <div className="px-4 py-3 border-t border-sand-200 bg-sand-50/50">
        <p className="text-[10px] text-twilight-400 text-center">EFIR Budget Planning • v1.0</p>
      </div>
    </aside>
  )
}
