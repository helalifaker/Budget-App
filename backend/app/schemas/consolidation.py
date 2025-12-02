"""
Pydantic schemas for consolidation and financial statements endpoints.

Request and response models for budget consolidation and financial reporting.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.configuration import BudgetVersionStatus
from app.models.consolidation import (
    ConsolidationCategory,
    LineType,
    StatementFormat,
    StatementType,
)

# ==============================================================================
# Budget Consolidation Schemas
# ==============================================================================


class ConsolidationLineItemResponse(BaseModel):
    """Schema for individual consolidation line item."""

    id: uuid.UUID
    account_code: str = Field(..., description="PCG account code")
    account_name: str = Field(..., description="Account name")
    consolidation_category: ConsolidationCategory = Field(
        ..., description="Consolidation category"
    )
    is_revenue: bool = Field(..., description="True if revenue, False if expense")
    amount_sar: Decimal = Field(..., description="Amount in SAR")
    source_table: str = Field(..., description="Source planning table")
    source_count: int = Field(..., description="Number of source records aggregated")
    is_calculated: bool = Field(..., description="True if auto-calculated")
    notes: str | None = Field(None, description="Optional notes")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetConsolidationResponse(BaseModel):
    """Schema for consolidated budget with summary totals."""

    budget_version_id: uuid.UUID
    budget_version_name: str = Field(..., description="Budget version name")
    fiscal_year: int = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    status: BudgetVersionStatus = Field(..., description="Budget version status")

    # Line items grouped by type
    revenue_items: list[ConsolidationLineItemResponse] = Field(
        default_factory=list, description="Revenue line items"
    )
    personnel_items: list[ConsolidationLineItemResponse] = Field(
        default_factory=list, description="Personnel cost line items"
    )
    operating_items: list[ConsolidationLineItemResponse] = Field(
        default_factory=list, description="Operating cost line items"
    )
    capex_items: list[ConsolidationLineItemResponse] = Field(
        default_factory=list, description="CapEx line items"
    )

    # Summary totals
    total_revenue: Decimal = Field(..., description="Total revenue")
    total_personnel_costs: Decimal = Field(..., description="Total personnel costs")
    total_operating_costs: Decimal = Field(..., description="Total operating costs")
    total_capex: Decimal = Field(..., description="Total capital expenditure")
    operating_result: Decimal = Field(
        ..., description="Operating result (revenue - personnel - operating)"
    )
    net_result: Decimal = Field(
        ..., description="Net result (operating result - capex if expensed)"
    )

    model_config = ConfigDict(from_attributes=True)


class ConsolidationValidationResponse(BaseModel):
    """Schema for consolidation validation results."""

    is_complete: bool = Field(..., description="Whether all required modules are complete")
    missing_modules: list[str] = Field(
        default_factory=list, description="List of missing module names"
    )
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    module_counts: dict[str, int] = Field(
        default_factory=dict, description="Record counts per module"
    )


class ConsolidationRequest(BaseModel):
    """Schema for consolidation request."""

    recalculate: bool = Field(
        default=True, description="Whether to force recalculation"
    )


# ==============================================================================
# Financial Statement Schemas
# ==============================================================================


class FinancialStatementLineResponse(BaseModel):
    """Schema for financial statement line item."""

    id: uuid.UUID
    line_number: int = Field(..., description="Sequential line number for ordering")
    line_type: LineType = Field(..., description="Type of line")
    indent_level: int = Field(..., description="Indentation level (0-3)")
    line_code: str | None = Field(None, description="Account or section code")
    line_description: str = Field(..., description="Line description")
    amount_sar: Decimal | None = Field(None, description="Amount in SAR")
    is_bold: bool = Field(..., description="Display in bold")
    is_underlined: bool = Field(..., description="Display underlined")
    source_consolidation_category: str | None = Field(
        None, description="Source consolidation category"
    )

    model_config = ConfigDict(from_attributes=True)


class IncomeStatementResponse(BaseModel):
    """Schema for income statement."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    statement_type: StatementType = Field(..., description="Statement type")
    statement_format: StatementFormat = Field(..., description="Format standard")
    statement_name: str = Field(..., description="Statement name")
    fiscal_year: int = Field(..., description="Fiscal year")
    total_amount_sar: Decimal = Field(..., description="Net result")
    is_calculated: bool = Field(..., description="True if auto-calculated")
    notes: str | None = Field(None, description="Optional notes")
    lines: list[FinancialStatementLineResponse] = Field(
        default_factory=list, description="Statement lines"
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceSheetResponse(BaseModel):
    """Schema for balance sheet (assets + liabilities)."""

    budget_version_id: uuid.UUID
    fiscal_year: int = Field(..., description="Fiscal year")
    assets: IncomeStatementResponse = Field(..., description="Assets statement")
    liabilities: IncomeStatementResponse = Field(..., description="Liabilities statement")
    is_balanced: bool = Field(
        ..., description="True if total assets = total liabilities"
    )

    model_config = ConfigDict(from_attributes=True)


class FinancialPeriodTotals(BaseModel):
    """Schema for period-specific financial totals."""

    budget_version_id: uuid.UUID
    period: str = Field(..., description="Period identifier (p1, summer, p2, annual)")
    total_revenue: Decimal = Field(..., description="Total revenue for period")
    total_expenses: Decimal = Field(..., description="Total expenses for period")
    operating_result: Decimal = Field(..., description="Operating result for period")
    net_result: Decimal = Field(..., description="Net result for period")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Approval Workflow Schemas
# ==============================================================================


class SubmitForApprovalRequest(BaseModel):
    """Schema for submit for approval request."""

    notes: str | None = Field(None, description="Submission notes")


class ApprovebudgetRequest(BaseModel):
    """Schema for approve budget request."""

    notes: str | None = Field(None, description="Approval notes")


class WorkflowActionResponse(BaseModel):
    """Schema for workflow action response."""

    budget_version_id: uuid.UUID
    previous_status: BudgetVersionStatus = Field(..., description="Previous status")
    new_status: BudgetVersionStatus = Field(..., description="New status")
    action_by: uuid.UUID = Field(..., description="User who performed action")
    action_at: datetime = Field(..., description="When action was performed")
    message: str = Field(..., description="Success message")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Statement Generation Schemas
# ==============================================================================


class GenerateStatementRequest(BaseModel):
    """Schema for statement generation request."""

    format: str = Field(
        default="pcg",
        description="Statement format ('pcg' for French PCG, 'ifrs' for IFRS)",
    )
    regenerate: bool = Field(
        default=False, description="Force regeneration if statement exists"
    )


class StatementFormatOptions(BaseModel):
    """Schema for available statement format options."""

    formats: list[str] = Field(
        default=["pcg", "ifrs"], description="Available format options"
    )
    default_format: str = Field(default="pcg", description="Default format")


# ==============================================================================
# Variance Analysis Schemas
# ==============================================================================


class ConsolidationVarianceItem(BaseModel):
    """Schema for consolidation variance item (comparing two versions)."""

    account_code: str = Field(..., description="PCG account code")
    account_name: str = Field(..., description="Account name")
    category: ConsolidationCategory = Field(..., description="Consolidation category")
    is_revenue: bool = Field(..., description="True if revenue")

    baseline_amount: Decimal = Field(..., description="Baseline version amount")
    comparison_amount: Decimal = Field(..., description="Comparison version amount")
    variance_amount: Decimal = Field(..., description="Absolute variance")
    variance_percent: Decimal = Field(..., description="Percentage variance")

    model_config = ConfigDict(from_attributes=True)


class ConsolidationVarianceResponse(BaseModel):
    """Schema for consolidation variance analysis."""

    baseline_version_id: uuid.UUID
    baseline_version_name: str = Field(..., description="Baseline version name")
    comparison_version_id: uuid.UUID
    comparison_version_name: str = Field(..., description="Comparison version name")

    revenue_variances: list[ConsolidationVarianceItem] = Field(
        default_factory=list, description="Revenue variances"
    )
    expense_variances: list[ConsolidationVarianceItem] = Field(
        default_factory=list, description="Expense variances"
    )

    total_revenue_variance: Decimal = Field(..., description="Total revenue variance")
    total_expense_variance: Decimal = Field(..., description="Total expense variance")
    net_result_variance: Decimal = Field(..., description="Net result variance")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Summary Schemas
# ==============================================================================


class ConsolidationSummary(BaseModel):
    """Schema for high-level consolidation summary."""

    budget_version_id: uuid.UUID
    budget_version_name: str = Field(..., description="Budget version name")
    fiscal_year: int = Field(..., description="Fiscal year")
    status: BudgetVersionStatus = Field(..., description="Budget version status")

    total_revenue: Decimal = Field(..., description="Total revenue")
    total_expenses: Decimal = Field(..., description="Total expenses (personnel + operating)")
    total_capex: Decimal = Field(..., description="Total capital expenditure")
    operating_result: Decimal = Field(..., description="Operating result")
    net_result: Decimal = Field(..., description="Net result")

    revenue_count: int = Field(..., description="Number of revenue line items")
    expense_count: int = Field(..., description="Number of expense line items")
    capex_count: int = Field(..., description="Number of CapEx line items")

    last_consolidated_at: datetime | None = Field(
        None, description="When last consolidated"
    )

    model_config = ConfigDict(from_attributes=True)
