import { Users, Calculator, Wallet, PieChart } from 'lucide-react'
import { CascadeConfirmDialog, type CascadeStep } from '@/components/workflow'

interface ValidationConfirmDialogProps {
  status: 'draft' | 'validated'
  onValidate: (confirmation: boolean) => void
  onUnvalidate: () => void
  disabled?: boolean
}

/**
 * Enrollment-specific cascade steps
 */
const ENROLLMENT_CASCADE_STEPS: CascadeStep[] = [
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
 * Enrollment-themed ValidationConfirmDialog
 *
 * Wraps the generic CascadeConfirmDialog with enrollment-specific cascade steps
 * and sage accent color.
 */
export function ValidationConfirmDialog({
  status,
  onValidate,
  onUnvalidate,
  disabled,
}: ValidationConfirmDialogProps) {
  return (
    <CascadeConfirmDialog
      status={status}
      onValidate={onValidate}
      onUnvalidate={onUnvalidate}
      disabled={disabled}
      cascadeSteps={ENROLLMENT_CASCADE_STEPS}
      lockedTitle="Enrollment Projections Locked"
      lockedDescription="Your projections have been confirmed. All downstream modules (Class Structure, DHG, Revenue) have been updated based on these numbers."
      draftTitle="Ready to Lock?"
      draftDescription="When you're satisfied with your enrollment projections, lock them to update all downstream budget modules."
      whatsNextTitle="What's Next?"
      whatsNextContent="Go to Class Structure to review how students will be grouped into classes, or continue to DHG Planning to see teacher requirements."
      unlockLabel="Unlock & Edit"
      lockLabel="Lock Enrollment Projections"
      confirmLabel="Lock & Continue"
      accentColor="sage"
    />
  )
}
