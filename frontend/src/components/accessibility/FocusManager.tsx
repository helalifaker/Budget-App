/* eslint-disable react-refresh/only-export-components */
/**
 * Focus Management Utilities
 *
 * Provides utilities for managing focus in complex UI interactions:
 * - Focus trapping within modals/dialogs
 * - Focus restoration after closing dialogs
 * - Focus indicators for keyboard navigation
 * - Roving tabindex for composite widgets
 *
 * WCAG 2.1 Success Criterion 2.4.3 (Level A) - Focus Order
 * WCAG 2.1 Success Criterion 2.4.7 (Level AA) - Focus Visible
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from 'react'
import { cn } from '@/lib/utils'

// ============================================================================
// Focus Trap
// ============================================================================

const FOCUSABLE_ELEMENTS = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
].join(', ')

/**
 * useFocusTrap keeps focus within a container when active.
 * Use for modals, dialogs, and dropdown menus.
 *
 * @example
 * const dialogRef = useRef<HTMLDivElement>(null)
 * useFocusTrap(dialogRef, isOpen)
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement | null>,
  isActive: boolean = true
) {
  const previousActiveElement = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!isActive || !containerRef.current) return

    // Store currently focused element
    previousActiveElement.current = document.activeElement as HTMLElement

    // Get all focusable elements
    const container = containerRef.current
    const focusableElements = container.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS)
    const firstElement = focusableElements[0]

    // Focus first element
    if (firstElement) {
      firstElement.focus()
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      // Get fresh list of focusable elements (may have changed)
      const currentFocusable = container.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS)
      const first = currentFocusable[0]
      const last = currentFocusable[currentFocusable.length - 1]

      if (event.shiftKey) {
        // Shift+Tab - go backwards
        if (document.activeElement === first) {
          event.preventDefault()
          last?.focus()
        }
      } else {
        // Tab - go forwards
        if (document.activeElement === last) {
          event.preventDefault()
          first?.focus()
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)

    return () => {
      container.removeEventListener('keydown', handleKeyDown)

      // Restore focus when trap is deactivated
      if (previousActiveElement.current && previousActiveElement.current.focus) {
        previousActiveElement.current.focus()
      }
    }
  }, [containerRef, isActive])
}

// ============================================================================
// Focus Restoration
// ============================================================================

interface FocusRestoreContextType {
  saveFocus: () => void
  restoreFocus: () => void
}

const FocusRestoreContext = createContext<FocusRestoreContextType | null>(null)

/**
 * FocusRestoreProvider saves and restores focus positions.
 * Useful for dialogs and multi-step wizards.
 */
export function FocusRestoreProvider({ children }: { children: ReactNode }) {
  const savedElement = useRef<HTMLElement | null>(null)

  const saveFocus = useCallback(() => {
    savedElement.current = document.activeElement as HTMLElement
  }, [])

  const restoreFocus = useCallback(() => {
    if (savedElement.current && savedElement.current.focus) {
      savedElement.current.focus()
    }
  }, [])

  return (
    <FocusRestoreContext.Provider value={{ saveFocus, restoreFocus }}>
      {children}
    </FocusRestoreContext.Provider>
  )
}

export function useFocusRestore() {
  const context = useContext(FocusRestoreContext)
  if (!context) {
    throw new Error('useFocusRestore must be used within a FocusRestoreProvider')
  }
  return context
}

// ============================================================================
// Roving Tabindex
// ============================================================================

interface RovingTabindexOptions {
  orientation?: 'horizontal' | 'vertical' | 'both'
  loop?: boolean
  onFocusChange?: (index: number) => void
}

/**
 * useRovingTabindex implements the roving tabindex pattern for composite widgets.
 * Only one element in the group is in the tab order at a time.
 *
 * @example
 * const { currentIndex, setCurrentIndex, getTabIndex, handleKeyDown } = useRovingTabindex(items.length)
 */
