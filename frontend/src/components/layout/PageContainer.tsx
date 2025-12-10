/**
 * Page Container - Content Wrapper
 *
 * Simple content wrapper for module pages:
 * - Centered responsive layout
 * - Viewport-optimized content area
 * - No header (title shown in ModuleHeader from ModuleLayout)
 *
 * UI Redesign: Removed duplicate header section - ModuleHeader now handles titles
 */

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageContainerProps {
  /** @deprecated Title now shown in ModuleHeader */
  title?: string
  /** @deprecated Description now shown in TaskDescription */
  description?: string
  /** Optional action buttons to display */
  actions?: ReactNode
  children: ReactNode
  /** @deprecated Use TaskDescription instead */
  breadcrumbs?: Array<{ label: string; href?: string }>
  /** Use viewport-fit layout (no scroll on main content) */
  viewportFit?: boolean
  /** @deprecated No longer used - header removed */
  compactHeader?: boolean
  className?: string
}

export function PageContainer({
  children,
  actions,
  viewportFit = false,
  className,
}: PageContainerProps) {
  return (
    <div
      className={cn(
        // Centered responsive layout
        'mx-auto w-full xl:max-w-[85%] 2xl:max-w-[80%]',
        viewportFit && 'page-viewport-fit',
        className
      )}
    >
      {/* Optional actions bar (if provided) */}
      {actions && (
        <div className="flex items-center justify-end px-6 py-3 border-b border-border-light">
          <div className="flex items-center gap-3">{actions}</div>
        </div>
      )}

      {/* Main Content */}
      <div className={cn(viewportFit ? 'flex-1 overflow-y-auto' : '')}>{children}</div>
    </div>
  )
}
