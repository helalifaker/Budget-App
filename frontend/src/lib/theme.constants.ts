// ============================================================================
// EFIR BUDGET APP - THEME CONSTANTS
// Complete TypeScript theme definition for React applications
// ============================================================================

// ============================================================================
// COLOR PALETTE
// ============================================================================

export const colors = {
  // -------------------------------------------------------------------------
  // Background Colors
  // -------------------------------------------------------------------------
  bg: {
    /** Main page background - warm off-white */
    canvas: '#FAF9F7',
    /** Card/surface background - pure white */
    paper: '#FFFFFF',
    /** Subtle backgrounds, hover states */
    subtle: '#F5F4F1',
    /** Warm tinted backgrounds */
    warm: '#FBF9F6',
    /** Muted background for disabled states */
    muted: '#F0EFEC',
  },

  // -------------------------------------------------------------------------
  // Border Colors
  // -------------------------------------------------------------------------
  border: {
    /** Default borders */
    light: '#E8E6E1',
    /** Emphasized borders, hover states */
    medium: '#D4D1C9',
    /** Strong borders, focus states */
    strong: '#C5C2B8',
  },

  // -------------------------------------------------------------------------
  // Text Colors
  // -------------------------------------------------------------------------
  text: {
    /** Primary text - warm black */
    primary: '#1A1917',
    /** Secondary text */
    secondary: '#5C5A54',
    /** Tertiary text, labels */
    tertiary: '#8A877E',
    /** Muted text, placeholders */
    muted: '#B5B2A9',
    /** Disabled text */
    disabled: '#D4D1C9',
  },

  // -------------------------------------------------------------------------
  // Accent Colors
  // -------------------------------------------------------------------------
  accent: {
    /** Gold - Primary accent, actions, links */
    gold: {
      DEFAULT: '#A68B5B',
      hover: '#8F7750',
      light: 'rgba(166, 139, 91, 0.12)',
      lighter: 'rgba(166, 139, 91, 0.06)',
    },
    /** Sage - Success, positive states */
    sage: {
      DEFAULT: '#7D9082',
      hover: '#6B7D70',
      light: 'rgba(125, 144, 130, 0.12)',
      lighter: 'rgba(125, 144, 130, 0.06)',
    },
    /** Terracotta - Warning, attention, deficits */
    terracotta: {
      DEFAULT: '#C4785D',
      hover: '#B06A50',
      light: 'rgba(196, 120, 93, 0.12)',
      lighter: 'rgba(196, 120, 93, 0.06)',
    },
    /** Slate - Neutral accent, analysis */
    slate: {
      DEFAULT: '#64748B',
      hover: '#576478',
      light: 'rgba(100, 116, 139, 0.10)',
      lighter: 'rgba(100, 116, 139, 0.05)',
    },
    /** Wine - Secondary accent, workforce */
    wine: {
      DEFAULT: '#8B5C6B',
      hover: '#7A505D',
      light: 'rgba(139, 92, 107, 0.10)',
      lighter: 'rgba(139, 92, 107, 0.05)',
    },
  },

  // -------------------------------------------------------------------------
  // Status Colors
  // -------------------------------------------------------------------------
  status: {
    success: '#7D9082',
    successBg: 'rgba(125, 144, 130, 0.12)',
    warning: '#B45309',
    warningBg: 'rgba(245, 158, 11, 0.12)',
    error: '#C4785D',
    errorBg: 'rgba(196, 120, 93, 0.12)',
    info: '#64748B',
    infoBg: 'rgba(100, 116, 139, 0.10)',
  },

  // -------------------------------------------------------------------------
  // Badge Colors
  // -------------------------------------------------------------------------
  badge: {
    red: { bg: '#FECACA', text: '#B91C1C' },
    green: { bg: 'rgba(125, 144, 130, 0.12)', text: '#7D9082' },
    amber: { bg: 'rgba(196, 120, 93, 0.12)', text: '#C4785D' },
    yellow: { bg: 'rgba(245, 158, 11, 0.12)', text: '#B45309' },
    neutral: { bg: '#F5F4F1', text: '#B5B2A9' },
  },
} as const

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // -------------------------------------------------------------------------
  // Font Families
  // -------------------------------------------------------------------------
  fontFamily: {
    /** Display headings - elegant serif */
    display: "'Cormorant Garamond', Georgia, 'Times New Roman', serif",
    /** Body text - clean sans-serif */
    body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    /** Code/monospace */
    mono: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
  },

  // -------------------------------------------------------------------------
  // Font Sizes
  // -------------------------------------------------------------------------
  fontSize: {
    /** 10px */
    xs: '0.625rem',
    /** 11px */
    sm: '0.6875rem',
    /** 12px - base size */
    base: '0.75rem',
    /** 13px */
    md: '0.8125rem',
    /** 14px */
    lg: '0.875rem',
    /** 15px */
    xl: '0.9375rem',
    /** 16px */
    '2xl': '1rem',
    /** 22px */
    '3xl': '1.375rem',
    /** 26px */
    '4xl': '1.625rem',
    /** 32px */
    '5xl': '2rem',
    /** 40px */
    '6xl': '2.5rem',
  },

  // -------------------------------------------------------------------------
  // Font Weights
  // -------------------------------------------------------------------------
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // -------------------------------------------------------------------------
  // Line Heights
  // -------------------------------------------------------------------------
  lineHeight: {
    none: 1,
    tight: 1.2,
    snug: 1.3,
    normal: 1.5,
    relaxed: 1.6,
    loose: 1.8,
  },

  // -------------------------------------------------------------------------
  // Letter Spacing
  // -------------------------------------------------------------------------
  letterSpacing: {
    tighter: '-0.5px',
    tight: '-0.3px',
    normal: '0',
    wide: '0.3px',
    wider: '0.5px',
    widest: '1px',
  },
} as const

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  0: '0',
  px: '1px',
  0.5: '0.125rem', // 2px
  1: '0.25rem', // 4px
  1.5: '0.375rem', // 6px
  2: '0.5rem', // 8px
  2.5: '0.625rem', // 10px
  3: '0.75rem', // 12px
  3.5: '0.875rem', // 14px
  4: '1rem', // 16px
  5: '1.25rem', // 20px
  6: '1.5rem', // 24px
  7: '1.75rem', // 28px
  8: '2rem', // 32px
  9: '2.25rem', // 36px
  10: '2.5rem', // 40px
  11: '2.75rem', // 44px
  12: '3rem', // 48px
  14: '3.5rem', // 56px
  16: '4rem', // 64px
  20: '5rem', // 80px
  24: '6rem', // 96px
} as const

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: '0',
  sm: '3px',
  md: '6px',
  lg: '8px',
  xl: '10px',
  '2xl': '12px',
  '3xl': '14px',
  '4xl': '16px',
  full: '9999px',
} as const

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: 'none',
  xs: '0 1px 2px rgba(26, 25, 23, 0.04)',
  sm: '0 2px 8px rgba(26, 25, 23, 0.06)',
  md: '0 4px 16px rgba(26, 25, 23, 0.08)',
  lg: '0 8px 32px rgba(26, 25, 23, 0.10)',
  xl: '0 12px 48px rgba(26, 25, 23, 0.12)',
  '2xl': '0 24px 64px rgba(26, 25, 23, 0.16)',
  inner: 'inset 0 2px 4px rgba(26, 25, 23, 0.06)',
  goldGlow: '0 0 0 3px rgba(166, 139, 91, 0.15)',
  sageGlow: '0 0 0 3px rgba(125, 144, 130, 0.15)',
  terracottaGlow: '0 0 0 3px rgba(196, 120, 93, 0.15)',
} as const

