/**
 * Reduced Motion Support
 *
 * Respects the user's `prefers-reduced-motion` system preference.
 * Provides hooks and components to conditionally render animations.
 *
 * WCAG 2.1 Success Criterion 2.3.3 (Level AAA) - Animation from Interactions
 *
 * Features:
 * - Detect system preference for reduced motion
 * - Provide alternative non-animated versions
 * - Allow user override in accessibility settings
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

interface ReducedMotionContextType {
  prefersReducedMotion: boolean
  userOverride: boolean | null
  effectiveReducedMotion: boolean
  setUserOverride: (value: boolean | null) => void
}

const ReducedMotionContext = createContext<ReducedMotionContextType | null>(null)

const STORAGE_KEY = 'efir-reduced-motion-preference'

/**
 * ReducedMotionProvider detects and manages motion preferences.
 */
export function ReducedMotionProvider({ children }: { children: ReactNode }) {
  // System preference
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  })

  // User override (null = use system, true = reduce, false = allow)
  const [userOverride, setUserOverride] = useState<boolean | null>(() => {
    if (typeof window === 'undefined') return null
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'true') return true
    if (stored === 'false') return false
    return null
  })

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches)
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

  // Effective value (user override takes precedence)
  const effectiveReducedMotion = userOverride ?? prefersReducedMotion

  // Apply CSS class to document
  useEffect(() => {
    if (effectiveReducedMotion) {
      document.documentElement.classList.add('reduce-motion')
    } else {
      document.documentElement.classList.remove('reduce-motion')
    }
  }, [effectiveReducedMotion])

  return (
    <ReducedMotionContext.Provider
      value={{
        prefersReducedMotion,
        userOverride,
        effectiveReducedMotion,
        setUserOverride,
      }}
    >
      {children}
    </ReducedMotionContext.Provider>
  )
}

/**
 * useReducedMotion hook for accessing motion preferences.
 *
 * @example
 * const { effectiveReducedMotion } = useReducedMotion()
 * const animationDuration = effectiveReducedMotion ? 0 : 300
 */
export function useReducedMotion() {
  const context = useContext(ReducedMotionContext)

  if (!context) {
    // Fallback for components outside provider
    const matches =
      typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

    return {
      prefersReducedMotion: matches,
      userOverride: null,
      effectiveReducedMotion: matches,
      setUserOverride: () => {},
    }
  }

  return context
}

/**
 * ReducedMotionStyles injects CSS for respecting motion preferences.
 */
export function ReducedMotionStyles() {
  return (
    <style>{`
      /* Respect system preference for reduced motion */
      @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      }

      /* Manual override class */
      .reduce-motion *,
      .reduce-motion *::before,
      .reduce-motion *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }

      /* Exception: allow essential animations even with reduced motion */
      .reduce-motion .essential-animation,
      @media (prefers-reduced-motion: reduce) {
        .essential-animation {
          animation-duration: 200ms !important;
          transition-duration: 200ms !important;
        }
      }
    `}</style>
  )
}

/**
 * Motion component conditionally renders based on motion preference.
 */
export function Motion({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { effectiveReducedMotion } = useReducedMotion()

  if (effectiveReducedMotion && fallback) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

export default ReducedMotionProvider
