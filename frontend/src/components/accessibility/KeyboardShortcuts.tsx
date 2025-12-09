/**
 * Keyboard Shortcuts System
 *
 * Provides global keyboard shortcuts and a help modal to discover them.
 * Implements WCAG 2.1 Success Criterion 2.1.4 (Level A) - Character Key Shortcuts
 *
 * Features:
 * - Global shortcuts (navigation, actions, help)
 * - AG Grid-specific shortcuts
 * - Help modal triggered by "?" key
 * - Customizable shortcut definitions
 * - Conflict prevention with input fields
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Keyboard, Command, Navigation, Grid3X3, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

// Platform detection for modifier key display
const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)
const MOD_KEY = isMac ? '⌘' : 'Ctrl'

export interface KeyboardShortcut {
  key: string
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[]
  label: string
  description: string
  category: 'navigation' | 'actions' | 'grid' | 'general'
  handler?: () => void
}

// Default keyboard shortcuts
export const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // General
  {
    key: '?',
    label: '?',
    description: 'Show keyboard shortcuts help',
    category: 'general',
  },
  {
    key: 'k',
    modifiers: ['meta'],
    label: `${MOD_KEY}+K`,
    description: 'Open command palette',
    category: 'general',
  },
  {
    key: 'Escape',
    label: 'Esc',
    description: 'Close dialogs / Cancel action',
    category: 'general',
  },

  // Navigation
  {
    key: '1',
    modifiers: ['alt'],
    label: 'Alt+1',
    description: 'Skip to main content',
    category: 'navigation',
  },
  {
    key: '2',
    modifiers: ['alt'],
    label: 'Alt+2',
    description: 'Skip to navigation',
    category: 'navigation',
  },
  {
    key: '3',
    modifiers: ['alt'],
    label: 'Alt+3',
    description: 'Skip to data grid',
    category: 'navigation',
  },
  {
    key: 'g',
    modifiers: ['alt'],
    label: 'Alt+G',
    description: 'Go to Dashboard',
    category: 'navigation',
  },
  {
    key: 'e',
    modifiers: ['alt'],
    label: 'Alt+E',
    description: 'Go to Enrollment Planning',
    category: 'navigation',
  },
  {
    key: 'd',
    modifiers: ['alt'],
    label: 'Alt+D',
    description: 'Go to DHG Workforce Planning',
    category: 'navigation',
  },
  {
    key: 'b',
    modifiers: ['alt'],
    label: 'Alt+B',
    description: 'Go to Budget Consolidation',
    category: 'navigation',
  },

  // Actions
  {
    key: 's',
    modifiers: ['meta'],
    label: `${MOD_KEY}+S`,
    description: 'Save current changes',
    category: 'actions',
  },
  {
    key: 'n',
    modifiers: ['alt'],
    label: 'Alt+N',
    description: 'Create new item',
    category: 'actions',
  },
  {
    key: 'f',
    modifiers: ['meta'],
    label: `${MOD_KEY}+F`,
    description: 'Focus search / filter',
    category: 'actions',
  },

  // AG Grid specific
  {
    key: 'Enter',
    label: 'Enter',
    description: 'Edit selected cell / Confirm edit',
    category: 'grid',
  },
  {
    key: 'Tab',
    label: 'Tab',
    description: 'Move to next cell',
    category: 'grid',
  },
  {
    key: 'Tab',
    modifiers: ['shift'],
    label: 'Shift+Tab',
    description: 'Move to previous cell',
    category: 'grid',
  },
  {
    key: 'ArrowUp',
    label: '↑',
    description: 'Move up one row',
    category: 'grid',
  },
  {
    key: 'ArrowDown',
    label: '↓',
    description: 'Move down one row',
    category: 'grid',
  },
  {
    key: 'ArrowLeft',
    label: '←',
    description: 'Move left one cell',
    category: 'grid',
  },
  {
    key: 'ArrowRight',
    label: '→',
    description: 'Move right one cell',
    category: 'grid',
  },
  {
    key: 'Home',
    label: 'Home',
    description: 'Go to first cell in row',
    category: 'grid',
  },
  {
    key: 'End',
    label: 'End',
    description: 'Go to last cell in row',
    category: 'grid',
  },
  {
    key: 'Home',
    modifiers: ['ctrl'],
    label: `${MOD_KEY}+Home`,
    description: 'Go to first cell in grid',
    category: 'grid',
  },
  {
    key: 'End',
    modifiers: ['ctrl'],
    label: `${MOD_KEY}+End`,
    description: 'Go to last cell in grid',
    category: 'grid',
  },
  {
    key: 'PageUp',
    label: 'PageUp',
    description: 'Page up in grid',
    category: 'grid',
  },
  {
    key: 'PageDown',
    label: 'PageDown',
    description: 'Page down in grid',
    category: 'grid',
  },
  {
    key: ' ',
    label: 'Space',
    description: 'Select/deselect row',
    category: 'grid',
  },
  {
    key: 'a',
    modifiers: ['ctrl'],
    label: `${MOD_KEY}+A`,
    description: 'Select all rows',
    category: 'grid',
  },
  {
    key: 'c',
    modifiers: ['ctrl'],
    label: `${MOD_KEY}+C`,
    description: 'Copy selected cells',
    category: 'grid',
  },
  {
    key: 'v',
    modifiers: ['ctrl'],
    label: `${MOD_KEY}+V`,
    description: 'Paste into cells',
    category: 'grid',
  },
  {
    key: 'Delete',
    label: 'Delete',
    description: 'Clear cell content',
    category: 'grid',
  },
  {
    key: 'F2',
    label: 'F2',
    description: 'Start editing cell',
    category: 'grid',
  },
]

const CATEGORY_ICONS = {
  general: Sparkles,
  navigation: Navigation,
  actions: Command,
  grid: Grid3X3,
}

const CATEGORY_LABELS = {
  general: 'General',
  navigation: 'Navigation',
  actions: 'Actions',
  grid: 'Data Grid (AG Grid)',
}

interface KeyboardShortcutsHelpProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  shortcuts?: KeyboardShortcut[]
}

/**
 * Keyboard Shortcuts Help Modal
 * Displays all available shortcuts organized by category
 */
