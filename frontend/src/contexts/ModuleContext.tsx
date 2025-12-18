/* eslint-disable react-refresh/only-export-components */
/**
 * ModuleContext - Executive Cockpit Module State Management
 *
 * Provides context for tracking the active module across the Executive Cockpit layout.
 * 10 Modules aligned with FP&A best practices:
 * - enrollment: Student enrollment planning (Academic Director)
 * - workforce: Teacher/HR workforce planning (HR Manager)
 * - revenue: Revenue planning (Finance Director)
 * - costs: Cost planning (Finance Director)
 * - investments: CapEx/Investment planning (Finance Director/CFO)
 * - consolidation: Budget consolidation & statements (Finance Director/CFO)
 * - insights: KPIs, dashboards, variance (All roles - read)
 * - strategic: Long-term planning & scenarios (CFO/Executive)
 * - settings: Global configuration (All roles - limited)
 * - admin: System administration (Admin only)
 *
 * Features:
 * - Auto-detects active module from current route
 * - Provides module metadata (icon, label, color, subpages)
 * - Tracks module health status for dock badges
 * - Subpage configuration for tab navigation
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useLocation } from '@tanstack/react-router'
import {
  Users,
  GraduationCap,
  BarChart3,
  LayoutDashboard,
  Settings,
  Shield,
  DollarSign,
  TrendingUp,
  PiggyBank,
  FileStack,
  Target,
  type LucideIcon,
} from 'lucide-react'

/**
 * Module identifiers - the 10 main workspaces
 *
 * Aligned with FP&A best practices and DB_golden_rules.md Section 9:
 * - enrollment: Student enrollment planning (Academic Director)
 * - workforce: Teacher/HR workforce planning (HR Manager)
 * - revenue: Revenue planning (Finance Director)
 * - costs: Cost planning (Finance Director)
 * - investments: CapEx/Investment planning (Finance Director/CFO)
 * - consolidation: Budget consolidation & statements (Finance Director/CFO)
 * - insights: KPIs, dashboards, variance (All roles - read)
 * - strategic: Long-term planning & scenarios (CFO/Executive)
 * - settings: Global configuration (All roles - limited)
 * - admin: System administration (Admin only)
 */
export type ModuleId =
  | 'command-center'
  | 'enrollment'
  | 'workforce'
  | 'revenue'
  | 'costs'
  | 'investments'
  | 'consolidation'
  | 'insights'
  | 'strategic'
  | 'settings'
  | 'admin'

/**
 * Module health status for dock badges
 */
export type ModuleStatus = 'healthy' | 'attention' | 'warning' | 'error' | 'inactive'

/**
 * Subpage definition for tab navigation within a module
 */
export interface SubpageDefinition {
  id: string
  label: string
  path: string
  icon?: LucideIcon
}

/**
 * Module metadata definition
 */
export interface ModuleDefinition {
  id: ModuleId
  label: string
  shortLabel: string
  icon: LucideIcon
  basePath: string
  color: 'gold' | 'sage' | 'wine' | 'slate' | 'neutral' | 'orange' | 'teal' | 'blue' | 'purple'
  description: string
  subpages: SubpageDefinition[]
  /** Whether this module has a separate settings tab */
  hasSettings: boolean
}

/**
 * Module color class definition
 */
export interface ModuleColorClasses {
  active: string
  underline: string
  hover: string
  text: string
  bg: string
}

/**
 * Module color mapping for CSS classes
 */
export const MODULE_COLORS: Record<
  'gold' | 'sage' | 'wine' | 'slate' | 'neutral' | 'orange' | 'teal' | 'blue' | 'purple',
  ModuleColorClasses
