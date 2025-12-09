/**
 * PageWrapper - Centered content container for module pages
 *
 * Creates a comfortable reading and interaction zone:
 * - Centers content at 3/4 of viewport width on large screens
 * - Full width with padding on mobile
 * - Generous vertical spacing for breathing room
 * - Consistent with the luxury/refined aesthetic
 */

import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageWrapperProps {
  children: ReactNode
  /** Additional CSS classes */
  className?: string
  /** Use full width instead of 3/4 (for data-heavy pages like grids) */
  fullWidth?: boolean
  /** Reduce vertical padding for compact pages */
  compact?: boolean
}

export function PageWrapper({
  children,
  className,
  fullWidth = false,
  compact = false,
}: PageWrapperProps) {
  return (
    <div
      className={cn(
        // Base container
        'w-full',
        // Horizontal centering and max width
        fullWidth ? 'px-6 lg:px-8' : 'mx-auto px-6 lg:px-8 xl:max-w-[85%] 2xl:max-w-[80%]',
        // Vertical padding
        compact ? 'py-4 lg:py-6' : 'py-6 lg:py-8',
        // Background
        'bg-canvas',
        // Custom classes
        className
      )}
    >
      {children}
    </div>
  )
}

/**
 * PageHeader - Standard header for module pages
 *
 * Provides consistent page title and description styling
 */
interface PageHeaderProps {
  title: string
  description?: string
  /** Icon component */
  icon?: React.ComponentType<{ className?: string }>
  /** Module color for accent */
  accentColor?: 'gold' | 'sage' | 'wine' | 'slate' | 'terracotta' | 'neutral'
  /** Right-side actions */
  actions?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  description,
  icon: Icon,
  accentColor = 'neutral',
  actions,
  className,
}: PageHeaderProps) {
  const accentClasses = {
    gold: 'text-gold-600',
    sage: 'text-sage-600',
    wine: 'text-wine-600',
    slate: 'text-slate-600',
    terracotta: 'text-terracotta-600',
    neutral: 'text-text-tertiary',
  }

  return (
    <div className={cn('flex items-start justify-between gap-4', 'mb-6 lg:mb-8', className)}>
      <div className="flex items-start gap-3">
        {Icon && (
          <div className={cn('p-2 rounded-lg bg-subtle', accentClasses[accentColor])}>
            <Icon className="w-5 h-5" />
          </div>
        )}
        <div>
          <h1 className="text-2xl lg:text-3xl font-display font-semibold text-text-primary tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-text-secondary font-body">{description}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

/**
 * PageSection - Section divider for page content
 */
interface PageSectionProps {
  title?: string
  description?: string
  children: ReactNode
  className?: string
}

export function PageSection({ title, description, children, className }: PageSectionProps) {
  return (
    <section className={cn('mb-6 lg:mb-8', className)}>
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h2 className="text-lg font-display font-semibold text-text-primary">{title}</h2>
          )}
          {description && <p className="mt-0.5 text-sm text-text-tertiary">{description}</p>}
        </div>
      )}
      {children}
    </section>
  )
}
