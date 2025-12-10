/**
 * ModuleLayout - New UI Redesign Main Layout
 *
 * Phase 2 layout component that combines all new components into a cohesive layout.
 *
 * Structure:
 * ```
 * ┌────────┬─────────────────────────────────────────────────────────────┐
 * │        │ ModuleHeader (48px) - Title + Search + Version + User       │
 * │        ├─────────────────────────────────────────────────────────────┤
 * │ App    │ WorkflowTabs (40px) - Horizontal tab navigation             │
 * │ Side   ├─────────────────────────────────────────────────────────────┤
 * │ bar    │ TaskDescription (32px) - Contextual help text               │
 * │ (64px) ├─────────────────────────────────────────────────────────────┤
 * │        │                                                             │
 * │        │ Content Area (flexible) - AG Grid / Forms / Tables          │
 * │        │                                                             │
 * └────────┴─────────────────────────────────────────────────────────────┘
 * Mobile: MobileBottomNav (fixed at bottom)
 * ```
 *
 * Total Chrome Height: 120px (48 + 40 + 32)
 *
 * Accessibility Features:
 * - Skip navigation links
 * - ARIA landmarks
 * - Live regions for screen readers
 * - Keyboard navigation
 * - Route announcements
 */

import { type ReactNode } from 'react'
import { AppSidebar } from './AppSidebar'
import { ModuleHeader } from './ModuleHeader'
import { WorkflowTabs } from './WorkflowTabs'
import { TaskDescription } from './TaskDescription'
import { MobileBottomNav } from './MobileBottomNav'
import { ModuleProvider, useActiveModule } from '@/contexts/ModuleContext'
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

interface ModuleLayoutProps {
  children: ReactNode
  /** Override the task description */
  description?: string
  /** Whether to show settings tab in workflow tabs */
  showSettingsTab?: boolean
  /** Path for settings tab (if shown) */
  settingsPath?: string
}

/**
 * Determine settings path based on active module
 */
function useSettingsConfig() {
  const { activeModule } = useActiveModule()

  // Settings paths by module (Phase 4 routes)
  const settingsPathMap: Record<string, string | undefined> = {
    enrollment: '/enrollment/settings',
    workforce: '/workforce/settings',
    finance: '/finance/settings',
  }

  const showSettings = Boolean(settingsPathMap[activeModule ?? ''])
  const settingsPath = settingsPathMap[activeModule ?? '']

  return { showSettings, settingsPath }
}

/**
 * ModuleLayoutInner contains the layout with keyboard shortcuts.
 * Separated to use hooks within the provider context.
 */
function ModuleLayoutInner({
  children,
  description,
  showSettingsTab,
  settingsPath,
}: ModuleLayoutProps) {
  // Global keyboard shortcuts with help modal
  const { KeyboardShortcutsHelp } = useKeyboardShortcuts()

  // Auto-detect settings configuration
  const { showSettings: autoShowSettings, settingsPath: autoSettingsPath } = useSettingsConfig()

  // Use provided values or auto-detected ones
  const finalShowSettings = showSettingsTab ?? autoShowSettings
  const finalSettingsPath = settingsPath ?? autoSettingsPath

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

      {/* Main layout container */}
      <div className="flex min-h-screen bg-canvas">
        {/* Sidebar - Desktop only */}
        <AppSidebar />

        {/* Main content area - shifted for sidebar on desktop */}
        <div
          className={cn(
            'flex-1 flex flex-col',
            'min-h-screen',
            // Offset for collapsed sidebar on desktop
            'md:ml-[var(--sidebar-width-collapsed)]'
          )}
        >
          {/* Module Header (48px) */}
          <ModuleHeader />

          {/* Workflow Tabs (40px) - with skip target */}
          <SkipTarget
            id="module-navigation"
            as="div"
            role="navigation"
            aria-label="Workflow navigation"
          >
            <WorkflowTabs showSettingsTab={finalShowSettings} settingsPath={finalSettingsPath} />
          </SkipTarget>

          {/* Task Description (32px) */}
          <TaskDescription description={description} />

          {/* Main content area */}
          <SkipTarget
            id="main-content"
            as="main"
            role="main"
            aria-label="Main content"
            className={cn(
              'flex-1 overflow-auto',
              // Height calculation: viewport - chrome (120px)
              'min-h-[var(--redesign-content-height)]',
              // Bottom padding on mobile for bottom nav
              'pb-20 md:pb-0'
            )}
          >
            {/* Data grid skip target (for AG Grid pages) */}
            <SkipTarget id="data-grid" as="div" className="contents">
              {children}
            </SkipTarget>
          </SkipTarget>
        </div>

        {/* Mobile Bottom Navigation */}
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
 * ModuleLayout wraps the application with providers.
 * Provider order (outer to inner):
 * 1. ReducedMotionProvider - Motion preferences
 * 2. HighContrastProvider - Contrast preferences
 * 3. LiveRegionProvider - Screen reader announcements
 * 4. ModuleProvider - Active module state
 */
export function ModuleLayout(props: ModuleLayoutProps) {
  return (
    <ReducedMotionProvider>
      <HighContrastProvider>
        <LiveRegionProvider>
          <ModuleProvider>
            <ModuleLayoutInner {...props} />
          </ModuleProvider>
        </LiveRegionProvider>
      </HighContrastProvider>
    </ReducedMotionProvider>
  )
}

export default ModuleLayout
