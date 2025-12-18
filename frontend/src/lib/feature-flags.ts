/**
 * Feature Flags
 *
 * Centralized feature flag management for gradual rollout of new features.
 * These can be toggled via environment variables or changed manually for testing.
 *
 * Usage:
 * ```tsx
 * import { USE_TANSTACK_TABLE } from '@/lib/feature-flags'
 *
 * const TableComponent = USE_TANSTACK_TABLE ? TanStackTable : AGGridTable
 * ```
 */

// ============================================================================
// TanStack Table Migration
// ============================================================================

/**
 * Enable TanStack Table instead of AG Grid.
 *
 * When true, components will use TanStack Table for rendering.
 * When false (default), AG Grid is used.
 *
 * Set via environment variable: VITE_USE_TANSTACK_TABLE=true
 *
 * Migration phases:
 * - Phase 1-2: false (foundation being built)
 * - Phase 3-6: true for specific routes (per-route flags below)
 * - Phase 7+: true globally (AG Grid removed)
 */
export const USE_TANSTACK_TABLE = import.meta.env.VITE_USE_TANSTACK_TABLE === 'true'

/**
 * Per-route TanStack Table flags for gradual migration.
 * These allow migrating one route at a time while keeping others on AG Grid.
 */
export const TANSTACK_ROUTES = {
  // Phase 2: Read-only grids (lowest risk)
  '/teachers/dhg/gap-analysis': import.meta.env.VITE_TANSTACK_WORKFORCE_GAP === 'true',
  '/teachers/employees': import.meta.env.VITE_TANSTACK_WORKFORCE_EMPLOYEES === 'true',
  '/teachers/aefe-positions': import.meta.env.VITE_TANSTACK_WORKFORCE_AEFE === 'true',

  // Phase 4: Simple editable grids
  '/settings/system': import.meta.env.VITE_TANSTACK_CONFIG_SYSTEM === 'true',
  '/settings/timetable': import.meta.env.VITE_TANSTACK_CONFIG_TIMETABLE === 'true',

  // Phase 6: Complex editable grids with clipboard
  '/students/settings': import.meta.env.VITE_TANSTACK_ENROLLMENT_SETTINGS === 'true',
  '/students/class-structure': import.meta.env.VITE_TANSTACK_ENROLLMENT_CLASS === 'true',
  '/finance/settings': import.meta.env.VITE_TANSTACK_FINANCE_SETTINGS === 'true',

  // Phase 7: Direct AG Grid routes
  '/finance/revenue': import.meta.env.VITE_TANSTACK_FINANCE_REVENUE === 'true',
  '/finance/costs': import.meta.env.VITE_TANSTACK_FINANCE_COSTS === 'true',
  '/finance/capex': import.meta.env.VITE_TANSTACK_FINANCE_CAPEX === 'true',

  // Phase 8: DHG multi-grid
  '/teachers/dhg/planning': import.meta.env.VITE_TANSTACK_PLANNING_DHG === 'true',
} as const

/**
 * Check if TanStack Table should be used for a specific route.
 *
 * @param route - The route path to check
 * @returns true if TanStack Table should be used
 *
 * @example
 * ```tsx
 * const useTanStack = shouldUseTanStack('/teachers/employees')
 * ```
 */
export function shouldUseTanStack(route: keyof typeof TANSTACK_ROUTES): boolean {
  // Global flag overrides per-route flags
  if (USE_TANSTACK_TABLE) return true

  return TANSTACK_ROUTES[route] ?? false
}

// ============================================================================
// Other Feature Flags (for future use)
// ============================================================================

/**
 * Enable experimental features.
 * These are features still in development that may not be stable.
 */
export const ENABLE_EXPERIMENTAL = import.meta.env.VITE_ENABLE_EXPERIMENTAL === 'true'

/**
 * Enable verbose logging for debugging.
 */
export const DEBUG_MODE = import.meta.env.VITE_DEBUG_MODE === 'true' || import.meta.env.DEV
