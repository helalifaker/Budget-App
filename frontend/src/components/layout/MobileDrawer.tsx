/**
 * MobileDrawer - Mobile Navigation Drawer
 *
 * Phase 5 component providing a slide-out navigation menu for mobile devices.
 * Triggered by the hamburger menu button in the mobile header.
 *
 * Features:
 * - Full module navigation with icons and labels
 * - Shows subpages for the active module
 * - Module-colored active indicators
 * - Budget version selector
 * - User info and sign-out
 * - Touch-friendly with smooth animations
 * - ARIA compliant for accessibility
 */

import { useNavigate } from '@tanstack/react-router'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetClose } from '@/components/ui/sheet'
import { useModule, ALL_MODULES, MODULES, type ModuleId } from '@/contexts/ModuleContext'
import { useAuth } from '@/contexts/AuthContext'
import { GlobalVersionSelector } from '@/components/GlobalVersionSelector'
import { cn } from '@/lib/utils'
import { User, LogOut, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'

interface MobileDrawerProps {
  /** Whether the drawer is open */
  isOpen: boolean
  /** Callback when drawer should close */
  onClose: () => void
}

export function MobileDrawer({ isOpen, onClose }: MobileDrawerProps) {
  const navigate = useNavigate()
  const { isModuleActive, getModuleColors, activeModuleDefinition } = useModule()
  const { user, signOut } = useAuth()

  const handleModuleSelect = (moduleId: ModuleId) => {
    const module = MODULES[moduleId]
    navigate({ to: module.basePath })
    onClose()
  }

  const handleSubpageSelect = (path: string) => {
    navigate({ to: path })
    onClose()
  }

  const handleSignOut = async () => {
    onClose()
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

  const handleHomeNavigate = () => {
    navigate({ to: '/command-center' })
    onClose()
  }

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="left" className={cn('w-[280px] p-0', 'bg-paper', 'flex flex-col')}>
        {/* Header with Logo */}
        <SheetHeader className="p-4 border-b border-border-light">
          <SheetTitle asChild>
            <button
              onClick={handleHomeNavigate}
              className={cn(
                'flex items-center gap-3',
                'text-left',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40 rounded-lg'
              )}
            >
              {/* Logo mark */}
              <div
                className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
                  'bg-gradient-to-br from-gold-400 via-gold to-gold-600',
                  'shadow-gold-glow'
                )}
                aria-hidden="true"
              >
                <span className="text-white font-bold text-base tracking-tight">EF</span>
              </div>

              {/* Text */}
              <div className="flex flex-col">
                <span className="text-base font-semibold text-text-primary tracking-tight leading-none">
                  EFIR Budget
                </span>
                <span className="text-xs text-text-tertiary font-medium">Planning Application</span>
              </div>
            </button>
          </SheetTitle>
        </SheetHeader>

        {/* Module Navigation */}
        <nav className="flex-1 overflow-y-auto py-2">
          <ul role="list" className="space-y-1 px-2">
            {ALL_MODULES.map((moduleId) => {
              const module = MODULES[moduleId]
              const ModuleIcon = module.icon
              const isActive = isModuleActive(moduleId)
              const colorClasses = getModuleColors(moduleId)

              return (
                <li key={moduleId}>
                  {/* Module Button */}
                  <button
                    onClick={() => handleModuleSelect(moduleId)}
                    aria-current={isActive ? 'page' : undefined}
                    aria-label={module.label}
                    className={cn(
                      // Layout
                      'relative flex items-center w-full',
                      'px-3 py-3 rounded-lg',
                      // Gap for icon and text
                      'gap-3',
                      // Typography
                      'text-base font-medium',
                      // Transition
                      'transition-all duration-150 ease-out',
                      // Active state scale
                      'active:scale-[0.98]',
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
                        'w-7 h-7 shrink-0',
                        'transition-colors duration-150'
                      )}
                    >
                      <ModuleIcon className="w-5 h-5" />
                    </div>

                    {/* Label */}
                    <span className="flex-1 text-left">{module.label}</span>

                    {/* Chevron for active module with subpages */}
                    {isActive &&
                      activeModuleDefinition &&
                      activeModuleDefinition.subpages.length > 0 && (
                        <ChevronRight
                          className={cn(
                            'w-4 h-4 text-text-tertiary',
                            'transition-transform duration-150',
                            'rotate-90'
                          )}
                        />
                      )}

                    {/* Active indicator line */}
                    {isActive && (
                      <span
                        className={cn(
                          'absolute left-0 top-1/2 -translate-y-1/2',
                          'w-1 h-8 rounded-r-full',
                          colorClasses.bg
                        )}
                        aria-hidden="true"
                      />
                    )}
                  </button>

                  {/* Subpages - visible only when module is active */}
                  {isActive &&
                    activeModuleDefinition &&
                    activeModuleDefinition.subpages.length > 0 && (
                      <ul
                        role="list"
                        className="mt-1 ml-10 space-y-0.5 border-l border-border-light pl-3"
                      >
                        {activeModuleDefinition.subpages.map((subpage) => {
                          const isSubpageActive = location.pathname === subpage.path

                          return (
                            <li key={subpage.id}>
                              <SheetClose asChild>
                                <button
                                  onClick={() => handleSubpageSelect(subpage.path)}
                                  aria-current={isSubpageActive ? 'page' : undefined}
                                  className={cn(
                                    'w-full text-left',
                                    'px-3 py-2 rounded-md',
                                    'text-sm font-medium',
                                    'transition-all duration-150',
                                    'active:scale-[0.98]',
                                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40',
                                    isSubpageActive
                                      ? cn('bg-subtle/80', colorClasses.text)
                                      : 'text-text-tertiary hover:text-text-secondary hover:bg-subtle/40'
                                  )}
                                >
                                  {subpage.label}
                                </button>
                              </SheetClose>
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

        {/* Footer with version and user */}
        <div className="border-t border-border-light p-4 space-y-3">
          {/* Budget Version Selector */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-tertiary">Budget Version</span>
            <GlobalVersionSelector />
          </div>

          {/* User info and Sign out */}
          <div className="flex items-center justify-between pt-2 border-t border-border-light">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-gold/10 text-gold">
                <User className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-text-primary truncate max-w-[120px]">
                {user?.email?.split('@')[0]}
              </span>
            </div>

            <button
              onClick={handleSignOut}
              className={cn(
                'flex items-center gap-1.5',
                'px-3 py-1.5 rounded-lg',
                'text-sm font-medium text-text-tertiary',
                'hover:text-text-primary hover:bg-subtle',
                'transition-colors',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/40'
              )}
              aria-label="Sign out"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export default MobileDrawer
