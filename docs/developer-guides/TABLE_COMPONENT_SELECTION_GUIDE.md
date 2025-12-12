# Table Component Selection Guide

This guide helps developers choose the right table component for their use case in the EFIR Budget Planning Application.

**Last Updated**: 2025-12-12

---

## Quick Decision Tree

```
Need a table component?
│
├─ Is it a simple, static display (< 20 rows)?
│   └─ YES → Use shadcn/ui Table
│
├─ Is it a data grid with sorting/filtering/pagination?
│   │
│   ├─ Is it read-only?
│   │   │
│   │   ├─ Is it on a critical initial load page?
│   │   │   └─ YES → Use DataTableLazy (lazy-loaded)
│   │   │
│   │   └─ NO → Use DataTable
│   │
│   └─ Is it editable?
│       │
│       ├─ Does it need budget version tracking & real-time sync?
│       │   └─ YES → Use EnhancedDataTable
│       │
│       └─ Does it need Excel-like experience (copy/paste, fill-down)?
│           └─ YES → Use ExcelDataTable
```

---

## Component Comparison

| Feature | shadcn Table | DataTable | DataTableLazy | EnhancedDataTable | ExcelDataTable |
|---------|--------------|-----------|---------------|-------------------|----------------|
| **Bundle Impact** | ~2KB | ~200KB | Lazy (~0KB initial) | ~200KB | ~200KB |
| **Sorting** | Manual | ✅ Built-in | ✅ | ✅ | ✅ |
| **Filtering** | Manual | ✅ Built-in | ✅ | ✅ | ✅ |
| **Pagination** | Manual | ✅ Built-in | ✅ | ✅ | ✅ |
| **Cell Editing** | ❌ | ❌ | ❌ | ✅ Auto-save | ✅ |
| **Excel Copy/Paste** | ❌ | ❌ | ❌ | ✅ | ✅ Native |
| **Undo/Redo** | ❌ | ❌ | ❌ | ✅ | ✅ (50 levels) |
| **Real-time Sync** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Conflict Resolution** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Cell Comments** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Cell History** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Status Bar** | ❌ | ❌ | ❌ | ❌ | ✅ Sum/Avg/Count |
| **Fill Down (Ctrl+D)** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Screen Reader** | Basic | ✅ Enhanced | ✅ | Basic | ✅ |
| **Keyboard Nav** | Basic | ✅ Full | ✅ | ✅ | ✅ Excel-style |

---

## Component Details

### 1. shadcn/ui Table (`@/components/ui/table`)

**Purpose**: Simple, static data display with maximum flexibility.

**Location**: `frontend/src/components/ui/table.tsx`

**When to Use**:
- Simple tables with < 20 rows
- Settings/configuration displays
- Summary cards with tabular data
- When you need full control over rendering

**When NOT to Use**:
- Large datasets (100+ rows)
- When sorting/filtering is needed
- Editable data grids

**Example**:
```tsx
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow
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
        <TableRow>
          <TableCell>Finance Director</TableCell>
          <TableCell>Budget approval, read all data</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}
```

---

### 2. DataTable (`@/components/DataTable`)

**Purpose**: Read-only AG Grid with accessibility features.

**Location**: `frontend/src/components/DataTable.tsx`

**When to Use**:
- Read-only data grids
- Need sorting, filtering, pagination
- Accessibility is a priority (screen readers)
- Displaying API data with loading/error states

**When NOT to Use**:
- Need cell editing
- Need Excel-like interactions
- Initial load performance is critical (use DataTableLazy)

**Key Features**:
- Built-in loading overlay
- Error state handling with retry button
- Network error detection
- ARIA labels and descriptions
- Screen reader announcements

**Example**:
```tsx
import { DataTable } from '@/components/DataTable'
import type { ColDef } from 'ag-grid-community'

function EmployeeList() {
  const { data, isLoading, error, refetch } = useEmployees()

  const columnDefs: ColDef[] = [
    { field: 'name', headerName: 'Name' },
    { field: 'department', headerName: 'Department' },
    { field: 'salary', headerName: 'Salary', valueFormatter: formatCurrency },
  ]

  return (
    <DataTable
      gridId="employee-list"
      gridLabel="Employee directory"
      gridDescription="List of all employees with their departments and salaries"
      rowData={data}
      columnDefs={columnDefs}
      loading={isLoading}
      error={error}
      onRetry={refetch}
    />
  )
}
```

