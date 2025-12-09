/**
 * SmartHeader - Executive Cockpit Topbar with Module Navigation
 *
 * A premium header combining:
 * - Logo (links to Command Center)
 * - Module tabs (horizontal navigation)
 * - Budget Version selector (compact)
 * - User avatar with dropdown
 *
 * This is the ONLY place module names appear (no repetition).
 * Hidden on mobile - MobileBottomNav handles module navigation there.
 */

import { useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { GlobalVersionSelector } from '@/components/GlobalVersionSelector'
import { AccessibilityToggle } from '@/components/accessibility'
import { useAuth } from '@/contexts/AuthContext'
import { useModule, MODULE_ORDER, MODULES, type ModuleId } from '@/contexts/ModuleContext'
import { toast } from 'sonner'
import { LogOut, User, Search, Command, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SmartHeaderProps {
  /** Callback to open command palette */
  onOpenCommandPalette?: () => void
}

export function SmartHeader({ onOpenCommandPalette }: SmartHeaderProps) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const { isModuleActive, getModuleColors } = useModule()

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

  const handleLogoClick = () => {
    navigate({ to: '/command-center' })
  }

  const handleModuleSelect = (moduleId: ModuleId) => {
    const module = MODULES[moduleId]
    navigate({ to: module.basePath })
  }

  const handleOpenCommandPalette = () => {
    // Trigger the global command palette via keyboard event
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
    })
    document.dispatchEvent(event)
    onOpenCommandPalette?.()
  }

  return (
    <header
      role="banner"
      aria-label="Application header"
      className={cn(
        // Hidden on mobile
        'hidden md:flex',
        // Size and layout
        'h-14 items-center justify-between px-4 lg:px-6',
        // Background
        'bg-white/98',
        'backdrop-blur-xl backdrop-saturate-150',
        // Border
        'border-b border-[#E8E6E1]',
        // Shadow
        'shadow-[0_1px_2px_rgba(0,0,0,0.04)]',
        // Z-index
        'relative z-20'
      )}
    >
      {/* Left: Logo */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={handleLogoClick}
          className={cn(
            'flex items-center gap-2 px-2 py-1.5 rounded-lg',
            'hover:bg-[#F5F4F1] active:bg-[#E8E6E1]',
            'transition-all duration-150',
            'focus:outline-none focus:ring-2 focus:ring-[#A68B5B]/40 focus:ring-offset-2'
          )}
          aria-label="Go to Command Center"
        >
          {/* Logo mark */}
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center',
              'bg-gradient-to-br from-[#BDA474] via-[#A68B5B] to-[#8F7750]',
              'shadow-[0_2px_8px_-2px_rgba(166,139,91,0.5)]'
            )}
            aria-hidden="true"
          >
            <span className="text-white font-bold text-sm tracking-tight">EF</span>
          </div>
          <div className="hidden lg:flex flex-col">
            <span className="text-sm font-semibold text-[#1A1917] tracking-tight leading-none">
              EFIR
            </span>
            <span className="text-[10px] text-[#8A877E] font-medium">Budget</span>
          </div>
        </button>

        {/* Separator */}
        <div className="h-6 w-px bg-[#E8E6E1] mx-2" aria-hidden="true" />
      </div>

      {/* Center: Module Tabs */}
      <nav role="navigation" aria-label="Module navigation" className="flex items-center gap-1">
        {MODULE_ORDER.map((moduleId) => {
          const module = MODULES[moduleId]
          const ModuleIcon = module.icon
          const isActive = isModuleActive(moduleId)
          const colorClasses = getModuleColors(moduleId)

          return (
            <button
              key={moduleId}
              onClick={() => handleModuleSelect(moduleId)}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                // Base styles
                'relative flex items-center gap-2',
                'px-3 py-2 rounded-lg',
                'text-sm font-medium',
                // Transition
                'transition-all duration-150 ease-out',
                // Focus state
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40',
                // States
                isActive
                  ? 'text-[#1A1917] bg-[#F5F4F1]'
                  : 'text-[#5C5A54] hover:text-[#1A1917] hover:bg-[#F5F4F1]/60'
              )}
            >
              <ModuleIcon
                className={cn(
                  'w-4 h-4 transition-colors',
                  isActive ? colorClasses.text : 'text-[#8A877E]'
                )}
              />
              <span className="hidden lg:inline">{module.label}</span>

              {/* Active indicator - colored underline */}
              {isActive && (
                <span
                  className={cn(
                    'absolute bottom-0 left-3 right-3 h-0.5 rounded-full',
                    colorClasses.bg
                  )}
                  aria-hidden="true"
                />
              )}
            </button>
          )
        })}

        {/* Configuration (Settings) - separate from main modules */}
        <div className="h-5 w-px bg-[#E8E6E1] mx-1" aria-hidden="true" />
        <button
          onClick={() => handleModuleSelect('configuration')}
          aria-current={isModuleActive('configuration') ? 'page' : undefined}
          aria-label="Configuration settings"
          className={cn(
            'relative flex items-center justify-center',
            'p-2 rounded-lg',
            'transition-all duration-150 ease-out',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40',
            isModuleActive('configuration')
              ? 'text-[#1A1917] bg-[#F5F4F1]'
              : 'text-[#8A877E] hover:text-[#5C5A54] hover:bg-[#F5F4F1]/60'
          )}
        >
          <Settings className="w-4 h-4" />
        </button>
      </nav>

      {/* Right: Search + Version + User */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Command Palette Trigger */}
        <button
          onClick={handleOpenCommandPalette}
          className={cn(
            'hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg',
            'bg-[#F5F4F1] hover:bg-[#E8E6E1]',
            'border border-[#E8E6E1]',
            'text-[#8A877E] text-sm',
            'transition-all duration-150',
            'focus:outline-none focus:ring-2 focus:ring-[#A68B5B]/40'
          )}
          aria-label="Open command palette (Cmd+K)"
        >
          <Search className="w-4 h-4" />
          <span className="text-[#B5B2A9]">Search...</span>
          <kbd
            className={cn(
              'inline-flex items-center gap-0.5',
              'px-1.5 py-0.5 rounded',
              'bg-white border border-[#E8E6E1]',
              'text-[10px] font-mono text-[#B5B2A9]'
            )}
          >
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </kbd>
        </button>

        {/* Search icon only on smaller screens */}
        <button
          onClick={handleOpenCommandPalette}
          className={cn(
            'lg:hidden p-2 rounded-lg',
            'text-[#8A877E] hover:text-[#5C5A54]',
            'hover:bg-[#F5F4F1]',
            'transition-colors',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#A68B5B]/40'
          )}
          aria-label="Open search"
        >
          <Search className="w-5 h-5" />
        </button>

        {/* Separator */}
        <div className="h-5 w-px bg-[#E8E6E1]" aria-hidden="true" />

        {/* Budget Version Selector */}
        <div className="hidden lg:block">
          <GlobalVersionSelector />
        </div>

        {/* Separator */}
        <div className="h-5 w-px bg-[#E8E6E1] hidden lg:block" aria-hidden="true" />

        {/* Accessibility toggle */}
        <AccessibilityToggle />

        {/* User info */}
        <div
          className={cn(
            'flex items-center gap-1.5',
            'px-2 py-1 rounded-lg',
            'hover:bg-[#F5F4F1]',
            'transition-colors'
          )}
        >
          <div className="p-1 rounded-md bg-[#A68B5B]/10 text-[#A68B5B]">
            <User className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-medium text-[#1A1917] max-w-[100px] truncate hidden xl:block">
            {user?.email?.split('@')[0]}
          </span>
        </div>

        {/* Sign out button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSignOut}
          className={cn('text-[#8A877E] hover:text-[#1A1917]', 'hover:bg-[#F5F4F1]', 'h-8 w-8 p-0')}
          aria-label="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
    </header>
  )
}
