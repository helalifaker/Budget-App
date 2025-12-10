/* eslint-disable react-refresh/only-export-components */
/**
 * Module Badge Component - EFIR Luxury Warm Theme
 *
 * Badge showing module with its associated color:
 * - Enrollment: Sage (#7D9082)
 * - Workforce: Wine (#8B5C6B)
 * - Finance: Gold (#A68B5B)
 * - Analysis: Slate (#64748B)
 * - Strategic: Slate (#64748B)
 * - Configuration: Terracotta (#C4785D)
 *
 * Uses Lucide icons only (no emoji)
 */

import * as React from 'react'
import { Users, GraduationCap, Wallet, BarChart3, Target, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Supported module types */
export type ModuleType =
  | 'enrollment'
  | 'workforce'
  | 'finance'
  | 'analysis'
  | 'strategic'
  | 'configuration'

interface ModuleBadgeProps {
  /** The module to display */
  module: ModuleType
  /** Show the module icon */
  showIcon?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Additional CSS classes */
  className?: string
}

/** Module configuration with colors and icons */
const moduleConfig: Record<
  ModuleType,
  {
    label: string
    bgColor: string
    textColor: string
    borderColor: string
    icon: React.ElementType
  }
> = {
  enrollment: {
    label: 'Enrollment',
    bgColor: 'bg-sage-50',
    textColor: 'text-sage-700',
    borderColor: 'border-sage-200',
    icon: GraduationCap,
  },
  workforce: {
    label: 'Workforce',
    bgColor: 'bg-wine-50',
    textColor: 'text-wine-700',
    borderColor: 'border-wine-200',
    icon: Users,
  },
  finance: {
    label: 'Finance',
    bgColor: 'bg-efir-gold-50',
    textColor: 'text-efir-gold-700',
    borderColor: 'border-efir-gold-200',
    icon: Wallet,
  },
  analysis: {
    label: 'Analysis',
    bgColor: 'bg-efir-slate-50',
    textColor: 'text-efir-slate-700',
    borderColor: 'border-efir-slate-200',
    icon: BarChart3,
  },
  strategic: {
    label: 'Strategic',
    bgColor: 'bg-efir-slate-50',
    textColor: 'text-efir-slate-700',
    borderColor: 'border-efir-slate-200',
    icon: Target,
  },
  configuration: {
    label: 'Configuration',
    bgColor: 'bg-terracotta-50',
    textColor: 'text-terracotta-700',
    borderColor: 'border-terracotta-200',
    icon: Settings,
  },
}

const sizeStyles = {
  sm: {
    badge: 'px-2 py-0.5 text-xs',
    icon: 'w-3 h-3',
  },
  md: {
    badge: 'px-2.5 py-1 text-xs',
    icon: 'w-3.5 h-3.5',
  },
  lg: {
    badge: 'px-3 py-1.5 text-sm',
    icon: 'w-4 h-4',
  },
}

export function ModuleBadge({ module, showIcon = true, size = 'md', className }: ModuleBadgeProps) {
  const config = moduleConfig[module]
  const sizeStyle = sizeStyles[size]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-body font-medium',
        'border transition-colors',
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizeStyle.badge,
        className
      )}
    >
      {showIcon && <Icon className={cn(sizeStyle.icon, 'flex-shrink-0')} />}
      <span>{config.label}</span>
    </div>
  )
}

export { moduleConfig }
