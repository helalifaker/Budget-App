/**
 * CockpitLayout - Executive Cockpit Main Layout
 *
 * The primary layout for the Executive Cockpit navigation pattern:
 *
 * Desktop (md+):
 * - SmartHeader (56px) - Logo, module tabs, search, version, user
 * - SubpageTabs (44px, if in module) - Horizontal subpage navigation
 * - Content Area - Main page content
 *
 * Mobile:
 * - ModuleDock (48px + subpage tabs) - Logo, module indicator, subpages
 * - Content Area - Main page content (with bottom padding for nav)
 * - MobileBottomNav (64px) - Fixed bottom module navigation
 *
 * NO SIDEBAR - maximizes content space for data-heavy pages.
 *
 * Accessibility Features:
 * - Skip navigation links
 * - ARIA landmarks
 * - Live regions for screen readers
 * - Keyboard navigation
 * - Route announcements
 */

import { type ReactNode } from 'react'
import { SmartHeader } from './SmartHeader'
import { ModuleDock } from './ModuleDock'
import { SubpageTabs } from './SubpageTabs'
import { MobileBottomNav } from './MobileBottomNav'
import { ModuleProvider } from '@/contexts/ModuleContext'
import { CommandPalette } from '@/components/CommandPalette'
import { cn } from '@/lib/utils'
import {
  SkipNavigation,
  SkipTarget,
  LiveRegionProvider,
  useKeyboardShortcuts,
  FocusVisibleStyles,
  ReducedMotionProvider,
  ReducedMotionStyles,
  HighContrastProvider,
  HighContrastStyles,
  RouteAnnouncer,
  PatternStyles,
} from '@/components/accessibility'

interface CockpitLayoutProps {
  children: ReactNode
}

/**
 * CockpitLayoutInner contains the layout with keyboard shortcuts.
 * Separated to use hooks within the provider context.
 */
function CockpitLayoutInner({ children }: CockpitLayoutProps) {
  // Global keyboard shortcuts with help modal
  const { KeyboardShortcutsHelp } = useKeyboardShortcuts()

  return (
    <>
      {/* Skip Navigation - visually hidden until focused */}
      <SkipNavigation
        links={[
          { id: 'main-content', label: 'Skip to main content', shortcut: 'Alt+1' },
          { id: 'module-navigation', label: 'Skip to module navigation', shortcut: 'Alt+2' },
          { id: 'data-grid', label: 'Skip to data grid', shortcut: 'Alt+3' },
        ]}
      />

      {/* Accessibility styles */}
      <FocusVisibleStyles />
      <ReducedMotionStyles />
      <HighContrastStyles />
      <PatternStyles />

      {/* Route change announcements for screen readers */}
      <RouteAnnouncer focusMainContent={true} delay={100} />

      {/* Main cockpit layout container */}
      <div
        className={cn(
          'flex flex-col min-h-screen',
          // Premium background
          'bg-[#FAF9F7]'
        )}
      >
        {/* Desktop: SmartHeader with module tabs */}
        <SmartHeader />

        {/* Mobile: ModuleDock (header + subpage tabs) */}
        <ModuleDock />

        {/* Desktop: Subpage tabs (below header, only when in module) */}
        <div className="hidden md:block">
          <SkipTarget
            id="module-navigation"
            as="div"
            role="navigation"
            aria-label="Subpage navigation"
          >
            <SubpageTabs />
          </SkipTarget>
        </div>

        {/* Main content area */}
        <SkipTarget
          id="main-content"
          as="main"
          role="main"
          aria-label="Main content"
          className={cn(
            'flex-1 overflow-y-auto',
            // Bottom padding on mobile for bottom nav
            'pb-20 md:pb-0'
          )}
        >
          {children}
        </SkipTarget>

        {/* Mobile: Bottom navigation */}
        <MobileBottomNav />

        {/* Global Command Palette (Cmd+K) */}
        <CommandPalette />

        {/* Keyboard Shortcuts Help Modal (Press ?) */}
        {KeyboardShortcutsHelp}
      </div>
    </>
  )
}

/**
 * CockpitLayout wraps the application with providers.
 * Provider order (outer to inner):
 * 1. ReducedMotionProvider - Motion preferences
 * 2. HighContrastProvider - Contrast preferences
 * 3. LiveRegionProvider - Screen reader announcements
 * 4. ModuleProvider - Active module state
 */
export function CockpitLayout({ children }: CockpitLayoutProps) {
  return (
    <ReducedMotionProvider>
      <HighContrastProvider>
        <LiveRegionProvider>
          <ModuleProvider>
            <CockpitLayoutInner>{children}</CockpitLayoutInner>
          </ModuleProvider>
        </LiveRegionProvider>
      </HighContrastProvider>
    </ReducedMotionProvider>
  )
}
