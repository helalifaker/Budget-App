# Table Component Selection Guide

This guide helps developers choose the right table component for their use case in the EFIR Budget Planning Application.

**Last Updated**: 2025-12-15

---

## Quick Decision Tree

```
Need a table component?
│
├─ Is it a simple, static display (< 20 rows)?
│   └─ YES → Use shadcn/ui Table
│
└─ Is it a data grid (sorting/selection/virtualization)?
    │
    ├─ Is it read-only?
    │   └─ YES → Use TanStackDataTable
    │
    └─ Is it editable?
        │
        ├─ Does it need Excel-like keyboard + clipboard (Ctrl+C/V/D, stats)?
        │   └─ YES → Use ExcelEditableTable (or ExcelEditableTableLazy)
        │
        └─ Otherwise → Use EditableTable
```

---

## Component Comparison

| Feature | shadcn Table | TanStackDataTable | EditableTable | ExcelEditableTable | ExcelEditableTableLazy |
|---------|--------------|-------------------|---------------|--------------------|------------------------|
| **Primary Use** | Static display | Read-only grids | Inline editing | Editing + clipboard | Code-split Excel grid |
| **Sorting** | Manual | ✅ | ✅ | ✅ | ✅ |
| **Row Selection** | Manual | ✅ | ✅ (optional) | ✅ (required) | ✅ |
| **Virtualization** | ❌ | ✅ (auto) | ❌ | ❌ | ❌ |
| **Cell Editing** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Copy/Paste** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Fill Down (Ctrl+D)** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Selection Stats** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **A11y (labels/roles)** | Basic | ✅ | ✅ | ✅ | ✅ |

---

## Component Details

### 1. shadcn/ui Table (`@/components/ui/table`)

**Purpose**: Simple, static data display with maximum flexibility.

**Location**: `frontend/src/components/ui/table.tsx`

**When to Use**:
- Simple tables with < 20 rows
- Settings/configuration displays
- Summary cards with tabular data

**When NOT to Use**:
- Large datasets (100+ rows)
- When sorting/selection is needed
- Editable data grids

**Example**:
```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function UserRoles() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Role</TableHead>
          <TableHead>Description</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Admin</TableCell>
          <TableCell>Full system access</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}
```

---

### 2. TanStackDataTable (`@/components/grid/tanstack`)

**Purpose**: Read-only grid with EFIR styling, sorting, selection, and optional virtualization.

**Location**: `frontend/src/components/grid/tanstack/TanStackDataTable.tsx`

**When to Use**:
- Read-only grids (reports, overview tables)
- Need sorting and/or row selection
- Large datasets (virtualization auto-enables when rows > 100)

**When NOT to Use**:
- Need inline editing (use `EditableTable`)
- Need clipboard/Excel shortcuts (use `ExcelEditableTable`)

**Example**:
```tsx
import type { ColumnDef } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'

type Row = { id: string; name: string; department: string; salary: number }

const columns: ColumnDef<Row, unknown>[] = [
  { accessorKey: 'name', header: 'Name' },
  { accessorKey: 'department', header: 'Department' },
  { accessorKey: 'salary', header: 'Salary' },
]

export function EmployeeList({ data }: { data: Row[] }) {
  return (
    <TanStackDataTable
      rowData={data}
      columnDefs={columns}
      getRowId={(row) => row.id}
      height={600}
      enableRowSelection
    />
  )
}
```

---

### 3. EditableTable (`@/components/grid/tanstack`)

**Purpose**: Inline cell editing with keyboard navigation (click/F2/type-to-edit).

**Location**: `frontend/src/components/grid/tanstack/EditableTable.tsx`

**When to Use**:
- Editing screens that don’t need clipboard workflows
- Forms-like grids (single-row edits, small tables)

**When NOT to Use**:
- Heavy keyboard data-entry workflows with copy/paste/fill-down (use `ExcelEditableTable`)

**Example**:
```tsx
import type { ColumnDef } from '@tanstack/react-table'
import { EditableTable, type EditableColumnMeta } from '@/components/grid/tanstack'

type Row = { id: string; name: string; enrollment: number }

const columns: ColumnDef<Row, unknown>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    meta: { editable: false } satisfies EditableColumnMeta,
  },
  {
    accessorKey: 'enrollment',
    header: 'Enrollment',
    meta: { editable: true, editorType: 'number', min: 0 } satisfies EditableColumnMeta,
  },
]

export function EnrollmentEditor({ data }: { data: Row[] }) {
  return (
    <EditableTable
      rowData={data}
      columnDefs={columns}
      getRowId={(row) => row.id}
      enableRowSelection
      onCellValueChanged={({ data, field, newValue }) => {
        // Parent updates rowData (controlled)
        console.log('changed', data.id, field, newValue)
      }}
    />
  )
}
```

