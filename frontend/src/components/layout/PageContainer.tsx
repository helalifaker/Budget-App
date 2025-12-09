/**
 * Premium Page Container - Sahara Luxe Theme
 *
 * Board-ready page layout with:
 * - Fixed header with title and actions
 * - Viewport-optimized content area
 * - Premium typography and spacing
 * - Subtle backdrop blur effects
 */

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageContainerProps {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
  breadcrumbs?: Array<{ label: string; href?: string }>
  /** Use viewport-fit layout (no scroll on main content) */
  viewportFit?: boolean
  /** Compact header for data-dense pages */
  compactHeader?: boolean
  className?: string
}

export function PageContainer({
  title,
  description,
  actions,
  children,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  breadcrumbs: _breadcrumbs,
  viewportFit = false,
  compactHeader = false,
  className,
}: PageContainerProps) {
  return (
    <div
      className={cn(
        // Centered 3/4 width layout
        'mx-auto w-full xl:max-w-[85%] 2xl:max-w-[80%]',
        viewportFit && 'page-viewport-fit',
        className
      )}
    >
      {/* Page Header */}
      <div
        className={cn(
          'flex items-center justify-between',
          'border-b border-border-light',
          'bg-paper/60 backdrop-blur-sm',
          compactHeader ? 'px-4 py-3' : 'px-6 py-5',
          viewportFit && 'flex-shrink-0'
        )}
      >
        <div className="min-w-0 flex-1">
          <h1
            className={cn(
              'font-display font-semibold text-text-primary tracking-tight',
              compactHeader ? 'text-xl' : 'text-2xl'
            )}
          >
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-text-secondary truncate">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3 ml-4 flex-shrink-0">{actions}</div>}
      </div>

      {/* Main Content */}
      <div className={cn(viewportFit ? 'flex-1 overflow-y-auto p-6' : 'p-6 lg:p-8')}>
        {children}
      </div>
    </div>
  )
}