export function KeyboardShortcutsHelp({
  open,
  onOpenChange,
  shortcuts = DEFAULT_SHORTCUTS,
}: KeyboardShortcutsHelpProps) {
  const categories = ['general', 'navigation', 'actions', 'grid'] as const

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5 text-gold-500" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Use these keyboard shortcuts to navigate and interact with the application efficiently.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {categories.map((category) => {
            const Icon = CATEGORY_ICONS[category]
            const categoryShortcuts = shortcuts.filter((s) => s.category === category)

            if (categoryShortcuts.length === 0) return null

            return (
              <section key={category} aria-labelledby={`${category}-heading`}>
                <h3
                  id={`${category}-heading`}
                  className="flex items-center gap-2 text-sm font-semibold text-text-secondary mb-3"
                >
                  <Icon className="h-4 w-4 text-gold-500" />
                  {CATEGORY_LABELS[category]}
                </h3>
                <div className="space-y-1">
                  {categoryShortcuts.map((shortcut, index) => (
                    <div
                      key={`${shortcut.key}-${index}`}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-subtle transition-colors"
                    >
                      <span className="text-sm text-text-secondary">{shortcut.description}</span>
                      <kbd
                        className={cn(
                          'px-2 py-1 text-xs font-mono rounded',
                          'bg-subtle text-text-secondary border border-border-light',
                          'shadow-sm'
                        )}
                      >
                        {shortcut.label}
                      </kbd>
                    </div>
                  ))}
                </div>
              </section>
            )
          })}
        </div>

        <div className="flex justify-between items-center mt-6 pt-4 border-t border-border-light">
          <p className="text-xs text-text-secondary">
            Press <kbd className="px-1.5 py-0.5 text-xs bg-subtle rounded border">?</kbd> anytime to
            show this help
          </p>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/**
 * useKeyboardShortcuts hook
 * Registers global keyboard shortcuts and returns the help modal state
 */
