"""
Workforce API endpoints.

Provides REST API for personnel management:
- Employee CRUD (Base 100 + Planned positions)
- Salary management with GOSI calculations
- EOS provision calculation and tracking
- AEFE position management (24 Detached + 4 Funded)
- Workforce summary statistics

KSA Labor Law Compliance:
- EOS: 0.5 months/year (years 1-5), 1.0 month/year (years 6+)
- GOSI: Saudi 21.5% (11.75% employer), Expatriate 2% employer only
- Basic salary must be at least 50% of gross
"""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.engine.workforce.eos import EOSInput, TerminationReason, calculate_eos
from app.models import AEFEPositionType, EmployeeCategory, EmployeeNationality
from app.schemas.workforce.personnel import (
    AEFEPositionResponse,
    AEFEPositionUpdate,
    EmployeeBulkResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeSalaryCreate,
    EmployeeSalaryResponse,
    EmployeeUpdate,
    EOSCalculationRequest,
    EOSCalculationResponse,
    EOSProvisionCreate,
    EOSProvisionResponse,
    InitializeAEFEPositionsRequest,
    PlaceholderEmployeeCreate,
    WorkforceSummaryResponse,
)
from app.services.exceptions import NotFoundError, ValidationError
from app.services.workforce.aefe_service import AEFEService
from app.services.workforce.employee_service import EmployeeService

router = APIRouter(prefix="/workforce", tags=["workforce"])


# ==============================================================================
# Service Dependencies
# ==============================================================================


def get_employee_service(db: AsyncSession = Depends(get_db)) -> EmployeeService:
    """
    Dependency to get employee service instance.

    Args:
        db: Database session

    Returns:
        EmployeeService instance
    """
    return EmployeeService(db)


def get_aefe_service(db: AsyncSession = Depends(get_db)) -> AEFEService:
    """
    Dependency to get AEFE service instance.

    Args:
        db: Database session

    Returns:
        AEFEService instance
    """
    return AEFEService(db)


# ==============================================================================
# Employee Endpoints
# ==============================================================================