> = {
  gold: {
    active: 'bg-gold-100 text-gold-700 border-gold-500',
    underline: 'bg-gold-500',
    hover: 'hover:bg-gold-50 hover:text-gold-600',
    text: 'text-gold-600',
    bg: 'bg-gold-500',
  },
  sage: {
    active: 'bg-sage-100 text-sage-700 border-sage-500',
    underline: 'bg-sage-500',
    hover: 'hover:bg-sage-50 hover:text-sage-600',
    text: 'text-sage-600',
    bg: 'bg-sage-500',
  },
  wine: {
    active: 'bg-wine-100 text-wine-700 border-wine-500',
    underline: 'bg-wine-500',
    hover: 'hover:bg-wine-50 hover:text-wine-600',
    text: 'text-wine-600',
    bg: 'bg-wine-500',
  },
  slate: {
    active: 'bg-slate-100 text-slate-700 border-slate-500',
    underline: 'bg-slate-500',
    hover: 'hover:bg-slate-50 hover:text-slate-600',
    text: 'text-slate-600',
    bg: 'bg-slate-500',
  },
  neutral: {
    active: 'bg-subtle text-text-primary border-border-strong',
    underline: 'bg-text-tertiary',
    hover: 'hover:bg-subtle hover:text-text-primary',
    text: 'text-text-secondary',
    bg: 'bg-text-tertiary',
  },
  orange: {
    active: 'bg-orange-100 text-orange-700 border-orange-500',
    underline: 'bg-orange-500',
    hover: 'hover:bg-orange-50 hover:text-orange-600',
    text: 'text-orange-600',
    bg: 'bg-orange-500',
  },
  teal: {
    active: 'bg-teal-100 text-teal-700 border-teal-500',
    underline: 'bg-teal-500',
    hover: 'hover:bg-teal-50 hover:text-teal-600',
    text: 'text-teal-600',
    bg: 'bg-teal-500',
  },
  blue: {
    active: 'bg-blue-100 text-blue-700 border-blue-500',
    underline: 'bg-blue-500',
    hover: 'hover:bg-blue-50 hover:text-blue-600',
    text: 'text-blue-600',
    bg: 'bg-blue-500',
  },
  purple: {
    active: 'bg-purple-100 text-purple-700 border-purple-500',
    underline: 'bg-purple-500',
    hover: 'hover:bg-purple-50 hover:text-purple-600',
    text: 'text-purple-600',
    bg: 'bg-purple-500',
  },
}

/**
 * Module definitions with metadata and subpages
 *
 * 10-Module Architecture (aligned with FP&A best practices):
 * - Enrollment: Projections → Class Structure → Validation + Settings (Academic Director)
 * - Workforce: Employees → DHG → Requirements → Gap Analysis + Settings (HR Manager)
 * - Revenue: Tuition → Other → Subsidies + Settings (Finance Director)
 * - Costs: Personnel → Operating → Overhead + Settings (Finance Director)
 * - Investments: CapEx → Projects → Cash Flow + Settings (Finance Director/CFO)
 * - Consolidation: Checklist → Rollup → Statements → Exports (Finance Director/CFO)
 * - Insights: KPIs → Variance → Trends → Reports (All roles - read)
 * - Strategic: Long-term → Scenarios → Targets (CFO/Executive)
 * - Settings: Versions → Parameters → System (All roles - limited)
 * - Admin: Users → Imports → Audit (Admin only)
 */
