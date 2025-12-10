/**
 * ModuleHeader - Module Title Bar
 *
 * New UI redesign component (Phase 2) displaying the current module title
 * and global actions.
 *
 * Layout:
 * - Height: 48px (var(--header-line-height))
 * - Left: Logo (mobile) + Module title (20px, semibold)
 * - Right: Search button, Hamburger menu (mobile), Version selector, User avatar
 *
 * Features:
 * - Displays active module name with icon
 * - Command palette trigger (Cmd+K)
 * - Budget version selector (compact)
 * - User avatar with sign-out option
 * - Accessibility toggle
 * - Mobile: Logo + Hamburger menu for navigation drawer (Phase 5)
 */

import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useActiveModule, MODULE_COLORS } from '@/contexts/ModuleContext'
import { useAuth } from '@/contexts/AuthContext'
import { GlobalVersionSelector } from '@/components/GlobalVersionSelector'
import { AccessibilityToggle } from '@/components/accessibility'
import { MobileDrawer } from './MobileDrawer'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { getTypographyClasses } from '@/styles/typography'
import { Search, Command, User, LogOut, LayoutDashboard, Menu } from 'lucide-react'
import { toast } from 'sonner'

interface ModuleHeaderProps {
  /** Additional CSS classes */
  className?: string
}

export function ModuleHeader({ className }: ModuleHeaderProps) {
  const navigate = useNavigate()
  const { definition } = useActiveModule()
  const { user, signOut } = useAuth()
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false)

  // Get module color classes
  const colorClasses = definition ? MODULE_COLORS[definition.color] : MODULE_COLORS.neutral

  // Get module icon
  const ModuleIcon = definition?.icon ?? LayoutDashboard

  // Determine display title
  const displayTitle = definition?.label ?? 'Dashboard'

  const handleOpenCommandPalette = () => {
    // Trigger the global command palette via keyboard event
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
    })
    document.dispatchEvent(event)
  }

  const handleSignOut = async () => {
    const { error } = await signOut()

    if (error) {
      toast.error('Sign out failed', {
        description: error.message,
      })
    } else {
      toast.success('Signed out successfully', {
        description: 'You have been logged out',
      })
      navigate({ to: '/login' })
    }
  }

  return (
    <header
      role="banner"
      aria-label="Module header"
      className={cn(
        // Height
        'h-[var(--header-line-height)]',
        // Layout
        'flex items-center justify-between',
        'px-4 lg:px-6',
        // Background
        'bg-paper/95 backdrop-blur-sm',
        // Border
        'border-b border-border-light',
        // Position
        'sticky top-0',
        // Z-index
        'z-20',
        className
      )}
    >
      {/* Left: Logo (mobile) + Module Title */}
      <div className="flex items-center gap-3">
        {/* Logo - Mobile only (sidebar is hidden on mobile) */}
        <button
          onClick={() => navigate({ to: '/command-center' })}
          className={cn(
            'md:hidden flex items-center justify-center shrink-0',
            'w-8 h-8 rounded-lg',
            'bg-gradient-to-br from-gold-400 via-gold to-gold-600',
            'shadow-gold-glow',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40 focus-visible:ring-offset-2'
          )}
          aria-label="Go to Command Center"
        >
          <span className="text-white font-bold text-sm tracking-tight">EF</span>
        </button>

        {/* Module Icon - Desktop only (on mobile we show logo) */}
        <div
          className={cn(
            'hidden md:flex items-center justify-center',
            'w-7 h-7 rounded-lg',
            'bg-subtle',
            colorClasses.text
          )}
          aria-hidden="true"
        >
          <ModuleIcon className="w-4 h-4" />
        </div>

        {/* Module Title */}
        <h1 className={cn(getTypographyClasses('moduleTitle'), 'text-text-primary')}>
          {displayTitle}
        </h1>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Command Palette Trigger - Desktop */}
        <button
          onClick={handleOpenCommandPalette}
          className={cn(
            'hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg',
            'bg-subtle hover:bg-border-light',
            'border border-border-light',
            'text-text-tertiary text-sm',
            'transition-all duration-150',
            'focus:outline-none focus:ring-2 focus:ring-gold/40'
          )}
          aria-label="Open command palette (Cmd+K)"
        >
          <Search className="w-4 h-4" />
          <span className="text-text-muted">Search...</span>
          <kbd
            className={cn(
              'inline-flex items-center gap-0.5',
              'px-1.5 py-0.5 rounded',
              'bg-paper border border-border-light',
              'text-[10px] font-mono text-text-muted'
            )}
          >
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </kbd>
        </button>

        {/* Search icon - Mobile/Tablet */}
        <button
          onClick={handleOpenCommandPalette}
          className={cn(
            'lg:hidden p-2 rounded-lg',
            'text-text-tertiary hover:text-text-secondary',
            'hover:bg-subtle',
            'transition-colors',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40'
          )}
          aria-label="Open search"
        >
          <Search className="w-5 h-5" />
        </button>

        {/* Separator */}
        <div className="h-5 w-px bg-border-light" aria-hidden="true" />

        {/* Budget Version Selector - visible on all screen sizes */}
        <GlobalVersionSelector />

        {/* Separator - Desktop only */}
        <div className="h-5 w-px bg-border-light hidden sm:block" aria-hidden="true" />

        {/* Accessibility toggle */}
        <AccessibilityToggle />

        {/* User info */}
        <div
          className={cn(
            'flex items-center gap-1.5',
            'px-2 py-1 rounded-lg',
            'hover:bg-subtle',
            'transition-colors'
          )}
        >
          <div className="p-1 rounded-md bg-gold/10 text-gold">
            <User className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-medium text-text-primary max-w-[80px] truncate hidden xl:block">
            {user?.email?.split('@')[0]}
          </span>
        </div>

        {/* Sign out button - Desktop only */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSignOut}
          className={cn(
            'hidden md:flex',
            'text-text-tertiary hover:text-text-primary',
            'hover:bg-subtle',
            'h-8 w-8 p-0'
          )}
          aria-label="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </Button>

        {/* Hamburger Menu - Mobile only */}
        <button
          onClick={() => setIsMobileDrawerOpen(true)}
          className={cn(
            'md:hidden p-2 rounded-lg',
            'text-text-tertiary hover:text-text-secondary',
            'hover:bg-subtle',
            'transition-colors',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40'
          )}
          aria-label="Open navigation menu"
          aria-expanded={isMobileDrawerOpen}
          aria-controls="mobile-drawer"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Navigation Drawer (Phase 5) */}
      <MobileDrawer isOpen={isMobileDrawerOpen} onClose={() => setIsMobileDrawerOpen(false)} />
    </header>
  )
}

export default ModuleHeader
