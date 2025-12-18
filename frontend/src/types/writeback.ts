import { z } from 'zod'

/**
 * Type definitions for cell-level writeback with optimistic locking
 * Phase 3.3: Frontend hooks for real-time cell-level writeback
 */

// Cell Update (single cell)
export const CellUpdateSchema = z.object({
  cellId: z.string().uuid(),
  value: z.number(),
  version: z.number().int().min(0),
})

export type CellUpdate = z.infer<typeof CellUpdateSchema>

// Batch Update (multiple cells)
export const BatchUpdateSchema = z.object({
  sessionId: z.string().uuid(),
  updates: z.array(
    z.object({
      cellId: z.string().uuid(),
      value: z.number(),
      version: z.number().int().min(0),
    })
  ),
})

export type BatchUpdate = z.infer<typeof BatchUpdateSchema>

// Cell Data (full cell structure)
export const CellDataSchema = z.object({
  id: z.string().uuid(),
  version_id: z.string().uuid(),
  module_code: z.string(),
  entity_id: z.string().uuid(),
  field_name: z.string(),
  period_code: z.string().optional(),
  value_numeric: z.number().optional(),
  value_text: z.string().optional(),
  version: z.number().int().min(0),
  is_locked: z.boolean(),
  modified_by: z.string().uuid(),
  modified_at: z.string(),
  created_at: z.string(),
})

export type CellData = z.infer<typeof CellDataSchema>

// Cell Change (change history entry)
export const CellChangeSchema = z.object({
  id: z.string().uuid(),
  cell_id: z.string().uuid(),
  session_id: z.string().uuid(),
  sequence_number: z.number().int().min(0),
  module_code: z.string(),
  entity_id: z.string().uuid(),
  field_name: z.string(),
  old_value: z.number().optional(),
  new_value: z.number().optional(),
  change_type: z.enum(['manual', 'spread', 'import', 'undo', 'redo']),
  changed_by: z.string().uuid(),
  changed_at: z.string(),
})

export type CellChange = z.infer<typeof CellChangeSchema>

// Cell Comment
export const CellCommentSchema = z.object({
  id: z.string().uuid(),
  cell_id: z.string().uuid(),
  comment_text: z.string(),
  is_resolved: z.boolean(),
  created_by: z.string().uuid(),
  created_at: z.string(),
  resolved_by: z.string().uuid().optional(),
  resolved_at: z.string().optional(),
})

export type CellComment = z.infer<typeof CellCommentSchema>

// API Response Schemas
export const CellUpdateResponseSchema = z.object({
  id: z.string().uuid(),
  value_numeric: z.number(),
  version: z.number().int().min(0),
  modified_by: z.string().uuid(),
  modified_at: z.string(),
})

export type CellUpdateResponse = z.infer<typeof CellUpdateResponseSchema>

export const BatchUpdateResponseSchema = z.object({
  session_id: z.string().uuid(),
  updated_count: z.number().int().min(0),
  conflicts: z.array(
    z.object({
      cell_id: z.string().uuid(),
      expected_version: z.number().int(),
      actual_version: z.number().int(),
      message: z.string(),
    })
  ),
})

export type BatchUpdateResponse = z.infer<typeof BatchUpdateResponseSchema>

// Conflict Detail
export interface ConflictDetail {
  cell_id: string
  expected_version: number
  actual_version: number
  message: string
}

// Change History Filters
export interface ChangeHistoryFilters {
  module_code?: string
  entity_id?: string
  field_name?: string
  limit?: number
  offset?: number
}

// Custom Error Classes
export class VersionConflictError extends Error {
  constructor(
    message: string,
    public cellId: string,
    public expectedVersion: number,
    public actualVersion: number
  ) {
    super(message)
    this.name = 'VersionConflictError'
  }
}

export class CellLockedError extends Error {
  constructor(
    message: string,
    public cellId: string
  ) {
    super(message)
    this.name = 'CellLockedError'
  }
}

export class BatchConflictError extends Error {
  constructor(
    message: string,
    public conflicts: ConflictDetail[]
  ) {
    super(message)
    this.name = 'BatchConflictError'
  }
}

/**
 * Phase 3.4: Supabase Realtime Synchronization Types
 */

/**
 * Realtime change event from Supabase
 */
export interface RealtimeChange {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE'
  cell: CellData
  userId: string
}

/**
 * Realtime comment event from Supabase
 */
export interface RealtimeCommentChange {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE'
  comment: CellComment
  userId: string
}

/**
 * User presence information
 */
export interface PresenceUser {
  user_id: string
  user_email: string
  joined_at: string
  editing_cell?: string
  last_activity?: string
}

/**
 * User activity broadcast payload
 */
export interface UserActivityPayload {
  action: 'viewing' | 'editing' | 'idle'
  cellId?: string
  moduleName?: string
  timestamp: string
}

/**
 * Conflict resolution strategy
 */
export type ConflictResolution = 'server' | 'client' | 'manual'

/**
 * Subscription status for Realtime connection
 */
export type SubscriptionStatus = 'IDLE' | 'CONNECTING' | 'SUBSCRIBED' | 'CLOSED' | 'CHANNEL_ERROR'

/**
 * Realtime sync options
 */
export interface RealtimeSyncOptions {
  versionId: string
  onCellChanged?: (change: RealtimeChange) => void
  onConnectionChange?: (status: SubscriptionStatus) => void
  showNotifications?: boolean
}

/**
 * Comment sync options
 */
export interface RealtimeCommentOptions {
  cellId: string
  onCommentChanged?: (change: RealtimeCommentChange) => void
  showNotifications?: boolean
}

/**
 * User presence options
 */
export interface UserPresenceOptions {
  versionId: string
  onUserJoin?: (user: PresenceUser) => void
  onUserLeave?: (user: PresenceUser) => void
  broadcastActivity?: boolean
}

/**
 * Cell Lock Request
 */
export const LockRequestSchema = z.object({
  lock_reason: z.string().optional(),
})

export type LockRequest = z.infer<typeof LockRequestSchema>

/**
 * Cell Lock Response
 */
export const CellLockResponseSchema = z.object({
  id: z.string().uuid(),
  is_locked: z.boolean(),
  lock_reason: z.string().optional(),
  locked_by: z.string().uuid().optional(),
  locked_at: z.string().optional(),
})

export type CellLockResponse = z.infer<typeof CellLockResponseSchema>
