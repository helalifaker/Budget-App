/**
 * CascadeDialog - Auto-cascade confirmation for planning changes
 *
 * When a planning step is saved that affects downstream calculations,
 * this dialog offers the user options to:
 * - Recalculate All: Automatically cascade changes through dependent steps
 * - Do it manually: Close and let user update steps individually
 * - Remind me later: Dismiss for now, show reminder badge
 *
 * Cascade dependencies:
 * - Enrollment → Class Structure → DHG → Costs
 * - Enrollment → Revenue
 * - DHG → Costs
 */

import { useMemo } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { CheckCircle2, RefreshCw, Clock, AlertTriangle } from 'lucide-react'
import { StepProgress, STEP_METADATA } from '@/types/planning-progress'

/**
 * Cascade dependency map: which steps need recalculation when a step changes
 */
const CASCADE_DEPENDENCIES: Record<string, string[]> = {
  enrollment: ['class_structure', 'revenue'],
  class_structure: ['dhg'],
  dhg: ['costs'],
  revenue: [],
  costs: [],
  capex: [],
}

/**
 * Get all downstream steps that need recalculation (recursively)
 */
function getDownstreamSteps(stepId: string, visited = new Set<string>()): string[] {
  if (visited.has(stepId)) return []
  visited.add(stepId)

  const directDeps = CASCADE_DEPENDENCIES[stepId] || []
  const allDeps: string[] = []

  for (const dep of directDeps) {
    allDeps.push(dep)
    allDeps.push(...getDownstreamSteps(dep, visited))
  }

  return [...new Set(allDeps)] // Remove duplicates
}

interface AffectedStep {
  stepId: string
  title: string
  willRecalculate: boolean
}

interface CascadeDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Callback to close the dialog */
  onOpenChange: (open: boolean) => void
  /** The step that was just saved/changed */
  changedStepId: StepProgress['step_id']
  /** Callback when user chooses to recalculate all */
  onRecalculateAll: () => void
  /** Callback when user chooses manual update */
  onManual: () => void
  /** Callback when user wants to be reminded later */
  onRemindLater: () => void
  /** Whether recalculation is in progress */
  isRecalculating?: boolean
}

export function CascadeDialog({
  open,
  onOpenChange,
  changedStepId,
  onRecalculateAll,
  onManual,
  onRemindLater,
  isRecalculating = false,
}: CascadeDialogProps) {
  // Get all downstream steps that will be affected
  const affectedSteps = useMemo((): AffectedStep[] => {
    const downstreamIds = getDownstreamSteps(changedStepId)
    return downstreamIds.map((stepId) => ({
      stepId,
      title: STEP_METADATA[stepId]?.title || stepId,
      willRecalculate: true,
    }))
  }, [changedStepId])

  const changedStepTitle = STEP_METADATA[changedStepId]?.title || changedStepId

  // Don't show dialog if there are no downstream dependencies
  if (affectedSteps.length === 0) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-success-600" />
            {changedStepTitle} saved successfully!
          </DialogTitle>
          <DialogDescription className="pt-2">
            Your changes affect downstream calculations:
          </DialogDescription>
        </DialogHeader>

        {/* Affected steps list */}
        <div className="py-4">
          <ul className="space-y-2">
            {affectedSteps.map((step) => (
              <li
                key={step.stepId}
                className="flex items-center gap-3 p-2 rounded-lg bg-subtle border border-border-light"
              >
                <AlertTriangle className="w-4 h-4 text-warning-600 flex-shrink-0" />
                <span className="text-sm text-text-primary">
                  <strong>{step.title}</strong> needs recalculation
                </span>
              </li>
            ))}
          </ul>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={onRemindLater} disabled={isRecalculating}>
            <Clock className="w-4 h-4 mr-2" />
            Remind me later
          </Button>
          <Button variant="outline" onClick={onManual} disabled={isRecalculating}>
            I&apos;ll do it manually
          </Button>
          <Button onClick={onRecalculateAll} disabled={isRecalculating}>
            {isRecalculating ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Recalculating...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Recalculate All
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Hook for managing cascade dialog state and actions
 */
import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cascadeApi } from '@/services/cascade'
import { toastMessages } from '@/lib/toast-messages'
import { planningProgressKeys } from '@/hooks/api/usePlanningProgress'

interface UseCascadeDialogOptions {
  versionId: string | undefined
}

interface UseCascadeDialogReturn {
  /** Whether the dialog is open */
  isOpen: boolean
  /** The step that triggered the cascade */
  changedStepId: StepProgress['step_id'] | null
  /** Show the cascade dialog for a step */
  showCascadeDialog: (stepId: StepProgress['step_id']) => void
  /** Close the dialog */
  closeCascadeDialog: () => void
  /** Handle recalculate all action */
  handleRecalculateAll: () => void
  /** Handle manual action */
  handleManual: () => void
  /** Handle remind later action */
  handleRemindLater: () => void
  /** Whether recalculation is in progress */
  isRecalculating: boolean
}

export function useCascadeDialog({ versionId }: UseCascadeDialogOptions): UseCascadeDialogReturn {
  const [isOpen, setIsOpen] = useState(false)
  const [changedStepId, setChangedStepId] = useState<StepProgress['step_id'] | null>(null)
  const queryClient = useQueryClient()

  const cascadeMutation = useMutation({
    mutationFn: ({ stepId }: { stepId: string }) => {
      if (!versionId) throw new Error('No version selected')
      return cascadeApi.recalculateFromStep(versionId, stepId)
    },
    onSuccess: () => {
      toastMessages.success.custom('All dependent steps have been recalculated')
      // Invalidate planning progress to refresh status badges
      queryClient.invalidateQueries({ queryKey: planningProgressKeys.all })
      setIsOpen(false)
      setChangedStepId(null)
    },
    onError: () => {
      toastMessages.error.custom('Failed to recalculate. Please try again or update manually.')
    },
  })

  const showCascadeDialog = useCallback((stepId: StepProgress['step_id']) => {
    // Only show if there are downstream dependencies
    const downstreamSteps = getDownstreamSteps(stepId)
    if (downstreamSteps.length > 0) {
      setChangedStepId(stepId)
      setIsOpen(true)
    }
  }, [])

  const closeCascadeDialog = useCallback(() => {
    setIsOpen(false)
    setChangedStepId(null)
  }, [])

  const handleRecalculateAll = useCallback(() => {
    if (changedStepId && versionId) {
      cascadeMutation.mutate({ stepId: changedStepId })
    }
  }, [changedStepId, versionId, cascadeMutation])

  const handleManual = useCallback(() => {
    setIsOpen(false)
    setChangedStepId(null)
  }, [])

  const handleRemindLater = useCallback(() => {
    toastMessages.info.custom('You can recalculate dependent steps from each planning page')
    setIsOpen(false)
    setChangedStepId(null)
  }, [])

  return {
    isOpen,
    changedStepId,
    showCascadeDialog,
    closeCascadeDialog,
    handleRecalculateAll,
    handleManual,
    handleRemindLater,
    isRecalculating: cascadeMutation.isPending,
  }
}
