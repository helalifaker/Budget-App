"""
Consolidation API endpoints.

Provides REST API for:
- Budget consolidation operations
- Financial statements generation
- Approval workflow management
- Period totals and variance analysis
"""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheInvalidator
from app.database import get_db
from app.dependencies.auth import ManagerDep, UserDep
from app.schemas.consolidation import (
    ApprovebudgetRequest,
    BalanceSheetResponse,
    BudgetConsolidationResponse,
    ConsolidationLineItemResponse,
    ConsolidationRequest,
    ConsolidationSummary,
    ConsolidationValidationResponse,
    FinancialPeriodTotals,
    IncomeStatementResponse,
    SubmitForApprovalRequest,
    WorkflowActionResponse,
)
from app.services.consolidation_service import ConsolidationService
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.services.financial_statements_service import FinancialStatementsService

router = APIRouter(prefix="/api/v1/consolidation", tags=["consolidation"])


def get_consolidation_service(
    db: AsyncSession = Depends(get_db),
) -> ConsolidationService:
    """
    Dependency to get consolidation service instance.

    Args:
        db: Database session

    Returns:
        ConsolidationService instance
    """
    return ConsolidationService(db)


def get_financial_statements_service(
    db: AsyncSession = Depends(get_db),
) -> FinancialStatementsService:
    """
    Dependency to get financial statements service instance.

    Args:
        db: Database session

    Returns:
        FinancialStatementsService instance
    """
    return FinancialStatementsService(db)


# ==============================================================================
# Budget Consolidation Endpoints
# ==============================================================================


@router.get("/{version_id}", response_model=BudgetConsolidationResponse)
async def get_consolidated_budget(
    version_id: uuid.UUID,
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    user: UserDep = ...,
):
    """
    Get consolidated budget for a budget version.

    Returns all consolidation line items grouped by type with summary totals.

    Args:
        version_id: Budget version UUID
        consolidation_service: Consolidation service
        user: Current authenticated user

    Returns:
        Consolidated budget with line items and totals

    Raises:
        404: Budget version not found
    """
    try:
        # Get consolidation entries
        consolidations = await consolidation_service.get_consolidation(version_id)

        # Get budget version info
        budget_version = await consolidation_service.budget_version_service.get_by_id(
            version_id
        )

        if not budget_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget version {version_id} not found",
            )

        # Group items by type
        revenue_items = []
        personnel_items = []
        operating_items = []
        capex_items = []

        total_revenue = Decimal("0.00")
        total_personnel = Decimal("0.00")
        total_operating = Decimal("0.00")
        total_capex = Decimal("0.00")

        for item in consolidations:
            item_response = ConsolidationLineItemResponse.model_validate(item)

            if item.is_revenue:
                revenue_items.append(item_response)
                total_revenue += item.amount_sar
            elif item.source_table == "personnel_cost_plans":
                personnel_items.append(item_response)
                total_personnel += item.amount_sar
            elif item.source_table == "operating_cost_plans":
                operating_items.append(item_response)
                total_operating += item.amount_sar
            elif item.source_table == "capex_plans":
                capex_items.append(item_response)
                total_capex += item.amount_sar

        # Calculate totals
        operating_result = total_revenue - total_personnel - total_operating
        net_result = operating_result  # Simplified - CapEx not expensed directly

        return BudgetConsolidationResponse(
            budget_version_id=version_id,
            budget_version_name=budget_version.name,
            fiscal_year=budget_version.fiscal_year,
            academic_year=budget_version.academic_year,
            status=budget_version.status,
            revenue_items=revenue_items,
            personnel_items=personnel_items,
            operating_items=operating_items,
            capex_items=capex_items,
            total_revenue=total_revenue,
            total_personnel_costs=total_personnel,
            total_operating_costs=total_operating,
            total_capex=total_capex,
            operating_result=operating_result,
            net_result=net_result,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consolidated budget: {e!s}",
        )


@router.post("/{version_id}/consolidate", response_model=BudgetConsolidationResponse)
async def consolidate_budget(
    version_id: uuid.UUID,
    request: ConsolidationRequest = ConsolidationRequest(),
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    user: UserDep = ...,
):
    """
    Run consolidation calculation for a budget version.

    Aggregates all planning modules (revenue, costs, CapEx) into consolidated
    budget line items.

    Args:
        version_id: Budget version UUID
        request: Consolidation request options
        consolidation_service: Consolidation service
        user: Current authenticated user

    Returns:
        Newly consolidated budget with line items and totals

    Raises:
        404: Budget version not found
        400: Validation error
    """
    try:
        # Run consolidation
        await consolidation_service.consolidate_budget(version_id, user_id=user.id)

        # Invalidate consolidation and dependent caches
        await CacheInvalidator.invalidate(str(version_id), "budget_consolidation")

        # Return consolidated budget
        return await get_consolidated_budget(version_id, consolidation_service, user)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to consolidate budget: {e!s}",
        )


