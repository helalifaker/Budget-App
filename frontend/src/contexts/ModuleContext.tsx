/* eslint-disable react-refresh/only-export-components */
/**
 * ModuleContext - Executive Cockpit Module State Management
 *
 * Provides context for tracking the active module across the Executive Cockpit layout.
 * Modules: workforce, enrollment, finance, analysis, strategic, configuration
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
  Wallet,
  BarChart3,
  Target,
  LayoutDashboard,
  Settings,
  type LucideIcon,
} from 'lucide-react'

/**
 * Module identifiers - the main workspaces
 */
export type ModuleId =
  | 'workforce'
  | 'enrollment'
  | 'finance'
  | 'analysis'
  | 'strategic'
  | 'configuration'
  | 'command-center'

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
  color: 'gold' | 'sage' | 'wine' | 'slate' | 'neutral'
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
  'gold' | 'sage' | 'wine' | 'slate' | 'neutral',
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
}

/**
 * Module definitions with metadata and subpages
 *
 * Phase 3 restructuring (UI Redesign):
 * - Enrollment: Planning → Class Structure → Validation + Settings
 * - Workforce: Employees → DHG → Requirements → Gap Analysis + Settings
 * - Finance: Revenue → Costs → CapEx → Statements + Settings
 * - Analysis: KPIs → Dashboards → Variance (no settings)
 * - Strategic: 5-Year Plan (no settings)
 * - Configuration: Versions → Uploads → System (no settings)
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
    label: 'Enrollment',
    shortLabel: 'Enrollment',
    icon: GraduationCap,
    basePath: '/enrollment',
    color: 'sage',
    description: 'Student enrollment and class structure',
    subpages: [
      { id: 'planning', label: 'Planning', path: '/enrollment/planning' },
      { id: 'class-structure', label: 'Class Structure', path: '/enrollment/class-structure' },
      { id: 'validation', label: 'Validation', path: '/enrollment/validation' },
    ],
    hasSettings: true,
  },
  workforce: {
    id: 'workforce',
    label: 'Workforce',
    shortLabel: 'Workforce',
    icon: Users,
    basePath: '/workforce',
    color: 'wine',
    description: 'Employee management and DHG planning',
    subpages: [
      { id: 'employees', label: 'Employees', path: '/workforce/employees' },
      { id: 'dhg', label: 'DHG', path: '/workforce/dhg' },
      { id: 'requirements', label: 'Requirements', path: '/workforce/dhg/requirements' },
      { id: 'gap-analysis', label: 'Gap Analysis', path: '/workforce/dhg/gap-analysis' },
    ],
    hasSettings: true,
  },
  finance: {
    id: 'finance',
    label: 'Finance',
    shortLabel: 'Finance',
    icon: Wallet,
    basePath: '/finance',
    color: 'gold',
    description: 'Revenue, costs, and financial statements',
    subpages: [
      { id: 'revenue', label: 'Revenue', path: '/finance/revenue' },
      { id: 'costs', label: 'Costs', path: '/finance/costs' },
      { id: 'capex', label: 'CapEx', path: '/finance/capex' },
      { id: 'statements', label: 'Statements', path: '/finance/statements' },
    ],
    hasSettings: true,
  },
  analysis: {
    id: 'analysis',
    label: 'Analysis',
    shortLabel: 'Analysis',
    icon: BarChart3,
    basePath: '/analysis',
    color: 'slate',
    description: 'KPIs, dashboards, and variance analysis',
    subpages: [
      { id: 'kpis', label: 'KPIs', path: '/analysis/kpis' },
      { id: 'dashboards', label: 'Dashboards', path: '/analysis/dashboards' },
      { id: 'variance', label: 'Variance', path: '/analysis/variance' },
    ],
    hasSettings: false,
  },
  strategic: {
    id: 'strategic',
    label: 'Strategic',
    shortLabel: 'Strategic',
    icon: Target,
    basePath: '/strategic',
    color: 'neutral',
    description: '5-year planning and projections',
    subpages: [{ id: 'five-year-plan', label: '5-Year Plan', path: '/strategic' }],
    hasSettings: false,
  },
  configuration: {
    id: 'configuration',
    label: 'Configuration',
    shortLabel: 'Config',
    icon: Settings,
    basePath: '/configuration',
    color: 'neutral',
    description: 'System settings, versions, and data imports',
    subpages: [
      { id: 'versions', label: 'Versions', path: '/configuration/versions' },
      { id: 'uploads', label: 'Uploads', path: '/configuration/uploads' },
      { id: 'system', label: 'System', path: '/configuration/system' },
    ],
    hasSettings: false,
  },
}

/**
 * Ordered list of modules for the dock (main modules only)
 */
export const MODULE_ORDER: ModuleId[] = [
  'enrollment',
  'workforce',
  'finance',
  'analysis',
  'strategic',
]

/**
 * All modules including configuration (for mobile nav)
 */
export const ALL_MODULES: ModuleId[] = [
  'enrollment',
  'workforce',
  'finance',
  'analysis',
  'strategic',
  'configuration',
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

  // Check each module's base path
  for (const moduleId of ALL_MODULES) {
    const module = MODULES[moduleId]
    if (pathname.startsWith(module.basePath)) {
      return moduleId
    }
  }

  // Legacy route mapping
  if (pathname.startsWith('/planning/enrollment') || pathname.startsWith('/planning/classes')) {
    return 'enrollment'
  }
  if (
    pathname.startsWith('/planning/revenue') ||
    pathname.startsWith('/planning/costs') ||
    pathname.startsWith('/planning/capex') ||
    pathname.startsWith('/consolidation')
  ) {
    return 'finance'
  }
  if (pathname.startsWith('/planning/dhg')) {
    return 'workforce'
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
