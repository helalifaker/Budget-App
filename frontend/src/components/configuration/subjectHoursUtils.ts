import { SubjectWithHours, LevelInfo } from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface SubjectHoursMatrixRow {
  id: string // subject_id used as row ID
  subjectId: string
  subjectCode: string
  subjectName: string
  category: 'core' | 'elective' | 'specialty' | 'local'
  isApplicable: boolean
  hours: Record<string, number | null> // levelId -> hours
  splitFlags: Record<string, boolean> // levelId -> isSplit
  notes: string
  isDirty: boolean
  isValid: boolean
  originalHours?: Record<string, number | null> // For tracking changes
}

// ============================================================================
// Validation helpers
// ============================================================================

export function validateHoursValue(value: number | null): boolean {
  if (value === null || value === undefined) return true // Empty is valid
  return value >= 0 && value <= 12 // Hours per week range
}

export function validateRow(row: SubjectHoursMatrixRow): boolean {
  if (!row.isApplicable) return true // Non-applicable rows are always valid
  return Object.values(row.hours).every(validateHoursValue)
}

// ============================================================================
// Transform API data to matrix rows
// ============================================================================

export function transformToMatrixRows(
  subjects: SubjectWithHours[],
  levels: LevelInfo[]
): SubjectHoursMatrixRow[] {
  return subjects.map((subject): SubjectHoursMatrixRow => {
    // Build hours map from subject data
    const hours: Record<string, number | null> = {}
    const splitFlags: Record<string, boolean> = {}

    for (const level of levels) {
      const levelHours = subject.hours[level.id]
      hours[level.id] = levelHours?.hours_per_week ?? null
      splitFlags[level.id] = levelHours?.is_split ?? false
    }

    const row: SubjectHoursMatrixRow = {
      id: subject.id,
      subjectId: subject.id,
      subjectCode: subject.code,
      subjectName: subject.name_fr || subject.name_en,
      category: subject.category as 'core' | 'elective' | 'specialty' | 'local',
      isApplicable: subject.is_applicable,
      hours,
      splitFlags,
      notes: '', // Will be populated from level-specific notes if needed
      isDirty: false,
      isValid: true,
      originalHours: { ...hours },
    }

    row.isValid = validateRow(row)
    return row
  })
}

// ============================================================================
// Transform matrix rows back to batch request entries
// ============================================================================

export interface SubjectHoursEntryForBatch {
  subject_id: string
  level_id: string
  hours_per_week: number | null
  is_split: boolean
  notes: string | null
}

export function transformToEntries(
  rows: SubjectHoursMatrixRow[],
  levels: LevelInfo[],
  onlyDirty: boolean = true
): SubjectHoursEntryForBatch[] {
  const entries: SubjectHoursEntryForBatch[] = []

  for (const row of rows) {
    // Skip non-applicable or non-dirty rows if filtering
    if (!row.isApplicable) continue
    if (onlyDirty && !row.isDirty) continue

    for (const level of levels) {
      const hours = row.hours[level.id]
      const isSplit = row.splitFlags[level.id] ?? false

      entries.push({
        subject_id: row.subjectId,
        level_id: level.id,
        hours_per_week: hours,
        is_split: isSplit,
        notes: row.notes || null,
      })
    }
  }

  return entries
}
