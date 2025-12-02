import { z } from 'zod'

export const enrollmentSchema = z.object({
  level_id: z.string().uuid('Invalid level selected'),
  nationality_type_id: z.string().uuid('Invalid nationality type selected'),
  student_count: z
    .number()
    .min(0, 'Student count must be 0 or more')
    .max(1000, 'Student count must be 1000 or less'),
})

export type EnrollmentFormData = z.infer<typeof enrollmentSchema>

export const classStructureSchema = z.object({
  level_id: z.string().uuid('Invalid level selected'),
  number_of_classes: z
    .number()
    .min(0, 'Number of classes must be 0 or more')
    .max(50, 'Number of classes must be 50 or less'),
  avg_class_size: z
    .number()
    .min(1, 'Average class size must be at least 1')
    .max(100, 'Average class size must be 100 or less'),
})

export type ClassStructureFormData = z.infer<typeof classStructureSchema>
