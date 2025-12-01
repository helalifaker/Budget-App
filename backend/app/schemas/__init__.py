"""
API Schemas - Pydantic models for FastAPI request/response

These schemas are separate from the engine models to maintain
clean separation between API layer and business logic.
"""

from app.schemas.enrollment import (
    EnrollmentProjectionRequest,
    EnrollmentProjectionResponse,
)
from app.schemas.kpi import (
    KPICalculationRequest,
    KPICalculationResponse,
)
from app.schemas.dhg import (
    DHGCalculationRequest,
    DHGCalculationResponse,
)
from app.schemas.revenue import (
    RevenueCalculationRequest,
    RevenueCalculationResponse,
)

__all__ = [
    # Enrollment
    "EnrollmentProjectionRequest",
    "EnrollmentProjectionResponse",
    # KPI
    "KPICalculationRequest",
    "KPICalculationResponse",
    # DHG
    "DHGCalculationRequest",
    "DHGCalculationResponse",
    # Revenue
    "RevenueCalculationRequest",
    "RevenueCalculationResponse",
]
