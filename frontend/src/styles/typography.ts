/**
 * EFIR Budget Planning Application - Typography Design System
 *
 * This file defines the typographic hierarchy for the new UI redesign.
 * Based on the UI_REDESIGN_PLAN.md Phase 1.1 specifications.
 *
 * Usage in components:
 * ```tsx
 * import { TYPOGRAPHY, getTypographyClasses } from '@/styles/typography';
 *
 * // Direct style object usage
 * <h1 style={TYPOGRAPHY.moduleTitle}>Enrollment</h1>
 *
 * // Tailwind class generation
 * <h1 className={getTypographyClasses('moduleTitle')}>Enrollment</h1>
 * ```
 */

/**
 * Typography style definitions
 * Each style includes size, weight, lineHeight, and optional color
 */
export const TYPOGRAPHY = {
  /** Module titles - large, bold headings (20px, 600 weight) */
  moduleTitle: {
    size: '20px',
    weight: '600',
    lineHeight: '1.3',
    letterSpacing: '-0.3px',
  },

  /** Workflow tab labels - medium weight, clear hierarchy (14px, 500 weight) */
  tabLabel: {
    size: '14px',
    weight: '500',
    lineHeight: '1.5',
    letterSpacing: '0',
  },

  /** Active tab - slightly bolder for emphasis */
  tabLabelActive: {
    size: '14px',
    weight: '600',
    lineHeight: '1.5',
    letterSpacing: '0',
  },

  /** Task/page descriptions - muted, informational text (14px, 400 weight) */
  description: {
    size: '14px',
    weight: '400',
    lineHeight: '1.5',
    color: 'var(--color-text-tertiary)',
  },

  /** Table/grid headers - compact, slightly bold (13px, 500 weight) */
  tableHeader: {
    size: '13px',
    weight: '500',
    lineHeight: '1.4',
    letterSpacing: '0.3px',
    textTransform: 'uppercase' as const,
  },

  /** Table/grid content - standard readable text (14px, 400 weight) */
  tableContent: {
    size: '14px',
    weight: '400',
    lineHeight: '1.4',
  },

  /** Button text - medium weight, clear action (14px, 500 weight) */
  button: {
    size: '14px',
    weight: '500',
    lineHeight: '1',
    letterSpacing: '0.1px',
  },

  /** Small button text - for compact buttons (13px, 500 weight) */
  buttonSmall: {
    size: '13px',
    weight: '500',
    lineHeight: '1',
  },

  /** Input/form labels (13px, 500 weight) */
  label: {
    size: '13px',
    weight: '500',
    lineHeight: '1.4',
    color: 'var(--color-text-secondary)',
  },

  /** Input field text (14px, 400 weight) */
  input: {
    size: '14px',
    weight: '400',
    lineHeight: '1.5',
  },

  /** Caption/helper text - small, muted (12px, 400 weight) */
  caption: {
    size: '12px',
    weight: '400',
    lineHeight: '1.4',
    color: 'var(--color-text-tertiary)',
  },

  /** Sidebar navigation icons label (12px, 500 weight) */
  sidebarLabel: {
    size: '12px',
    weight: '500',
    lineHeight: '1.3',
  },

  /** Badge/status text (11px, 600 weight) */
  badge: {
    size: '11px',
    weight: '600',
    lineHeight: '1',
    letterSpacing: '0.3px',
    textTransform: 'uppercase' as const,
  },

  /** KPI value - large display numbers */
  kpiValue: {
    size: '28px',
    weight: '600',
    lineHeight: '1',
    letterSpacing: '-0.5px',
    fontFamily: 'var(--font-display)',
  },

  /** KPI label - small descriptive text */
  kpiLabel: {
    size: '12px',
    weight: '500',
    lineHeight: '1.3',
    letterSpacing: '0.5px',
    textTransform: 'uppercase' as const,
    color: 'var(--color-text-tertiary)',
  },
} as const

/**
 * Type for typography style keys
 */
export type TypographyStyle = keyof typeof TYPOGRAPHY

/**
 * Maps typography styles to Tailwind-compatible CSS classes
 * These classes reference the custom font-size utilities defined in tailwind.config.ts
 */
