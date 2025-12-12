import { useState } from 'react'
import {
  Lock,
  Unlock,
  CheckCircle2,
  ArrowDown,
  Users,
  Calculator,
  Wallet,
  PieChart,
} from 'lucide-react'
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

interface ValidationConfirmDialogProps {
  status: 'draft' | 'validated'
  onValidate: (confirmation: boolean) => void
  onUnvalidate: () => void
  disabled?: boolean
}

/**
 * Cascade steps shown in the validation dialog
 * Helps users understand what will be updated when they lock
 */
const CASCADE_STEPS = [
  {
    icon: Users,
    title: 'Class Structure',
    description: 'Number of class sections per grade will be calculated',
  },
  {
    icon: Calculator,
    title: 'Teacher Planning (DHG)',
    description: 'Required teaching hours based on class count',
  },
  {
    icon: Wallet,
    title: 'Revenue Projections',
    description: 'Tuition and fees based on student numbers',
  },
  {
    icon: PieChart,
    title: 'Budget Consolidation',
    description: 'Overall financial picture will be updated',
  },
]

/**
 * ValidationConfirmDialog - Human-friendly validation flow
 *
 * Redesigned to clearly explain:
 * - What "locking" means
 * - What modules will be updated
 * - That users can unlock later if needed
 *
 * Uses sage accent colors for enrollment module theming.
 */
export function ValidationConfirmDialog({
  status,
  onValidate,
  onUnvalidate,
  disabled,
}: ValidationConfirmDialogProps) {
  const [open, setOpen] = useState(false)

  // Validated state - show success card with unlock option
  if (status === 'validated') {
    return (
      <Card className="border-sage bg-sage-lighter">
        <CardContent className="p-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-sage text-white">
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>

            <div className="flex-1">
              <h3 className="font-semibold text-sage text-lg">Enrollment Projections Locked</h3>
              <p className="text-sm text-text-secondary mt-1">
                Your projections have been confirmed. All downstream modules (Class Structure, DHG,
                Revenue) have been updated based on these numbers.
              </p>

              <div className="mt-3 p-3 rounded bg-white/50 border border-sage-light">
                <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                  What's Next?
                </h4>
                <p className="text-sm text-text-primary">
                  Go to <span className="font-medium">Class Structure</span> to review how students
                  will be grouped into classes, or continue to{' '}
                  <span className="font-medium">DHG Planning</span> to see teacher requirements.
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-text-tertiary">
                  Need to make changes? You can unlock and edit your projections.
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
                  Unlock & Edit
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
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-sage-light text-sage">
                <Lock className="h-5 w-5" />
              </div>
            </div>

            <div className="flex-1">
              <h3 className="font-semibold text-text-primary text-lg">Ready to Lock?</h3>
              <p className="text-sm text-text-secondary mt-1">
                When you're satisfied with your enrollment projections, lock them to update all
                downstream budget modules.
              </p>

              <div className="mt-3 space-y-2">
                <h4 className="text-xs font-medium text-sage uppercase tracking-wider">
                  This will update:
                </h4>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 text-xs bg-sage-lighter text-text-secondary px-2 py-1 rounded">
                    <Users className="h-3 w-3 text-sage" />
                    Class Structure
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs bg-sage-lighter text-text-secondary px-2 py-1 rounded">
                    <Calculator className="h-3 w-3 text-sage" />
                    DHG/Teachers
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs bg-sage-lighter text-text-secondary px-2 py-1 rounded">
                    <Wallet className="h-3 w-3 text-sage" />
                    Revenue
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs bg-sage-lighter text-text-secondary px-2 py-1 rounded">
                    <PieChart className="h-3 w-3 text-sage" />
                    Budget
                  </span>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-end">
                <Button
                  type="button"
                  onClick={() => setOpen(true)}
                  disabled={disabled}
                  className="gap-2 bg-sage hover:bg-sage-hover"
                >
                  <Lock className="h-4 w-4" />
                  Lock Enrollment Projections
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
            <DialogTitle className="flex items-center gap-2 text-sage">
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
                  <span className="text-sage">✓</span>
                  <span>Your enrollment numbers become read-only</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-sage">✓</span>
                  <span>You can unlock later if you need to make changes</span>
                </li>
              </ul>
            </div>

            {/* Cascade modules */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-text-primary">
                <ArrowDown className="h-4 w-4 text-sage" />
                <span>The following modules will automatically update:</span>
              </div>

              <div className="space-y-2 pl-1">
                {CASCADE_STEPS.map((step, index) => (
                  <div
                    key={index}
                    className={cn(
                      'flex items-start gap-3 p-2 rounded',
                      'bg-sage-lighter border border-sage-light'
                    )}
                  >
                    <div className="flex items-center justify-center h-6 w-6 rounded bg-sage text-white text-xs font-bold flex-shrink-0">
                      {index + 1}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-primary">{step.title}</div>
                      <div className="text-xs text-text-secondary">{step.description}</div>
                    </div>
                  </div>
                ))}
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
              className="gap-2 bg-sage hover:bg-sage-hover"
            >
              <Lock className="h-4 w-4" />
              Lock & Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
