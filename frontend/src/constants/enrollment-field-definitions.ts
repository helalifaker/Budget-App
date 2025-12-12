import type { FieldDefinition } from '@/components/ui/HelpTooltip'

/**
 * Enrollment Field Definitions
 *
 * Centralized metadata for all enrollment planning fields.
 * Used by HelpTooltip components to provide consistent, helpful explanations.
 *
 * Each field includes:
 * - label: Human-friendly display name
 * - shortLabel: Abbreviated version for tight spaces
 * - description: What the field does
 * - why: Business context (why it matters)
 * - unit: The measurement unit
 * - range: Valid input range
 * - example: A practical example
 * - format: How to display the value
 * - category: 'basic' (always visible) or 'advanced' (behind toggle)
 */
export const ENROLLMENT_FIELDS = {
  // ============================================================================
  // BASIC FIELDS (Always Visible)
  // These are the essential adjustments most users might need
  // ============================================================================

  ps_entry_adjustment: {
    label: 'New Preschool Students',
    shortLabel: 'PS Entry',
    description:
      'Adjust the expected number of new Petite Section (preschool) students entering next year.',
    why: 'Use this if you have specific information about factors affecting new enrollments, such as new housing developments nearby or increased competition from other schools.',
    unit: 'students',
    range: { min: -20, max: 20, step: 5 },
    example: '+10 if you expect more families moving to the area',
    format: 'number',
    category: 'basic',
  } satisfies FieldDefinition,

  retention_adjustment: {
    label: 'Student Retention Adjustment',
    shortLabel: 'Retention',
    description:
      'Adjust the percentage of students who return each year, relative to the scenario default.',
    why: 'Higher retention means more students stay year-over-year. Use this if you have implemented new retention programs or expect changes in student mobility.',
    unit: 'percentage points',
    range: { min: -0.05, max: 0.05, step: 0.01 },
    example: '+2% if you implemented new retention programs',
    format: 'percentage',
    category: 'basic',
  } satisfies FieldDefinition,

  // ============================================================================
  // ADVANCED FIELDS (Behind Toggle)
  // These are power-user features for fine-tuning projections
  // ============================================================================

  lateral_multiplier: {
    label: 'Transfer Students Factor',
    shortLabel: 'Transfers',
    description:
      'Multiply the expected number of mid-year transfer students (students joining from other schools during the academic year).',
    why: 'A value of 1.0 uses the historical average. Increase if you expect more transfers due to marketing efforts or decreased competition; decrease if you expect fewer.',
    unit: 'multiplier',
    range: { min: 0.5, max: 1.5, step: 0.1 },
    example: '1.2 = expect 20% more transfers than the historical average',
    format: 'multiplier',
    category: 'advanced',
  } satisfies FieldDefinition,

  class_size_override: {
    label: 'Default Class Size',
    shortLabel: 'Class Size',
    description:
      'Override the default target class size for all grades. This sets a school-wide target.',
    why: 'Individual grades can still be customized in the grade-specific settings below. This is useful for setting a general policy change.',
    unit: 'students',
    range: { min: 20, max: 30, step: 1 },
    example: '26 students per class is typical for this school',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,

  max_divisions: {
    label: 'Maximum Classes Per Grade',
    shortLabel: 'Max Classes',
    description:
      'The maximum number of class sections (A, B, C, D...) allowed for this grade level.',
    why: 'This limit is typically set by classroom availability and staffing capacity. Projections will not exceed this number of classes.',
    unit: 'classes',
    range: { min: 1, max: 10, step: 1 },
    example: '4 means you can have at most 4 sections (e.g., CP-A, CP-B, CP-C, CP-D)',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,

  class_size_ceiling: {
    label: 'Maximum Students Per Class',
    shortLabel: 'Max Size',
    description: 'The maximum number of students allowed in a single class section.',
    why: 'This is typically set by regulatory limits and pedagogical best practices. Class sizes will not exceed this ceiling.',
    unit: 'students',
    range: { min: 15, max: 35, step: 1 },
    example: '28 for elementary (maternelle/élémentaire), 30 for secondary (collège/lycée)',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,

  grade_retention_rate: {
    label: 'Retention Rate',
    shortLabel: 'Retention',
    description: 'The percentage of students in this grade who continue to the next grade level.',
    why: 'Higher retention (closer to 100%) means more students stay. The default is based on historical data for this grade.',
    unit: 'percentage',
    range: { min: 0.85, max: 1.0, step: 0.01 },
    example: '97% means 3% of students leave each year (transfer or other reasons)',
    format: 'percentage',
    category: 'advanced',
  } satisfies FieldDefinition,

  grade_lateral_entry: {
    label: 'Transfer Students',
    shortLabel: 'Transfers',
    description: 'Expected number of new students joining mid-year at this specific grade level.',
    why: 'Students transferring from other schools during the year. This is in addition to the students progressing from the previous grade.',
    unit: 'students',
    range: { min: 0, max: 20, step: 1 },
    example: '5 = expect 5 transfer students joining this grade',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,

  // ============================================================================
  // CYCLE-LEVEL FIELDS
  // Used in the LevelOverridesPanel for cycle (school level) adjustments
  // ============================================================================

  cycle_class_size_ceiling: {
    label: 'Class Size Ceiling',
    shortLabel: 'Max Size',
    description: 'Maximum students per class for all grades in this cycle (school level).',
    why: 'Sets a uniform limit for the entire cycle. Individual grades can override this in advanced settings.',
    unit: 'students',
    range: { min: 15, max: 35, step: 1 },
    example: 'Maternelle: 28, Élémentaire: 28, Collège: 30, Lycée: 30',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,

  cycle_max_divisions: {
    label: 'Maximum Divisions',
    shortLabel: 'Max Divisions',
    description: 'Maximum number of class sections per grade for all grades in this cycle.',
    why: 'A division is a class section (e.g., CM1-A, CM1-B). This limits how many sections can be created.',
    unit: 'classes',
    range: { min: 2, max: 8, step: 1 },
    example: '6 = each grade can have up to 6 sections (A through F)',
    format: 'number',
    category: 'advanced',
  } satisfies FieldDefinition,
} as const

/**
 * Type for field keys
 */
export type EnrollmentFieldKey = keyof typeof ENROLLMENT_FIELDS

/**
 * Get field definition by key
 */
export function getFieldDefinition(key: EnrollmentFieldKey): FieldDefinition {
  return ENROLLMENT_FIELDS[key]
}

/**
 * Get all basic fields (always visible)
 */
export function getBasicFields(): FieldDefinition[] {
  return Object.values(ENROLLMENT_FIELDS).filter((f) => f.category === 'basic')
}

/**
 * Get all advanced fields (behind toggle)
 */
export function getAdvancedFields(): FieldDefinition[] {
  return Object.values(ENROLLMENT_FIELDS).filter((f) => f.category === 'advanced')
}

/**
 * Step introduction content for each tab
 * Used by StepIntroCard component
 */
export const STEP_INTRO_CONTENT = {
  projections: {
    stepNumber: 1,
    title: 'Enrollment Projections',
    why: 'Project how many students you will have next year and for the next 5 years. This is the primary driver for your entire budget - more students means more revenue but also more teachers needed.',
    whatToDo: [
      'Select a scenario (Base Case recommended for most schools)',
      'Review the projected numbers in the results table',
      'Adjust parameters only if you have specific information about next year',
      'Click "Calculate" to update the projections',
    ],
    tip: 'Most schools can use the Base Case scenario without adjustments. Only change parameters if you have specific information about expected changes.',
  },
  distribution: {
    stepNumber: 2,
    title: 'Nationality Distribution',
    why: 'Different nationalities have different fee structures. Defining the distribution helps calculate accurate revenue projections.',
    whatToDo: [
      'Review the current distribution for each grade level',
      'Adjust percentages if you expect changes in the student mix',
      'Ensure French + Saudi + Other = 100% for each level',
    ],
    tip: 'The distribution affects fee calculations in the Revenue module. Use historical data as your guide.',
  },
  validation: {
    stepNumber: 3,
    title: 'Lock & Continue',
    why: 'Locking your projections confirms the numbers and triggers updates to downstream modules (Class Structure, Teacher Planning, Revenue).',
    whatToDo: [
      'Review all projections one final time',
      'Click "Lock Enrollment" to confirm',
      'Proceed to Class Structure to review class formation',
    ],
    tip: 'You can unlock and edit projections later if needed. Locking simply confirms your current numbers.',
  },
} as const

export type StepIntroKey = keyof typeof STEP_INTRO_CONTENT
