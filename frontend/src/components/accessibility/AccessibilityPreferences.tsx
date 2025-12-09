/**
 * Accessibility Preferences Panel
 *
 * Allows users to customize accessibility settings.
 * Settings are persisted in localStorage.
 *
 * Features:
 * - Reduced motion toggle
 * - High contrast toggle
 * - Font size adjustment
 * - Focus indicator style
 * - Screen reader verbosity
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Accessibility, Eye, Zap, Type, Focus } from 'lucide-react'
import { useReducedMotion } from './ReducedMotion'
import { useHighContrast } from './HighContrast'
import { cn } from '@/lib/utils'

// Font size options
type FontSize = 'small' | 'medium' | 'large' | 'x-large'

const FONT_SIZE_VALUES: Record<FontSize, string> = {
  small: '14px',
  medium: '16px',
  large: '18px',
  'x-large': '20px',
}

const FONT_SIZE_STORAGE_KEY = 'efir-font-size-preference'
const FOCUS_STYLE_STORAGE_KEY = 'efir-focus-style-preference'

interface AccessibilityPreferencesProps {
  trigger?: React.ReactNode
}

/**
 * AccessibilityPreferences panel for user customization
 */
export function AccessibilityPreferences({ trigger }: AccessibilityPreferencesProps) {
  const [open, setOpen] = useState(false)

  // Motion preferences
  const {
    prefersReducedMotion,
    userOverride: motionOverride,
    setUserOverride: setMotionOverride,
  } = useReducedMotion()

  // Contrast preferences
  const {
    prefersHighContrast,
    userOverride: contrastOverride,
    setUserOverride: setContrastOverride,
  } = useHighContrast()

  // Font size preference
  const [fontSize, setFontSize] = useState<FontSize>(() => {
    if (typeof window === 'undefined') return 'medium'
    return (localStorage.getItem(FONT_SIZE_STORAGE_KEY) as FontSize) || 'medium'
  })

  // Focus style preference
  const [focusStyle, setFocusStyle] = useState<'outline' | 'ring' | 'both'>(() => {
    if (typeof window === 'undefined') return 'both'
    return (localStorage.getItem(FOCUS_STYLE_STORAGE_KEY) as 'outline' | 'ring' | 'both') || 'both'
  })

  // Apply font size to document
  useEffect(() => {
    document.documentElement.style.fontSize = FONT_SIZE_VALUES[fontSize]
    localStorage.setItem(FONT_SIZE_STORAGE_KEY, fontSize)
  }, [fontSize])

  // Apply focus style
  useEffect(() => {
    document.documentElement.dataset.focusStyle = focusStyle
    localStorage.setItem(FOCUS_STYLE_STORAGE_KEY, focusStyle)
  }, [focusStyle])

  // Reset all preferences
  const resetPreferences = () => {
    setMotionOverride(null)
    setContrastOverride(null)
    setFontSize('medium')
    setFocusStyle('both')
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10"
            aria-label="Accessibility settings"
          >
            <Accessibility className="h-5 w-5" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Accessibility className="h-5 w-5 text-gold-500" />
            Accessibility Settings
          </DialogTitle>
          <DialogDescription>
            Customize the application to meet your accessibility needs.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Reduced Motion */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-subtle">
                <Zap className="h-4 w-4 text-text-secondary" />
              </div>
              <div>
                <Label htmlFor="reduced-motion" className="text-sm font-medium text-text-primary">
                  Reduce Motion
                </Label>
                <p className="text-xs text-text-secondary">
                  Minimize animations and transitions
                  {prefersReducedMotion && ' (System preference detected)'}
                </p>
              </div>
            </div>
            <Switch
              id="reduced-motion"
              checked={motionOverride ?? prefersReducedMotion}
              onCheckedChange={(checked: boolean) => setMotionOverride(checked)}
              aria-describedby="reduced-motion-desc"
            />
          </div>

          {/* High Contrast */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-subtle">
                <Eye className="h-4 w-4 text-text-secondary" />
              </div>
              <div>
                <Label htmlFor="high-contrast" className="text-sm font-medium text-text-primary">
                  High Contrast
                </Label>
                <p className="text-xs text-text-secondary">
                  Increase color contrast for better visibility
                  {prefersHighContrast && ' (System preference detected)'}
                </p>
              </div>
            </div>
            <Switch
              id="high-contrast"
              checked={contrastOverride ?? prefersHighContrast}
              onCheckedChange={(checked: boolean) => setContrastOverride(checked)}
              aria-describedby="high-contrast-desc"
            />
          </div>

          {/* Font Size */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-subtle">
                <Type className="h-4 w-4 text-text-secondary" />
              </div>
              <Label htmlFor="font-size" className="text-sm font-medium text-text-primary">
                Text Size
              </Label>
            </div>
            <Select value={fontSize} onValueChange={(v) => setFontSize(v as FontSize)}>
              <SelectTrigger id="font-size" className="w-full">
                <SelectValue placeholder="Select text size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="small">Small (14px)</SelectItem>
                <SelectItem value="medium">Medium (16px) - Default</SelectItem>
                <SelectItem value="large">Large (18px)</SelectItem>
                <SelectItem value="x-large">Extra Large (20px)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Focus Indicator Style */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-subtle">
                <Focus className="h-4 w-4 text-text-secondary" />
              </div>
              <Label htmlFor="focus-style" className="text-sm font-medium text-text-primary">
                Focus Indicator Style
              </Label>
            </div>
            <Select
              value={focusStyle}
              onValueChange={(v) => setFocusStyle(v as 'outline' | 'ring' | 'both')}
            >
              <SelectTrigger id="focus-style" className="w-full">
                <SelectValue placeholder="Select focus style" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="outline">Outline only</SelectItem>
                <SelectItem value="ring">Ring only</SelectItem>
                <SelectItem value="both">Both (Default)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Preview */}
          <div className="pt-4 border-t border-border-light">
            <p className="text-xs text-text-secondary mb-2">Preview</p>
            <div className="p-4 rounded-lg bg-subtle space-y-2">
              <p className="text-sm text-text-primary">
                This is sample text at your selected size.
              </p>
              <Button size="sm" className="mr-2">
                Sample Button
              </Button>
              <button
                className={cn(
                  'px-3 py-1.5 text-sm rounded border border-border-medium',
                  'focus:outline-2 focus:outline-gold-500 focus:ring-2 focus:ring-gold-500'
                )}
              >
                Focus me
              </button>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between pt-4 border-t border-border-light">
          <Button variant="ghost" size="sm" onClick={resetPreferences}>
            Reset to defaults
          </Button>
          <Button variant="outline" size="sm" onClick={() => setOpen(false)}>
            Done
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Quick accessibility toggle button for the header
 */
export function AccessibilityToggle() {
  const { effectiveReducedMotion, setUserOverride: setMotion } = useReducedMotion()
  const { effectiveHighContrast, setUserOverride: setContrast } = useHighContrast()

  return (
    <div className="flex items-center gap-1">
      <Button
        variant={effectiveReducedMotion ? 'secondary' : 'ghost'}
        size="icon"
        className="h-8 w-8"
        onClick={() => setMotion(!effectiveReducedMotion)}
        aria-label={effectiveReducedMotion ? 'Enable animations' : 'Reduce motion'}
        aria-pressed={effectiveReducedMotion}
      >
        <Zap className={cn('h-4 w-4', effectiveReducedMotion && 'text-gold-600')} />
      </Button>
      <Button
        variant={effectiveHighContrast ? 'secondary' : 'ghost'}
        size="icon"
        className="h-8 w-8"
        onClick={() => setContrast(!effectiveHighContrast)}
        aria-label={effectiveHighContrast ? 'Disable high contrast' : 'Enable high contrast'}
        aria-pressed={effectiveHighContrast}
      >
        <Eye className={cn('h-4 w-4', effectiveHighContrast && 'text-gold-600')} />
      </Button>
      <AccessibilityPreferences />
    </div>
  )
}

export default AccessibilityPreferences
