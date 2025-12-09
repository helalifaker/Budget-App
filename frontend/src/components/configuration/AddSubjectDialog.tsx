import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Plus } from 'lucide-react'

// Category type
type SubjectCategory = 'core' | 'elective' | 'specialty' | 'local'

// Validation schema for new subject
const addSubjectSchema = z.object({
  code: z
    .string()
    .min(2, 'Code must be at least 2 characters')
    .max(6, 'Code must be at most 6 characters')
    .regex(/^[A-Z0-9]+$/, 'Code must be uppercase letters and numbers only')
    .transform((val) => val.toUpperCase()),
  name_fr: z
    .string()
    .min(1, 'French name is required')
    .max(100, 'French name must be at most 100 characters'),
  name_en: z
    .string()
    .min(1, 'English name is required')
    .max(100, 'English name must be at most 100 characters'),
  category: z
    .string()
    .min(1, 'Please select a category')
    .refine(
      (val): val is SubjectCategory => ['core', 'elective', 'specialty', 'local'].includes(val),
      'Invalid category'
    ),
  applicable_cycles: z.array(z.string()).min(1, 'Please select at least one applicable cycle'),
})

type AddSubjectFormValues = z.infer<typeof addSubjectSchema>

interface AddSubjectDialogProps {
  onAddSubject: (data: AddSubjectFormValues) => Promise<void>
  isAdding?: boolean
  existingCodes?: string[]
}

// Available cycles for subject configuration
const CYCLES = [
  { code: 'MAT', name: 'Maternelle' },
  { code: 'ELEM', name: 'Élémentaire' },
  { code: 'COLL', name: 'Collège' },
  { code: 'LYC', name: 'Lycée' },
]

// Category options
const CATEGORIES = [
  { value: 'core', label: 'Core', description: 'Required subjects (French, Math, etc.)' },
  {
    value: 'elective',
    label: 'Elective',
    description: 'Optional subjects (additional languages, etc.)',
  },
  {
    value: 'specialty',
    label: 'Specialty',
    description: 'Specialized tracks (Sciences, Literature, etc.)',
  },
  {
    value: 'local',
    label: 'Local',
    description: 'Local curriculum subjects (Arabic, Saudi culture)',
  },
]

export function AddSubjectDialog({
  onAddSubject,
  isAdding = false,
  existingCodes = [],
}: AddSubjectDialogProps) {
  const [open, setOpen] = useState(false)

  const form = useForm<AddSubjectFormValues>({
    resolver: zodResolver(addSubjectSchema),
    defaultValues: {
      code: '',
      name_fr: '',
      name_en: '',
      category: undefined,
      applicable_cycles: ['COLL', 'LYC'], // Default to secondary school
    },
  })

  const onSubmit = async (data: AddSubjectFormValues) => {
    // Check if code already exists
    if (existingCodes.includes(data.code)) {
      form.setError('code', { message: 'This code already exists' })
      return
    }

    await onAddSubject(data)
    form.reset()
    setOpen(false)
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      form.reset()
    }
    setOpen(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Plus className="h-4 w-4 mr-2" />
          Add Subject
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add New Subject</DialogTitle>
          <DialogDescription>
            Create a new custom subject for your curriculum. This subject will be available for hour
            allocation.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Subject Code */}
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Subject Code</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g., ARAB, INFO, PHYS"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                      className="font-mono uppercase"
                    />
                  </FormControl>
                  <FormDescription>2-6 uppercase letters/numbers. Must be unique.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* French Name */}
            <FormField
              control={form.control}
              name="name_fr"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>French Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Arabe, Informatique" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* English Name */}
            <FormField
              control={form.control}
              name="name_en"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>English Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Arabic, Computer Science" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Category */}
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          <div className="flex flex-col">
                            <span>{cat.label}</span>
                            <span className="text-xs text-muted-foreground">{cat.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Applicable Cycles */}
            <FormField
              control={form.control}
              name="applicable_cycles"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Applicable Cycles</FormLabel>
                  <FormDescription>
                    Select the education cycles where this subject applies.
                  </FormDescription>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {CYCLES.map((cycle) => (
                      <div key={cycle.code} className="flex items-center space-x-2">
                        <Checkbox
                          id={`cycle-${cycle.code}`}
                          checked={field.value?.includes(cycle.code)}
                          onCheckedChange={(checked) => {
                            const newValue = checked
                              ? [...(field.value || []), cycle.code]
                              : (field.value || []).filter((c) => c !== cycle.code)
                            field.onChange(newValue)
                          }}
                        />
                        <label htmlFor={`cycle-${cycle.code}`} className="text-sm cursor-pointer">
                          {cycle.name}
                        </label>
                      </div>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isAdding}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isAdding}>
                {isAdding ? 'Adding...' : 'Add Subject'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