export const MODULES: Record<ModuleId, ModuleDefinition> = {
  'command-center': {
    id: 'command-center',
    label: 'Command Center',
    shortLabel: 'Home',
    icon: LayoutDashboard,
    basePath: '/command-center',
    color: 'gold',
    description: 'Global overview and quick actions',
    subpages: [],
    hasSettings: false,
  },
  enrollment: {
    id: 'enrollment',
    label: 'Enrollment Planning',
    shortLabel: 'Enrollment',
    icon: GraduationCap,
    basePath: '/enrollment',
    color: 'sage',
    description: 'Student enrollment projections and class formation',
    subpages: [
      { id: 'projections', label: 'Projections', path: '/enrollment/projections' },
      { id: 'class-structure', label: 'Class Structure', path: '/enrollment/class-structure' },
      { id: 'validation', label: 'Validation', path: '/enrollment/validation' },
    ],
    hasSettings: true,
  },
  workforce: {
    id: 'workforce',
    label: 'Workforce Planning',
    shortLabel: 'Workforce',
    icon: Users,
    basePath: '/workforce',
    color: 'wine',
    description: 'Employee management and DHG workforce planning',
    subpages: [
      { id: 'employees', label: 'Employees', path: '/workforce/employees' },
      { id: 'dhg', label: 'DHG', path: '/workforce/dhg' },
      { id: 'requirements', label: 'Requirements', path: '/workforce/requirements' },
      { id: 'gap-analysis', label: 'Gap Analysis', path: '/workforce/gap-analysis' },
      { id: 'salaries', label: 'Salaries', path: '/workforce/salaries' },
    ],
    hasSettings: true,
  },
  revenue: {
    id: 'revenue',
    label: 'Revenue Planning',
    shortLabel: 'Revenue',
    icon: DollarSign,
    basePath: '/revenue',
    color: 'gold',
    description: 'Tuition and other revenue projections',
    subpages: [
      { id: 'tuition', label: 'Tuition', path: '/revenue/tuition' },
      { id: 'other', label: 'Other Revenue', path: '/revenue/other' },
      { id: 'subsidies', label: 'Subsidies', path: '/revenue/subsidies' },
    ],
    hasSettings: true,
  },
  costs: {
    id: 'costs',
    label: 'Cost Planning',
    shortLabel: 'Costs',
    icon: TrendingUp,
    basePath: '/costs',
    color: 'orange',
    description: 'Personnel, operating, and overhead costs',
    subpages: [
      { id: 'personnel', label: 'Personnel', path: '/costs/personnel' },
      { id: 'operating', label: 'Operating', path: '/costs/operating' },
      { id: 'overhead', label: 'Overhead', path: '/costs/overhead' },
    ],
    hasSettings: true,
  },
  investments: {
    id: 'investments',
    label: 'Investment Planning',
    shortLabel: 'Investments',
    icon: PiggyBank,
    basePath: '/investments',
    color: 'teal',
    description: 'Capital expenditure and project budgeting',
    subpages: [
      { id: 'capex', label: 'CapEx', path: '/investments/capex' },
      { id: 'projects', label: 'Projects', path: '/investments/projects' },
      { id: 'cashflow', label: 'Cash Flow', path: '/investments/cashflow' },
    ],
    hasSettings: true,
  },
  consolidation: {
    id: 'consolidation',
    label: 'Consolidation',
    shortLabel: 'Consolidation',
    icon: FileStack,
    basePath: '/consolidation',
    color: 'blue',
    description: 'Budget consolidation and financial statements',
    subpages: [
      { id: 'checklist', label: 'Checklist', path: '/consolidation/checklist' },
      { id: 'rollup', label: 'Rollup', path: '/consolidation/rollup' },
      { id: 'statements', label: 'Statements', path: '/consolidation/statements' },
      { id: 'exports', label: 'Exports', path: '/consolidation/exports' },
    ],
    hasSettings: false,
  },
  insights: {
    id: 'insights',
    label: 'Insights',
    shortLabel: 'Insights',
    icon: BarChart3,
    basePath: '/insights',
    color: 'slate',
    description: 'KPIs, dashboards, and variance analysis',
    subpages: [
      { id: 'kpis', label: 'KPIs', path: '/insights/kpis' },
      { id: 'variance', label: 'Variance', path: '/insights/variance' },
      { id: 'trends', label: 'Trends', path: '/insights/trends' },
      { id: 'reports', label: 'Reports', path: '/insights/reports' },
    ],
    hasSettings: false,
  },
  strategic: {
    id: 'strategic',
    label: 'Strategic Planning',
    shortLabel: 'Strategic',
    icon: Target,
    basePath: '/strategic',
    color: 'purple',
    description: 'Long-term planning and scenario modeling',
    subpages: [
      { id: 'long-term', label: 'Long-term', path: '/strategic/long-term' },
      { id: 'scenarios', label: 'Scenarios', path: '/strategic/scenarios' },
      { id: 'targets', label: 'Targets', path: '/strategic/targets' },
    ],
    hasSettings: false,
  },
  settings: {
    id: 'settings',
    label: 'Settings',
    shortLabel: 'Settings',
    icon: Settings,
    basePath: '/settings',
    color: 'neutral',
    description: 'Global configuration and parameters',
    subpages: [
      { id: 'versions', label: 'Versions', path: '/settings/versions' },
      { id: 'system', label: 'System', path: '/settings/system' },
    ],
    hasSettings: false,
  },
  admin: {
    id: 'admin',
    label: 'Admin',
    shortLabel: 'Admin',
    icon: Shield,
    basePath: '/admin',
    color: 'neutral',
    description: 'System administration and data imports',
    subpages: [{ id: 'uploads', label: 'Data Uploads', path: '/admin/uploads' }],
    hasSettings: false,
  },
}

