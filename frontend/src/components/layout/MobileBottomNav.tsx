/**
 * MobileBottomNav - Mobile Bottom Navigation Bar
 *
 * Fixed bottom navigation for mobile devices showing module icons.
 * Only visible on mobile (md:hidden).
 *
 * Features:
 * - 5-6 module icons with labels
 * - Active module has colored background
 * - Touch-friendly (44px min height)
 * - Safe area insets for notched devices
 * - Haptic feedback indication
 */

import { useNavigate } from '@tanstack/react-router'
import { useModule, ALL_MODULES, MODULES, type ModuleId } from '@/contexts/ModuleContext'
import { cn } from '@/lib/utils'

interface MobileBottomNavProps {
  /** Additional CSS classes */
  className?: string
}

export function MobileBottomNav({ className }: MobileBottomNavProps) {
  const navigate = useNavigate()
  const { isModuleActive, getModuleColors } = useModule()

  const handleModuleSelect = (moduleId: ModuleId) => {
    const module = MODULES[moduleId]
    navigate({ to: module.basePath })
  }

  return (
    <nav
      role="navigation"
      aria-label="Module navigation"
      className={cn(
        // Only visible on mobile
        'md:hidden',
        // Fixed at bottom
        'fixed bottom-0 left-0 right-0',
        // Layout
        'flex items-center justify-around',
        // Height with safe area
        'h-16 pb-[env(safe-area-inset-bottom)]',
        // Background
        'bg-white/95 backdrop-blur-lg',
        // Border
        'border-t border-[#E8E6E1]',
        // Shadow
        'shadow-[0_-2px_10px_rgba(0,0,0,0.05)]',
        // Z-index above content
        'z-50',
        className
      )}
    >
      {ALL_MODULES.map((moduleId) => {
        const module = MODULES[moduleId]
        const ModuleIcon = module.icon
        const isActive = isModuleActive(moduleId)
        const colorClasses = getModuleColors(moduleId)

        return (
          <button
            key={moduleId}
            onClick={() => handleModuleSelect(moduleId)}
            aria-current={isActive ? 'page' : undefined}
            aria-label={`${module.label} module`}
            className={cn(
              // Base styles
              'flex flex-col items-center justify-center',
              'flex-1',
              // Min touch target (44px)
              'min-h-[44px] py-1.5',
              // Transition
              'transition-all duration-150 ease-out',
              // Focus state
              'focus:outline-none focus-visible:bg-[#F5F4F1]',
              // Active haptic feel
              'active:scale-95'
            )}
          >
            {/* Icon container */}
            <div
              className={cn(
                'flex items-center justify-center',
                'w-8 h-8 rounded-lg',
                'transition-all duration-150',
                isActive ? cn(colorClasses.active, 'shadow-sm') : 'text-[#5C5A54]'
              )}
            >
              <ModuleIcon className="w-5 h-5" />
            </div>

            {/* Label */}
            <span
              className={cn(
                'text-[10px] font-medium mt-0.5',
                'transition-colors duration-150',
                isActive ? 'text-[#1A1917]' : 'text-[#8A877E]'
              )}
            >
              {module.shortLabel}
            </span>
          </button>
        )
      })}
    </nav>
  )
}

export default MobileBottomNav
