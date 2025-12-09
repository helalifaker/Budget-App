import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { GraduationCap, ChevronDown, AlertTriangle } from 'lucide-react'
import { TemplateInfo } from '@/types/api'

interface TemplateSelectorProps {
  templates: TemplateInfo[]
  currentCycleCode: string
  onApplyTemplate: (templateCode: string, overwriteExisting: boolean) => Promise<void>
  isApplying?: boolean
  disabled?: boolean
}

export function TemplateSelector({
  templates,
  currentCycleCode,
  onApplyTemplate,
  isApplying = false,
  disabled = false,
}: TemplateSelectorProps) {
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    template: TemplateInfo | null
  }>({ open: false, template: null })
  const [overwriteExisting, setOverwriteExisting] = useState(false)

  // Filter templates applicable to current cycle
  const applicableTemplates = templates.filter((t) => t.cycle_codes.includes(currentCycleCode))

  const handleTemplateSelect = (template: TemplateInfo) => {
    setConfirmDialog({ open: true, template })
    setOverwriteExisting(false)
  }

  const handleConfirm = async () => {
    if (confirmDialog.template) {
      await onApplyTemplate(confirmDialog.template.code, overwriteExisting)
      setConfirmDialog({ open: false, template: null })
    }
  }

  const handleCancel = () => {
    setConfirmDialog({ open: false, template: null })
    setOverwriteExisting(false)
  }

  if (applicableTemplates.length === 0) {
    return null
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" disabled={disabled || isApplying}>
            <GraduationCap className="h-4 w-4 mr-2" />
            Load Template
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-64">
          <DropdownMenuLabel>Curriculum Templates</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {applicableTemplates.map((template) => (
            <DropdownMenuItem
              key={template.code}
              onClick={() => handleTemplateSelect(template)}
              className="flex flex-col items-start gap-1 py-2"
            >
              <span className="font-medium">{template.name}</span>
              {template.description && (
                <span className="text-xs text-muted-foreground">{template.description}</span>
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => !open && handleCancel()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply Curriculum Template</DialogTitle>
            <DialogDescription>
              This will populate subject hours with values from the{' '}
              <strong>{confirmDialog.template?.name}</strong> template.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Warning about existing data */}
            <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-amber-800">Existing data</p>
                <p className="text-amber-700">
                  If you already have hours configured, they will be preserved unless you check the
                  "Overwrite" option below.
                </p>
              </div>
            </div>

            {/* Overwrite checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="overwrite"
                checked={overwriteExisting}
                onCheckedChange={(checked) => setOverwriteExisting(checked === true)}
              />
              <Label htmlFor="overwrite" className="text-sm cursor-pointer">
                Overwrite existing values
              </Label>
            </div>

            {/* Template info */}
            {confirmDialog.template && (
              <div className="text-sm text-muted-foreground">
                <p>
                  <strong>Template:</strong> {confirmDialog.template.name}
                </p>
                {confirmDialog.template.description && (
                  <p>
                    <strong>Description:</strong> {confirmDialog.template.description}
                  </p>
                )}
                <p>
                  <strong>Applicable cycles:</strong>{' '}
                  {confirmDialog.template.cycle_codes.join(', ')}
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel} disabled={isApplying}>
              Cancel
            </Button>
            <Button onClick={handleConfirm} disabled={isApplying}>
              {isApplying ? 'Applying...' : 'Apply Template'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