/**
 * Ordered list of modules for the sidebar (main planning modules)
 */
export const MODULE_ORDER: ModuleId[] = [
  'enrollment',
  'workforce',
  'revenue',
  'costs',
  'investments',
  'consolidation',
  'insights',
  'strategic',
  'settings',
]

/**
 * All modules for navigation (excludes Admin - shown separately for admin role)
 */
export const ALL_MODULES: ModuleId[] = [
  'enrollment',
  'workforce',
  'revenue',
  'costs',
  'investments',
  'consolidation',
  'insights',
  'strategic',
  'settings',
]

/**
 * All modules including Admin (for admin users only)
 */
export const ALL_MODULES_WITH_ADMIN: ModuleId[] = [
  'enrollment',
  'workforce',
  'revenue',
  'costs',
  'investments',
  'consolidation',
  'insights',
  'strategic',
  'settings',
  'admin',
]

/**
 * Module context value
 */
interface ModuleContextValue {
  /** Currently active module based on route */
  activeModule: ModuleId | null
  /** Active module definition */
  activeModuleDefinition: ModuleDefinition | null
  /** Currently active subpage based on route */
  activeSubpage: SubpageDefinition | null
  /** All module definitions */
  modules: typeof MODULES
  /** Ordered list for dock display */
  moduleOrder: ModuleId[]
  /** All modules including configuration */
  allModules: ModuleId[]
  /** Check if a specific module is active */
  isModuleActive: (moduleId: ModuleId) => boolean
  /** Check if a specific subpage is active */
  isSubpageActive: (path: string) => boolean
  /** Get module definition by ID */
  getModule: (moduleId: ModuleId) => ModuleDefinition | undefined
  /** Get module color classes */
  getModuleColors: (moduleId: ModuleId) => ModuleColorClasses
}

const ModuleContext = createContext<ModuleContextValue | null>(null)

/**
 * Determine active module from pathname
 */
function getActiveModuleFromPath(pathname: string): ModuleId | null {
  // Command center / dashboard
  if (pathname === '/' || pathname === '/command-center' || pathname === '/dashboard') {
    return 'command-center'
  }

  // Check admin module first (requires special access)
  if (pathname.startsWith('/admin')) {
    return 'admin'
  }

  // Enrollment module routes (was: students)
  if (pathname.startsWith('/enrollment')) {
    return 'enrollment'
  }

  // Workforce module routes (was: teachers)
  if (pathname.startsWith('/workforce')) {
    return 'workforce'
  }

  // Revenue module routes (was: finance/revenue)
  if (pathname.startsWith('/revenue')) {
    return 'revenue'
  }

  // Costs module routes (was: finance/costs)
  if (pathname.startsWith('/costs')) {
    return 'costs'
  }

  // Investments module routes (was: finance/capex)
  if (pathname.startsWith('/investments')) {
    return 'investments'
  }

  // Consolidation module routes
  if (pathname.startsWith('/consolidation')) {
    return 'consolidation'
  }

  // Insights module routes
  if (pathname.startsWith('/insights')) {
    return 'insights'
  }

  // Strategic module routes (elevated from settings)
  if (pathname.startsWith('/strategic')) {
    return 'strategic'
  }

  // Settings module routes
  if (pathname.startsWith('/settings')) {
    return 'settings'
  }

  return null
}