// ============================================================================
// TRANSITIONS
// ============================================================================

export const transitions = {
  none: 'none',
  fast: '150ms ease',
  normal: '200ms ease',
  slow: '300ms ease',
  slower: '500ms ease',
  // Specific transitions
  colors: 'color 200ms ease, background-color 200ms ease, border-color 200ms ease',
  transform: 'transform 200ms ease',
  opacity: 'opacity 200ms ease',
  shadow: 'box-shadow 200ms ease',
  all: 'all 200ms ease',
} as const

// ============================================================================
// Z-INDEX
// ============================================================================

export const zIndex = {
  behind: -1,
  base: 0,
  docked: 10,
  dropdown: 100,
  sticky: 200,
  banner: 250,
  overlay: 300,
  modal: 400,
  popover: 500,
  tooltip: 600,
  toast: 700,
  max: 9999,
} as const

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  xs: '480px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const

// ============================================================================
// MODULE THEME MAPPING
// ============================================================================

export type ModuleType = 'workforce' | 'enrollment' | 'finance' | 'analysis' | 'strategic'

export const moduleTheme: Record<
  ModuleType,
  {
    bg: string
    color: string
    icon: string
    label: string
  }
> = {
  workforce: {
    bg: colors.accent.wine.light,
    color: colors.accent.wine.DEFAULT,
    icon: '👥',
    label: 'Workforce',
  },
  enrollment: {
    bg: colors.accent.sage.light,
    color: colors.accent.sage.DEFAULT,
    icon: '🎓',
    label: 'Enrollment',
  },
  finance: {
    bg: colors.accent.gold.light,
    color: colors.accent.gold.DEFAULT,
    icon: '💰',
    label: 'Finance',
  },
  analysis: {
    bg: colors.accent.slate.light,
    color: colors.accent.slate.DEFAULT,
    icon: '📊',
    label: 'Analysis',
  },
  strategic: {
    bg: colors.bg.subtle,
    color: colors.text.tertiary,
    icon: '🎯',
    label: 'Strategic',
  },
}