---

### 4. ExcelEditableTable (`@/components/grid/tanstack/ExcelEditableTable`)

**Purpose**: EditableTable + Excel-like keyboard shortcuts + clipboard support.

**Location**: `frontend/src/components/grid/tanstack/ExcelEditableTable.tsx`

**When to Use**:
- Data-entry screens where users expect Excel-like workflows
- Copy/paste from Excel and fill-down are core to productivity

**Notes**:
- Copy/paste behavior is row-based (matches the app’s prior behavior).

**Example**:
```tsx
import type { ColumnDef } from '@tanstack/react-table'
import { ExcelEditableTable } from '@/components/grid/tanstack/ExcelEditableTable'
import type { EditableColumnMeta } from '@/components/grid/tanstack'

type Row = { id: string; code: string; hours: number }

const columns: ColumnDef<Row, unknown>[] = [
  { accessorKey: 'code', header: 'Code', meta: { editable: false } satisfies EditableColumnMeta },
  { accessorKey: 'hours', header: 'Hours', meta: { editable: true, editorType: 'number', min: 0 } satisfies EditableColumnMeta },
]

export function HoursGrid({ data }: { data: Row[] }) {
  return (
    <ExcelEditableTable
      rowData={data}
      columnDefs={columns}
      getRowId={(row) => row.id}
      enableRowSelection
      showSelectionStats
      onCellValueChanged={({ data, field, newValue }) => {
        console.log('changed', data.id, field, newValue)
      }}
    />
  )
}
```

---

### 5. ExcelEditableTableLazy (`@/components/grid/tanstack`)

**Purpose**: Lazy-loaded `ExcelEditableTable` for routes/tabs where initial load performance matters.

**Location**: `frontend/src/components/grid/tanstack/ExcelEditableTableLazy.tsx`

**Example**:
```tsx
import { ExcelEditableTableLazy } from '@/components/grid/tanstack'

export function HeavyTab({ data, columns }: { data: unknown[]; columns: unknown[] }) {
  return (
    <ExcelEditableTableLazy
      rowData={data}
      columnDefs={columns as any}
      getRowId={(row: any) => row.id}
      enableRowSelection
    />
  )
}
```

---

## Import Cheat Sheet

```tsx
// shadcn/ui Table (static displays)
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

// TanStack grid components
import { TanStackDataTable, EditableTable, ExcelEditableTableLazy } from '@/components/grid/tanstack'
import { ExcelEditableTable } from '@/components/grid/tanstack/ExcelEditableTable'
```

---

## Common Patterns

### Loading & Error States

```tsx
<TanStackDataTable
  rowData={data}
  columnDefs={columns}
  getRowId={(row) => row.id}
  loading={isLoading}
  error={error}
  onRetry={refetch}
/>
```

### Custom Cell Rendering

```tsx
const columns = [
  {
    accessorKey: 'amount',
    header: 'Amount',
    cell: ({ getValue }) => new Intl.NumberFormat('en-SA').format(Number(getValue() ?? 0)),
  },
]
```

### Pinned Columns

```tsx
import type { EditableColumnMeta } from '@/components/grid/tanstack'

const columns = [
  {
    accessorKey: 'name',
    header: 'Name',
    size: 220,
    meta: { pinned: 'left' as const, editable: false } satisfies EditableColumnMeta,
  },
]
```

---

## Troubleshooting

### Table not rendering

1. Ensure the container has a height (e.g. pass `height={600}`).
2. Ensure `getRowId` returns a stable, unique ID.
3. Ensure `columnDefs` has at least one column with `accessorKey` / `accessorFn`.

### Copy/paste not working in ExcelEditableTable

1. The table container must be focused (click inside the grid first).
2. Check browser clipboard permissions (especially in Safari).

---

## Related Documentation

- [TanStack Table Documentation](https://tanstack.com/table/latest)
- [TanStack Virtual Documentation](https://tanstack.com/virtual/latest)
- [shadcn/ui Table](https://ui.shadcn.com/docs/components/table)
- [Frontend README](../../frontend/README.md)
- [Developer Guide](./DEVELOPER_GUIDE.md)
