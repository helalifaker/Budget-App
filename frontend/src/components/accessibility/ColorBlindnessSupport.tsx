/* eslint-disable react-refresh/only-export-components */
/**
 * Color Blindness Support Components
 *
 * Provides visual patterns and icons in addition to colors to convey information.
 * Supports users with various types of color vision deficiency:
 * - Deuteranopia (green-blind)
 * - Protanopia (red-blind)
 * - Tritanopia (blue-blind)
 * - Achromatopsia (complete color blindness)
 *
 * WCAG 2.1 Success Criteria:
 * - 1.4.1 (Level A) - Use of Color
 * - 1.4.11 (Level AA) - Non-text Contrast
 */

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  AlertCircle,
  Clock,
  CheckCheck,
  CircleDot,
  Circle,
  Minus,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'

// ============================================================================
// Status Indicators with Icons and Patterns
// ============================================================================

export type StatusType = 'success' | 'error' | 'warning' | 'info' | 'pending' | 'neutral'

interface StatusIndicatorProps {
  status: StatusType
  label?: string
  showIcon?: boolean
  showPattern?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const STATUS_CONFIG: Record<
  StatusType,
  {
    icon: typeof CheckCircle2
    pattern: string
    bgColor: string
    textColor: string
    borderColor: string
    ariaLabel: string
  }
> = {
  success: {
    icon: CheckCircle2,
    pattern: 'pattern-dots',
    bgColor: 'bg-sage-100',
    textColor: 'text-sage-700',
    borderColor: 'border-sage-500',
    ariaLabel: 'Success',
  },
  error: {
    icon: XCircle,
    pattern: 'pattern-diagonal',
    bgColor: 'bg-error-100',
    textColor: 'text-error-700',
    borderColor: 'border-error-500',
    ariaLabel: 'Error',
  },
  warning: {
    icon: AlertTriangle,
    pattern: 'pattern-zigzag',
    bgColor: 'bg-terracotta-100',
    textColor: 'text-terracotta-700',
    borderColor: 'border-terracotta-500',
    ariaLabel: 'Warning',
  },
  info: {
    icon: Info,
    pattern: 'pattern-horizontal',
    bgColor: 'bg-twilight-100',
    textColor: 'text-text-secondary',
    borderColor: 'border-twilight-500',
    ariaLabel: 'Information',
  },
  pending: {
    icon: Clock,
    pattern: 'pattern-cross',
    bgColor: 'bg-gold-100',
    textColor: 'text-gold-700',
    borderColor: 'border-gold-500',
    ariaLabel: 'Pending',
  },
  neutral: {
    icon: Circle,
    pattern: 'pattern-none',
    bgColor: 'bg-subtle',
    textColor: 'text-text-secondary',
    borderColor: 'border-border-medium',
    ariaLabel: 'Neutral',
  },
}

const SIZE_CONFIG = {
  sm: { icon: 'h-3 w-3', text: 'text-xs', padding: 'px-1.5 py-0.5' },
  md: { icon: 'h-4 w-4', text: 'text-sm', padding: 'px-2 py-1' },
  lg: { icon: 'h-5 w-5', text: 'text-base', padding: 'px-3 py-1.5' },
}

/**
 * StatusIndicator displays status with icon, color, AND pattern for maximum accessibility.
 * Never relies on color alone to convey meaning.
 */
export function StatusIndicator({
  status,
  label,
  showIcon = true,
  showPattern = false,
  size = 'md',
  className,
}: StatusIndicatorProps) {
  const config = STATUS_CONFIG[status]
  const sizeConfig = SIZE_CONFIG[size]
  const Icon = config.icon

  return (
    <span
      role="status"
      aria-label={label || config.ariaLabel}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        'border-2',
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizeConfig.padding,
        sizeConfig.text,
        showPattern && config.pattern,
        className
      )}
    >
      {showIcon && <Icon className={cn(sizeConfig.icon, 'flex-shrink-0')} aria-hidden="true" />}
      {label && <span>{label}</span>}
    </span>
  )
}

