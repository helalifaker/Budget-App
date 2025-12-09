/**
 * ModuleDock - Mobile Header with Subpage Tabs
 *
 * On mobile, this replaces SmartHeader (which is hidden).
 * Shows:
 * - Compact logo
 * - Current module indicator
 * - Search button
 * - Horizontal scroll of subpage tabs if in a module
 *
 * Note: Main module navigation is handled by MobileBottomNav on mobile.
 */

import { useNavigate } from '@tanstack/react-router'
import { useActiveModule, useActiveSubpages, MODULE_COLORS } from '@/contexts/ModuleContext'
import { cn } from '@/lib/utils'
import { Search, Menu } from 'lucide-react'

interface ModuleDockProps {
  /** Callback to open command palette */
  onOpenCommandPalette?: () => void
  /** Callback to open mobile menu */
  onOpenMobileMenu?: () => void
}

export function ModuleDock({ onOpenCommandPalette, onOpenMobileMenu }: ModuleDockProps) {
  const navigate = useNavigate()
  const { activeModule, definition } = useActiveModule()
  const { subpages, isSubpageActive, hasSubpages, moduleColor } = useActiveSubpages()

  const colorClasses = MODULE_COLORS[moduleColor]

  const handleLogoClick = () => {
    navigate({ to: '/command-center' })
  }

  const handleSubpageClick = (path: string) => {
    navigate({ to: path })
  }

  const handleOpenCommandPalette = () => {
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
    })
    document.dispatchEvent(event)
    onOpenCommandPalette?.()
  }

  return (
    <div
      className={cn(
        // Only visible on mobile
        'md:hidden',
        // Layout
        'flex flex-col',
        // Background
        'bg-white/95 backdrop-blur-lg',
        // Border
        'border-b border-[#E8E6E1]',
        // Shadow
        'shadow-sm',
        // Z-index
        'relative z-20'
      )}
    >
      {/* Top bar: Logo + Module name + Actions */}
      <div className="flex items-center justify-between h-12 px-4">
        {/* Left: Logo + Module */}
        <div className="flex items-center gap-3">
          {/* Menu button */}
          <button
            onClick={onOpenMobileMenu}
            className={cn(
              'p-2 -ml-2 rounded-lg',
              'text-[#5C5A54] hover:text-[#1A1917]',
              'hover:bg-[#F5F4F1]',
              'transition-colors',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40'
            )}
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Logo */}
          <button
            onClick={handleLogoClick}
            className={cn(
              'flex items-center gap-2',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40 rounded'
            )}
            aria-label="Go to Command Center"
          >
            <div
              className={cn(
                'w-7 h-7 rounded-md flex items-center justify-center',
                'bg-gradient-to-br from-[#BDA474] via-[#A68B5B] to-[#8F7750]'
              )}
              aria-hidden="true"
            >
              <span className="text-white font-bold text-xs">EF</span>
            </div>
          </button>

          {/* Current module indicator */}
          {definition && (
            <>
              <div className="h-4 w-px bg-[#E8E6E1]" aria-hidden="true" />
              <div className="flex items-center gap-1.5">
                <definition.icon className={cn('w-4 h-4', colorClasses.text)} />
                <span className="text-sm font-medium text-[#1A1917]">{definition.label}</span>
              </div>
            </>
          )}
        </div>

        {/* Right: Search */}
        <button
          onClick={handleOpenCommandPalette}
          className={cn(
            'p-2 rounded-lg',
            'text-[#8A877E] hover:text-[#5C5A54]',
            'hover:bg-[#F5F4F1]',
            'transition-colors',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40'
          )}
          aria-label="Open search"
        >
          <Search className="w-5 h-5" />
        </button>
      </div>

      {/* Subpage tabs (if in module with subpages) */}
      {hasSubpages && activeModule !== 'command-center' && (
        <nav
          role="navigation"
          aria-label="Subpage navigation"
          className={cn(
            'flex items-center gap-1 px-4 pb-2',
            'overflow-x-auto scrollbar-hide',
            '-mx-1'
          )}
        >
          {subpages.map((subpage) => {
            const isActive = isSubpageActive(subpage.path)

            return (
              <button
                key={subpage.id}
                onClick={() => handleSubpageClick(subpage.path)}
                aria-current={isActive ? 'page' : undefined}
                className={cn(
                  // Base styles
                  'relative flex items-center justify-center',
                  'px-3 py-1.5 rounded-md',
                  'text-sm font-medium whitespace-nowrap',
                  // Transition
                  'transition-all duration-150 ease-out',
                  // Focus
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40',
                  // Touch target
                  'min-h-[32px]',
                  // States
                  isActive
                    ? 'text-[#1A1917] bg-[#F5F4F1]'
                    : 'text-[#5C5A54] hover:text-[#1A1917] hover:bg-[#F5F4F1]/60'
                )}
              >
                {subpage.label}

                {/* Active indicator */}
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
        </nav>
      )}
    </div>
  )
}
