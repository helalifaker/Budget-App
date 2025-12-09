/**
 * Premium Header Component - Sahara Luxe Theme
 *
 * Compact 56px header with:
 * - Subtle glass morphism effect
 * - Gold accent borders
 * - Premium user controls
 * - Viewport-optimized height
 */

import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { GlobalVersionSelector } from '@/components/GlobalVersionSelector'
import { AccessibilityToggle } from '@/components/accessibility'
import { toast } from 'sonner'
import { LogOut, User } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Header() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

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
      aria-label="Application header"
      className={cn(
        // Size and layout
        'h-14 flex items-center justify-between px-5',
        // Premium background with glass effect
        'bg-white/80 backdrop-blur-md',
        // Bottom border with gold accent
        'border-b border-border-light',
        // Subtle shadow
        'shadow-sm'
      )}
    >
      {/* Left: Compact app title */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <h2 className="text-base font-display font-semibold text-text-primary tracking-tight">
          EFIR Budget
        </h2>
        {/* Gold accent dot */}
        <div
          className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
          aria-hidden="true"
        />
      </div>

      {/* Center: Global Version Selector */}
      <div className="flex-1 flex justify-center px-4 max-w-md">
        <GlobalVersionSelector />
      </div>

      {/* Right: Accessibility toggle, User info & logout */}
      <div data-testid="user-menu" className="flex items-center gap-3 flex-shrink-0">
        {/* Accessibility settings toggle */}
        <AccessibilityToggle />

        {/* Separator */}
        <div className="h-5 w-px bg-subtle" aria-hidden="true" />

        {/* User info */}
        <div
          data-testid="user-info"
          className={cn('flex items-center gap-2', 'px-2.5 py-1.5 rounded-lg', 'bg-subtle/80')}
        >
          <div className="p-1 rounded-md bg-gold-100 text-gold-700">
            <User data-testid="user-avatar" className="w-3.5 h-3.5" />
          </div>
          <span
            data-testid="user-email"
            className="text-sm font-medium text-text-primary max-w-[140px] truncate"
          >
            {user?.email}
          </span>
        </div>

        {/* Sign out button */}
        <Button
          data-testid="logout-button"
          variant="ghost"
          size="sm"
          onClick={handleSignOut}
          className="text-text-secondary hover:text-text-primary hover:bg-subtle"
        >
          <LogOut className="w-4 h-4" />
          <span className="sr-only sm:not-sr-only">Sign Out</span>
        </Button>
      </div>
    </header>
  )
}
