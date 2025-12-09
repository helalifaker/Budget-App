/**
 * High Contrast Mode Support
 *
 * Respects the user's `prefers-contrast` system preference.
 * Provides enhanced contrast for users with low vision.
 *
 * WCAG 2.1 Success Criterion 1.4.6 (Level AAA) - Contrast (Enhanced)
 *
 * Features:
 * - Detect system preference for high contrast
 * - Apply enhanced contrast styles
 * - Allow user override in accessibility settings
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

interface HighContrastContextType {
  prefersHighContrast: boolean
  userOverride: boolean | null
  effectiveHighContrast: boolean
  setUserOverride: (value: boolean | null) => void
}

const HighContrastContext = createContext<HighContrastContextType | null>(null)

const STORAGE_KEY = 'efir-high-contrast-preference'

/**
 * HighContrastProvider detects and manages contrast preferences.
 */
export function HighContrastProvider({ children }: { children: ReactNode }) {
  // System preference
  const [prefersHighContrast, setPrefersHighContrast] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-contrast: more)').matches
  })

  // User override
  const [userOverride, setUserOverride] = useState<boolean | null>(() => {
    if (typeof window === 'undefined') return null
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'true') return true
    if (stored === 'false') return false
    return null
  })

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: more)')

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersHighContrast(e.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  // Persist user override
  useEffect(() => {
    if (userOverride === null) {
      localStorage.removeItem(STORAGE_KEY)
    } else {
      localStorage.setItem(STORAGE_KEY, String(userOverride))
    }
  }, [userOverride])

  // Effective value
  const effectiveHighContrast = userOverride ?? prefersHighContrast

  // Apply CSS class to document
  useEffect(() => {
    if (effectiveHighContrast) {
      document.documentElement.classList.add('high-contrast')
    } else {
      document.documentElement.classList.remove('high-contrast')
    }
  }, [effectiveHighContrast])

  return (
    <HighContrastContext.Provider
      value={{
        prefersHighContrast,
        userOverride,
        effectiveHighContrast,
        setUserOverride,
      }}
    >
      {children}
    </HighContrastContext.Provider>
  )
}

/**
 * useHighContrast hook for accessing contrast preferences.
 */
export function useHighContrast() {
  const context = useContext(HighContrastContext)

  if (!context) {
    const matches =
      typeof window !== 'undefined' && window.matchMedia('(prefers-contrast: more)').matches

    return {
      prefersHighContrast: matches,
      userOverride: null,
      effectiveHighContrast: matches,
      setUserOverride: () => {},
    }
  }

  return context
}

/**
 * HighContrastStyles injects CSS for high contrast mode.
 */
export function HighContrastStyles() {
  return (
    <style>{`
      /* High contrast mode styles */
      .high-contrast {
        /* Increase text contrast */
        --color-text-primary: #000000;
        --color-text-secondary: #1a1a1a;
        --color-text-muted: #333333;

        /* Stronger borders */
        --border-color: #000000;

        /* Enhanced focus indicators */
        --focus-ring-color: #0000ff;
        --focus-ring-width: 3px;
      }

      .high-contrast *:focus-visible {
        outline: 3px solid #0000ff !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 5px rgba(0, 0, 255, 0.3) !important;
      }

      /* High contrast text colors */
      .high-contrast .text-text-tertiary,
      .high-contrast .text-text-secondary,
      .high-contrast .text-text-secondary {
        color: #1a1a1a !important;
      }

      .high-contrast .text-text-muted {
        color: #333333 !important;
      }

      /* High contrast backgrounds */
      .high-contrast .bg-subtle,
      .high-contrast .bg-subtle {
        background-color: #ffffff !important;
      }

      /* High contrast borders */
      .high-contrast .border-border-light,
      .high-contrast .border-border-medium {
        border-color: #666666 !important;
      }

      /* High contrast buttons */
      .high-contrast button,
      .high-contrast [role="button"] {
        border: 2px solid #000000 !important;
      }

      .high-contrast button:hover,
      .high-contrast [role="button"]:hover {
        background-color: #000000 !important;
        color: #ffffff !important;
      }

      /* High contrast links */
      .high-contrast a {
        color: #0000ee !important;
        text-decoration: underline !important;
      }

      .high-contrast a:visited {
        color: #551a8b !important;
      }

      /* High contrast form inputs */
      .high-contrast input,
      .high-contrast select,
      .high-contrast textarea {
        border: 2px solid #000000 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
      }

      /* High contrast badges and status indicators */
      .high-contrast .bg-success-500,
      .high-contrast .bg-sage-500 {
        background-color: #006600 !important;
      }

      .high-contrast .bg-error-500,
      .high-contrast .bg-terracotta-500 {
        background-color: #cc0000 !important;
      }

      .high-contrast .bg-warning-500,
      .high-contrast .bg-gold-500 {
        background-color: #cc6600 !important;
      }

      /* Respect system preference */
      @media (prefers-contrast: more) {
        :root {
          --color-text-primary: #000000;
          --color-text-secondary: #1a1a1a;
        }

        *:focus-visible {
          outline: 3px solid #0000ff !important;
          outline-offset: 2px !important;
        }
      }
    `}</style>
  )
}

export default HighContrastProvider