@router.post("/{version_id}/submit", response_model=WorkflowActionResponse)
async def submit_for_approval(
    version_id: uuid.UUID,
    request: SubmitForApprovalRequest = SubmitForApprovalRequest(notes="Submitted for approval"),
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    user: UserDep = ...,
):
    """
    Submit budget version for approval.

    Changes status from WORKING to SUBMITTED. Validates completeness before submission.

    Args:
        version_id: Budget version UUID
        request: Submission request with optional notes
        consolidation_service: Consolidation service
        user: Current authenticated user

    Returns:
        Workflow action response with status change details

    Raises:
        404: Budget version not found
        422: Business rule violation (wrong status, incomplete budget)
    """
    try:
        # Get current status
        budget_version = await consolidation_service.budget_version_service.get_by_id(
            version_id
        )

        if not budget_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget version {version_id} not found",
            )

        previous_status = budget_version.status

        # Submit for approval
        updated = await consolidation_service.submit_for_approval(
            version_id, user_id=user.id
        )

        return WorkflowActionResponse(
            budget_version_id=version_id,
            previous_status=previous_status,
            new_status=updated.status,
            action_by=user.id,
            action_at=updated.submitted_at or datetime.utcnow(),
            message=f"Budget '{updated.name}' successfully submitted for approval",
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "rule": e.details.get("rule"), "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit budget: {e!s}",
        )


@router.post("/{version_id}/approve", response_model=WorkflowActionResponse)
async def approve_budget(
    version_id: uuid.UUID,
    request: ApprovebudgetRequest = ApprovebudgetRequest(notes="Approved"),
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    manager: ManagerDep = ...,  # Requires manager role
):
    """
    Approve budget version.

    Changes status from SUBMITTED to APPROVED. Only managers can approve budgets.
    Previous approved versions are marked as SUPERSEDED.

    Args:
        version_id: Budget version UUID
        request: Approval request with optional notes
        consolidation_service: Consolidation service
        manager: Current authenticated manager user

    Returns:
        Workflow action response with status change details

    Raises:
        404: Budget version not found
        422: Business rule violation (wrong status)
        403: Insufficient permissions (not a manager)
    """
    try:
        # Get current status
        budget_version = await consolidation_service.budget_version_service.get_by_id(
            version_id
        )

        if not budget_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget version {version_id} not found",
            )

        previous_status = budget_version.status

        # Approve budget
        updated = await consolidation_service.approve_budget(
            version_id, user_id=manager.id
        )

        return WorkflowActionResponse(
            budget_version_id=version_id,
            previous_status=previous_status,
            new_status=updated.status,
            action_by=manager.id,
            action_at=updated.approved_at or datetime.utcnow(),
            message=f"Budget '{updated.name}' successfully approved",
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "rule": e.details.get("rule"), "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve budget: {e!s}",
        )


@router.get("/{version_id}/validation", response_model=ConsolidationValidationResponse)
async def validate_budget_completeness(
    version_id: uuid.UUID,
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    user: UserDep = ...,
):
    """
    Validate budget completeness.

    Checks that all required modules have data before submission/consolidation.

    Args:
        version_id: Budget version UUID
        consolidation_service: Consolidation service
        user: Current authenticated user

    Returns:
        Validation results with missing modules and warnings

    Raises:
        404: Budget version not found
    """
    try:
        validation = await consolidation_service.validate_completeness(version_id)
        return ConsolidationValidationResponse(**validation)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate budget: {e!s}",
        )


@router.get("/{version_id}/summary", response_model=ConsolidationSummary)
async def get_consolidation_summary(
    version_id: uuid.UUID,
    consolidation_service: ConsolidationService = Depends(get_consolidation_service),
    user: UserDep = ...,
):
    """
    Get high-level consolidation summary.

    Returns summary totals and counts without detailed line items.

    Args:
        version_id: Budget version UUID
        consolidation_service: Consolidation service
        user: Current authenticated user

    Returns:
        Consolidation summary with totals and counts

    Raises:
        404: Budget version not found
    """
    try:
        # Get consolidated budget
        full_response = await get_consolidated_budget(
            version_id, consolidation_service, user
        )

        # Get budget version
        budget_version = await consolidation_service.budget_version_service.get_by_id(
            version_id
        )

        if not budget_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget version {version_id} not found",
            )

        return ConsolidationSummary(
            budget_version_id=version_id,
            budget_version_name=budget_version.name,
            fiscal_year=budget_version.fiscal_year,
            status=budget_version.status,
            total_revenue=full_response.total_revenue,
            total_expenses=full_response.total_personnel_costs
            + full_response.total_operating_costs,
            total_capex=full_response.total_capex,
            operating_result=full_response.operating_result,
            net_result=full_response.net_result,
            revenue_count=len(full_response.revenue_items),
            expense_count=len(full_response.personnel_items)
            + len(full_response.operating_items),
            capex_count=len(full_response.capex_items),
            last_consolidated_at=budget_version.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consolidation summary: {e!s}",
        )


