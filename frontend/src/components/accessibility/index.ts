/**
 * Accessibility Components
 *
 * Comprehensive accessibility system for WCAG 2.1 AA compliance.
 *
 * Features:
 * - Skip navigation for keyboard users
 * - Live regions for screen reader announcements
 * - Keyboard shortcuts with help modal
 * - Focus management utilities
 * - Reduced motion support
 * - High contrast mode
 * - Route change announcements
 * - User accessibility preferences
 * - Accessible form components
 */

// Skip Navigation
export { SkipNavigation, SkipTarget, type SkipLink } from './SkipNavigation'

// Live Regions
export { LiveRegionProvider, useLiveAnnounce, StatusMessage } from './LiveRegion'

// Keyboard Shortcuts
export {
  KeyboardShortcutsHelp,
  useKeyboardShortcuts,
  DEFAULT_SHORTCUTS,
  type KeyboardShortcut,
} from './KeyboardShortcuts'

// Focus Management
export {
  useFocusTrap,
  FocusRestoreProvider,
  useFocusRestore,
  useRovingTabindex,
  FocusRing,
  FocusVisibleStyles,
  AutoFocus,
} from './FocusManager'

// Reduced Motion Support
export { ReducedMotionProvider, useReducedMotion, ReducedMotionStyles } from './ReducedMotion'

// High Contrast Mode
export { HighContrastProvider, useHighContrast, HighContrastStyles } from './HighContrast'

// Route Change Announcements
export { RouteAnnouncer } from './RouteAnnouncer'

// User Accessibility Preferences
export { AccessibilityPreferences, AccessibilityToggle } from './AccessibilityPreferences'

// Accessible Form Components
export {
  FormField,
  AccessibleInput,
  AccessibleTextarea,
  FormErrorSummary,
  CharacterCounter,
  RequiredFieldsLegend,
} from './FormAccessibility'

// Color Blindness Support
export {
  StatusIndicator,
  TrendIndicator,
  ProgressStateIndicator,
  ColorBlindnessProvider,
  useColorBlindness,
  PatternStyles,
  DataCell,
  AccessibleLegend,
  type StatusType,
  type TrendType,
  type ProgressState,
} from './ColorBlindnessSupport'