export const TYPOGRAPHY_CLASSES: Record<TypographyStyle, string> = {
  moduleTitle: 'text-module-title font-semibold tracking-tight',
  tabLabel: 'text-tab-label font-medium',
  tabLabelActive: 'text-tab-label font-semibold',
  description: 'text-description text-text-tertiary',
  tableHeader: 'text-table-header font-medium uppercase tracking-wide',
  tableContent: 'text-table-content',
  button: 'text-button font-medium tracking-wide',
  buttonSmall: 'text-button-small font-medium',
  label: 'text-label font-medium text-text-secondary',
  input: 'text-input',
  caption: 'text-caption text-text-tertiary',
  sidebarLabel: 'text-sidebar-label font-medium',
  badge: 'text-badge font-semibold uppercase tracking-wide',
  kpiValue: 'text-kpi-value font-display font-semibold tracking-tight',
  kpiLabel: 'text-kpi-label font-medium uppercase tracking-wider text-text-tertiary',
}

/**
 * Helper function to get Tailwind classes for a typography style
 * @param style - The typography style key
 * @returns Tailwind class string
 */
export function getTypographyClasses(style: TypographyStyle): string {
  return TYPOGRAPHY_CLASSES[style]
}

/**
 * Helper function to get inline style object for a typography style
 * Useful when you need more control or CSS-in-JS compatibility
 * @param style - The typography style key
 * @returns CSSProperties-compatible object
 */
export function getTypographyStyle(style: TypographyStyle): React.CSSProperties {
  const typographyStyle = TYPOGRAPHY[style]
  return {
    fontSize: typographyStyle.size,
    fontWeight: typographyStyle.weight as React.CSSProperties['fontWeight'],
    lineHeight: typographyStyle.lineHeight,
    ...('letterSpacing' in typographyStyle && { letterSpacing: typographyStyle.letterSpacing }),
    ...('color' in typographyStyle && { color: typographyStyle.color }),
    ...('textTransform' in typographyStyle && { textTransform: typographyStyle.textTransform }),
    ...('fontFamily' in typographyStyle && { fontFamily: typographyStyle.fontFamily }),
  }
}

/**
 * Layout dimensions for the new UI design
 * These match the CSS variables in index.css
 */
export const LAYOUT = {
  /** Sidebar width when collapsed (icons only) */
  sidebarCollapsed: '64px',
  /** Sidebar width when expanded (icons + labels) */
  sidebarExpanded: '240px',
  /** Module header line height */
  headerHeight: '48px',
  /** Workflow tabs line height */
  tabsHeight: '40px',
  /** Task description line height */
  descriptionHeight: '32px',
  /** Total chrome height (header + tabs + description) */
  chromeHeight: '120px',
  /** Sidebar hover expand animation duration */
  sidebarAnimationDuration: '200ms',
} as const

/**
 * Module colors for the redesign
 * Each module has a distinct accent color
 */
export const MODULE_COLORS = {
  enrollment: {
    name: 'Sage',
    hex: '#7D9082',
    cssVar: 'var(--color-sage)',
    tailwind: 'sage',
  },
  workforce: {
    name: 'Wine',
    hex: '#8B5C6B',
    cssVar: 'var(--color-wine)',
    tailwind: 'wine',
  },
  finance: {
    name: 'Gold',
    hex: '#A68B5B',
    cssVar: 'var(--color-gold)',
    tailwind: 'gold',
  },
  analysis: {
    name: 'Slate',
    hex: '#64748B',
    cssVar: 'var(--color-slate)',
    tailwind: 'slate',
  },
  strategic: {
    name: 'Neutral',
    hex: '#6B7280',
    cssVar: 'var(--color-text-tertiary)',
    tailwind: 'gray-500',
  },
  configuration: {
    name: 'Neutral',
    hex: '#6B7280',
    cssVar: 'var(--color-text-tertiary)',
    tailwind: 'gray-500',
  },
} as const

export type ModuleName = keyof typeof MODULE_COLORS

/**
 * Get the color configuration for a module
 * @param moduleName - The module identifier
 * @returns Color configuration object
 */
export function getModuleColor(moduleName: ModuleName) {
  return MODULE_COLORS[moduleName]
}
