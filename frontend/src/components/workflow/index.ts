/**
 * Workflow Components
 *
 * Generic, reusable components for multi-step workflows across the application.
 * These components can be themed using the accentColor prop to match different modules.
 *
 * Usage:
 * - StepIntroCard: Explains what to do at each workflow step
 * - WhatsNextCard: Shows next steps after completing a workflow
 * - CascadeConfirmDialog: Confirms locking data with cascade effect explanation
 */

export { StepIntroCard, StepIntroCardCompact } from './StepIntroCard'
export type { NextStep } from './WhatsNextCard'
export { WhatsNextCard } from './WhatsNextCard'
export type { CascadeStep } from './CascadeConfirmDialog'
export { CascadeConfirmDialog } from './CascadeConfirmDialog'