export function useRovingTabindex(itemCount: number, options: RovingTabindexOptions = {}) {
  const { orientation = 'vertical', loop = true, onFocusChange } = options
  const [currentIndex, setCurrentIndex] = useState(0)
  const itemRefs = useRef<(HTMLElement | null)[]>([])

  const setItemRef = useCallback(
    (index: number) => (el: HTMLElement | null) => {
      itemRefs.current[index] = el
    },
    []
  )

  const focusItem = useCallback(
    (index: number) => {
      const newIndex = loop
        ? ((index % itemCount) + itemCount) % itemCount
        : Math.max(0, Math.min(index, itemCount - 1))

      setCurrentIndex(newIndex)
      itemRefs.current[newIndex]?.focus()
      onFocusChange?.(newIndex)
    },
    [itemCount, loop, onFocusChange]
  )

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      let handled = false

      switch (event.key) {
        case 'ArrowDown':
          if (orientation === 'vertical' || orientation === 'both') {
            focusItem(currentIndex + 1)
            handled = true
          }
          break
        case 'ArrowUp':
          if (orientation === 'vertical' || orientation === 'both') {
            focusItem(currentIndex - 1)
            handled = true
          }
          break
        case 'ArrowRight':
          if (orientation === 'horizontal' || orientation === 'both') {
            focusItem(currentIndex + 1)
            handled = true
          }
          break
        case 'ArrowLeft':
          if (orientation === 'horizontal' || orientation === 'both') {
            focusItem(currentIndex - 1)
            handled = true
          }
          break
        case 'Home':
          focusItem(0)
          handled = true
          break
        case 'End':
          focusItem(itemCount - 1)
          handled = true
          break
      }

      if (handled) {
        event.preventDefault()
      }
    },
    [currentIndex, focusItem, itemCount, orientation]
  )

  const getTabIndex = useCallback(
    (index: number) => (index === currentIndex ? 0 : -1),
    [currentIndex]
  )

  return {
    currentIndex,
    setCurrentIndex,
    getTabIndex,
    handleKeyDown,
    setItemRef,
    focusItem,
  }
}

// ============================================================================
// Focus Indicator Component
// ============================================================================

interface FocusRingProps {
  children: ReactNode
  className?: string
  as?: React.ElementType
}

/**
 * FocusRing wraps an element to ensure it has a visible focus indicator.
 * Uses a combination of ring and outline for maximum compatibility.
 */
export function FocusRing({ children, className, as: Component = 'div' }: FocusRingProps) {
  return (
    <Component
      className={cn(
        'focus-within:ring-2 focus-within:ring-gold-500 focus-within:ring-offset-2',
        'focus-within:outline-none',
        'rounded transition-shadow',
        className
      )}
    >
      {children}
    </Component>
  )
}

// ============================================================================
// Focus Visible Polyfill Styles
// ============================================================================

/**
 * FocusVisibleStyles injects CSS for :focus-visible polyfill.
 * This ensures focus rings only show for keyboard navigation, not mouse clicks.
 */
export function FocusVisibleStyles() {
  return (
    <style>{`
      /* Only show focus ring for keyboard navigation */
      :focus:not(:focus-visible) {
        outline: none;
      }

      :focus-visible {
        outline: 2px solid #edad3e;
        outline-offset: 2px;
        box-shadow: 0 0 0 3px rgba(237, 173, 62, 0.4);
      }

      /* Enhanced focus for interactive elements */
      button:focus-visible,
      a:focus-visible,
      input:focus-visible,
      select:focus-visible,
      textarea:focus-visible,
      [tabindex]:focus-visible {
        outline: 2px solid #edad3e;
        outline-offset: 2px;
        box-shadow: 0 0 0 4px rgba(237, 173, 62, 0.25);
      }

      /* AG Grid cell focus enhancement */
      .ag-cell:focus {
        outline: 2px solid #edad3e !important;
        outline-offset: -1px !important;
        box-shadow: inset 0 0 0 2px rgba(237, 173, 62, 0.4) !important;
      }

      .ag-cell-focus {
        border: 2px solid #edad3e !important;
        background-color: rgba(237, 173, 62, 0.1) !important;
      }

      /* Skip link animations */
      @keyframes slideInFromLeft {
        from {
          transform: translateX(-100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      .skip-nav-container a:focus {
        animation: slideInFromLeft 0.2s ease-out;
      }
    `}</style>
  )
}

// ============================================================================
// Auto Focus Component
// ============================================================================

interface AutoFocusProps {
  children: ReactNode
  enabled?: boolean
  delay?: number
}

/**
 * AutoFocus automatically focuses its first focusable child when mounted.
 * Useful for dialogs and forms.
 */
export function AutoFocus({ children, enabled = true, delay = 0 }: AutoFocusProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!enabled) return

    const focusFirst = () => {
      const container = containerRef.current
      if (!container) return

      const focusable = container.querySelector<HTMLElement>(FOCUSABLE_ELEMENTS)
      if (focusable) {
        focusable.focus()
      }
    }

    if (delay > 0) {
      const timer = setTimeout(focusFirst, delay)
      return () => clearTimeout(timer)
    } else {
      focusFirst()
    }
  }, [enabled, delay])

  return <div ref={containerRef}>{children}</div>
}

export default FocusRing
