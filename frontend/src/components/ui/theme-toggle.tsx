/**
 * ThemeToggle component for switching between light and dark modes.
 *
 * Features:
 * - Accessible button with ARIA labels
 * - Animated icons
 * - Keyboard support
 */

import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'

interface ThemeToggleProps {
  className?: string
}

/**
 * Theme toggle button component.
 *
 * @example
 * ```tsx
 * <ThemeToggle className="ml-auto" />
 * ```
 */
export function ThemeToggle({ className }: ThemeToggleProps) {
  const { resolvedTheme, toggleTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className={className}
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {resolvedTheme === 'dark' ? (
        <Sun
          className="h-5 w-5 transition-transform duration-200 hover:rotate-45"
          aria-hidden="true"
        />
      ) : (
        <Moon
          className="h-5 w-5 transition-transform duration-200 hover:-rotate-12"
          aria-hidden="true"
        />
      )}
      <span className="sr-only">
        {resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      </span>
    </Button>
  )
}

export default ThemeToggle
