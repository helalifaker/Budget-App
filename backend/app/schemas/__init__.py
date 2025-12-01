"""
API Schemas - Pydantic models for FastAPI request/response

These schemas are separate from the engine models to maintain
clean separation between API layer and business logic.
"""

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
from app.schemas.costs import (
    RevenuePlanCreate,
    RevenuePlanResponse,
    RevenuePlanUpdate,
    PersonnelCostPlanCreate,
    PersonnelCostPlanResponse,
    PersonnelCostPlanUpdate,
    OperatingCostPlanCreate,
    OperatingCostPlanResponse,
    OperatingCostPlanUpdate,
    CapExPlanCreate,
    CapExPlanResponse,
    CapExPlanUpdate,
    DepreciationCalculationRequest,
    DepreciationCalculationResponse,
)

__all__ = [
    # DHG
    "DHGCalculationRequest",
    "DHGCalculationResponse",
    # Enrollment
    "EnrollmentProjectionRequest",
    "EnrollmentProjectionResponse",
    # KPI
    "KPICalculationRequest",
    "KPICalculationResponse",
    # Revenue
    "RevenueCalculationRequest",
    "RevenueCalculationResponse",
    # Costs - Revenue Planning
    "RevenuePlanCreate",
    "RevenuePlanResponse",
    "RevenuePlanUpdate",
    # Costs - Personnel
    "PersonnelCostPlanCreate",
    "PersonnelCostPlanResponse",
    "PersonnelCostPlanUpdate",
    # Costs - Operating
    "OperatingCostPlanCreate",
    "OperatingCostPlanResponse",
    "OperatingCostPlanUpdate",
    # Costs - CapEx
    "CapExPlanCreate",
    "CapExPlanResponse",
    "CapExPlanUpdate",
    "DepreciationCalculationRequest",
    "DepreciationCalculationResponse",
]