/**
 * Determine active subpage from pathname
 */
function getActiveSubpageFromPath(
  pathname: string,
  module: ModuleDefinition | null
): SubpageDefinition | null {
  if (!module) return null

  // Exact match for subpages
  for (const subpage of module.subpages) {
    if (pathname === subpage.path || pathname.startsWith(subpage.path + '/')) {
      return subpage
    }
  }

  // If on module index, no specific subpage is active
  if (pathname === module.basePath || pathname === module.basePath + '/') {
    return null
  }

  return null
}

interface ModuleProviderProps {
  children: ReactNode
}

/**
 * ModuleProvider - Provides module context to the application
 */
export function ModuleProvider({ children }: ModuleProviderProps) {
  const location = useLocation()

  const value = useMemo<ModuleContextValue>(() => {
    const activeModule = getActiveModuleFromPath(location.pathname)
    const activeModuleDefinition = activeModule ? MODULES[activeModule] : null
    const activeSubpage = getActiveSubpageFromPath(location.pathname, activeModuleDefinition)

    return {
      activeModule,
      activeModuleDefinition,
      activeSubpage,
      modules: MODULES,
      moduleOrder: MODULE_ORDER,
      allModules: ALL_MODULES,
      isModuleActive: (moduleId: ModuleId) => activeModule === moduleId,
      isSubpageActive: (path: string) => {
        return location.pathname === path || location.pathname.startsWith(path + '/')
      },
      getModule: (moduleId: ModuleId) => MODULES[moduleId],
      getModuleColors: (moduleId: ModuleId) => {
        const module = MODULES[moduleId]
        return MODULE_COLORS[module?.color || 'neutral']
      },
    }
  }, [location.pathname])

  return <ModuleContext.Provider value={value}>{children}</ModuleContext.Provider>
}

/**
 * Hook to access module context
 */
export function useModule() {
  const context = useContext(ModuleContext)
  if (!context) {
    throw new Error('useModule must be used within a ModuleProvider')
  }
  return context
}

/**
 * Hook to get the active module definition
 */
export function useActiveModule() {
  const { activeModule, activeModuleDefinition, activeSubpage } = useModule()
  return {
    activeModule,
    definition: activeModuleDefinition,
    activeSubpage,
  }
}

/**
 * Hook to get subpages for the active module
 */
export function useActiveSubpages() {
  const { activeModuleDefinition, activeSubpage, isSubpageActive } = useModule()
  return {
    subpages: activeModuleDefinition?.subpages || [],
    activeSubpage,
    isSubpageActive,
    hasSubpages: (activeModuleDefinition?.subpages.length || 0) > 0,
    hasSettings: activeModuleDefinition?.hasSettings ?? false,
    moduleColor: activeModuleDefinition?.color || 'neutral',
  }
}

/**
 * Re-export TAB_DESCRIPTIONS from TaskDescription component
 * for centralized access to route descriptions
 */
export { TAB_DESCRIPTIONS } from '@/components/layout/TaskDescription'

/**
 * Settings route helper - generates the settings path for a module
 */
export function getModuleSettingsPath(moduleId: ModuleId): string | null {
  const module = MODULES[moduleId]
  if (!module?.hasSettings) return null
  return `${module.basePath}/settings`
}

/**
 * Check if a module has settings
 */
export function moduleHasSettings(moduleId: ModuleId): boolean {
  return MODULES[moduleId]?.hasSettings ?? false
}
