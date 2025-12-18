/**
 * AppSidebar - Collapsible Sidebar Navigation
 *
 * New UI redesign component (Phase 2) providing module navigation via a collapsible sidebar.
 *
 * Behavior:
 * - Desktop: 64px collapsed (icons only), 240px expanded on hover
 * - Mobile: Hidden (uses MobileBottomNav instead)
 *
 * Features:
 * - Module icons with optional labels on hover
 * - Active module highlighting with accent color
 * - Shows workflow steps (subpages) for active module when expanded
 * - Smooth 200ms expand/collapse animation
 * - Keyboard accessible (Tab + Enter/Space)
 * - ARIA landmarks and labels
 */

import { useState, useRef, useCallback, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  useModule,
  ALL_MODULES,
  ALL_MODULES_WITH_ADMIN,
  MODULES,
  type ModuleId,
} from '@/contexts/ModuleContext'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import { LAYOUT } from '@/styles/typography'

interface AppSidebarProps {
  /** Additional CSS classes */
  className?: string
}

export function AppSidebar({ className }: AppSidebarProps) {
  const navigate = useNavigate()
  const { session } = useAuth()
  const { isModuleActive, getModuleColors, activeModuleDefinition } = useModule()
  const [isExpanded, setIsExpanded] = useState(false)
  const sidebarRef = useRef<HTMLElement>(null)
  const expandTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Show Admin module only for admin users
  const isAdmin = session?.user?.user_metadata?.role === 'Admin'
  const modulesToShow = useMemo(() => (isAdmin ? ALL_MODULES_WITH_ADMIN : ALL_MODULES), [isAdmin])

  // Handle hover with slight delay for smooth UX
  const handleMouseEnter = useCallback(() => {
    if (expandTimeoutRef.current) {
      clearTimeout(expandTimeoutRef.current)
    }
    expandTimeoutRef.current = setTimeout(() => {
      setIsExpanded(true)
    }, 50) // Small delay to prevent accidental expansion
  }, [])

  const handleMouseLeave = useCallback(() => {
    if (expandTimeoutRef.current) {
      clearTimeout(expandTimeoutRef.current)
    }
    expandTimeoutRef.current = setTimeout(() => {
      setIsExpanded(false)
    }, 100) // Delay to allow moving to submenus
  }, [])

  const handleModuleSelect = (moduleId: ModuleId) => {
    const module = MODULES[moduleId]
    navigate({ to: module.basePath })
  }

  const handleSubpageSelect = (path: string) => {
    navigate({ to: path })
  }

  // Keyboard handler for module navigation
  const handleModuleKeyDown = (event: React.KeyboardEvent, moduleId: ModuleId) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleModuleSelect(moduleId)
    }
  }

  return (
    <aside
      ref={sidebarRef}
      role="navigation"
      aria-label="Module navigation"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        // Hidden on mobile
        'hidden md:flex',
        // Fixed position
        'fixed left-0 top-0 bottom-0',
        // Flex column layout
        'flex-col',
        // Width transition
        'transition-[width] ease-out',
        isExpanded ? 'w-[var(--sidebar-width-expanded)]' : 'w-[var(--sidebar-width-collapsed)]',
        // Background
        'bg-paper',
        // Border
        'border-r border-border-light',
        // Shadow when expanded
        isExpanded ? 'shadow-lg' : 'shadow-sm',
        // Z-index
        'z-30',
        className
      )}
      style={{
        transitionDuration: LAYOUT.sidebarAnimationDuration,
      }}
    >
      {/* Logo Area */}
      <div
        className={cn(
          'flex items-center',
          'h-[var(--header-line-height)]',
          'px-3',
          'border-b border-border-light',
          'shrink-0'
        )}
      >
        <button
          onClick={() => navigate({ to: '/command-center' })}
          className={cn(
            'flex items-center gap-3',
            'px-2 py-1.5 rounded-lg',
            'hover:bg-subtle active:bg-border-light',
            'transition-all duration-150',
            'focus:outline-none focus:ring-2 focus:ring-gold/40 focus:ring-offset-2'
          )}
          aria-label="Go to Command Center"
        >
          {/* Logo mark */}
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
              'bg-gradient-to-br from-gold-400 via-gold to-gold-600',
              'shadow-gold-glow'
            )}
            aria-hidden="true"
          >
            <span className="text-white font-bold text-sm tracking-tight">EF</span>
          </div>

          {/* Text - only visible when expanded */}
          <div
            className={cn(
              'flex flex-col overflow-hidden',
              'transition-opacity duration-150',
              isExpanded ? 'opacity-100' : 'opacity-0 w-0'
            )}
          >
            <span className="text-sm font-semibold text-text-primary tracking-tight leading-none whitespace-nowrap">
              EFIR Budget
            </span>
            <span className="text-[10px] text-text-tertiary font-medium whitespace-nowrap">
              Planning Application
            </span>
          </div>
        </button>
      </div>

      {/* Module Navigation */}
      <nav className="flex-1 overflow-y-auto py-2">
        <ul role="list" className="space-y-1 px-2">
          {modulesToShow.map((moduleId) => {
            const module = MODULES[moduleId]
            const ModuleIcon = module.icon
            const isActive = isModuleActive(moduleId)
            const colorClasses = getModuleColors(moduleId)

            return (
              <li key={moduleId}>
                {/* Module Button */}
                <button
                  onClick={() => handleModuleSelect(moduleId)}
                  onKeyDown={(e) => handleModuleKeyDown(e, moduleId)}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={module.label}
                  className={cn(
                    // Layout
                    'relative flex items-center w-full',
                    'px-3 py-2.5 rounded-lg',
                    // Gap for icon and text
                    'gap-3',
                    // Typography
                    'text-sm font-medium',
                    // Transition
                    'transition-all duration-150 ease-out',
                    // Focus state
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40',
                    // States
                    isActive
                      ? cn('bg-subtle', colorClasses.text)
                      : 'text-text-secondary hover:text-text-primary hover:bg-subtle/60'
                  )}
                >
                  {/* Icon */}
                  <div
                    className={cn(
                      'flex items-center justify-center',
                      'w-6 h-6 shrink-0',
                      'transition-colors duration-150'
                    )}
                  >
                    <ModuleIcon className="w-5 h-5" />
                  </div>

                  {/* Label - visible when expanded */}
                  <span
                    className={cn(
                      'whitespace-nowrap overflow-hidden',
                      'transition-opacity duration-150',
                      isExpanded ? 'opacity-100' : 'opacity-0 w-0'
                    )}
                  >
                    {module.label}
                  </span>

                  {/* Active indicator line */}
                  {isActive && (
                    <span
                      className={cn(
                        'absolute left-0 top-1/2 -translate-y-1/2',
                        'w-1 h-6 rounded-r-full',
                        colorClasses.bg
                      )}
                      aria-hidden="true"
                    />
                  )}
                </button>

                {/* Subpages - visible only when expanded and module is active */}
                {isActive &&
                  isExpanded &&
                  activeModuleDefinition &&
                  activeModuleDefinition.subpages.length > 0 && (
                    <ul role="list" className="mt-1 ml-8 space-y-0.5">
                      {activeModuleDefinition.subpages.map((subpage) => {
                        const isSubpageActive = location.pathname === subpage.path

                        return (
                          <li key={subpage.id}>
                            <button
                              onClick={() => handleSubpageSelect(subpage.path)}
                              aria-current={isSubpageActive ? 'page' : undefined}
                              className={cn(
                                'w-full text-left',
                                'px-3 py-1.5 rounded-md',
                                'text-xs font-medium',
                                'transition-all duration-150',
                                'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40',
                                isSubpageActive
                                  ? cn('bg-subtle/80', colorClasses.text)
                                  : 'text-text-tertiary hover:text-text-secondary hover:bg-subtle/40'
                              )}
                            >
                              {subpage.label}
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  )}
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer - Collapsed indicator */}
      <div
        className={cn(
          'px-3 py-3',
          'border-t border-border-light',
          'flex items-center justify-center',
          'shrink-0'
        )}
      >
        <div
          className={cn(
            'text-[10px] text-text-muted font-medium',
            'transition-opacity duration-150',
            isExpanded ? 'opacity-100' : 'opacity-0'
          )}
        >
          Hover to expand
        </div>
        {/* Expand indicator when collapsed */}
        {!isExpanded && (
          <div className="w-4 h-1 bg-border-medium rounded-full" aria-hidden="true" />
        )}
      </div>
    </aside>
  )
}

export default AppSidebar
