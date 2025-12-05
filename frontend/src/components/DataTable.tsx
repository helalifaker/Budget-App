import { AgGridReact, AgGridReactProps } from 'ag-grid-react'
import { useCallback, useMemo } from 'react'
import { themeQuartz } from 'ag-grid-community'

interface DataTableProps<TData = unknown> extends AgGridReactProps<TData> {
  loading?: boolean
  error?: Error | null
}

export function DataTable<TData = unknown>({
  loading = false,
  error = null,
  rowData,
  ...props
}: DataTableProps<TData>) {
  const defaultColDef = useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      ...props.defaultColDef,
    }),
    [props.defaultColDef]
  )

  const onGridReady = useCallback(
    (params: Parameters<NonNullable<AgGridReactProps['onGridReady']>>[0]) => {
      if (props.onGridReady) {
        props.onGridReady(params)
      }
    },
    [props]
  )

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-card border border-sand-200">
        <div className="text-center">
          <p className="text-error-600 font-medium">Error loading data</p>
          <p className="text-sm text-twilight-600 mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[600px] rounded-card border border-sand-200 overflow-hidden">
      {loading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
          <div className="text-twilight-600">Loading...</div>
        </div>
      )}
      <AgGridReact
        {...props}
        rowData={rowData}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        pagination={props.pagination !== undefined ? props.pagination : true}
        paginationPageSize={props.paginationPageSize || 50}
        domLayout="normal"
        theme={themeQuartz}
      />
    </div>
  )
}
