/**
 * E2E Test Helper: AG Grid Interactions
 * Reusable helpers for interacting with AG Grid in E2E tests
 */

import { Page, Locator } from '@playwright/test'

/**
 * Get AG Grid row by index
 */
export async function getGridRow(page: Page, rowIndex: number): Promise<Locator> {
  return page.locator(`.ag-row[row-index="${rowIndex}"]`)
}

/**
 * Get AG Grid cell by row and column index
 */
export async function getGridCell(
  page: Page,
  rowIndex: number,
  colIndex: number
): Promise<Locator> {
  return page.locator(
    `.ag-row[row-index="${rowIndex}"] .ag-cell[col-id="${colIndex}"], .ag-row[row-index="${rowIndex}"] [col-id="${colIndex}"]`
  )
}

/**
 * Get AG Grid cell by row index and column field name
 */
export async function getGridCellByField(
  page: Page,
  rowIndex: number,
  field: string
): Promise<Locator> {
  return page.locator(`.ag-row[row-index="${rowIndex}"] .ag-cell[col-id="${field}"]`)
}

/**
 * Click AG Grid cell to start editing
 */
export async function editGridCell(
  page: Page,
  rowIndex: number,
  field: string,
  value: string
): Promise<void> {
  const cell = await getGridCellByField(page, rowIndex, field)
  await cell.dblclick() // Double click to edit

  // Wait for editor to appear
  await page.waitForTimeout(300)

  // Find input in cell
  const input = cell.locator('input')
  await input.fill(value)
  await input.press('Tab') // Complete editing

  await page.waitForTimeout(500) // Wait for save
}

/**
 * Get total row count in AG Grid
 */
export async function getGridRowCount(page: Page): Promise<number> {
  const rows = page.locator('.ag-row')
  return await rows.count()
}

/**
 * Sort AG Grid column
 */
export async function sortGridColumn(page: Page, columnName: string): Promise<void> {
  const header = page.locator(`.ag-header-cell:has-text("${columnName}")`)
  await header.click()
  await page.waitForTimeout(500)
}

/**
 * Filter AG Grid column
 */
export async function filterGridColumn(
  page: Page,
  columnName: string,
  filterValue: string
): Promise<void> {
  // Click filter menu icon
  const header = page.locator(`.ag-header-cell:has-text("${columnName}")`)
  const filterIcon = header.locator('.ag-icon-filter')
  await filterIcon.click()

  // Wait for filter menu
  await page.waitForTimeout(500)

  // Enter filter value
  const filterInput = page.locator('.ag-filter-body input').first()
  await filterInput.fill(filterValue)
  await page.waitForTimeout(1000) // Wait for filter to apply
}

/**
 * Clear all AG Grid filters
 */
export async function clearGridFilters(page: Page): Promise<void> {
  const clearButton = page.locator(
    'button:has-text("Clear Filters"), [data-testid="clear-filters"]'
  )
  if (await clearButton.isVisible()) {
    await clearButton.click()
    await page.waitForTimeout(500)
  }
}

/**
 * Export AG Grid to CSV
 */
export async function exportGrid(page: Page, format: 'csv' | 'excel' = 'csv'): Promise<void> {
  const exportButton = page.locator(`button:has-text("Export"), [data-testid="export-button"]`)
  await exportButton.click()

  if (format === 'excel') {
    const excelOption = page.locator('button:has-text("Excel"), [data-testid="export-excel"]')
    if (await excelOption.isVisible()) {
      await excelOption.click()
    }
  }
}

/**
 * Wait for AG Grid to finish loading
 */
export async function waitForGridReady(page: Page): Promise<void> {
  // Wait for grid to render
  await page.waitForSelector('.ag-root-wrapper', { timeout: 10000 })

  // Wait for loading overlay to disappear
  await page.waitForSelector('.ag-overlay-loading-center', {
    state: 'hidden',
    timeout: 10000,
  })

  // Wait for rows to render
  await page.waitForSelector('.ag-row', { timeout: 10000 })
}

/**
 * Select AG Grid row by clicking checkbox
 */
export async function selectGridRow(page: Page, rowIndex: number): Promise<void> {
  const checkbox = page.locator(`.ag-row[row-index="${rowIndex}"] .ag-selection-checkbox input`)
  await checkbox.check()
}

/**
 * Get selected row count
 */
export async function getSelectedRowCount(page: Page): Promise<number> {
  const selectedRows = page.locator('.ag-row.ag-row-selected')
  return await selectedRows.count()
}
