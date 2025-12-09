/**
 * Skip Navigation Component
 *
 * Provides skip links for keyboard users to bypass repetitive navigation
 * and jump directly to main content, navigation, or specific sections.
 *
 * WCAG 2.1 Success Criterion 2.4.1 (Level A) - Bypass Blocks
 *
 * These links are visually hidden until focused, then appear prominently
 * at the top of the viewport.
 */

import { cn } from '@/lib/utils'

export interface SkipLink {
  id: string
  label: string
  shortcut?: string
}

interface SkipNavigationProps {
  links?: SkipLink[]
}

const DEFAULT_SKIP_LINKS: SkipLink[] = [
  { id: 'main-content', label: 'Skip to main content', shortcut: 'Alt+1' },
  { id: 'main-navigation', label: 'Skip to navigation', shortcut: 'Alt+2' },
  { id: 'data-grid', label: 'Skip to data grid', shortcut: 'Alt+3' },
]

/**
 * SkipNavigation renders visually hidden links that become visible on focus.
 * Keyboard users can Tab to these links first and skip to major page sections.
 */
export function SkipNavigation({ links = DEFAULT_SKIP_LINKS }: SkipNavigationProps) {
  const handleSkipClick = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault()
    const target = document.getElementById(targetId)

    if (target) {
      // Set tabindex to make the target focusable if it's not naturally focusable
      if (!target.hasAttribute('tabindex')) {
        target.setAttribute('tabindex', '-1')
      }

      // Focus and scroll to the target
      target.focus({ preventScroll: false })
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <nav aria-label="Skip navigation" className="skip-nav-container">
      <ul className="skip-nav-list" role="list">
        {links.map((link) => (
          <li key={link.id}>
            <a
              href={`#${link.id}`}
              onClick={(e) => handleSkipClick(e, link.id)}
              className={cn(
                // Visually hidden by default
                'sr-only',
                // Visible when focused - appears at top left
                'focus:not-sr-only focus:absolute focus:z-[100] focus:top-0 focus:left-0',
                // Styling when visible
                'focus:bg-gold-500 focus:text-white focus:px-4 focus:py-3',
                'focus:font-semibold focus:text-sm',
                'focus:shadow-lg focus:rounded-br-lg',
                // Animation
                'focus:animate-in focus:slide-in-from-left-2 focus:duration-200',
                // Focus ring for visibility
                'focus:outline-none focus:ring-2 focus:ring-gold-600 focus:ring-offset-2'
              )}
            >
              {link.label}
              {link.shortcut && <span className="ml-2 text-xs opacity-80">({link.shortcut})</span>}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

/**
 * SkipTarget marks a section that can be jumped to via skip navigation.
 * Use this wrapper around major content sections.
 */
export function SkipTarget({
  id,
  children,
  as: Component = 'div',
  className,
  ...props
}: {
  id: string
  children: React.ReactNode
  as?: React.ElementType
  className?: string
} & React.HTMLAttributes<HTMLElement>) {
  return (
    <Component
      id={id}
      tabIndex={-1}
      className={cn('outline-none focus:outline-none', className)}
      {...props}
    >
      {children}
    </Component>
  )
}

export default SkipNavigation
