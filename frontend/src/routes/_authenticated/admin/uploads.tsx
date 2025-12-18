/**
 * Admin Uploads Page - /admin/uploads
 *
 * Allows administrators to upload historical actuals data from Excel/CSV files.
 *
 * Features:
 * - Drag & drop file upload
 * - Fiscal year selection
 * - Module auto-detection or manual selection
 * - Preview with validation feedback
 * - Import execution with progress
 * - Template downloads
 * - Import history view
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useCallback, useRef } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  usePreviewImport,
  useExecuteImport,
  useImportHistory,
  useDownloadTemplate,
  useDeleteHistoricalData,
} from '@/hooks/api/useHistoricalImport'
import type { ImportModule, ImportPreviewResponse } from '@/services/historical-import'
import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  X,
  Trash2,
  FileX,
  RefreshCw,
  History,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/_authenticated/admin/uploads')({
  component: AdminUploadsPage,
})

const MODULES: { value: ImportModule; label: string }[] = [
  { value: 'enrollment', label: 'Enrollment (Student Counts)' },
  { value: 'dhg', label: 'DHG (Teacher FTE)' },
  { value: 'revenue', label: 'Revenue' },
  { value: 'costs', label: 'Costs' },
  { value: 'capex', label: 'CapEx' },
]

// Sentinel value for "auto-detect" in module select (empty string not allowed by Radix Select)
const AUTO_DETECT_VALUE = '__auto__'

// Generate fiscal year options (current year + 5 years back)
const currentYear = new Date().getFullYear()
const FISCAL_YEARS = Array.from({ length: 6 }, (_, i) => currentYear - i)

function AdminUploadsPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fiscalYear, setFiscalYear] = useState<number>(currentYear - 1) // Default to last year
  const [selectedModule, setSelectedModule] = useState<ImportModule | typeof AUTO_DETECT_VALUE>(
    AUTO_DETECT_VALUE
  )
  const [overwrite, setOverwrite] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ year: number; module?: ImportModule } | null>(
    null
  )
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Hooks
  const { preview, previewData, isPreviewLoading, previewError, resetPreview } = usePreviewImport()

  const { execute, importResult, isImporting, importError, resetImport } = useExecuteImport()

  const { data: importHistory, isLoading: historyLoading } = useImportHistory()
  const { downloadTemplate, isDownloading } = useDownloadTemplate()
  const { deleteData, isDeleting } = useDeleteHistoricalData()

  // File drop handling
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      const file = e.dataTransfer.files[0]
      if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.csv'))) {
        setSelectedFile(file)
        resetPreview()
        resetImport()
      }
    },
    [resetPreview, resetImport]
  )

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      resetPreview()
      resetImport()
    }
  }

  const handlePreview = () => {
    if (selectedFile) {
      preview({
        file: selectedFile,
        fiscalYear,
        module: selectedModule === AUTO_DETECT_VALUE ? undefined : selectedModule,
      })
    }
  }

  const handleImport = () => {
    if (selectedFile) {
      execute({
        file: selectedFile,
        fiscalYear,
        module: selectedModule === AUTO_DETECT_VALUE ? undefined : selectedModule,
        overwrite,
      })
    }
  }

  const handleClearFile = () => {
    setSelectedFile(null)
    resetPreview()
    resetImport()
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleDeleteConfirm = () => {
    if (deleteTarget) {
      deleteData({ fiscalYear: deleteTarget.year, module: deleteTarget.module })
      setShowDeleteDialog(false)
      setDeleteTarget(null)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <PageContainer
      title="Data Uploads"
      description="Upload historical data from Excel or CSV files to enable year-over-year comparisons in planning grids."
    >
      <div className="space-y-6">
        {/* Import Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Card */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5" />
                  Upload File
                </CardTitle>
                <CardDescription>
                  Drag and drop an Excel (.xlsx) or CSV file, or click to browse
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* File dropzone */}
                <div
                  className={cn(
                    'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                    'hover:border-primary-400 hover:bg-primary-50/50',
                    selectedFile
                      ? 'border-success-400 bg-success-50/50'
                      : 'border-border-medium bg-subtle'
                  )}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.csv"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div className="space-y-2">
                      <CheckCircle2 className="w-12 h-12 mx-auto text-success-600" />
                      <p className="font-medium text-success-700">{selectedFile.name}</p>
                      <p className="text-sm text-text-muted">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleClearFile()
                        }}
                      >
                        <X className="w-4 h-4 mr-1" />
                        Clear
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-12 h-12 mx-auto text-text-muted" />
                      <p className="font-medium text-text-secondary">
                        Drop your file here, or click to browse
                      </p>
                      <p className="text-sm text-text-muted">Accepted: .xlsx, .csv</p>
                    </div>
                  )}
                </div>

                {/* Configuration row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-text-secondary mb-1 block">
                      Fiscal Year
                    </label>
                    <Select
                      value={String(fiscalYear)}
                      onValueChange={(val) => setFiscalYear(Number(val))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FISCAL_YEARS.map((year) => (
                          <SelectItem key={year} value={String(year)}>
                            {year}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-text-secondary mb-1 block">
                      Module (Auto-detect if empty)
                    </label>
                    <Select
                      value={selectedModule}
                      onValueChange={(val) =>
                        setSelectedModule(val as ImportModule | typeof AUTO_DETECT_VALUE)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Auto-detect from columns" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={AUTO_DETECT_VALUE}>Auto-detect</SelectItem>
                        {MODULES.map(({ value, label }) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-end">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={overwrite}
                        onChange={(e) => setOverwrite(e.target.checked)}
                        className="rounded border-border-medium"
                      />
                      <span className="text-sm text-text-secondary">Overwrite existing data</span>
                    </label>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-3">
                  <Button onClick={handlePreview} disabled={!selectedFile || isPreviewLoading}>
                    {isPreviewLoading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <FileSpreadsheet className="w-4 h-4 mr-2" />
                    )}
                    Preview Import
                  </Button>
                  <Button
                    variant="default"
                    onClick={handleImport}
                    disabled={!previewData?.can_import || isImporting}
                  >
                    {isImporting ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Upload className="w-4 h-4 mr-2" />
                    )}
                    Import Data
                  </Button>
                </div>

                {/* Errors */}
                {(previewError || importError) && (
                  <div className="flex items-start gap-2 p-3 bg-error-50 border border-error-200 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-error-800">Error</p>
                      <p className="text-sm text-error-700">
                        {previewError?.message || importError?.message}
                      </p>
                    </div>
                  </div>
                )}

                {/* Import Result Feedback */}
                {importResult && (
                  <div
                    className={cn(
                      'flex items-start gap-3 p-4 rounded-lg border-2',
                      importResult.status === 'success' && 'bg-success-50 border-success-300',
                      importResult.status === 'partial' && 'bg-warning-50 border-warning-300',
                      importResult.status === 'error' && 'bg-error-50 border-error-300'
                    )}
                  >
                    {importResult.status === 'success' && (
                      <CheckCircle2 className="w-6 h-6 text-success-600 flex-shrink-0" />
                    )}
                    {importResult.status === 'partial' && (
                      <AlertTriangle className="w-6 h-6 text-warning-600 flex-shrink-0" />
                    )}
                    {importResult.status === 'error' && (
                      <AlertCircle className="w-6 h-6 text-error-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p
                        className={cn(
                          'font-semibold text-lg',
                          importResult.status === 'success' && 'text-success-800',
                          importResult.status === 'partial' && 'text-warning-800',
                          importResult.status === 'error' && 'text-error-800'
                        )}
                      >
                        {importResult.status === 'success' && '✓ Import Successful!'}
                        {importResult.status === 'partial' && '⚠ Partial Import'}
                        {importResult.status === 'error' && '✕ Import Failed'}
                      </p>
                      <p
                        className={cn(
                          'text-sm mt-1',
                          importResult.status === 'success' && 'text-success-700',
                          importResult.status === 'partial' && 'text-warning-700',
                          importResult.status === 'error' && 'text-error-700'
                        )}
                      >
                        {importResult.message}
                      </p>
                      {/* Stats breakdown */}
                      <div className="flex flex-wrap gap-4 mt-3 text-sm">
                        {importResult.imported_count > 0 && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-success-100 text-success-800 rounded-full">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            {importResult.imported_count} imported
                          </span>
                        )}
                        {importResult.updated_count > 0 && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                            <RefreshCw className="w-3.5 h-3.5" />
                            {importResult.updated_count} updated
                          </span>
                        )}
                        {importResult.skipped_count > 0 && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                            <X className="w-3.5 h-3.5" />
                            {importResult.skipped_count} skipped
                          </span>
                        )}
                        {importResult.error_count > 0 && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-error-100 text-error-800 rounded-full">
                            <AlertCircle className="w-3.5 h-3.5" />
                            {importResult.error_count} errors
                          </span>
                        )}
                      </div>
                      {/* Show errors if any */}
                      {importResult.errors && importResult.errors.length > 0 && (
                        <div className="mt-3 p-2 bg-error-100 rounded text-sm text-error-700">
                          <p className="font-medium mb-1">Error Details:</p>
                          <ul className="list-disc list-inside space-y-0.5">
                            {importResult.errors.slice(0, 5).map((err, i) => (
                              <li key={i}>{err}</li>
                            ))}
                            {importResult.errors.length > 5 && (
                              <li className="text-error-500">
                                ...and {importResult.errors.length - 5} more
                              </li>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Templates Card */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="w-5 h-5" />
                  Templates
                </CardTitle>
                <CardDescription>Download Excel templates for each module</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {MODULES.map(({ value, label }) => (
                  <Button
                    key={value}
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => downloadTemplate(value)}
                    disabled={isDownloading}
                  >
                    <FileSpreadsheet className="w-4 h-4 mr-2" />
                    {label}
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Quick Info */}
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-base">Column Requirements</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2 text-text-secondary">
                <p>
                  <strong>Enrollment:</strong> level_code, student_count
                </p>
                <p>
                  <strong>DHG:</strong> subject_code, fte_count
                </p>
                <p>
                  <strong>Revenue/Costs:</strong> account_code, annual_amount
                </p>
                <p>
                  <strong>CapEx:</strong> account_code, total_cost
                </p>
                <p className="text-text-muted mt-2">
                  All files should include a <code className="bg-subtle px-1">fiscal_year</code>{' '}
                  column.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Preview Results */}
        {previewData && <PreviewResultCard preview={previewData} />}

        {/* Import History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="w-5 h-5" />
              Import History
            </CardTitle>
            <CardDescription>Recent historical data imports</CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin text-text-muted" />
              </div>
            ) : importHistory && importHistory.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fiscal Year</TableHead>
                    <TableHead>Module</TableHead>
                    <TableHead>Records</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Imported At</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {importHistory.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-medium">{entry.fiscal_year}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{entry.module.toUpperCase()}</Badge>
                      </TableCell>
                      <TableCell>{entry.record_count}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            entry.status === 'success'
                              ? 'success'
                              : entry.status === 'partial'
                                ? 'warning'
                                : 'destructive'
                          }
                        >
                          {entry.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-text-muted">
                        {formatDate(entry.imported_at)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeleteTarget({ year: entry.fiscal_year, module: entry.module })
                            setShowDeleteDialog(true)
                          }}
                        >
                          <Trash2 className="w-4 h-4 text-error-600" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-text-muted">
                <FileX className="w-12 h-12 mx-auto mb-2 text-text-muted" />
                <p>No import history yet</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Historical Data</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete historical data for fiscal year{' '}
              <strong>{deleteTarget?.year}</strong>
              {deleteTarget?.module && (
                <>
                  {' '}
                  (module: <strong>{deleteTarget.module}</strong>)
                </>
              )}
              ? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm} disabled={isDeleting}>
              {isDeleting ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageContainer>
  )
}

/**
 * Preview result card component
 */
function PreviewResultCard({ preview }: { preview: ImportPreviewResponse }) {
  // Defensive: ensure arrays are defined (handles edge cases in mocked/test environments)
  const warnings = preview.warnings ?? []
  const errors = preview.errors ?? []
  const sampleData = preview.sample_data ?? []
  const hasWarnings = warnings.length > 0
  const hasErrors = errors.length > 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {preview.can_import ? (
            <CheckCircle2 className="w-5 h-5 text-success-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-error-600" />
          )}
          Import Preview
        </CardTitle>
        <CardDescription>
          {preview.can_import
            ? 'File is valid and ready to import'
            : 'File has errors that must be fixed before import'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-subtle rounded-lg p-3">
            <p className="text-sm text-text-muted">Fiscal Year</p>
            <p className="text-xl font-bold">{preview.fiscal_year}</p>
          </div>
          <div className="bg-subtle rounded-lg p-3">
            <p className="text-sm text-text-muted">Detected Module</p>
            <p className="text-xl font-bold">
              {preview.detected_module?.toUpperCase() || 'Unknown'}
            </p>
          </div>
          <div className="bg-success-50 rounded-lg p-3">
            <p className="text-sm text-success-600">Valid Rows</p>
            <p className="text-xl font-bold text-success-700">{preview.valid_rows}</p>
          </div>
          <div
            className={cn('rounded-lg p-3', preview.invalid_rows > 0 ? 'bg-error-50' : 'bg-subtle')}
          >
            <p
              className={cn(
                'text-sm',
                preview.invalid_rows > 0 ? 'text-error-600' : 'text-text-muted'
              )}
            >
              Invalid Rows
            </p>
            <p
              className={cn('text-xl font-bold', preview.invalid_rows > 0 ? 'text-error-700' : '')}
            >
              {preview.invalid_rows}
            </p>
          </div>
        </div>

        {/* Warnings */}
        {hasWarnings && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-warning-700">
              <AlertTriangle className="w-4 h-4" />
              <span className="font-medium">Warnings ({warnings.length})</span>
            </div>
            <ul className="text-sm text-warning-600 space-y-1 ml-6 list-disc">
              {warnings.slice(0, 5).map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
              {warnings.length > 5 && (
                <li className="text-text-muted">...and {warnings.length - 5} more</li>
              )}
            </ul>
          </div>
        )}

        {/* Errors */}
        {hasErrors && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-error-700">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium">Errors ({errors.length})</span>
            </div>
            <ul className="text-sm text-error-600 space-y-1 ml-6 list-disc">
              {errors.slice(0, 5).map((error, i) => (
                <li key={i}>{error}</li>
              ))}
              {errors.length > 5 && (
                <li className="text-text-muted">...and {errors.length - 5} more</li>
              )}
            </ul>
          </div>
        )}

        {/* Sample data */}
        {sampleData.length > 0 && (
          <div className="space-y-2">
            <p className="font-medium text-text-secondary">Sample Data (first 5 rows)</p>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {Object.keys(sampleData[0]).map((key) => (
                      <TableHead key={key}>{key}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sampleData.map((row, i) => (
                    <TableRow key={i}>
                      {Object.values(row).map((val, j) => (
                        <TableCell key={j}>{String(val ?? '')}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
