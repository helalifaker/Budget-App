/**
 * WorkflowTabs - Horizontal Workflow Step Navigation
 *
 * New UI redesign component (Phase 2) providing tab navigation for workflow
 * steps within a module.
 *
 * Layout:
 * - Height: 40px (var(--tabs-line-height))
 * - Text-only tabs (no icons per design spec)
 * - Active tab with colored underline
 * - Optional Settings tab at the end (separated)
 *
 * Features:
 * - Keyboard navigation (Arrow keys, Home, End)
 * - Module-colored active indicator
 * - Scrollable on mobile for many tabs
 * - ARIA tablist semantics
 * - Touch-friendly hit areas
 */

import { useNavigate, useLocation } from '@tanstack/react-router'
import { useActiveSubpages, MODULE_COLORS, useActiveModule } from '@/contexts/ModuleContext'
import { cn } from '@/lib/utils'
import { getTypographyClasses } from '@/styles/typography'
import { Settings } from 'lucide-react'

interface WorkflowTabsProps {
  /** Additional CSS classes */
  className?: string
  /** Whether to show a settings tab at the end */
  showSettingsTab?: boolean
  /** Path for the settings tab (if shown) */
  settingsPath?: string
}

export function WorkflowTabs({
  className,
  showSettingsTab = false,
  settingsPath,
}: WorkflowTabsProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { subpages, hasSubpages, moduleColor } = useActiveSubpages()
  const { activeModule, definition } = useActiveModule()

  // Don't render if no subpages or on command-center
  if (!hasSubpages || activeModule === 'command-center' || !definition) {
    return null
  }

  const colorClasses = MODULE_COLORS[moduleColor]

  const handleTabClick = (path: string) => {
    navigate({ to: path })
  }

  // Check if a specific path is active
  const isPathActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  // Keyboard handler for tab navigation
  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    const totalTabs = subpages.length + (showSettingsTab ? 1 : 0)
    let newIndex = index

    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault()
        newIndex = index > 0 ? index - 1 : totalTabs - 1
        break
      case 'ArrowRight':
        event.preventDefault()
        newIndex = index < totalTabs - 1 ? index + 1 : 0
        break
      case 'Home':
        event.preventDefault()
        newIndex = 0
        break
      case 'End':
        event.preventDefault()
        newIndex = totalTabs - 1
        break
      default:
        return
    }

    // Focus the new tab
    const selector =
      newIndex === subpages.length && showSettingsTab
        ? '[data-tab-settings="true"]'
        : `[data-tab-index="${newIndex}"]`
    const newTab = document.querySelector(selector) as HTMLElement
    if (newTab) {
      newTab.focus()
      // Navigate to the new tab
      if (newIndex === subpages.length && showSettingsTab && settingsPath) {
        navigate({ to: settingsPath })
      } else if (newIndex < subpages.length) {
        navigate({ to: subpages[newIndex].path })
      }
    }
  }

  return (
    <nav
      role="navigation"
      aria-label="Workflow navigation"
      className={cn(
        // Height
        'h-[var(--tabs-line-height)]',
        // Layout
        'flex items-center',
        'px-4 lg:px-6',
        // Background
        'bg-paper/80 backdrop-blur-sm',
        // Border
        'border-b border-border-light',
        className
      )}
    >
      {/* Scrollable tabs container */}
      <div
        role="tablist"
        aria-label={`${definition.label} workflow steps`}
        className={cn(
          'flex items-center gap-1',
          'flex-1',
          // Horizontal scroll on mobile
          'overflow-x-auto scrollbar-hide',
          '-mx-1 px-1'
        )}
      >
        {subpages.map((subpage, index) => {
          const isActive = isPathActive(subpage.path)

          return (
            <button
              key={subpage.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`${subpage.id}-panel`}
              data-tab-index={index}
              tabIndex={isActive ? 0 : -1}
              onClick={() => handleTabClick(subpage.path)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={cn(
                // Base styles
                'relative flex items-center justify-center',
                'px-3 py-2',
                // Typography
                getTypographyClasses(isActive ? 'tabLabelActive' : 'tabLabel'),
                // Min touch target
                'min-h-[36px]',
                // Whitespace
                'whitespace-nowrap',
                // Transition
                'transition-all duration-150 ease-out',
                // Focus state
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
                'focus-visible:ring-gold/40 rounded-md',
                // States
                isActive
                  ? 'text-text-primary'
                  : 'text-text-secondary hover:text-text-primary hover:bg-subtle/50'
              )}
            >
              {/* Tab label */}
              <span>{subpage.label}</span>

              {/* Active indicator - colored underline */}
              {isActive && (
                <span
                  className={cn(
                    'absolute bottom-0 left-2 right-2 h-0.5 rounded-full',
                    colorClasses.bg
                  )}
                  aria-hidden="true"
                />
              )}
            </button>
          )
        })}

        {/* Settings Tab (optional) */}
        {showSettingsTab && settingsPath && (
          <>
            {/* Separator */}
            <div className="h-5 w-px bg-border-light mx-2 shrink-0" aria-hidden="true" />

            <button
              role="tab"
              aria-selected={isPathActive(settingsPath)}
              data-tab-settings="true"
              tabIndex={isPathActive(settingsPath) ? 0 : -1}
              onClick={() => handleTabClick(settingsPath)}
              onKeyDown={(e) => handleKeyDown(e, subpages.length)}
              className={cn(
                // Base styles
                'relative flex items-center gap-1.5',
                'px-3 py-2',
                // Typography
                getTypographyClasses(isPathActive(settingsPath) ? 'tabLabelActive' : 'tabLabel'),
                // Min touch target
                'min-h-[36px]',
                // Whitespace
                'whitespace-nowrap',
                // Transition
                'transition-all duration-150 ease-out',
                // Focus state
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
                'focus-visible:ring-gold/40 rounded-md',
                // States
                isPathActive(settingsPath)
                  ? 'text-text-primary'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-subtle/50'
              )}
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>

              {/* Active indicator */}
              {isPathActive(settingsPath) && (
                <span
                  className={cn(
                    'absolute bottom-0 left-2 right-2 h-0.5 rounded-full',
                    'bg-text-tertiary'
                  )}
                  aria-hidden="true"
                />
              )}
            </button>
          </>
        )}
      </div>
    </nav>
  )
}

export default WorkflowTabs
