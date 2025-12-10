/* eslint-disable react-refresh/only-export-components */
/**
 * Premium Badge Component - EFIR Luxury Warm Theme
 *
 * Status indicators with:
 * - Sage (#7D9082) for success
 * - Terracotta (#C4785D) for warning
 * - Slate (#64748B) for info
 * - Module color variants (gold, sage, wine, slate)
 * - Consistent border styling
 */

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  // Base styles
  [
    'inline-flex items-center rounded-full',
    'px-2.5 py-0.5',
    'text-xs font-semibold font-body',
    'border',
    'transition-colors',
    'focus:outline-none focus:ring-2 focus:ring-efir-gold focus:ring-offset-2',
  ],
  {
    variants: {
      variant: {
        // Default - Gold for primary status
        default: [
          'border-efir-gold-200 bg-efir-gold-50 text-efir-gold-800',
          'hover:bg-efir-gold-100',
        ],
        // Secondary - Subtle background, secondary text
        secondary: ['border-border-medium bg-subtle text-text-secondary', 'hover:bg-bg-muted'],
        // Destructive - Terracotta error state
        destructive: [
          'border-terracotta-200 bg-terracotta-50 text-terracotta-800',
          'hover:bg-terracotta-100',
        ],
        // Outline - Bordered only
        outline: ['border-border-medium bg-transparent text-text-primary', 'hover:bg-subtle'],
        // Success - Sage green (#7D9082)
        success: ['border-sage-200 bg-sage-50 text-sage-800', 'hover:bg-sage-100'],
        // Warning - Terracotta (#C4785D)
        warning: [
          'border-terracotta-200 bg-terracotta-50 text-terracotta-800',
          'hover:bg-terracotta-100',
        ],
        // Info - Slate (#64748B)
        info: [
          'border-efir-slate-200 bg-efir-slate-50 text-efir-slate-800',
          'hover:bg-efir-slate-100',
        ],
        // Neutral - Subtle background, secondary text
        neutral: ['border-border-light bg-subtle text-text-secondary', 'hover:bg-bg-muted'],
        // Premium - Gold with glow effect
        premium: [
          'border-efir-gold-300 bg-gradient-to-r from-efir-gold-100 to-efir-gold-50 text-efir-gold-900',
          'shadow-xs',
          'hover:shadow-efir-sm',
        ],
        // Module variants
        gold: ['border-efir-gold-200 bg-efir-gold-50 text-efir-gold-700', 'hover:bg-efir-gold-100'],
        sage: ['border-sage-200 bg-sage-50 text-sage-700', 'hover:bg-sage-100'],
        wine: ['border-wine-200 bg-wine-50 text-wine-700', 'hover:bg-wine-100'],
        slate: [
          'border-efir-slate-200 bg-efir-slate-50 text-efir-slate-700',
          'hover:bg-efir-slate-100',
        ],
        terracotta: [
          'border-terracotta-200 bg-terracotta-50 text-terracotta-700',
          'hover:bg-terracotta-100',
        ],
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