# ==============================================================================
# Financial Statements Endpoints
# ==============================================================================


@router.get("/statements/income/{version_id}", response_model=IncomeStatementResponse)
async def get_income_statement(
    version_id: uuid.UUID,
    format: str = Query(
        default="pcg",
        description="Statement format: 'pcg' for French PCG, 'ifrs' for IFRS",
    ),
    statements_service: FinancialStatementsService = Depends(
        get_financial_statements_service
    ),
    user: UserDep = ...,
):
    """
    Get income statement for a budget version.

    Generates or retrieves income statement in French PCG or IFRS format.

    Args:
        version_id: Budget version UUID
        format: Statement format ('pcg' or 'ifrs')
        statements_service: Financial statements service
        user: Current authenticated user

    Returns:
        Income statement with all line items

    Raises:
        404: Budget version not found
        400: Invalid format
    """
    try:
        statement = await statements_service.get_income_statement(version_id, format)
        return IncomeStatementResponse.model_validate(statement)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get income statement: {e!s}",
        )


@router.get("/statements/balance/{version_id}", response_model=BalanceSheetResponse)
async def get_balance_sheet(
    version_id: uuid.UUID,
    statements_service: FinancialStatementsService = Depends(
        get_financial_statements_service
    ),
    user: UserDep = ...,
):
    """
    Get balance sheet for a budget version.

    Generates or retrieves balance sheet with assets and liabilities.

    Args:
        version_id: Budget version UUID
        statements_service: Financial statements service
        user: Current authenticated user

    Returns:
        Balance sheet with assets and liabilities statements

    Raises:
        404: Budget version not found
    """
    try:
        balance_sheet = await statements_service.get_balance_sheet(version_id)

        # Check if balanced
        assets_total = balance_sheet["assets"].total_amount_sar
        liabilities_total = balance_sheet["liabilities"].total_amount_sar
        is_balanced = assets_total == liabilities_total

        # Get budget version for fiscal year
        budget_version = await statements_service.budget_version_service.get_by_id(
            version_id
        )

        if not budget_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget version {version_id} not found",
            )

        return BalanceSheetResponse(
            budget_version_id=version_id,
            fiscal_year=budget_version.fiscal_year,
            assets=IncomeStatementResponse.model_validate(balance_sheet["assets"]),
            liabilities=IncomeStatementResponse.model_validate(
                balance_sheet["liabilities"]
            ),
            is_balanced=is_balanced,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance sheet: {e!s}",
        )


@router.get("/statements/{version_id}/periods", response_model=list[FinancialPeriodTotals])
async def get_period_totals(
    version_id: uuid.UUID,
    statements_service: FinancialStatementsService = Depends(
        get_financial_statements_service
    ),
    user: UserDep = ...,
):
    """
    Get financial totals for all periods.

    Returns totals for Period 1 (Jan-Jun), Summer (Jul-Aug), Period 2 (Sep-Dec),
    and Annual.

    Args:
        version_id: Budget version UUID
        statements_service: Financial statements service
        user: Current authenticated user

    Returns:
        List of period totals

    Raises:
        404: Budget version not found
    """
    try:
        periods = ["p1", "summer", "p2", "annual"]
        period_totals = []

        for period in periods:
            totals = await statements_service.get_period_totals(version_id, period)
            period_totals.append(
                FinancialPeriodTotals(
                    budget_version_id=version_id,
                    period=period,
                    total_revenue=totals["total_revenue"],
                    total_expenses=totals["total_expenses"],
                    operating_result=totals["operating_result"],
                    net_result=totals["net_result"],
                )
            )

        return period_totals

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get period totals: {e!s}",
        )


@router.get(
    "/statements/{version_id}/periods/{period}", response_model=FinancialPeriodTotals
)
async def get_period_total(
    version_id: uuid.UUID,
    period: str,
    statements_service: FinancialStatementsService = Depends(
        get_financial_statements_service
    ),
    user: UserDep = ...,
):
    """
    Get financial totals for a specific period.

    Args:
        version_id: Budget version UUID
        period: Period identifier ('p1', 'summer', 'p2', 'annual')
        statements_service: Financial statements service
        user: Current authenticated user

    Returns:
        Period totals

    Raises:
        404: Budget version not found
        400: Invalid period
    """
    try:
        totals = await statements_service.get_period_totals(version_id, period)
        return FinancialPeriodTotals(
            budget_version_id=version_id,
            period=period,
            total_revenue=totals["total_revenue"],
            total_expenses=totals["total_expenses"],
            operating_result=totals["operating_result"],
            net_result=totals["net_result"],
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get period total: {e!s}",
        )
