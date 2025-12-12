import { useState } from 'react'
import { Lock, Unlock, CheckCircle2, ArrowDown, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Definition of a cascade step (downstream module affected)
 */
export interface CascadeStep {
  /** Icon to display */
  icon: LucideIcon
  /** Title of the module */
  title: string
  /** Description of what will be updated */
  description: string
}

interface CascadeConfirmDialogProps {
  /** Current status: draft (can lock) or validated (can unlock) */
  status: 'draft' | 'validated'
  /** Callback when user confirms validation/lock */
  onValidate: (confirmation: boolean) => void
  /** Callback when user unlocks */
  onUnvalidate: () => void
  /** Disabled state */
  disabled?: boolean
  /** Steps that will cascade when locking */
  cascadeSteps: CascadeStep[]
  /** Title when locked */
  lockedTitle?: string
  /** Description when locked */
  lockedDescription?: string
  /** Title when in draft state */
  draftTitle?: string
  /** Description when in draft state */
  draftDescription?: string
  /** What's next section title */
  whatsNextTitle?: string
  /** What's next section content */
  whatsNextContent?: string
  /** Unlock button label */
  unlockLabel?: string
  /** Lock button label */
  lockLabel?: string
  /** Confirm button label */
  confirmLabel?: string
  /** Theme accent color */
  accentColor?: 'sage' | 'gold' | 'blue' | 'purple'
}

/**
 * Color theme mappings for different modules
 */
const COLOR_THEMES = {
  sage: {
    cardBorder: 'border-sage',
    cardBg: 'bg-sage-lighter',
    iconBg: 'bg-sage',
    iconText: 'text-white',
    title: 'text-sage',
    sectionTitle: 'text-sage',
    tagBg: 'bg-sage-lighter',
    tagIcon: 'text-sage',
    stepBorder: 'border-sage-light',
    stepBg: 'bg-sage-lighter',
    buttonBg: 'bg-sage',
    buttonHover: 'hover:bg-sage-hover',
    draftIconBg: 'bg-sage-light',
    draftIconText: 'text-sage',
    whatsNextBg: 'bg-white/50',
    whatsNextBorder: 'border-sage-light',
  },
  gold: {
    cardBorder: 'border-efir-gold-500',
    cardBg: 'bg-efir-gold-50',
    iconBg: 'bg-efir-gold-500',
    iconText: 'text-white',
    title: 'text-efir-gold-700',
    sectionTitle: 'text-efir-gold-700',
    tagBg: 'bg-efir-gold-100',
    tagIcon: 'text-efir-gold-700',
    stepBorder: 'border-efir-gold-200',
    stepBg: 'bg-efir-gold-50',
    buttonBg: 'bg-efir-gold-500',
    buttonHover: 'hover:bg-efir-gold-600',
    draftIconBg: 'bg-efir-gold-100',
    draftIconText: 'text-efir-gold-700',
    whatsNextBg: 'bg-white/50',
    whatsNextBorder: 'border-efir-gold-200',
  },
  blue: {
    cardBorder: 'border-blue-500',
    cardBg: 'bg-blue-50',
    iconBg: 'bg-blue-500',
    iconText: 'text-white',
    title: 'text-blue-700',
    sectionTitle: 'text-blue-700',
    tagBg: 'bg-blue-100',
    tagIcon: 'text-blue-700',
    stepBorder: 'border-blue-200',
    stepBg: 'bg-blue-50',
    buttonBg: 'bg-blue-500',
    buttonHover: 'hover:bg-blue-600',
    draftIconBg: 'bg-blue-100',
    draftIconText: 'text-blue-700',
    whatsNextBg: 'bg-white/50',
    whatsNextBorder: 'border-blue-200',
  },
  purple: {
    cardBorder: 'border-purple-500',
    cardBg: 'bg-purple-50',
    iconBg: 'bg-purple-500',
    iconText: 'text-white',
    title: 'text-purple-700',
    sectionTitle: 'text-purple-700',
    tagBg: 'bg-purple-100',
    tagIcon: 'text-purple-700',
    stepBorder: 'border-purple-200',
    stepBg: 'bg-purple-50',
    buttonBg: 'bg-purple-500',
    buttonHover: 'hover:bg-purple-600',
    draftIconBg: 'bg-purple-100',
    draftIconText: 'text-purple-700',
    whatsNextBg: 'bg-white/50',
    whatsNextBorder: 'border-purple-200',
  },
}

/**
 * CascadeConfirmDialog - Human-friendly validation flow for locking data
 *
 * Redesigned to clearly explain:
 * - What "locking" means
 * - What modules will be updated (cascade effect)
 * - That users can unlock later if needed
 *
 * Can be themed for different modules using accentColor prop.
 */
export function CascadeConfirmDialog({
  status,
  onValidate,
  onUnvalidate,
  disabled,
  cascadeSteps,
  lockedTitle = 'Data Locked',
  lockedDescription = 'Your data has been confirmed. All downstream modules have been updated.',
  draftTitle = 'Ready to Lock?',
  draftDescription = 'Lock your data to update all downstream budget modules.',
  whatsNextTitle = "What's Next?",
  whatsNextContent = 'Continue to the next step in your workflow.',
  unlockLabel = 'Unlock & Edit',
  lockLabel = 'Lock Data',
  confirmLabel = 'Lock & Continue',
  accentColor = 'sage',
}: CascadeConfirmDialogProps) {
  const [open, setOpen] = useState(false)
  const theme = COLOR_THEMES[accentColor]

  // Validated state - show success card with unlock option
  if (status === 'validated') {
    return (
      <Card className={cn(theme.cardBorder, theme.cardBg)}>
        <CardContent className="p-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <div
                className={cn(
                  'flex items-center justify-center h-10 w-10 rounded-full',
                  theme.iconBg,
                  theme.iconText
                )}
              >
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>

            <div className="flex-1">
              <h3 className={cn('font-semibold text-lg', theme.title)}>{lockedTitle}</h3>
              <p className="text-sm text-text-secondary mt-1">{lockedDescription}</p>

              <div
                className={cn('mt-3 p-3 rounded border', theme.whatsNextBg, theme.whatsNextBorder)}
              >
                <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                  {whatsNextTitle}
                </h4>
                <p className="text-sm text-text-primary">{whatsNextContent}</p>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-text-tertiary">
                  Need to make changes? You can unlock and edit your data.
                </p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onUnvalidate}
                  disabled={disabled}
                  className="gap-1.5"
                >
                  <Unlock className="h-3.5 w-3.5" />
                  {unlockLabel}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Draft state - show action card with lock button
  return (
    <>
      <Card className="border-border-light">
        <CardContent className="p-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <div
                className={cn(
                  'flex items-center justify-center h-10 w-10 rounded-full',
                  theme.draftIconBg,
                  theme.draftIconText
                )}
              >
                <Lock className="h-5 w-5" />
              </div>
            </div>

            <div className="flex-1">
              <h3 className="font-semibold text-text-primary text-lg">{draftTitle}</h3>
              <p className="text-sm text-text-secondary mt-1">{draftDescription}</p>

              <div className="mt-3 space-y-2">
                <h4
                  className={cn('text-xs font-medium uppercase tracking-wider', theme.sectionTitle)}
                >
                  This will update:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {cascadeSteps.map((step, index) => {
                    const Icon = step.icon
                    return (
                      <span
                        key={index}
                        className={cn(
                          'inline-flex items-center gap-1 text-xs px-2 py-1 rounded',
                          theme.tagBg,
                          'text-text-secondary'
                        )}
                      >
                        <Icon className={cn('h-3 w-3', theme.tagIcon)} />
                        {step.title}
                      </span>
                    )
                  })}
                </div>
              </div>

              <div className="mt-4 flex items-center justify-end">
                <Button
                  type="button"
                  onClick={() => setOpen(true)}
                  disabled={disabled}
                  className={cn('gap-2', theme.buttonBg, theme.buttonHover)}
                >
                  <Lock className="h-4 w-4" />
                  {lockLabel}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className={cn('flex items-center gap-2', theme.title)}>
              <Lock className="h-5 w-5" />
              Confirm Lock
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Explanation */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-text-primary">What happens when you lock:</h4>
              <ul className="space-y-1 text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className={theme.title}>✓</span>
                  <span>Your data becomes read-only</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className={theme.title}>✓</span>
                  <span>You can unlock later if you need to make changes</span>
                </li>
              </ul>
            </div>

            {/* Cascade modules */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-text-primary">
                <ArrowDown className={cn('h-4 w-4', theme.title)} />
                <span>The following modules will automatically update:</span>
              </div>

              <div className="space-y-2 pl-1">
                {cascadeSteps.map((step, index) => {
                  const Icon = step.icon
                  return (
                    <div
                      key={index}
                      className={cn(
                        'flex items-start gap-3 p-2 rounded border',
                        theme.stepBg,
                        theme.stepBorder
                      )}
                    >
                      <div
                        className={cn(
                          'flex items-center justify-center h-6 w-6 rounded text-xs font-bold flex-shrink-0',
                          theme.iconBg,
                          theme.iconText
                        )}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5 text-sm font-medium text-text-primary">
                          <Icon className={cn('h-3.5 w-3.5', theme.title)} />
                          {step.title}
                        </div>
                        <div className="text-xs text-text-secondary">{step.description}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => {
                onValidate(true)
                setOpen(false)
              }}
              className={cn('gap-2', theme.buttonBg, theme.buttonHover)}
            >
              <Lock className="h-4 w-4" />
              {confirmLabel}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
