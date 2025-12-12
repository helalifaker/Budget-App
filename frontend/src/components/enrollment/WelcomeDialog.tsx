import { useState, useEffect } from 'react'
import { GraduationCap, ArrowRight, TrendingUp, Calculator, DollarSign } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

interface WelcomeDialogProps {
  /** Storage key for tracking first visit */
  storageKey?: string
  /** Callback when user clicks Get Started */
  onGetStarted?: () => void
  /** Callback when user clicks Skip */
  onSkip?: () => void
}

/**
 * Process steps shown in the welcome dialog
 * Helps users understand the enrollment planning workflow
 */
const PROCESS_STEPS = [
  {
    number: 1,
    title: 'Select a Scenario',
    description: 'Choose conservative, base, or optimistic assumptions',
    icon: TrendingUp,
  },
  {
    number: 2,
    title: 'Review & Adjust',
    description: 'Check the projections, adjust if needed (most users can use defaults)',
    icon: Calculator,
  },
  {
    number: 3,
    title: 'Lock & Continue',
    description: 'Confirm your projections to update the budget',
    icon: DollarSign,
  },
]

/**
 * WelcomeDialog - First-time user onboarding for enrollment planning
 *
 * Shows on first visit to enrollment planning to help school directors
 * understand:
 * - The PURPOSE of enrollment planning
 * - How projections drive the budget
 * - The 3-step process overview
 *
 * Uses localStorage to remember if user has seen the dialog.
 * User can choose "Get Started" or "Skip" (for returning users).
 */
export function WelcomeDialog({
  storageKey = 'enrollment-welcome-seen',
  onGetStarted,
  onSkip,
}: WelcomeDialogProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Check localStorage on mount to show dialog for first-time users
  useEffect(() => {
    const hasSeen = localStorage.getItem(storageKey)
    if (!hasSeen) {
      setIsOpen(true)
    }
  }, [storageKey])

  const handleClose = (shouldRemember = true) => {
    if (shouldRemember) {
      localStorage.setItem(storageKey, 'true')
    }
    setIsOpen(false)
  }

  const handleGetStarted = () => {
    handleClose(true)
    onGetStarted?.()
  }

  const handleSkip = () => {
    handleClose(true)
    onSkip?.()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose(true)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-sage">
            <GraduationCap className="h-6 w-6" />
            Welcome to Enrollment Planning
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-2">
          {/* Introduction */}
          <div className="space-y-2">
            <p className="text-sm text-text-secondary leading-relaxed">
              This module helps you project student enrollment for the upcoming budget year and the
              next 5 years.
            </p>
          </div>

          {/* What enrollment projections drive */}
          <div className="bg-sage-lighter rounded-lg p-4 space-y-3">
            <h4 className="text-sm font-semibold text-sage uppercase tracking-wider">
              Your Enrollment Projections Drive
            </h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage text-white text-xs">
                  $
                </span>
                <span>
                  <strong className="text-text-primary">Revenue calculations</strong> — more
                  students = more tuition
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage text-white text-xs">
                  👤
                </span>
                <span>
                  <strong className="text-text-primary">Teacher staffing needs</strong> — more
                  students = more teachers
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage text-white text-xs">
                  📊
                </span>
                <span>
                  <strong className="text-text-primary">Class structure planning</strong> — how to
                  group students
                </span>
              </li>
            </ul>
          </div>

          {/* Process steps */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-text-secondary">
              The Process <span className="text-text-tertiary">(3 simple steps, ~10 minutes)</span>
            </h4>

            <div className="space-y-3">
              {PROCESS_STEPS.map((step) => {
                const Icon = step.icon
                return (
                  <div
                    key={step.number}
                    className={cn(
                      'flex items-start gap-3 p-3 rounded-lg',
                      'border border-border-light hover:border-sage-light',
                      'transition-colors duration-200'
                    )}
                  >
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-sage text-white text-sm font-bold flex-shrink-0">
                      {step.number}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-sage" />
                        <span className="text-sm font-semibold text-text-primary">
                          {step.title}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary mt-0.5">{step.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="ghost" onClick={handleSkip}>
            Skip, I know what to do
          </Button>
          <Button
            type="button"
            onClick={handleGetStarted}
            className="gap-2 bg-sage hover:bg-sage-hover"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
