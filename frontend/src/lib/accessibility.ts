/**
 * Accessibility utilities for EFIR Budget Planning Application.
 *
 * Provides helpers for:
 * - Screen reader announcements
 * - Focus management
 * - Keyboard navigation
 * - ARIA attribute helpers
 */

/**
 * Announce a message to screen readers using an ARIA live region.
 *
 * @param message - The message to announce
 * @param priority - 'polite' waits for pause, 'assertive' interrupts immediately
 *
 * @example
 * ```tsx
 * announce('Budget saved successfully', 'polite');
 * announce('Error: Please fill in required fields', 'assertive');
 * ```
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcer = getOrCreateAnnouncer(priority)
  announcer.textContent = ''
  // Small delay to ensure screen readers detect the change
  requestAnimationFrame(() => {
    announcer.textContent = message
  })
}

/**
 * Get or create the ARIA live region announcer element.
 */
function getOrCreateAnnouncer(priority: 'polite' | 'assertive'): HTMLElement {
  const id = `efir-announcer-${priority}`
  let announcer = document.getElementById(id)

  if (!announcer) {
    announcer = document.createElement('div')
    announcer.id = id
    announcer.setAttribute('aria-live', priority)
    announcer.setAttribute('aria-atomic', 'true')
    announcer.setAttribute('role', 'status')
    announcer.className = 'sr-only'
    announcer.style.cssText = `
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    `
    document.body.appendChild(announcer)
  }

  return announcer
}

/**
 * Focus trap for modal dialogs.
 *
 * @param containerRef - Ref to the container element
 * @returns Cleanup function
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   return focusTrap(dialogRef.current);
 * }, [isOpen]);
 * ```
 */
export function focusTrap(container: HTMLElement | null): () => void {
  if (!container) return () => {}

  const focusableElements = container.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )

  if (focusableElements.length === 0) return () => {}

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault()
        lastElement.focus()
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault()
        firstElement.focus()
      }
    }
  }

  container.addEventListener('keydown', handleKeyDown)
  firstElement.focus()

  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

/**
 * Skip to main content link handler.
 *
 * @param mainContentId - ID of the main content container
 *
 * @example
 * ```tsx
 * <a href="#main" onClick={() => skipToMain('main-content')}>
 *   Skip to main content
 * </a>
 * ```
 */
export function skipToMain(mainContentId: string): void {
  const main = document.getElementById(mainContentId)
  if (main) {
    main.setAttribute('tabindex', '-1')
    main.focus()
    main.removeAttribute('tabindex')
  }
}

/**
 * Generate unique IDs for accessible form elements.
 */
let idCounter = 0
export function generateId(prefix: string = 'efir'): string {
  idCounter += 1
  return `${prefix}-${idCounter}`
}

/**
 * Check if reduced motion is preferred.
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * ARIA attribute helper for describedby.
 * Returns an object with aria-describedby if the ID is provided.
 */
export function ariaDescribedBy(
  id: string | undefined
): { 'aria-describedby': string } | Record<string, never> {
  return id ? { 'aria-describedby': id } : {}
}

/**
 * ARIA attribute helper for labelled by.
 * Returns an object with aria-labelledby if the ID is provided.
 */
export function ariaLabelledBy(
  id: string | undefined
): { 'aria-labelledby': string } | Record<string, never> {
  return id ? { 'aria-labelledby': id } : {}
}

/**
 * Get appropriate role for interactive elements.
 */
export function getInteractiveRole(
  element: 'button' | 'link' | 'checkbox' | 'radio' | 'tab' | 'menuitem'
): string {
  const roles: Record<string, string> = {
    button: 'button',
    link: 'link',
    checkbox: 'checkbox',
    radio: 'radio',
    tab: 'tab',
    menuitem: 'menuitem',
  }
  return roles[element] || 'button'
}

/**
 * Hook-like helper for handling escape key press.
 *
 * @param callback - Function to call on escape
 * @returns Cleanup function
 */
export function onEscapeKey(callback: () => void): () => void {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      callback()
    }
  }

  document.addEventListener('keydown', handleKeyDown)
  return () => document.removeEventListener('keydown', handleKeyDown)
}