---

### 3. DataTableLazy (`@/components/DataTableLazy`)

**Purpose**: Lazy-loaded DataTable for better initial bundle size.

**Location**: `frontend/src/components/DataTableLazy.tsx`

**When to Use**:
- DataTable functionality needed
- Table is below the fold or on a secondary tab
- Initial page load performance is critical
- Route-level code splitting

**When NOT to Use**:
- Table is immediately visible on page load
- User interaction with table is time-critical

**Bundle Impact**:
- Saves ~200KB from initial bundle
- AG Grid loaded on-demand when component mounts

**Example**:
```tsx
import { DataTableLazy } from '@/components/DataTableLazy'

function ReportsPage() {
  // Grid loads only when user navigates to this page
  return (
    <DataTableLazy
      rowData={reportData}
      columnDefs={columns}
      loading={isLoading}
    />
  )
}
```

---

### 4. EnhancedDataTable (`@/components/EnhancedDataTable`)

**Purpose**: Cell-level editing with real-time sync and version conflict resolution.

**Location**: `frontend/src/components/EnhancedDataTable.tsx`

**When to Use**:
- Collaborative budget planning screens
- Need to track budget versions
- Real-time updates from other users
- Cell-level comments and history
- Cell locking/unlocking

**When NOT to Use**:
- Simple data entry without version tracking
- Read-only displays
- When Excel-like fill-down is needed

**Key Features**:
- **Cell Writeback**: Auto-saves on edit with optimistic updates
- **Version Conflict**: Detects and highlights conflicting edits
- **Real-time Sync**: Shows changes from other users
- **User Presence**: Displays who's currently editing
- **Context Menu**: Comments, history, lock/unlock

**Example**:
```tsx
import { EnhancedDataTable } from '@/components/EnhancedDataTable'

function EnrollmentPlanning() {
  const { budgetVersionId } = useBudgetVersion()

  return (
    <EnhancedDataTable
      budgetVersionId={budgetVersionId}
      moduleCode="enrollment"
      enableWriteback={true}
      rowData={enrollmentData}
      columnDefs={columns}
      onCellSaved={(cell) => console.log('Saved:', cell)}
    />
  )
}
```

---

### 5. ExcelDataTable (`@/components/grid/ExcelDataTable`)

**Purpose**: True Excel-like experience with full keyboard and clipboard support.

**Location**: `frontend/src/components/grid/ExcelDataTable.tsx`

**When to Use**:
- Data entry screens where users expect Excel behavior
- Need copy/paste compatibility with Excel
- Fill-down operations (Ctrl+D)
- Status bar with Sum/Average/Count
- Heavy keyboard-based data entry

**When NOT to Use**:
- Need budget version tracking (use EnhancedDataTable)
- Need real-time collaborative editing
- Simple read-only displays

**Keyboard Shortcuts**:
| Shortcut | Action |
|----------|--------|
| Ctrl+C | Copy selection |
| Ctrl+V | Paste from clipboard |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+A | Select all rows |
| Ctrl+D | Fill down |
| Tab | Next cell |
| Shift+Tab | Previous cell |
| Enter | Next row / Finish edit |
| F2 | Edit current cell |
| Delete | Clear selected cells |
| Escape | Cancel edit / Deselect |

**Example**:
```tsx
import { ExcelDataTable } from '@/components/grid'

function SubjectHoursMatrix() {
  const handleCellsCleared = (cells) => {
    console.log('Cleared cells:', cells)
  }

  const handleCellsFilled = (cells) => {
    console.log('Filled cells:', cells)
  }

  return (
    <ExcelDataTable
      tableId="subject-hours"
      tableLabel="Subject Hours Configuration"
      rowData={subjectData}
      columnDefs={columns}
      showStatusBar={true}
      showShortcuts={true}
      height={500}
      onCellsCleared={handleCellsCleared}
      onCellsFilled={handleCellsFilled}
    />
  )
}
```

