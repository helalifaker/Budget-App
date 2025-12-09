/**
 * SubpageTabs - Horizontal Subpage Navigation
 *
 * Displays horizontal tabs for navigating between subpages within a module.
 * Only renders when inside a module that has subpages defined.
 *
 * Features:
 * - Module-colored active indicator (underline)
 * - Scrollable on mobile for many tabs
 * - Touch-friendly with proper hit areas
 * - Keyboard navigation support
 * - Accessibility: role="tablist" with proper ARIA
 */

import { useNavigate } from '@tanstack/react-router'
import { useActiveSubpages, MODULE_COLORS, useActiveModule } from '@/contexts/ModuleContext'
import { cn } from '@/lib/utils'

interface SubpageTabsProps {
  /** Additional CSS classes */
  className?: string
}

export function SubpageTabs({ className }: SubpageTabsProps) {
  const navigate = useNavigate()
  const { subpages, isSubpageActive, hasSubpages, moduleColor } = useActiveSubpages()
  const { activeModule, definition } = useActiveModule()

  // Don't render if no subpages or on command-center
  if (!hasSubpages || activeModule === 'command-center' || !definition) {
    return null
  }

  const colorClasses = MODULE_COLORS[moduleColor]

  const handleTabClick = (path: string) => {
    navigate({ to: path })
  }

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    const tabs = subpages
    let newIndex = index

    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault()
        newIndex = index > 0 ? index - 1 : tabs.length - 1
        break
      case 'ArrowRight':
        event.preventDefault()
        newIndex = index < tabs.length - 1 ? index + 1 : 0
        break
      case 'Home':
        event.preventDefault()
        newIndex = 0
        break
      case 'End':
        event.preventDefault()
        newIndex = tabs.length - 1
        break
      default:
        return
    }

    // Focus and navigate to the new tab
    const newTab = document.querySelector(`[data-subpage-index="${newIndex}"]`) as HTMLElement
    if (newTab) {
      newTab.focus()
      navigate({ to: tabs[newIndex].path })
    }
  }

  return (
    <nav
      role="navigation"
      aria-label="Subpage navigation"
      className={cn(
        // Layout
        'flex items-center',
        'px-4 md:px-6',
        // Background - subtle separation from main content
        'bg-white/80 backdrop-blur-sm',
        // Border
        'border-b border-[#E8E6E1]',
        // Height
        'h-11',
        className
      )}
    >
      {/* Scrollable tabs container */}
      <div
        role="tablist"
        aria-label={`${definition.label} subpages`}
        className={cn(
          'flex items-center gap-1',
          // Horizontal scroll on mobile
          'overflow-x-auto scrollbar-hide',
          // Fade edges for scroll indication
          '-mx-1 px-1'
        )}
      >
        {subpages.map((subpage, index) => {
          const isActive = isSubpageActive(subpage.path)

          return (
            <button
              key={subpage.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`${subpage.id}-panel`}
              data-subpage-index={index}
              tabIndex={isActive ? 0 : -1}
              onClick={() => handleTabClick(subpage.path)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={cn(
                // Base styles
                'relative flex items-center justify-center',
                'px-3 py-2 rounded-md',
                'text-sm font-medium whitespace-nowrap',
                // Transition
                'transition-all duration-150 ease-out',
                // Focus state
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
                'focus-visible:ring-[#A68B5B]/40',
                // Touch target
                'min-h-[36px] min-w-[64px]',
                // States
                isActive
                  ? 'text-[#1A1917]'
                  : 'text-[#5C5A54] hover:text-[#1A1917] hover:bg-[#F5F4F1]'
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
      </div>
    </nav>
  )
}

export default SubpageTabs
