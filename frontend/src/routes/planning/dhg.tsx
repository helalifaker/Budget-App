import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { SummaryCard } from '@/components/SummaryCard'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  useSubjectHours,
  useTeacherFTE,
  useTRMDGaps,
  useHSAPlanning,
  useCalculateFTE,
} from '@/hooks/api/useDHG'
import { Users, Clock, AlertTriangle, TrendingUp, Calculator, Save } from 'lucide-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'

export const Route = createFileRoute('/planning/dhg')({
  component: DHGPage,
})

function DHGPage() {
  const [selectedVersion, setSelectedVersion] = useState<string>()
  const [activeTab, setActiveTab] = useState<'hours' | 'fte' | 'trmd' | 'hsa'>('hours')

  const { data: subjectHours, isLoading: loadingHours } = useSubjectHours(selectedVersion!)
  const { data: teacherFTE, isLoading: loadingFTE } = useTeacherFTE(selectedVersion!)
  const { data: trmdGaps, isLoading: loadingTRMD } = useTRMDGaps(selectedVersion!)
  const { data: hsaPlanning, isLoading: loadingHSA } = useHSAPlanning(selectedVersion!)
  const calculateFTE = useCalculateFTE()

  const handleCalculateFTE = () => {
    if (selectedVersion) {
      calculateFTE.mutate(selectedVersion)
    }
  }

  // Summary metrics
  const totalFTE = teacherFTE?.items.reduce((sum, item) => sum + item.adjusted_fte, 0) || 0
  const totalHSAHours = teacherFTE?.items.reduce((sum, item) => sum + item.hsa_hours, 0) || 0
  const totalDeficit = trmdGaps?.items.reduce((sum, item) => sum + item.deficit_hours, 0) || 0
  const hsaAssignments = hsaPlanning?.items.length || 0

  return (
    <MainLayout>
      <PageContainer
        title="DHG Workforce Planning"
        description="Teacher hours and FTE planning using DHG methodology"
      >
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <BudgetVersionSelector value={selectedVersion} onChange={setSelectedVersion} />
            <Button
              onClick={handleCalculateFTE}
              disabled={!selectedVersion || calculateFTE.isPending}
            >
              <Calculator className="w-4 h-4 mr-2" />
              Recalculate FTE
            </Button>
          </div>

          {selectedVersion && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <SummaryCard
                  title="Total FTE Required"
                  value={totalFTE.toFixed(2)}
                  subtitle="Full-time equivalents"
                  icon={<Users className="w-5 h-5" />}
                />
                <SummaryCard
                  title="HSA Hours"
                  value={totalHSAHours.toFixed(1)}
                  subtitle="Overtime hours"
                  icon={<Clock className="w-5 h-5" />}
                />
                <SummaryCard
                  title="Deficit Hours"
                  value={totalDeficit.toFixed(1)}
                  subtitle="Hours to fill"
                  icon={<AlertTriangle className="w-5 h-5" />}
                  valueClassName={totalDeficit > 0 ? 'text-red-600' : 'text-green-600'}
                />
                <SummaryCard
                  title="HSA Assignments"
                  value={hsaAssignments}
                  subtitle="Teachers with overtime"
                  icon={<TrendingUp className="w-5 h-5" />}
                />
              </div>

              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="hours">Subject Hours</TabsTrigger>
                  <TabsTrigger value="fte">Teacher FTE</TabsTrigger>
                  <TabsTrigger value="trmd">TRMD Gap Analysis</TabsTrigger>
                  <TabsTrigger value="hsa">HSA Planning</TabsTrigger>
                </TabsList>

                <TabsContent value="hours" className="mt-6">
                  <SubjectHoursTab data={subjectHours?.items || []} isLoading={loadingHours} />
                </TabsContent>

                <TabsContent value="fte" className="mt-6">
                  <TeacherFTETab data={teacherFTE?.items || []} isLoading={loadingFTE} />
                </TabsContent>

                <TabsContent value="trmd" className="mt-6">
                  <TRMDTab data={trmdGaps?.items || []} isLoading={loadingTRMD} />
                </TabsContent>

                <TabsContent value="hsa" className="mt-6">
                  <HSATab data={hsaPlanning?.items || []} isLoading={loadingHSA} />
                </TabsContent>
              </Tabs>
            </>
          )}

          {!selectedVersion && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>Select a budget version to view DHG workforce planning</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}

interface SubjectHoursItem {
  id?: string
  budget_version_id?: string
  level_id?: string
  subject_id?: string
  created_at?: string
  updated_at?: string
  subject_name?: string
  level_name?: string
  hours_per_week: number
  is_split: boolean
  number_of_classes?: number
}

function SubjectHoursTab({ data, isLoading }: { data: SubjectHoursItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    { headerName: 'Subject', field: 'subject_name', pinned: 'left', width: 200 },
    { headerName: 'Level', field: 'level_name', width: 120 },
    {
      headerName: 'Hours/Week',
      field: 'hours_per_week',
      width: 120,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Split Class',
      field: 'is_split',
      width: 120,
      cellRenderer: (params: { value: boolean; setValue: (value: boolean) => void }) => (
        <input
          type="checkbox"
          checked={params.value}
          onChange={(e) => {
            params.setValue(e.target.checked)
          }}
          className="w-4 h-4"
        />
      ),
    },
    {
      headerName: 'Total Hours',
      valueGetter: (params: { data: SubjectHoursItem }) => {
        const hours = params.data.hours_per_week
        const classes = params.data.number_of_classes || 1
        return hours * classes
      },
      width: 130,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Subject Hours Matrix</CardTitle>
        <p className="text-sm text-gray-600">
          Edit hours per week for each subject at each level. Changes auto-save.
        </p>
      </CardHeader>
      <CardContent>
        <div className="ag-theme-quartz" style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
          />
        </div>
      </CardContent>
    </Card>
  )
}

interface TeacherFTEItem {
  id?: string
  created_at?: string
  updated_at?: string
  budget_version_id?: string
  level_id?: string | null
  cycle_id?: string
  subject_id?: string
  cycle_name?: string
  subject_name?: string
  total_hours: number
  standard_fte: number
  adjusted_fte: number
  hsa_hours: number
}

function TeacherFTETab({ data, isLoading }: { data: TeacherFTEItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    { headerName: 'Cycle', field: 'cycle_name', width: 150 },
    { headerName: 'Subject', field: 'subject_name', width: 200 },
    {
      headerName: 'Total Hours',
      field: 'total_hours',
      width: 130,
      valueFormatter: (params) => params.value.toFixed(1),
    },
    {
      headerName: 'Standard FTE',
      field: 'standard_fte',
      width: 140,
      valueFormatter: (params) => params.value.toFixed(2),
    },
    {
      headerName: 'Adjusted FTE',
      field: 'adjusted_fte',
      width: 140,
      valueFormatter: (params) => params.value.toFixed(2),
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'HSA Hours',
      field: 'hsa_hours',
      width: 130,
      valueFormatter: (params) => params.value.toFixed(1),
      cellStyle: (params) => (params.value > 0 ? { color: '#F59E0B' } : undefined),
    },
  ]

  const totalStandardFTE = data.reduce((sum, item) => sum + item.standard_fte, 0)
  const totalAdjustedFTE = data.reduce((sum, item) => sum + item.adjusted_fte, 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Teacher FTE Requirements</CardTitle>
        <p className="text-sm text-gray-600">
          Calculated teacher requirements based on subject hours. Primary: 24h/week, Secondary:
          18h/week.
        </p>
        <div className="flex gap-4 mt-2">
          <Badge variant="info">Standard FTE: {totalStandardFTE.toFixed(2)}</Badge>
          <Badge variant="success">Adjusted FTE: {totalAdjustedFTE.toFixed(2)}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="ag-theme-quartz" style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
          />
        </div>
      </CardContent>
    </Card>
  )
}

interface TRMDItem {
  id?: string
  budget_version_id?: string
  subject_id?: string
  created_at?: string
  updated_at?: string
  subject_name?: string
  hours_needed: number
  aefe_positions: number
  local_positions: number
  deficit_hours: number
  hsa_required: number
}

function TRMDTab({ data, isLoading }: { data: TRMDItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    { headerName: 'Subject', field: 'subject_name', pinned: 'left', width: 200 },
    {
      headerName: 'Hours Needed',
      field: 'hours_needed',
      width: 140,
      valueFormatter: (params) => params.value.toFixed(1),
    },
    {
      headerName: 'AEFE Positions',
      field: 'aefe_positions',
      width: 150,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Local Positions',
      field: 'local_positions',
      width: 150,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Deficit/Surplus',
      field: 'deficit_hours',
      width: 150,
      valueFormatter: (params) => params.value.toFixed(1),
      cellStyle: (params) => ({
        color: params.value > 0 ? '#EF4444' : '#10B981',
        fontWeight: 'bold',
      }),
      cellRenderer: (params: { value: number }) => {
        const value = params.value
        const icon = value > 0 ? '▼' : '▲'
        return `${icon} ${Math.abs(value).toFixed(1)}h`
      },
    },
    {
      headerName: 'HSA Required',
      field: 'hsa_required',
      width: 140,
      valueFormatter: (params) => params.value.toFixed(1),
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>TRMD Gap Analysis</CardTitle>
        <p className="text-sm text-gray-600">
          Compare needs vs available positions. Red = deficit (need to recruit or assign HSA), Green
          = surplus.
        </p>
      </CardHeader>
      <CardContent>
        <div className="ag-theme-quartz" style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
          />
        </div>
      </CardContent>
    </Card>
  )
}

interface HSAItem {
  teacher_name?: string
  subject_name?: string
  hsa_hours: number
  notes?: string | null
}

function HSATab({ data, isLoading }: { data: HSAItem[]; isLoading: boolean }) {
  const columnDefs: ColDef[] = [
    { headerName: 'Teacher', field: 'teacher_name', width: 200 },
    { headerName: 'Subject', field: 'subject_name', width: 200 },
    {
      headerName: 'HSA Hours',
      field: 'hsa_hours',
      width: 140,
      editable: true,
      cellDataType: 'number',
      cellEditor: 'agNumberCellEditor',
      cellEditorParams: {
        min: 0,
        max: 4,
      },
    },
    {
      headerName: 'Status',
      valueGetter: (params: { data: HSAItem }) => {
        const hours = params.data.hsa_hours
        if (hours > 4) return 'Exceeds Max'
        if (hours >= 2) return 'Within Limit'
        return 'Below Target'
      },
      width: 140,
      cellRenderer: (params: { value: string }) => {
        const status = params.value
        const variant =
          status === 'Exceeds Max'
            ? 'destructive'
            : status === 'Within Limit'
              ? 'success'
              : 'warning'
        return <Badge variant={variant}>{status}</Badge>
      },
    },
    { headerName: 'Notes', field: 'notes', width: 300, editable: true },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>HSA Overtime Planning</CardTitle>
        <p className="text-sm text-gray-600">
          Assign overtime hours to teachers. Maximum: 2-4 hours per teacher per week.
        </p>
        <div className="mt-2">
          <Button size="sm">
            <Save className="w-4 h-4 mr-2" />
            Add HSA Assignment
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="ag-theme-quartz" style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            onCellValueChanged={(event) => {
              const hours = event.data.hsa_hours
              if (hours > 4) {
                alert('Warning: HSA hours exceed maximum of 4 hours per teacher')
              }
            }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