// ============================================================================
// Data Visualization Patterns
// ============================================================================

export type TrendType = 'up' | 'down' | 'stable' | 'unknown'

interface TrendIndicatorProps {
  trend: TrendType
  value?: string | number
  label?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const TREND_CONFIG: Record<
  TrendType,
  {
    icon: typeof TrendingUp
    pattern: string
    color: string
    ariaLabel: string
  }
> = {
  up: {
    icon: TrendingUp,
    pattern: 'pattern-arrow-up',
    color: 'text-sage-600',
    ariaLabel: 'Increasing',
  },
  down: {
    icon: TrendingDown,
    pattern: 'pattern-arrow-down',
    color: 'text-error-600',
    ariaLabel: 'Decreasing',
  },
  stable: {
    icon: Minus,
    pattern: 'pattern-horizontal',
    color: 'text-text-secondary',
    ariaLabel: 'Stable',
  },
  unknown: {
    icon: CircleDot,
    pattern: 'pattern-dots',
    color: 'text-sand-600',
    ariaLabel: 'Unknown',
  },
}

/**
 * TrendIndicator shows directional trends with icons for color-blind users.
 */
export function TrendIndicator({
  trend,
  value,
  label,
  size = 'md',
  className,
}: TrendIndicatorProps) {
  const config = TREND_CONFIG[trend]
  const sizeConfig = SIZE_CONFIG[size]
  const Icon = config.icon

  return (
    <span
      role="status"
      aria-label={`${label || config.ariaLabel}${value ? `: ${value}` : ''}`}
      className={cn('inline-flex items-center gap-1', config.color, sizeConfig.text, className)}
    >
      <Icon className={cn(sizeConfig.icon, 'flex-shrink-0')} aria-hidden="true" />
      {value && <span className="font-medium">{value}</span>}
    </span>
  )
}

// ============================================================================
// Progress States with Patterns
// ============================================================================

export type ProgressState = 'not_started' | 'in_progress' | 'completed' | 'blocked'

interface ProgressStateIndicatorProps {
  state: ProgressState
  label?: string
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const PROGRESS_CONFIG: Record<
  ProgressState,
  {
    icon: typeof Circle
    fillPattern: string
    color: string
    bgColor: string
    label: string
  }
> = {
  not_started: {
    icon: Circle,
    fillPattern: 'bg-transparent border-2 border-border-medium',
    color: 'text-text-secondary',
    bgColor: 'bg-subtle',
    label: 'Not started',
  },
  in_progress: {
    icon: CircleDot,
    fillPattern: 'bg-gold-200 border-2 border-gold-500',
    color: 'text-gold-700',
    bgColor: 'bg-gold-100',
    label: 'In progress',
  },
  completed: {
    icon: CheckCheck,
    fillPattern: 'bg-sage-500 border-2 border-sage-600',
    color: 'text-sage-700',
    bgColor: 'bg-sage-100',
    label: 'Completed',
  },
  blocked: {
    icon: AlertCircle,
    fillPattern: 'bg-error-200 border-2 border-error-500 pattern-diagonal',
    color: 'text-error-700',
    bgColor: 'bg-error-100',
    label: 'Blocked',
  },
}

/**
 * ProgressStateIndicator shows workflow state with distinct visual patterns.
 */
export function ProgressStateIndicator({
  state,
  label,
  showLabel = true,
  size = 'md',
  className,
}: ProgressStateIndicatorProps) {
  const config = PROGRESS_CONFIG[state]
  const sizeConfig = SIZE_CONFIG[size]
  const Icon = config.icon

  return (
    <span
      role="status"
      aria-label={label || config.label}
      className={cn('inline-flex items-center gap-2', sizeConfig.text, className)}
    >
      <span
        className={cn(
          'rounded-full flex items-center justify-center',
          config.fillPattern,
          size === 'sm' && 'h-4 w-4',
          size === 'md' && 'h-5 w-5',
          size === 'lg' && 'h-6 w-6'
        )}
        aria-hidden="true"
      >
        <Icon
          className={cn(
            config.color,
            size === 'sm' && 'h-2.5 w-2.5',
            size === 'md' && 'h-3 w-3',
            size === 'lg' && 'h-4 w-4'
          )}
        />
      </span>
      {showLabel && <span className={config.color}>{label || config.label}</span>}
    </span>
  )
}

// ============================================================================
// Color Blindness Mode Context
// ============================================================================

type ColorBlindnessMode = 'normal' | 'deuteranopia' | 'protanopia' | 'tritanopia' | 'monochrome'

interface ColorBlindnessContextType {
  mode: ColorBlindnessMode
  setMode: (mode: ColorBlindnessMode) => void
  simulationEnabled: boolean
  toggleSimulation: () => void
}

const ColorBlindnessContext = createContext<ColorBlindnessContextType | null>(null)

interface ColorBlindnessProviderProps {
  children: ReactNode
  defaultMode?: ColorBlindnessMode
}

/**
 * ColorBlindnessProvider allows testing how the app appears to color-blind users.
 * Applies CSS filters to simulate different types of color vision deficiency.
 */
export function ColorBlindnessProvider({
  children,
  defaultMode = 'normal',
}: ColorBlindnessProviderProps) {
  const [mode, setMode] = useState<ColorBlindnessMode>(defaultMode)
  const [simulationEnabled, setSimulationEnabled] = useState(false)

  const toggleSimulation = useCallback(() => {
    setSimulationEnabled((prev) => !prev)
  }, [])

  return (
    <ColorBlindnessContext.Provider value={{ mode, setMode, simulationEnabled, toggleSimulation }}>
      {children}
      <ColorBlindnessSimulationStyles mode={mode} enabled={simulationEnabled} />
    </ColorBlindnessContext.Provider>
  )
}

export function useColorBlindness() {
  const context = useContext(ColorBlindnessContext)
  if (!context) {
    throw new Error('useColorBlindness must be used within a ColorBlindnessProvider')
  }
  return context
}

/**
 * CSS filters for color blindness simulation (development/testing only).
 */
function ColorBlindnessSimulationStyles({
  mode,
  enabled,
}: {
  mode: ColorBlindnessMode
  enabled: boolean
}) {
  if (!enabled || mode === 'normal') return null

  const filters: Record<ColorBlindnessMode, string> = {
    normal: 'none',
    // Deuteranopia (green-blind) - most common
    deuteranopia: `
      url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><filter id="deuteranopia"><feColorMatrix type="matrix" values="0.625 0.375 0 0 0 0.7 0.3 0 0 0 0 0.3 0.7 0 0 0 0 0 1 0"/></filter></svg>#deuteranopia')
    `,
    // Protanopia (red-blind)
    protanopia: `
      url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><filter id="protanopia"><feColorMatrix type="matrix" values="0.567 0.433 0 0 0 0.558 0.442 0 0 0 0 0.242 0.758 0 0 0 0 0 1 0"/></filter></svg>#protanopia')
    `,
    // Tritanopia (blue-blind)
    tritanopia: `
      url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><filter id="tritanopia"><feColorMatrix type="matrix" values="0.95 0.05 0 0 0 0 0.433 0.567 0 0 0 0.475 0.525 0 0 0 0 0 1 0"/></filter></svg>#tritanopia')
    `,
    // Monochrome (complete color blindness)
    monochrome: 'grayscale(100%)',
  }

  return (
    <style>{`
      html {
        filter: ${filters[mode]};
      }
    `}</style>
  )
}

// ============================================================================
// Pattern CSS Styles
// ============================================================================

/**
 * PatternStyles injects CSS for visual patterns used alongside colors.
 */
export function PatternStyles() {
  return (
    <style>{`
      /* Dot pattern - for success states */
      .pattern-dots {
        background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
        background-size: 6px 6px;
        background-position: 0 0;
      }

      /* Diagonal lines pattern - for error states */
      .pattern-diagonal {
        background-image: repeating-linear-gradient(
          45deg,
          transparent,
          transparent 2px,
          currentColor 2px,
          currentColor 3px
        );
        background-size: 8px 8px;
      }

      /* Zigzag pattern - for warning states */
      .pattern-zigzag {
        background-image: linear-gradient(135deg, currentColor 25%, transparent 25%),
          linear-gradient(225deg, currentColor 25%, transparent 25%),
          linear-gradient(45deg, currentColor 25%, transparent 25%),
          linear-gradient(315deg, currentColor 25%, transparent 25%);
        background-size: 6px 6px;
        background-position: 0 0, 3px 0, 3px -3px, 0 3px;
      }

      /* Horizontal lines pattern - for info/stable states */
      .pattern-horizontal {
        background-image: repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          currentColor 2px,
          currentColor 3px
        );
        background-size: 100% 6px;
      }

      /* Cross pattern - for pending states */
      .pattern-cross {
        background-image:
          linear-gradient(currentColor 1px, transparent 1px),
          linear-gradient(90deg, currentColor 1px, transparent 1px);
        background-size: 6px 6px;
      }

      /* Vertical lines pattern */
      .pattern-vertical {
        background-image: repeating-linear-gradient(
          90deg,
          transparent,
          transparent 2px,
          currentColor 2px,
          currentColor 3px
        );
        background-size: 6px 100%;
      }

      /* No pattern */
      .pattern-none {
        background-image: none;
      }

      /* Pattern opacity control */
      .pattern-dots,
      .pattern-diagonal,
      .pattern-zigzag,
      .pattern-horizontal,
      .pattern-cross,
      .pattern-vertical {
        background-color: inherit;
      }

      .pattern-dots::before,
      .pattern-diagonal::before,
      .pattern-zigzag::before,
      .pattern-horizontal::before,
      .pattern-cross::before,
      .pattern-vertical::before {
        opacity: 0.15;
      }
    `}</style>
  )
}

// ============================================================================
// Data Table Cell Patterns
// ============================================================================

interface DataCellProps {
  value: number | string
  status?: StatusType
  trend?: TrendType
  className?: string
}

/**
 * DataCell renders values with status/trend indicators for color-blind users.
 * Designed for use in AG Grid or data tables.
 */
export function DataCell({ value, status, trend, className }: DataCellProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {status && <StatusIndicator status={status} size="sm" showIcon showPattern={false} />}
      <span className="font-mono">{value}</span>
      {trend && <TrendIndicator trend={trend} size="sm" />}
    </div>
  )
}

// ============================================================================
// Legend Component for Charts
// ============================================================================

interface LegendItem {
  label: string
  color: string
  pattern?: string
  icon?: typeof Circle
}

interface AccessibleLegendProps {
  items: LegendItem[]
  orientation?: 'horizontal' | 'vertical'
  className?: string
}

/**
 * AccessibleLegend displays chart legend items with icons and patterns.
 */
export function AccessibleLegend({
  items,
  orientation = 'horizontal',
  className,
}: AccessibleLegendProps) {
  return (
    <div
      role="list"
      aria-label="Chart legend"
      className={cn('flex gap-4', orientation === 'vertical' && 'flex-col gap-2', className)}
    >
      {items.map((item, index) => {
        const Icon = item.icon || Circle
        return (
          <div key={index} role="listitem" className="flex items-center gap-2 text-sm">
            <span
              className={cn(
                'h-4 w-4 rounded border-2 flex items-center justify-center',
                item.color,
                item.pattern
              )}
              aria-hidden="true"
            >
              <Icon className="h-2.5 w-2.5" />
            </span>
            <span className="text-text-secondary">{item.label}</span>
          </div>
        )
      })}
    </div>
  )
}

export default StatusIndicator