---

## Import Cheat Sheet

```tsx
// shadcn/ui Table (static displays)
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

// DataTable (read-only grid with accessibility)
import { DataTable } from '@/components/DataTable'

// DataTableLazy (code-split DataTable)
import { DataTableLazy } from '@/components/DataTableLazy'

// EnhancedDataTable (collaborative editing with versions)
import { EnhancedDataTable } from '@/components/EnhancedDataTable'

// ExcelDataTable (Excel-like experience)
import { ExcelDataTable } from '@/components/grid'
// or
import { ExcelDataTable } from '@/components/grid/ExcelDataTable'

// Cell renderers (for custom cell formatting)
import { AccountCodeRenderer, CurrencyRenderer, StatusBadgeRenderer } from '@/components/grid'
```

---

## Performance Considerations

### Bundle Size Impact

```
Total AG Grid package: ~200KB gzipped

Component                  Initial Bundle    On-Demand
──────────────────────────────────────────────────────
shadcn/ui Table            ~2KB              -
DataTable                  ~200KB            -
DataTableLazy              ~0KB              ~200KB
EnhancedDataTable          ~200KB            -
ExcelDataTable             ~200KB            -
```

### Recommendations

1. **Landing/Dashboard Pages**: Use `DataTableLazy` to defer AG Grid loading
2. **Data Entry Modules**: Use `ExcelDataTable` or `EnhancedDataTable` (already loaded)
3. **Settings Pages**: Use shadcn/ui `Table` for simple config displays
4. **Reports**: Use `DataTable` for read-only report grids

---

## Migration Guide

### From shadcn Table to DataTable

```tsx
// Before: shadcn Table
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {data.map((item) => (
      <TableRow key={item.id}>
        <TableCell>{item.name}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>

// After: DataTable
<DataTable
  rowData={data}
  columnDefs={[{ field: 'name', headerName: 'Name' }]}
/>
```

### From DataTable to EnhancedDataTable

```tsx
// Before: DataTable (read-only)
<DataTable
  rowData={data}
  columnDefs={columns}
  loading={isLoading}
/>

// After: EnhancedDataTable (with editing)
<EnhancedDataTable
  budgetVersionId={budgetVersionId}
  moduleCode="module-name"
  enableWriteback={true}
  rowData={data}
  columnDefs={columns}
  loading={isLoading}
/>
```

---

## Common Patterns

### Loading States

All AG Grid components support `loading` and `error` props:

```tsx
<DataTable
  loading={isLoading}
  error={error}
  onRetry={refetch}
  rowData={data}
  columnDefs={columns}
/>
```

### Custom Cell Renderers

```tsx
import { CurrencyRenderer, StatusBadgeRenderer } from '@/components/grid'

const columnDefs = [
  { field: 'amount', cellRenderer: CurrencyRenderer },
  { field: 'status', cellRenderer: StatusBadgeRenderer },
]
```

### Conditional Editing

```tsx
const columnDefs = [
  { field: 'name', editable: true },
  { field: 'total', editable: false }, // Calculated field
  {
    field: 'budget',
    editable: (params) => params.data.status !== 'locked',
  },
]
```

---

## Troubleshooting

### AG Grid not rendering

1. Ensure container has explicit height
2. Check if `rowData` is undefined vs empty array
3. Verify `columnDefs` has at least one column with `field`

### Copy/paste not working in ExcelDataTable

1. Ensure container has `tabIndex={0}` (handled internally)
2. User must focus the table before keyboard shortcuts work
3. Check browser clipboard permissions

### EnhancedDataTable conflicts

1. Check `budgetVersionId` is correct
2. Ensure backend is running for real-time sync
3. Check network tab for WebSocket connection

---

## Related Documentation

- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)
- [shadcn/ui Table](https://ui.shadcn.com/docs/components/table)
- [Frontend README](../../frontend/README.md)
- [Developer Guide](./DEVELOPER_GUIDE.md)