export function useKeyboardShortcuts(customShortcuts?: KeyboardShortcut[]) {
  const [helpOpen, setHelpOpen] = useState(false)
  const navigate = useNavigate()

  // Use a no-op announce function - the component using this hook
  // should be wrapped in LiveRegionProvider at the app level
  // If not, announcements will simply be skipped (graceful degradation)
  const announceRef = useRef<(message: string) => void>(() => {})

  const announce = useCallback((message: string) => {
    announceRef.current(message)
  }, [])

  const skipToElement = useCallback((elementId: string) => {
    const element = document.getElementById(elementId)
    if (element) {
      if (!element.hasAttribute('tabindex')) {
        element.setAttribute('tabindex', '-1')
      }
      element.focus({ preventScroll: false })
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [])

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      const target = event.target as HTMLElement
      const isInputField =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable

      // Allow some shortcuts even in input fields
      const allowInInput =
        event.key === 'Escape' || (event.key === 'k' && (event.metaKey || event.ctrlKey))

      if (isInputField && !allowInInput) return

      const isMod = isMac ? event.metaKey : event.ctrlKey

      // Help modal - ? key
      if (
        event.key === '?' &&
        !event.shiftKey &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey
      ) {
        event.preventDefault()
        setHelpOpen(true)
        announce('Keyboard shortcuts help opened')
        return
      }

      // Skip navigation - Alt+1, Alt+2, Alt+3
      if (event.altKey && !event.shiftKey && !isMod) {
        switch (event.key) {
          case '1':
            event.preventDefault()
            skipToElement('main-content')
            announce('Skipped to main content')
            return
          case '2':
            event.preventDefault()
            skipToElement('main-navigation')
            announce('Skipped to navigation')
            return
          case '3':
            event.preventDefault()
            skipToElement('data-grid')
            announce('Skipped to data grid')
            return
        }
      }

      // Navigation shortcuts - Alt+G, Alt+E, Alt+D, Alt+B
      if (event.altKey && !event.shiftKey && !isMod) {
        switch (event.key.toLowerCase()) {
          case 'g':
            event.preventDefault()
            navigate({ to: '/dashboard' })
            announce('Navigated to Dashboard')
            return
          case 'e':
            event.preventDefault()
            navigate({ to: '/enrollment/planning' })
            announce('Navigated to Enrollment Planning')
            return
          case 'd':
            event.preventDefault()
            navigate({ to: '/planning/dhg' })
            announce('Navigated to DHG Workforce Planning')
            return
          case 'b':
            event.preventDefault()
            navigate({ to: '/finance/consolidation' })
            announce('Navigated to Budget Consolidation')
            return
        }
      }

      // Command palette - Cmd/Ctrl+K (handled by CommandPalette component)
      // Save - Cmd/Ctrl+S (handled by individual pages)
      // We just prevent browser default
      if (isMod && event.key === 's') {
        event.preventDefault()
        // Trigger custom save event that pages can listen to
        window.dispatchEvent(new CustomEvent('app:save'))
        return
      }

      // Process custom shortcuts
      if (customShortcuts) {
        for (const shortcut of customShortcuts) {
          const modMatch =
            !shortcut.modifiers ||
            shortcut.modifiers.length === 0 ||
            shortcut.modifiers.every((mod) => {
              switch (mod) {
                case 'ctrl':
                  return event.ctrlKey
                case 'alt':
                  return event.altKey
                case 'shift':
                  return event.shiftKey
                case 'meta':
                  return event.metaKey
                default:
                  return false
              }
            })

          if (event.key === shortcut.key && modMatch && shortcut.handler) {
            event.preventDefault()
            shortcut.handler()
            return
          }
        }
      }
    },
    [announce, navigate, skipToElement, customShortcuts]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  return {
    helpOpen,
    setHelpOpen,
    KeyboardShortcutsHelp: (
      <KeyboardShortcutsHelp
        open={helpOpen}
        onOpenChange={setHelpOpen}
        shortcuts={[...DEFAULT_SHORTCUTS, ...(customShortcuts || [])]}
      />
    ),
  }
}

export default KeyboardShortcutsHelp
