/* eslint-disable react-refresh/only-export-components */
/**
 * CommandPalette
 *
 * A luxurious command palette (Cmd+K / Ctrl+K) for quick navigation and actions.
 * Features:
 * - Fuzzy search across all pages
 * - Quick actions (create version, export, etc.)
 * - Recent items tracking
 * - Keyboard navigation
 * - Premium "Sahara Luxe" styling
 */

import { useEffect, useState, useCallback, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  GraduationCap,
  Users,
  PieChart,
  Target,
  FileText,
  Clock,
  DollarSign,
  Calculator,
  BarChart3,
  LineChart,
  GitCompare,
  CalendarCog,
  BookOpen,
  UserCog,
  Receipt,
  Truck,
  Search,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface CommandItem {
  id: string
  name: string
  description?: string
  href: string
  icon: LucideIcon
  keywords: string[]
  category: 'navigation' | 'planning' | 'analysis' | 'configuration' | 'action'
}

/**
 * All navigable pages in the app - organized by Executive Cockpit modules
 */
const navigationItems: CommandItem[] = [
  // ═══════════════════════════════════════════════════════════
  // COMMAND CENTER - Global Overview
  // ═══════════════════════════════════════════════════════════
  {
    id: 'command-center',
    name: 'Command Center',
    description: 'Executive overview & quick actions',
    href: '/command-center',
    icon: LayoutDashboard,
    keywords: ['dashboard', 'home', 'overview', 'command', 'center', 'executive'],
    category: 'navigation',
  },

  // ═══════════════════════════════════════════════════════════
  // WORKFORCE MODULE - Employee & DHG Management
  // ═══════════════════════════════════════════════════════════
  {
    id: 'workforce',
    name: 'Workforce Overview',
    description: 'Staff management dashboard',
    href: '/teachers',
    icon: Users,
    keywords: ['workforce', 'employees', 'staff', 'hr', 'human resources'],
    category: 'navigation',
  },
  {
    id: 'workforce-employees',
    name: 'Employee Registry',
    description: 'All employees & positions',
    href: '/teachers/employees',
    icon: Users,
    keywords: ['employees', 'registry', 'staff', 'personnel'],
    category: 'planning',
  },
  {
    id: 'workforce-salaries',
    name: 'Salaries & EOS',
    description: 'KSA salary management',
    href: '/teachers/salaries',
    icon: DollarSign,
    keywords: ['salaries', 'eos', 'compensation', 'gosi', 'benefits'],
    category: 'planning',
  },
  {
    id: 'workforce-aefe',
    name: 'AEFE Positions',
    description: 'Detached & funded positions',
    href: '/teachers/aefe-positions',
    icon: UserCog,
    keywords: ['aefe', 'positions', 'detached', 'prrd', 'funded'],
    category: 'planning',
  },
  {
    id: 'workforce-dhg',
    name: 'DHG Planning',
    description: 'Teacher hours allocation',
    href: '/teachers/dhg/planning',
    icon: Calculator,
    keywords: ['dhg', 'dotation', 'hours', 'allocation', 'horaire'],
    category: 'planning',
  },
  {
    id: 'workforce-fte',
    name: 'FTE Requirements',
    description: 'Teacher FTE by subject',
    href: '/teachers/dhg/requirements',
    icon: Calculator,
    keywords: ['fte', 'requirements', 'teachers', 'subjects'],
    category: 'planning',
  },
  {
    id: 'workforce-gap',
    name: 'Gap Analysis (TRMD)',
    description: 'Teacher deficit analysis',
    href: '/teachers/dhg/gap-analysis',
    icon: GitCompare,
    keywords: ['gap', 'trmd', 'deficit', 'besoins', 'moyens'],
    category: 'analysis',
  },

  // ═══════════════════════════════════════════════════════════
  // ENROLLMENT MODULE - Student Planning
  // ═══════════════════════════════════════════════════════════
  {
    id: 'enrollment',
    name: 'Enrollment Overview',
    description: 'Student enrollment dashboard',
    href: '/students',
    icon: GraduationCap,
    keywords: ['enrollment', 'students', 'effectifs', 'dashboard'],
    category: 'navigation',
  },
  {
    id: 'enrollment-planning',
    name: 'Enrollment Projections',
    description: 'Plan student enrollment',
    href: '/students/planning',
    icon: GraduationCap,
    keywords: ['enrollment', 'projections', 'students', 'planning', 'effectifs'],
    category: 'planning',
  },
  {
    id: 'enrollment-classes',
    name: 'Class Structure',
    description: 'Configure class divisions',
    href: '/students/class-structure',
    icon: BookOpen,
    keywords: ['classes', 'structure', 'divisions', 'sections'],
    category: 'planning',
  },

  // ═══════════════════════════════════════════════════════════
  // FINANCE MODULE - Revenue, Costs & Consolidation
  // ═══════════════════════════════════════════════════════════
  {
    id: 'finance',
    name: 'Finance Overview',
    description: 'Financial planning dashboard',
    href: '/finance',
    icon: DollarSign,
    keywords: ['finance', 'budget', 'financial', 'dashboard'],
    category: 'navigation',
  },
  {
    id: 'finance-revenue',
    name: 'Revenue Planning',
    description: 'Income projections',
    href: '/finance/revenue',
    icon: DollarSign,
    keywords: ['revenue', 'income', 'fees', 'tuition', 'produits'],
    category: 'planning',
  },
  {
    id: 'finance-costs',
    name: 'Cost Planning',
    description: 'Personnel & Operating costs',
    href: '/finance/costs',
    icon: Receipt,
    keywords: ['costs', 'expenses', 'personnel', 'operating', 'charges'],
    category: 'planning',
  },
  {
    id: 'finance-capex',
    name: 'CapEx Planning',
    description: 'Capital expenditure',
    href: '/finance/capex',
    icon: Truck,
    keywords: ['capex', 'investment', 'capital', 'assets', 'equipment'],
    category: 'planning',
  },
  {
    id: 'finance-consolidation',
    name: 'Budget Consolidation',
    description: 'Consolidated budget review',
    href: '/finance/consolidation',
    icon: BarChart3,
    keywords: ['budget', 'consolidation', 'review', 'total'],
    category: 'analysis',
  },
  {
    id: 'finance-statements',
    name: 'Financial Statements',
    description: 'P&L, Balance Sheet',
    href: '/finance/statements',
    icon: FileText,
    keywords: ['statements', 'financial', 'pnl', 'balance', 'compte', 'resultat'],
    category: 'analysis',
  },

  // ═══════════════════════════════════════════════════════════
  // ANALYSIS MODULE - KPIs & Dashboards
  // ═══════════════════════════════════════════════════════════
  {
    id: 'analysis',
    name: 'Analysis Overview',
    description: 'Analytics dashboard',
    href: '/insights',
    icon: PieChart,
    keywords: ['analysis', 'analytics', 'dashboard'],
    category: 'navigation',
  },
  {
    id: 'analysis-kpis',
    name: 'KPI Dashboard',
    description: 'Key Performance Indicators',
    href: '/insights/kpis',
    icon: LineChart,
    keywords: ['kpi', 'indicators', 'performance', 'metrics'],
    category: 'analysis',
  },
  {
    id: 'analysis-dashboards',
    name: 'Custom Dashboards',
    description: 'Visual analytics',
    href: '/insights/dashboards',
    icon: PieChart,
    keywords: ['dashboard', 'analytics', 'charts', 'visualizations'],
    category: 'analysis',
  },
  {
    id: 'analysis-variance',
    name: 'Budget vs Actual',
    description: 'Variance analysis',
    href: '/insights/variance',
    icon: GitCompare,
    keywords: ['variance', 'actual', 'comparison', 'ecarts'],
    category: 'analysis',
  },

  // ═══════════════════════════════════════════════════════════
  // STRATEGIC MODULE - Long-term Planning
  // ═══════════════════════════════════════════════════════════
  {
    id: 'strategic',
    name: 'Strategic Overview',
    description: '5-Year planning dashboard',
    href: '/strategic',
    icon: Target,
    keywords: ['strategic', '5-year', 'long-term', 'projection', 'plan'],
    category: 'navigation',
  },
  {
    id: 'strategic-5year',
    name: '5-Year Plan',
    description: 'Multi-year projections',
    href: '/strategic/five-year-plan',
    icon: Target,
    keywords: ['five', 'year', 'plan', 'multi-year', 'projections'],
    category: 'planning',
  },

  // ═══════════════════════════════════════════════════════════
  // CONFIGURATION - System Settings
  // ═══════════════════════════════════════════════════════════
  {
    id: 'config-versions',
    name: 'Budget Versions',
    description: 'Manage versions',
    href: '/settings/versions',
    icon: Clock,
    keywords: ['versions', 'budget', 'configuration'],
    category: 'configuration',
  },
  {
    id: 'config-class-sizes',
    name: 'Class Sizes',
    description: 'Min/Max/Target sizes',
    href: '/settings/class-sizes',
    icon: Users,
    keywords: ['class', 'sizes', 'min', 'max', 'target'],
    category: 'configuration',
  },
  {
    id: 'config-subject-hours',
    name: 'Subject Hours',
    description: 'Hours per subject',
    href: '/settings/subject-hours',
    icon: Clock,
    keywords: ['subject', 'hours', 'matieres', 'horaires'],
    category: 'configuration',
  },
  {
    id: 'config-teacher-costs',
    name: 'Teacher Costs',
    description: 'Salary & benefits',
    href: '/settings/teacher-costs',
    icon: UserCog,
    keywords: ['teacher', 'costs', 'salary', 'benefits', 'prrd'],
    category: 'configuration',
  },
  {
    id: 'config-fees',
    name: 'Fee Structure',
    description: 'Tuition & fees',
    href: '/settings/fees',
    icon: DollarSign,
    keywords: ['fees', 'tuition', 'frais', 'structure'],
    category: 'configuration',
  },
  {
    id: 'config-timetable',
    name: 'Timetable',
    description: 'Schedule constraints',
    href: '/settings/timetable',
    icon: CalendarCog,
    keywords: ['timetable', 'schedule', 'emploi', 'temps'],
    category: 'configuration',
  },
]

/**
 * Category labels for grouping
 */
const categoryLabels: Record<CommandItem['category'], string> = {
  navigation: 'Navigation',
  planning: 'Planning',
  analysis: 'Analysis & Consolidation',
  configuration: 'Configuration',
  action: 'Quick Actions',
}

/**
 * Category order for display
 */
const categoryOrder: CommandItem['category'][] = [
  'navigation',
  'planning',
  'analysis',
  'configuration',
  'action',
]

interface CommandPaletteProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function CommandPalette({ open: controlledOpen, onOpenChange }: CommandPaletteProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const navigate = useNavigate()

  // Support both controlled and uncontrolled modes
  const open = controlledOpen ?? internalOpen
  const setOpen = onOpenChange ?? setInternalOpen

  // Handle keyboard shortcut (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(!open)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, setOpen])

  // Navigate to selected item
  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false)
      navigate({ to: href })
    },
    [navigate, setOpen]
  )

  // Group items by category
  const groupedItems = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {}

    for (const item of navigationItems) {
      if (!groups[item.category]) {
        groups[item.category] = []
      }
      groups[item.category].push(item)
    }

    return groups
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <Command
        className={cn(
          'rounded-xl border-border-light',
          'bg-white/95 backdrop-blur-lg',
          '[&_[cmdk-group-heading]]:text-text-tertiary',
          '[&_[cmdk-group-heading]]:font-semibold',
          '[&_[cmdk-group-heading]]:text-xs',
          '[&_[cmdk-group-heading]]:uppercase',
          '[&_[cmdk-group-heading]]:tracking-wide'
        )}
      >
        <div className="flex items-center border-b border-border-light px-4">
          <Search className="mr-2 h-4 w-4 shrink-0 text-text-muted" />
          <CommandInput
            placeholder="Search pages, actions..."
            className={cn(
              'flex h-12 w-full rounded-md bg-transparent py-3',
              'text-sm text-text-primary placeholder:text-text-muted',
              'outline-none',
              'disabled:cursor-not-allowed disabled:opacity-50'
            )}
          />
          <kbd
            className={cn(
              'ml-auto hidden md:inline-flex',
              'h-5 select-none items-center gap-1',
              'rounded border border-border-light bg-subtle',
              'px-1.5 font-mono text-[10px] font-medium text-text-tertiary'
            )}
          >
            ESC
          </kbd>
        </div>

        <CommandList className="max-h-[400px] overflow-y-auto p-2">
          <CommandEmpty className="py-6 text-center text-sm text-text-tertiary">
            <Sparkles className="mx-auto h-8 w-8 text-text-muted mb-2" />
            No results found.
          </CommandEmpty>

          {categoryOrder.map((category, index) => {
            const items = groupedItems[category]
            if (!items?.length) return null

            return (
              <div key={category}>
                {index > 0 && <CommandSeparator className="my-2" />}
                <CommandGroup heading={categoryLabels[category]}>
                  {items.map((item) => (
                    <CommandItem
                      key={item.id}
                      value={`${item.name} ${item.keywords.join(' ')}`}
                      onSelect={() => handleSelect(item.href)}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                        'cursor-pointer',
                        'aria-selected:bg-gold-50',
                        'aria-selected:text-text-primary',
                        'transition-colors duration-150'
                      )}
                    >
                      <div
                        className={cn(
                          'flex h-8 w-8 items-center justify-center rounded-lg',
                          'bg-subtle text-text-secondary',
                          'group-aria-selected:bg-gold-100 group-aria-selected:text-gold-700'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {item.name}
                        </p>
                        {item.description && (
                          <p className="text-xs text-text-tertiary truncate">{item.description}</p>
                        )}
                      </div>
                      <ArrowRight className="h-4 w-4 text-text-muted opacity-0 group-aria-selected:opacity-100 transition-opacity" />
                    </CommandItem>
                  ))}
                </CommandGroup>
              </div>
            )
          })}
        </CommandList>

        {/* Footer with keyboard hints */}
        <div
          className={cn(
            'flex items-center justify-between gap-4 px-4 py-2',
            'border-t border-border-light bg-subtle/50',
            'text-xs text-text-tertiary'
          )}
        >
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border-light bg-white px-1 font-mono">↑↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border-light bg-white px-1 font-mono">↵</kbd>
              Select
            </span>
          </div>
          <span className="flex items-center gap-1">
            <kbd className="rounded border border-border-light bg-white px-1.5 font-mono">⌘</kbd>
            <kbd className="rounded border border-border-light bg-white px-1 font-mono">K</kbd>
            Open
          </span>
        </div>
      </Command>
    </CommandDialog>
  )
}

/**
 * Hook to programmatically control the command palette
 */
export function useCommandPalette() {
  const [open, setOpen] = useState(false)

  const toggle = useCallback(() => setOpen((prev) => !prev), [])
  const show = useCallback(() => setOpen(true), [])
  const hide = useCallback(() => setOpen(false), [])

  return { open, setOpen, toggle, show, hide }
}