// ============================================================================
// STATUS THEME MAPPING
// ============================================================================

export type StatusType = 'healthy' | 'warning' | 'alert' | 'inactive' | 'pending'

export const statusTheme: Record<
  StatusType,
  {
    bg: string
    color: string
    label: string
    icon: string
  }
> = {
  healthy: {
    bg: colors.accent.sage.light,
    color: colors.accent.sage.DEFAULT,
    label: 'Healthy',
    icon: '✓',
  },
  warning: {
    bg: colors.status.warningBg,
    color: colors.status.warning,
    label: 'Attention',
    icon: '⚠',
  },
  alert: {
    bg: colors.accent.terracotta.light,
    color: colors.accent.terracotta.DEFAULT,
    label: 'Warning',
    icon: '⚠',
  },
  inactive: {
    bg: colors.bg.subtle,
    color: colors.text.muted,
    label: 'Inactive',
    icon: '◯',
  },
  pending: {
    bg: colors.accent.gold.light,
    color: colors.accent.gold.DEFAULT,
    label: 'Pending',
    icon: '◐',
  },
}

// ============================================================================
// KPI INDICATOR MAPPING
// ============================================================================

export type KpiIndicator = 'positive' | 'negative' | 'neutral' | 'info'

export const kpiTheme: Record<
  KpiIndicator,
  {
    textColor: string
    barColor: string
    bgColor: string
    icon: string
  }
> = {
  positive: {
    textColor: colors.accent.sage.DEFAULT,
    barColor: colors.accent.sage.DEFAULT,
    bgColor: colors.accent.sage.light,
    icon: '↗',
  },
  negative: {
    textColor: colors.accent.terracotta.DEFAULT,
    barColor: colors.accent.terracotta.DEFAULT,
    bgColor: colors.accent.terracotta.light,
    icon: '↘',
  },
  neutral: {
    textColor: colors.text.primary,
    barColor: colors.accent.gold.DEFAULT,
    bgColor: colors.accent.gold.light,
    icon: '→',
  },
  info: {
    textColor: colors.accent.slate.DEFAULT,
    barColor: colors.accent.slate.DEFAULT,
    bgColor: colors.accent.slate.light,
    icon: '●',
  },
}

// ============================================================================
// PROGRESS BAR MAPPING
// ============================================================================

export type ProgressType = 'complete' | 'progress' | 'low' | 'none'

export const progressTheme: Record<ProgressType, { color: string }> = {
  complete: { color: colors.accent.sage.DEFAULT },
  progress: { color: colors.accent.gold.DEFAULT },
  low: { color: colors.accent.terracotta.DEFAULT },
  none: { color: colors.border.light },
}

// ============================================================================
// COMBINED THEME EXPORT
// ============================================================================

export const theme = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
  zIndex,
  breakpoints,
  moduleTheme,
  statusTheme,
  kpiTheme,
  progressTheme,
} as const

export type Theme = typeof theme

export default theme
