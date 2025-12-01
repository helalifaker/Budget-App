"""
API Schemas - Pydantic models for FastAPI request/response

These schemas are separate from the engine models to maintain
clean separation between API layer and business logic.
"""

from app.schemas.costs import (
    CapExPlanCreate,
    CapExPlanResponse,
    CapExPlanUpdate,
    DepreciationCalculationRequest,
    DepreciationCalculationResponse,
    OperatingCostPlanCreate,
    OperatingCostPlanResponse,
    OperatingCostPlanUpdate,
    PersonnelCostPlanCreate,
    PersonnelCostPlanResponse,
    PersonnelCostPlanUpdate,
    RevenuePlanCreate,
    RevenuePlanResponse,
    RevenuePlanUpdate,
)
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

__all__ = [
    "CapExPlanCreate",
    "CapExPlanResponse",
    "CapExPlanUpdate",
    "DHGCalculationRequest",
    "DHGCalculationResponse",
    "DepreciationCalculationRequest",
    "DepreciationCalculationResponse",
    "EnrollmentProjectionRequest",
    "EnrollmentProjectionResponse",
    "KPICalculationRequest",
    "KPICalculationResponse",
    "OperatingCostPlanCreate",
    "OperatingCostPlanResponse",
    "OperatingCostPlanUpdate",
    "PersonnelCostPlanCreate",
    "PersonnelCostPlanResponse",
    "PersonnelCostPlanUpdate",
    "RevenueCalculationRequest",
    "RevenueCalculationResponse",
    "RevenuePlanCreate",
    "RevenuePlanResponse",
    "RevenuePlanUpdate",
]
