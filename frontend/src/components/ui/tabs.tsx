/**
 * Premium Tabs Component - EFIR Luxury Warm Theme
 *
 * Board-ready tab navigation with:
 * - Module-colored bottom border (2px) on active state
 * - Tertiary text for inactive tabs
 * - Secondary text on hover with subtle background
 * - Smooth transitions
 */

import * as React from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

/** Module accent color type for active tab indicator */
type TabAccent = 'gold' | 'sage' | 'terracotta' | 'slate' | 'wine'

const tabTriggerVariants = cva(
  // Base styles
  [
    'inline-flex items-center justify-center gap-2',
    'whitespace-nowrap px-4 py-2 rounded-t-lg',
    'text-sm font-medium font-body',
    'transition-all duration-200',
    'ring-offset-paper',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-efir-gold focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    // Inactive state - tertiary text
    'text-text-tertiary',
    // Hover state - secondary text, subtle background
    'hover:text-text-secondary hover:bg-subtle',
    // Bottom border placeholder
    'relative',
    'after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px]',
    'after:transition-all after:duration-200',
  ],
  {
    variants: {
      accent: {
        gold: [
          'data-[state=active]:text-text-primary',
          'data-[state=active]:font-semibold',
          'data-[state=active]:after:bg-efir-gold-500',
        ],
        sage: [
          'data-[state=active]:text-text-primary',
          'data-[state=active]:font-semibold',
          'data-[state=active]:after:bg-sage-500',
        ],
        terracotta: [
          'data-[state=active]:text-text-primary',
          'data-[state=active]:font-semibold',
          'data-[state=active]:after:bg-terracotta-500',
        ],
        slate: [
          'data-[state=active]:text-text-primary',
          'data-[state=active]:font-semibold',
          'data-[state=active]:after:bg-efir-slate-500',
        ],
        wine: [
          'data-[state=active]:text-text-primary',
          'data-[state=active]:font-semibold',
          'data-[state=active]:after:bg-wine-500',
        ],
      },
    },
    defaultVariants: {
      accent: 'gold',
    },
  }
)

const Tabs = TabsPrimitive.Root

interface TabsListProps extends React.ComponentPropsWithoutRef<typeof TabsPrimitive.List> {
  /** Visual style variant */
  variant?: 'default' | 'underline'
}

const TabsList = React.forwardRef<React.ElementRef<typeof TabsPrimitive.List>, TabsListProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <TabsPrimitive.List
      ref={ref}
      className={cn(
        // Layout
        'inline-flex h-11 items-center justify-center',
        variant === 'default' && ['p-1', 'rounded-xl bg-subtle', 'border border-border-light'],
        variant === 'underline' && ['gap-1', 'border-b border-border-light'],
        // Text
        'text-text-tertiary',
        className
      )}
      {...props}
    />
  )
)
TabsList.displayName = TabsPrimitive.List.displayName

interface TabsTriggerProps
  extends
    React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>,
    VariantProps<typeof tabTriggerVariants> {}

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  TabsTriggerProps
>(({ className, accent = 'gold', ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(tabTriggerVariants({ accent }), className)}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      // Spacing
      'mt-4',
      // Animation
      'animate-fade-in',
      // Focus ring
      'ring-offset-paper',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-efir-gold focus-visible:ring-offset-2',
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent, type TabAccent }
