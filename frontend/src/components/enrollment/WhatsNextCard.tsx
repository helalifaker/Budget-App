import { Users, Calculator, BarChart3 } from 'lucide-react'
import { WhatsNextCard as GenericWhatsNextCard, type NextStep } from '@/components/workflow'

interface EnrollmentWhatsNextCardProps {
  /** Callback when user wants to edit projections */
  onEdit?: () => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Enrollment-specific next steps
 */
const ENROLLMENT_NEXT_STEPS: NextStep[] = [
  {
    number: 1,
    title: 'Class Structure',
    description:
      'Review how students are grouped into classes (auto-calculated based on your projections)',
    icon: Users,
    href: '/students/class-structure',
  },
  {
    number: 2,
    title: 'Teacher Planning (DHG)',
    description: 'Calculate required teaching hours and staffing needs',
    icon: Calculator,
    href: '/teachers/dhg/planning',
  },
  {
    number: 3,
    title: 'Budget Consolidation',
    description: 'See the financial impact of your projections',
    icon: BarChart3,
    href: '/consolidation/budget',
  },
]

/**
 * Enrollment-themed WhatsNextCard
 *
 * Wraps the generic WhatsNextCard with enrollment-specific next steps
 * and sage accent color.
 */
export function WhatsNextCard({ onEdit, className }: EnrollmentWhatsNextCardProps) {
  return (
    <GenericWhatsNextCard
      successTitle="Enrollment Projections Locked"
      successDescription="You can now proceed to the next planning steps. Your enrollment numbers are feeding into the calculations below."
      nextSteps={ENROLLMENT_NEXT_STEPS}
      onEdit={onEdit}
      editLabel="Edit Projections"
      footerText="Want to make changes? You can unlock your projections."
      accentColor="sage"
      className={className}
    />
  )
}