@router.get(
    "/employees/{version_id}",
    response_model=EmployeeBulkResponse,
    summary="Get all employees for a budget version",
)
async def get_employees(
    version_id: uuid.UUID,
    include_inactive: bool = Query(
        default=False, description="Include inactive employees"
    ),
    category: EmployeeCategory | None = Query(
        default=None, description="Filter by category"
    ),
    is_placeholder: bool | None = Query(
        default=None, description="Filter by placeholder status (Base 100 vs Planned)"
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get all employees for a budget version with optional filtering.

    Returns employees with counts for Base 100 (is_placeholder=False) vs
    Planned (is_placeholder=True) positions.

    Args:
        version_id: Budget version UUID
        include_inactive: Include inactive employees
        category: Filter by employee category
        is_placeholder: Filter by placeholder status
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        EmployeeBulkResponse with employee list and counts
    """
    try:
        employees = await employee_service.get_by_version(
            version_id=version_id,
            include_inactive=include_inactive,
            category=category,
            is_placeholder=is_placeholder,
        )

        base_100_count = sum(1 for e in employees if not e.is_placeholder)
        planned_count = sum(1 for e in employees if e.is_placeholder)

        return EmployeeBulkResponse(
            employees=[EmployeeResponse.model_validate(e) for e in employees],
            total=len(employees),
            base_100_count=base_100_count,
            planned_count=planned_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/employees/{version_id}/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get a specific employee",
)
async def get_employee(
    version_id: uuid.UUID,
    employee_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get a specific employee by ID.

    Args:
        version_id: Budget version UUID (for validation)
        employee_id: Employee UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Employee details
    """
    try:
        employee = await employee_service.get_by_id(employee_id, raise_if_not_found=True)
        # employee is guaranteed to be non-None due to raise_if_not_found=True
        assert employee is not None  # Type narrowing for mypy
        if employee.version_id != version_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found in this budget version",
            )
        return EmployeeResponse.model_validate(employee)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
async def create_employee(
    employee_data: EmployeeCreate,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Create a new employee with auto-generated employee code.

    Employee codes follow the format EMP001, EMP002, etc.

    Args:
        employee_data: Employee creation data
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Created employee with generated code
    """
    try:
        # Convert Pydantic model to dict, excluding version_id
        data = employee_data.model_dump(exclude={"version_id"})

        employee = await employee_service.create_employee(
            version_id=employee_data.version_id,
            data=data,
            user_id=user.user_id,
        )
        return EmployeeResponse.model_validate(employee)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update an employee",
)
async def update_employee(
    employee_id: uuid.UUID,
    employee_data: EmployeeUpdate,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Update an existing employee.

    Args:
        employee_id: Employee UUID
        employee_data: Updated employee data
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Updated employee
    """
    try:
        # Only include non-None fields
        data = employee_data.model_dump(exclude_none=True)

        employee = await employee_service.update(
            id=employee_id,
            data=data,
            user_id=user.user_id,
        )
        return EmployeeResponse.model_validate(employee)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete an employee",
)
async def delete_employee(
    employee_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Soft delete an employee (sets deleted_at timestamp).

    Args:
        employee_id: Employee UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        No content
    """
    try:
        await employee_service.soft_delete(id=employee_id, user_id=user.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Placeholder Employee Endpoints (from DHG Gap)
# ==============================================================================


@router.post(
    "/employees/placeholder",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create placeholder employee from DHG gap",
)
async def create_placeholder_employee(
    placeholder_data: PlaceholderEmployeeCreate,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Create a placeholder employee from DHG gap analysis.

    Placeholder employees are marked with is_placeholder=True and represent
    planned hiring needs. They can be validated later when actual hiring occurs.

    Args:
        placeholder_data: Placeholder creation data
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Created placeholder employee
    """
    try:
        employee = await employee_service.create_placeholder(
            version_id=placeholder_data.version_id,
            category=placeholder_data.category,
            cycle_id=placeholder_data.cycle_id,
            subject_id=placeholder_data.subject_id,
            fte=placeholder_data.fte,
            estimated_salary_sar=placeholder_data.estimated_salary_sar,
            notes=placeholder_data.notes,
            user_id=user.user_id,
        )
        return EmployeeResponse.model_validate(employee)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/employees/{employee_id}/validate",
    response_model=EmployeeResponse,
    summary="Validate and convert placeholder to Base 100",
)
async def validate_placeholder_employee(
    employee_id: uuid.UUID,
    full_name: str = Query(..., description="Actual employee name"),
    nationality: EmployeeNationality = Query(..., description="Employee nationality"),
    hire_date: date = Query(..., description="Actual hire date"),
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Validate a placeholder employee, converting it to a Base 100 employee.

    This endpoint is used when an actual hire is made for a placeholder position.
    After validation, is_placeholder will be set to False.

    Args:
        employee_id: Placeholder employee UUID
        full_name: Actual employee name
        nationality: Employee nationality
        hire_date: Actual hire date
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Validated employee (now Base 100)
    """
    try:
        employee = await employee_service.validate_placeholder(
            employee_id=employee_id,
            full_name=full_name,
            nationality=nationality,
            hire_date=hire_date,
            user_id=user.user_id,
        )
        return EmployeeResponse.model_validate(employee)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Salary Endpoints
# ==============================================================================


@router.get(
    "/employees/{employee_id}/salary",
    response_model=EmployeeSalaryResponse | None,
    summary="Get current salary for an employee",
)
async def get_employee_salary(
    employee_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get the current active salary for an employee.

    Includes GOSI calculations based on employee nationality.

    Args:
        employee_id: Employee UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Current salary or None if no salary is set
    """
    try:
        salary = await employee_service.get_current_salary(employee_id)
        if salary:
            return EmployeeSalaryResponse.model_validate(salary)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/employees/{employee_id}/salary/history",
    response_model=list[EmployeeSalaryResponse],
    summary="Get salary history for an employee",
)
async def get_salary_history(
    employee_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get all salary records for an employee ordered by effective date.

    Args:
        employee_id: Employee UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        List of salary records (most recent first)
    """
    try:
        salaries = await employee_service.get_salary_history(employee_id)
        return [EmployeeSalaryResponse.model_validate(s) for s in salaries]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/employees/{employee_id}/salary",
    response_model=EmployeeSalaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add salary for an employee",
)
async def add_employee_salary(
    employee_id: uuid.UUID,
    salary_data: EmployeeSalaryCreate,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Add a new salary record for an employee.

    GOSI contributions are automatically calculated based on nationality:
    - Saudi: 21.5% total (11.75% employer + 9.75% employee)
    - Expatriate: 2% (employer only)

    Previous salary records are automatically closed when adding a new one.

    Args:
        employee_id: Employee UUID
        salary_data: Salary creation data
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Created salary with GOSI calculations
    """
    try:
        salary = await employee_service.add_salary(
            employee_id=employee_id,
            version_id=salary_data.version_id,
            basic_salary_sar=salary_data.basic_salary_sar,
            housing_allowance_sar=salary_data.housing_allowance_sar,
            transport_allowance_sar=salary_data.transport_allowance_sar,
            other_allowances_sar=salary_data.other_allowances_sar,
            effective_from=salary_data.effective_from,
            effective_to=salary_data.effective_to,
            user_id=user.user_id,
        )
        return EmployeeSalaryResponse.model_validate(salary)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# EOS Calculation Endpoints
# ==============================================================================


@router.post(
    "/eos/calculate",
    response_model=EOSCalculationResponse,
    summary="Calculate EOS (preview only)",
)
async def calculate_eos_preview(
    request: EOSCalculationRequest,
    user: UserDep = ...,
):
    """
    Calculate EOS for preview without saving.

    KSA Labor Law formula:
    - Years 1-5: 0.5 × monthly basic salary × years
    - Years 6+: 1.0 × monthly basic salary × years

    Resignation factors:
    - <2 years: 0%
    - 2-5 years: 33%
    - 5-10 years: 67%
    - >10 years: 100%

    Args:
        request: EOS calculation parameters
        user: Current authenticated user

    Returns:
        EOS calculation result with breakdown
    """
    try:
        termination_date = request.termination_date or date.today()

        # Map termination type to reason
        termination_reason = TerminationReason.TERMINATION
        if request.termination_type:
            if request.termination_type.value == "resignation":
                termination_reason = TerminationReason.RESIGNATION
            elif request.termination_type.value == "retirement":
                termination_reason = TerminationReason.RETIREMENT

        result = calculate_eos(
            EOSInput(
                hire_date=request.hire_date,
                termination_date=termination_date,
                basic_salary_sar=request.basic_salary_sar,
                termination_reason=termination_reason,
            )
        )

        # Create calculation breakdown string
        breakdown_parts = [
            f"Years of service: {result.years_of_service} years, {result.months_of_service} months",
            f"Years 1-5 component: {result.years_1_to_5_amount_sar:,.2f} SAR",
            f"Years 6+ component: {result.years_6_plus_amount_sar:,.2f} SAR",
        ]
        if result.resignation_factor < Decimal("1.00"):
            breakdown_parts.append(
                f"Resignation factor: {result.resignation_factor * 100:.0f}%"
            )
        breakdown = " | ".join(breakdown_parts)

        return EOSCalculationResponse(
            years_of_service=result.years_of_service,
            months_of_service=result.months_of_service,
            total_service_years=result.total_service_years,
            years_1_to_5_amount_sar=result.years_1_to_5_amount_sar,
            years_6_plus_amount_sar=result.years_6_plus_amount_sar,
            gross_eos_sar=result.gross_eos_sar,
            resignation_factor=result.resignation_factor,
            final_eos_sar=result.final_eos_sar,
            calculation_breakdown=breakdown,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/employees/{employee_id}/eos",
    response_model=EOSProvisionResponse | None,
    summary="Get current EOS provision for an employee",
)
async def get_eos_provision(
    employee_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get the most recent EOS provision for an employee.

    Args:
        employee_id: Employee UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        EOS provision or None if none exists
    """
    try:
        provision = await employee_service.get_eos_provision(employee_id)
        if provision:
            return EOSProvisionResponse.model_validate(provision)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/employees/{employee_id}/eos",
    response_model=EOSProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate and save EOS provision for an employee",
)
async def calculate_employee_eos_provision(
    employee_id: uuid.UUID,
    eos_data: EOSProvisionCreate,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Calculate and save EOS provision for an employee.

    This creates a permanent record of the EOS provision calculation
    as of the specified date.

    Note: EOS is not applicable for AEFE employees (Detached/Funded).

    Args:
        employee_id: Employee UUID
        eos_data: EOS provision creation data
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Saved EOS provision record
    """
    try:
        provision = await employee_service.calculate_eos_provision(
            employee_id=employee_id,
            version_id=eos_data.version_id,
            as_of_date=eos_data.as_of_date,
            user_id=user.user_id,
        )
        return EOSProvisionResponse.model_validate(provision)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/eos/calculate-all/{version_id}",
    summary="Calculate EOS for all eligible employees",
)
async def calculate_all_eos(
    version_id: uuid.UUID,
    as_of_date: date = Query(default=None, description="Date for calculation"),
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Calculate EOS provision for all eligible employees in a budget version.

    Excludes AEFE employees (Detached and Funded) as they are not eligible for EOS.

    Args:
        version_id: Budget version UUID
        as_of_date: Date for calculation (defaults to today)
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Dictionary with calculated_count and total_provision_sar
    """
    try:
        result = await employee_service.calculate_all_eos(
            version_id=version_id,
            as_of_date=as_of_date or date.today(),
            user_id=user.user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/eos/summary/{version_id}",
    summary="Get EOS provision summary",
)
async def get_eos_summary(
    version_id: uuid.UUID,
    as_of_date: date = Query(default=None, description="Filter by date"),
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get EOS provision summary statistics for a budget version.

    Includes:
    - Employee count with EOS provisions
    - Total provision amount in SAR

    Args:
        version_id: Budget version UUID
        as_of_date: Filter by as_of_date (optional)
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Summary dictionary
    """
    try:
        return await employee_service.get_eos_summary(version_id, as_of_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# AEFE Position Endpoints
# ==============================================================================


@router.put(
    "/aefe-positions/{version_id}/prrd-rate",
    summary="Update PRRD rate for all detached positions",
)
async def update_prrd_rate(
    version_id: uuid.UUID,
    prrd_amount_eur: Decimal = Query(..., description="PRRD amount in EUR"),
    exchange_rate_eur_sar: Decimal = Query(..., description="EUR to SAR exchange rate"),
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Update PRRD rate for all detached positions in a budget version.

    This updates the PRRD amount and exchange rate for all 24 detached positions.
    Funded positions (4) are not affected as they have zero cost.

    Args:
        version_id: Budget version UUID
        prrd_amount_eur: PRRD amount in EUR
        exchange_rate_eur_sar: EUR to SAR exchange rate
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        Dictionary with updated_count and total_prrd_sar
    """
    try:
        positions = await aefe_service.update_prrd_rates(
            version_id=version_id,
            prrd_amount_eur=prrd_amount_eur,
            exchange_rate_eur_sar=exchange_rate_eur_sar,
            user_id=user.user_id,
        )
        total_prrd_sar = sum(p.prrd_amount_sar or Decimal("0") for p in positions)
        return {
            "updated_count": len(positions),
            "total_prrd_sar": total_prrd_sar,
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/aefe-positions/initialize",
    response_model=list[AEFEPositionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initialize 28 AEFE positions",
)
async def initialize_aefe_positions(
    init_request: InitializeAEFEPositionsRequest,
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Initialize 28 AEFE positions for a budget version.

    Creates:
    - 24 Detached positions (school pays PRRD)
    - 4 Funded positions (zero cost)

    Should be called once when setting up a new budget version.

    Args:
        init_request: Initialization parameters
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        List of created AEFE positions
    """
    try:
        positions = await aefe_service.initialize_positions(
            version_id=init_request.version_id,
            academic_year=init_request.academic_year,
            prrd_amount_eur=init_request.prrd_amount_eur,
            exchange_rate_eur_sar=init_request.exchange_rate_eur_sar,
            user_id=user.user_id,
        )
        return [AEFEPositionResponse.model_validate(p) for p in positions]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/aefe-positions/{version_id}",
    response_model=list[AEFEPositionResponse],
    summary="Get AEFE positions for a budget version",
)
async def get_aefe_positions(
    version_id: uuid.UUID,
    position_type: AEFEPositionType | None = Query(
        default=None, description="Filter by position type"
    ),
    filled_only: bool | None = Query(
        default=None, description="Filter by fill status"
    ),
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Get AEFE positions for a budget version.

    Args:
        version_id: Budget version UUID
        position_type: Filter by position type (DETACHED/FUNDED)
        filled_only: True for filled only, False for vacant only
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        List of AEFE positions
    """
    try:
        positions = await aefe_service.get_positions_by_version(
            version_id=version_id,
            position_type=position_type,
            filled_only=filled_only,
        )
        return [AEFEPositionResponse.model_validate(p) for p in positions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/aefe-positions/{position_id}",
    response_model=AEFEPositionResponse,
    summary="Update an AEFE position",
)
async def update_aefe_position(
    position_id: uuid.UUID,
    position_data: AEFEPositionUpdate,
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Update an AEFE position.

    Args:
        position_id: Position UUID
        position_data: Updated position data
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        Updated position
    """
    try:
        data = position_data.model_dump(exclude_none=True)
        position = await aefe_service.update(
            id=position_id,
            data=data,
            user_id=user.user_id,
        )
        return AEFEPositionResponse.model_validate(position)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/aefe-positions/{position_id}/assign",
    response_model=AEFEPositionResponse,
    summary="Assign an employee to an AEFE position",
)
async def assign_aefe_position(
    position_id: uuid.UUID,
    employee_id: uuid.UUID = Query(..., description="Employee to assign"),
    cycle_id: uuid.UUID | None = Query(default=None, description="Academic cycle"),
    subject_id: uuid.UUID | None = Query(default=None, description="Teaching subject"),
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Assign an employee to an AEFE position.

    The employee's category must match the position type:
    - DETACHED positions require AEFE_DETACHED employees
    - FUNDED positions require AEFE_FUNDED employees

    Args:
        position_id: Position UUID
        employee_id: Employee UUID to assign
        cycle_id: Academic cycle (optional)
        subject_id: Teaching subject (optional)
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        Updated position with assignment
    """
    try:
        position = await aefe_service.assign_employee(
            position_id=position_id,
            employee_id=employee_id,
            cycle_id=cycle_id,
            subject_id=subject_id,
            user_id=user.user_id,
        )
        return AEFEPositionResponse.model_validate(position)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/aefe-positions/{position_id}/unassign",
    response_model=AEFEPositionResponse,
    summary="Remove employee from an AEFE position",
)
async def unassign_aefe_position(
    position_id: uuid.UUID,
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Remove the current employee assignment from an AEFE position.

    Args:
        position_id: Position UUID
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        Updated position (now vacant)
    """
    try:
        position = await aefe_service.unassign_employee(
            position_id=position_id,
            user_id=user.user_id,
        )
        return AEFEPositionResponse.model_validate(position)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/aefe-positions/{version_id}/summary",
    response_model=dict,
    summary="Get AEFE positions summary",
)
async def get_aefe_positions_summary(
    version_id: uuid.UUID,
    aefe_service: AEFEService = Depends(get_aefe_service),
    user: UserDep = ...,
):
    """
    Get summary statistics for AEFE positions.

    Includes:
    - Total, filled, and vacant counts
    - Breakdown by position type (Detached vs Funded)
    - Total PRRD costs in EUR and SAR

    Args:
        version_id: Budget version UUID
        aefe_service: AEFE service
        user: Current authenticated user

    Returns:
        Summary dictionary
    """
    try:
        summary = await aefe_service.get_position_summary(version_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Workforce Summary Endpoints
# ==============================================================================


@router.get(
    "/summary/{version_id}",
    response_model=WorkforceSummaryResponse,
    summary="Get workforce summary statistics",
)
async def get_workforce_summary(
    version_id: uuid.UUID,
    employee_service: EmployeeService = Depends(get_employee_service),
    user: UserDep = ...,
):
    """
    Get comprehensive workforce summary for a budget version.

    Includes:
    - Employee counts (total, active, Base 100 vs Planned)
    - Breakdown by category and nationality
    - Total FTE
    - AEFE position fill rates
    - Payroll totals (monthly payroll, GOSI, EOS provision)

    Args:
        version_id: Budget version UUID
        employee_service: Employee service
        user: Current authenticated user

    Returns:
        Comprehensive workforce summary
    """
    try:
        summary = await employee_service.get_workforce_summary(version_id)
        return WorkforceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
