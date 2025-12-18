/**
 * Hooks barrel export
 *
 * Organized by concern:
 * - api/     - API hooks (queries/mutations)
 * - grid/    - Grid/Excel keyboard and clipboard
 * - sync/    - Realtime sync, auto-save, background refetch
 * - state/   - Draft editing, undo/redo
 * - utils/   - General utilities
 */

// API hooks
export * from './api'

// Grid hooks
export * from './grid'

// Sync hooks
export * from './sync'

// State hooks
export * from './state'

// Utility hooks
export * from './utils'

// Domain-specific (root level)
export { useImpactCalculation } from './useImpactCalculation'
