/**
 * Planning Progress Types
 *
 * TypeScript type definitions for the planning progress tracking and validation system.
 * These types match the backend Pydantic schemas.
 */

// ==============================================================================
// Validation Types
// ==============================================================================

/**
 * Validation check result for a planning step
 */
export interface StepValidation {
  /** Unique identifier for this validation check */
  check_id: string
  /** Validation check result status */
  status: 'passed' | 'failed' | 'warning' | 'info'
  /** Human-readable validation message */
  message: string
  /** Additional details about the validation check */
  details?: Record<string, unknown>
}

/**
 * Blocker preventing progress on a planning step
 */
export interface StepBlocker {
  /** Description of the blocking issue */
  message: string
  /** Suggested action to resolve the blocker */
  resolution: string
}

/**
 * Progress and validation status for a single planning step
 */
export interface StepProgress {
  /** Step identifier: enrollment, class_structure, dhg, revenue, costs, capex */
  step_id: 'enrollment' | 'class_structure' | 'dhg' | 'revenue' | 'costs' | 'capex'
  /** Step sequence number (1-6) */
  step_number: number
  /** Current status of this planning step */
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'error'
  /** Completion percentage (0-100) */
  progress_percentage: number
  /** List of validation check results */
  validation: StepValidation[]
  /** List of blockers preventing progress on this step */
  blockers: StepBlocker[]
  /** Key metrics for this step (e.g., total_students, total_fte) */
  metrics: Record<string, number | string>
}

// ==============================================================================
// Response Types
// ==============================================================================

/**
 * Overall planning progress for a budget version
 */
export interface PlanningProgressResponse {
  /** Budget version UUID */
  budget_version_id: string
  /** Overall completion percentage (0-100) */
  overall_progress: number
  /** Number of completed steps (0-6) */
  completed_steps: number
  /** Total number of planning steps (always 6) */
  total_steps: number
  /** Progress details for each of the 6 planning steps */
  steps: StepProgress[]
}

// ==============================================================================
// Step Metadata Types
// ==============================================================================

/**
 * Static metadata for a planning step
 */
export interface StepMetadata {
  step_id: string
  step_number: number
  title: string
  description: string
  route: string
  icon: string
  prerequisite_steps: string[]
}

/**
 * Static step metadata for all 6 planning steps
 */
export const STEP_METADATA: Record<string, StepMetadata> = {
  enrollment: {
    step_id: 'enrollment',
    step_number: 1,
    title: 'Enrollment Planning',
    description: 'Project student enrollment by level and nationality',
    route: '/enrollment/planning',
    icon: 'Users',
    prerequisite_steps: [],
  },
  class_structure: {
    step_id: 'class_structure',
    step_number: 2,
    title: 'Class Structure',
    description: 'Calculate number of classes from enrollment',
    route: '/enrollment/class-structure',
    icon: 'Grid3x3',
    prerequisite_steps: ['enrollment'],
  },
  dhg: {
    step_id: 'dhg',
    step_number: 3,
    title: 'DHG Workforce Planning',
    description: 'Calculate teacher FTE requirements and allocations',
    route: '/planning/dhg',
    icon: 'Calculator',
    prerequisite_steps: ['class_structure'],
  },
  revenue: {
    step_id: 'revenue',
    step_number: 4,
    title: 'Revenue Planning',
    description: 'Project tuition, fees, and other revenue streams',
    route: '/finance/revenue',
    icon: 'DollarSign',
    prerequisite_steps: ['enrollment'],
  },
  costs: {
    step_id: 'costs',
    step_number: 5,
    title: 'Cost Planning',
    description: 'Plan personnel and operating costs',
    route: '/finance/costs',
    icon: 'TrendingDown',
    prerequisite_steps: ['dhg', 'enrollment'],
  },
  capex: {
    step_id: 'capex',
    step_number: 6,
    title: 'CapEx Planning',
    description: 'Plan capital expenditures and depreciation (optional)',
    route: '/finance/capex',
    icon: 'Building2',
    prerequisite_steps: [],
  },
}

// ==============================================================================
// Utility Types
// ==============================================================================

/**
 * Helper type for step status colors
 */
export type StepStatusColor = {
  bg: string
  border: string
  text: string
}

/**
 * Step status color mapping
 */
export const STEP_STATUS_COLORS: Record<StepProgress['status'], StepStatusColor> = {
  completed: {
    bg: 'bg-success-100',
    border: 'border-success-500',
    text: 'text-success-700',
  },
  in_progress: {
    bg: 'bg-warning-100',
    border: 'border-warning-500',
    text: 'text-warning-700',
  },
  error: {
    bg: 'bg-error-100',
    border: 'border-error-500',
    text: 'text-error-700',
  },
  blocked: {
    bg: 'bg-twilight-100',
    border: 'border-twilight-400',
    text: 'text-text-secondary',
  },
  not_started: {
    bg: 'bg-subtle',
    border: 'border-border-light',
    text: 'text-sand-600',
  },
}

/**
 * Validation status color mapping
 */
export const VALIDATION_STATUS_COLORS: Record<StepValidation['status'], string> = {
  passed: 'text-success-600',
  failed: 'text-error-600',
  warning: 'text-warning-600',
  info: 'text-info-600',
}
