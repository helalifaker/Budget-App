"""
API routes for calculation engines.

All calculation endpoints are stateless and perform pure calculations
without database I/O.
"""


from fastapi import APIRouter, HTTPException, status

from app.engine.dhg import calculate_dhg_hours, validate_dhg_input
from app.engine.enrollment import calculate_enrollment_projection
from app.engine.kpi import calculate_all_kpis, validate_kpi_input
from app.engine.revenue import calculate_total_student_revenue, validate_tuition_input
from app.schemas.dhg import (
    DHGCalculationRequest,
    DHGCalculationResponse,
)
from app.schemas.enrollment import (
    EnrollmentProjectionRequest,
    EnrollmentProjectionResponse,
)
from app.schemas.kpi import (
    KPICalculationRequest,
    KPICalculationResponse,
)
from app.schemas.revenue import (
    RevenueCalculationRequest,
    RevenueCalculationResponse,
)

router = APIRouter(prefix="/api/v1/calculations", tags=["calculations"])


@router.post(
    "/enrollment/project",
    response_model=EnrollmentProjectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate enrollment projection",
    description="Calculate multi-year enrollment projection with growth scenarios",
)
async def calculate_enrollment(
    request: EnrollmentProjectionRequest,
) -> EnrollmentProjectionResponse:
    """
    Calculate enrollment projection for a level.

    Args:
        request: Enrollment input with current enrollment and growth parameters

    Returns:
        Enrollment projection result with year-by-year projections

    Example:
        POST /api/v1/calculations/enrollment/project
        {
            "level_id": "uuid",
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 5
        }
    """
    try:
        result = calculate_enrollment_projection(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Enrollment calculation failed: {e!s}",
        )


@router.post(
    "/kpi/calculate",
    response_model=KPICalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate KPIs",
    description="Calculate all key performance indicators for budget planning",
)
async def calculate_kpis(
    request: KPICalculationRequest,
) -> KPICalculationResponse:
    """
    Calculate all KPIs from input data.

    Args:
        request: KPI input with enrollment, financial, and teacher data

    Returns:
        KPI calculation result with all 7 KPIs

    Example:
        POST /api/v1/calculations/kpi/calculate
        {
            "total_students": 1850,
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "dhg_hours_total": 877.5,
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675
        }
    """
    try:
        # Validate input
        validate_kpi_input(request)

        # Calculate KPIs
        result = calculate_all_kpis(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid KPI input: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KPI calculation failed: {e!s}",
        )


@router.post(
    "/dhg/calculate",
    response_model=DHGCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate DHG hours",
    description="Calculate DHG (Dotation Horaire Globale) teaching hours for a level",
)
async def calculate_dhg(
    request: DHGCalculationRequest,
) -> DHGCalculationResponse:
    """
    Calculate DHG hours for a level.

    Args:
        request: DHG input with class count and subject hours

    Returns:
        DHG hours result with total hours and subject breakdown

    Example:
        POST /api/v1/calculations/dhg/calculate
        {
            "level_id": "uuid",
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [
                {
                    "subject_id": "uuid",
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": "uuid",
                    "level_code": "6EME",
                    "hours_per_week": 4.5
                }
            ]
        }
    """
    try:
        # Validate input
        validate_dhg_input(request)

        # Calculate DHG hours
        result = calculate_dhg_hours(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid DHG input: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DHG calculation failed: {e!s}",
        )


@router.post(
    "/revenue/calculate",
    response_model=RevenueCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate student revenue",
    description="Calculate tuition revenue with sibling discounts and trimester distribution",
)
async def calculate_revenue(
    request: RevenueCalculationRequest,
) -> RevenueCalculationResponse:
    """
    Calculate revenue for a student.

    Args:
        request: Tuition input with fees and sibling information

    Returns:
        Student revenue result with tuition and trimester distribution

    Example:
        POST /api/v1/calculations/revenue/calculate
        {
            "level_id": "uuid",
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 45000,
            "dai_fee": 2000,
            "registration_fee": 1000,
            "sibling_order": 3
        }
    """
    try:
        # Validate input
        validate_tuition_input(request)

        # Calculate revenue
        result = calculate_total_student_revenue(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid revenue input: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revenue calculation failed: {e!s}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Verify calculation endpoints are operational",
)
async def health_check():
    """Health check endpoint for calculation services."""
    return {
        "status": "healthy",
        "services": {
            "enrollment": "operational",
            "kpi": "operational",
            "dhg": "operational",
            "revenue": "operational",
        },
    }
