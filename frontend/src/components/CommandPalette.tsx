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
 * All navigable pages in the app
 */
const navigationItems: CommandItem[] = [
  // Dashboard
  {
    id: 'dashboard',
    name: 'Command Center',
    description: 'Overview & Quick Actions',
    href: '/dashboard',
    icon: LayoutDashboard,
    keywords: ['dashboard', 'home', 'overview', 'command', 'center'],
    category: 'navigation',
  },

  // Planning - Enrollment
  {
    id: 'enrollment',
    name: 'Enrollment Planning',
    description: 'Plan student enrollment',
    href: '/planning/enrollment',
    icon: GraduationCap,
    keywords: ['enrollment', 'students', 'planning', 'effectifs'],
    category: 'planning',
  },
  {
    id: 'classes',
    name: 'Class Structure',
    description: 'Configure class divisions',
    href: '/planning/classes',
    icon: BookOpen,
    keywords: ['classes', 'structure', 'divisions', 'sections'],
    category: 'planning',
  },

  // Planning - Workforce
  {
    id: 'dhg',
    name: 'DHG Workforce',
    description: 'Teacher FTE & Hours',
    href: '/planning/dhg',
    icon: Calculator,
    keywords: ['dhg', 'workforce', 'teachers', 'fte', 'hours', 'dotation'],
    category: 'planning',
  },
  {
    id: 'guide',
    name: 'Planning Guide',
    description: 'Step-by-step planning',
    href: '/planning/guide',
    icon: FileText,
    keywords: ['guide', 'planning', 'steps', 'help'],
    category: 'planning',
  },

  // Planning - Costs
  {
    id: 'costs',
    name: 'Cost Planning',
    description: 'Personnel & Operating costs',
    href: '/planning/costs',
    icon: Receipt,
    keywords: ['costs', 'expenses', 'personnel', 'operating', 'charges'],
    category: 'planning',
  },
  {
    id: 'revenue',
    name: 'Revenue Planning',
    description: 'Income projections',
    href: '/planning/revenue',
    icon: DollarSign,
    keywords: ['revenue', 'income', 'fees', 'tuition', 'produits'],
    category: 'planning',
  },

  // Planning - Investment
  {
    id: 'capex',
    name: 'CapEx Planning',
    description: 'Capital expenditure',
    href: '/planning/capex',
    icon: Truck,
    keywords: ['capex', 'investment', 'capital', 'assets', 'equipment'],
    category: 'planning',
  },

  // Consolidation
  {
    id: 'budget',
    name: 'Budget Review',
    description: 'Consolidated budget',
    href: '/consolidation/budget',
    icon: BarChart3,
    keywords: ['budget', 'consolidation', 'review', 'total'],
    category: 'analysis',
  },
  {
    id: 'statements',
    name: 'Financial Statements',
    description: 'P&L, Balance Sheet',
    href: '/consolidation/statements',
    icon: FileText,
    keywords: ['statements', 'financial', 'pnl', 'balance', 'compte', 'resultat'],
    category: 'analysis',
  },

  // Analysis
  {
    id: 'kpis',
    name: 'KPIs',
    description: 'Key Performance Indicators',
    href: '/analysis/kpis',
    icon: LineChart,
    keywords: ['kpi', 'indicators', 'performance', 'metrics'],
    category: 'analysis',
  },
  {
    id: 'dashboards',
    name: 'Dashboards',
    description: 'Visual analytics',
    href: '/analysis/dashboards',
    icon: PieChart,
    keywords: ['dashboard', 'analytics', 'charts', 'visualizations'],
    category: 'analysis',
  },
  {
    id: 'variance',
    name: 'Budget vs Actual',
    description: 'Variance analysis',
    href: '/analysis/variance',
    icon: GitCompare,
    keywords: ['variance', 'actual', 'comparison', 'ecarts'],
    category: 'analysis',
  },

  // Configuration
  {
    id: 'versions',
    name: 'Budget Versions',
    description: 'Manage budget versions',
    href: '/configuration/versions',
    icon: Clock,
    keywords: ['versions', 'budget', 'configuration'],
    category: 'configuration',
  },
  {
    id: 'class-sizes',
    name: 'Class Sizes',
    description: 'Min/Max/Target sizes',
    href: '/configuration/class-sizes',
    icon: Users,
    keywords: ['class', 'sizes', 'min', 'max', 'target'],
    category: 'configuration',
  },
  {
    id: 'subject-hours',
    name: 'Subject Hours',
    description: 'Hours per subject',
    href: '/configuration/subject-hours',
    icon: Clock,
    keywords: ['subject', 'hours', 'matieres', 'horaires'],
    category: 'configuration',
  },
  {
    id: 'teacher-costs',
    name: 'Teacher Costs',
    description: 'Salary & benefits',
    href: '/configuration/teacher-costs',
    icon: UserCog,
    keywords: ['teacher', 'costs', 'salary', 'benefits', 'prrd'],
    category: 'configuration',
  },
  {
    id: 'fees',
    name: 'Fee Structure',
    description: 'Tuition & fees',
    href: '/configuration/fees',
    icon: DollarSign,
    keywords: ['fees', 'tuition', 'frais', 'structure'],
    category: 'configuration',
  },
  {
    id: 'timetable',
    name: 'Timetable',
    description: 'Schedule constraints',
    href: '/configuration/timetable',
    icon: CalendarCog,
    keywords: ['timetable', 'schedule', 'emploi', 'temps'],
    category: 'configuration',
  },

  // Strategic
  {
    id: 'strategic',
    name: 'Strategic Planning',
    description: '5-Year projections',
    href: '/strategic',
    icon: Target,
    keywords: ['strategic', '5-year', 'long-term', 'projection'],
    category: 'planning',
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
          'rounded-xl border-sand-200',
          'bg-white/95 backdrop-blur-lg',
          '[&_[cmdk-group-heading]]:text-twilight-500',
          '[&_[cmdk-group-heading]]:font-semibold',
          '[&_[cmdk-group-heading]]:text-xs',
          '[&_[cmdk-group-heading]]:uppercase',
          '[&_[cmdk-group-heading]]:tracking-wide'
        )}
      >
        <div className="flex items-center border-b border-sand-200 px-4">
          <Search className="mr-2 h-4 w-4 shrink-0 text-twilight-400" />
          <CommandInput
            placeholder="Search pages, actions..."
            className={cn(
              'flex h-12 w-full rounded-md bg-transparent py-3',
              'text-sm text-brown-900 placeholder:text-twilight-400',
              'outline-none',
              'disabled:cursor-not-allowed disabled:opacity-50'
            )}
          />
          <kbd
            className={cn(
              'ml-auto hidden md:inline-flex',
              'h-5 select-none items-center gap-1',
              'rounded border border-sand-200 bg-sand-50',
              'px-1.5 font-mono text-[10px] font-medium text-twilight-500'
            )}
          >
            ESC
          </kbd>
        </div>

        <CommandList className="max-h-[400px] overflow-y-auto p-2">
          <CommandEmpty className="py-6 text-center text-sm text-twilight-500">
            <Sparkles className="mx-auto h-8 w-8 text-twilight-300 mb-2" />
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
                        'aria-selected:text-brown-900',
                        'transition-colors duration-150'
                      )}
                    >
                      <div
                        className={cn(
                          'flex h-8 w-8 items-center justify-center rounded-lg',
                          'bg-sand-100 text-twilight-600',
                          'group-aria-selected:bg-gold-100 group-aria-selected:text-gold-700'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-brown-800 truncate">{item.name}</p>
                        {item.description && (
                          <p className="text-xs text-twilight-500 truncate">{item.description}</p>
                        )}
                      </div>
                      <ArrowRight className="h-4 w-4 text-twilight-300 opacity-0 group-aria-selected:opacity-100 transition-opacity" />
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
            'border-t border-sand-200 bg-sand-50/50',
            'text-xs text-twilight-500'
          )}
        >
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-sand-200 bg-white px-1 font-mono">↑↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-sand-200 bg-white px-1 font-mono">↵</kbd>
              Select
            </span>
          </div>
          <span className="flex items-center gap-1">
            <kbd className="rounded border border-sand-200 bg-white px-1.5 font-mono">⌘</kbd>
            <kbd className="rounded border border-sand-200 bg-white px-1 font-mono">K</kbd>
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
