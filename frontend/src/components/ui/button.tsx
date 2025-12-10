/* eslint-disable react-refresh/only-export-components */
/**
 * Premium Button Components - EFIR Luxury Warm Theme
 *
 * Executive-ready buttons with:
 * - Gold primary styling (#A68B5B)
 * - Terracotta destructive styling (#C4785D)
 * - Warm hover animations
 * - WCAG compliant touch targets
 * - Multiple variants for all use cases
 */

import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  // Base styles - all buttons
  [
    'inline-flex items-center justify-center gap-2',
    'whitespace-nowrap rounded-lg text-sm font-medium',
    'font-body',
    'transition-all duration-200 ease-out',
    // Focus ring - Gold glow
    'ring-offset-paper',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-efir-gold focus-visible:ring-offset-2',
    'focus-visible:shadow-gold-glow',
    // Disabled state
    'disabled:pointer-events-none disabled:opacity-50',
    // Active press effect
    'active:scale-[0.98]',
  ],
  {
    variants: {
      variant: {
        // Primary - Gold background (#A68B5B)
        default: [
          'bg-efir-gold-500 text-white font-semibold',
          'shadow-efir-sm',
          'hover:bg-efir-gold-600 hover:shadow-efir-md',
        ],
        // Destructive - Terracotta (#C4785D)
        destructive: [
          'bg-terracotta-500 text-white',
          'shadow-efir-sm',
          'hover:bg-terracotta-600 hover:shadow-efir-md',
          'hover:shadow-terracotta-glow',
        ],
        // Outline - Bordered with hover fill
        outline: [
          'border border-border-medium bg-paper',
          'text-text-primary',
          'shadow-xs',
          'hover:bg-subtle hover:border-border-strong',
          'hover:shadow-efir-sm',
        ],
        // Secondary - Paper background, medium border
        secondary: [
          'bg-paper border border-border-medium',
          'text-text-primary',
          'shadow-xs',
          'hover:bg-subtle hover:border-border-strong',
        ],
        // Ghost - Transparent, hover subtle background
        ghost: ['text-text-secondary', 'hover:bg-subtle', 'hover:text-text-primary'],
        // Link - Text only
        link: [
          'text-efir-gold-500 font-medium',
          'underline-offset-4',
          'hover:underline hover:text-efir-gold-600',
        ],
        // Premium - Extra luxe styling with gradient
        premium: [
          'bg-gradient-to-r from-efir-gold-400 via-efir-gold-500 to-efir-gold-600',
          'text-white font-semibold',
          'shadow-efir-md',
          'hover:shadow-efir-lg hover:shadow-gold-glow',
          'hover:from-efir-gold-500 hover:via-efir-gold-600 hover:to-efir-gold-700',
          'border border-efir-gold-400/20',
        ],
        // Success - Sage green (#7D9082)
        success: [
          'bg-sage-500 text-white',
          'shadow-efir-sm',
          'hover:bg-sage-600 hover:shadow-efir-md',
          'hover:shadow-sage-glow',
        ],
        // Info - Slate (#64748B)
        info: [
          'bg-efir-slate-500 text-white',
          'shadow-efir-sm',
          'hover:bg-efir-slate-600 hover:shadow-efir-md',
        ],
        // Wine - Secondary accent (#8B5C6B)
        wine: [
          'bg-wine-500 text-white',
          'shadow-efir-sm',
          'hover:bg-wine-600 hover:shadow-efir-md',
        ],
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-10 rounded-lg px-3', // WCAG touch target minimum
        lg: 'h-11 rounded-lg px-8',
        xl: 'h-12 rounded-lg px-10 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
