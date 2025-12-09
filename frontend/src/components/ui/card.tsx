/**
 * Premium Card Components - EFIR Luxury Warm Theme
 *
 * Board-ready card designs with:
 * - Paper background (#FFFFFF)
 * - Light border (#E8E6E1)
 * - Warm shadow system
 * - Module accent border variants (3px left border)
 * - Subtle hover lift animations
 */

import * as React from 'react'
import { cn } from '@/lib/utils'

/** Module accent color type for left border styling */
export type ModuleAccent = 'gold' | 'sage' | 'terracotta' | 'slate' | 'wine' | 'none'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Add colored accent border on left (3px) */
  accent?: boolean
  /** Module accent color for left border */
  moduleAccent?: ModuleAccent
  /** Elevated variant with stronger shadow */
  elevated?: boolean
  /** Compact padding for data-dense layouts */
  compact?: boolean
  /** Remove hover effects for static cards */
  static?: boolean
}

const accentColorMap: Record<ModuleAccent, string> = {
  gold: 'from-efir-gold-400 to-efir-gold-600',
  sage: 'from-sage-400 to-sage-600',
  terracotta: 'from-terracotta-400 to-terracotta-600',
  slate: 'from-efir-slate-400 to-efir-slate-600',
  wine: 'from-wine-400 to-wine-600',
  none: '',
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    { className, accent, moduleAccent = 'gold', elevated, compact, static: isStatic, ...props },
    ref
  ) => {
    const showAccent = accent && moduleAccent !== 'none'

    return (
      <div
        ref={ref}
        className={cn(
          // Base styles
          'relative bg-paper rounded-xl overflow-hidden',
          'border border-[#E8E6E1]',
          'transition-all duration-300 ease-out',
          // Shadow
          elevated ? 'shadow-efir-lg' : 'shadow-efir-sm',
          // Hover effects (unless static)
          !isStatic && ['hover:shadow-efir-md', 'hover:border-[#D4D1C9]', 'hover:-translate-y-0.5'],
          // Compact padding
          compact && '[&_.card-content]:p-4 [&_.card-header]:px-4 [&_.card-header]:py-3',
          // Left padding for accent bar
          showAccent && 'pl-1',
          className
        )}
        {...props}
      >
        {/* Module accent bar (3px) */}
        {showAccent && (
          <div
            className={cn(
              'absolute top-0 left-0 w-[3px] h-full bg-gradient-to-b rounded-l-xl',
              accentColorMap[moduleAccent]
            )}
            aria-hidden="true"
          />
        )}
        {props.children}
      </div>
    )
  }
)
Card.displayName = 'Card'

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'card-header flex flex-col space-y-1.5 px-5 py-4',
        'border-b border-[#E8E6E1]',
        'bg-gradient-to-r from-subtle/80 to-transparent',
        className
      )}
      {...props}
    />
  )
)
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'text-lg font-display font-semibold leading-none tracking-tight',
        'text-text-primary',
        className
      )}
      {...props}
    />
  )
)
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('text-sm text-text-secondary mt-1', className)} {...props} />
))
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('card-content p-5', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex items-center px-5 py-4',
        'border-t border-[#E8E6E1]',
        'bg-subtle/50',
        className
      )}
      {...props}
    />
  )
)
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
