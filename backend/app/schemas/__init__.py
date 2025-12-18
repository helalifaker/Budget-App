"""
API Schemas - Pydantic models for FastAPI request/response

These schemas are separate from the engine models to maintain
clean separation between API layer and business logic.
"""

from app.schemas.costs.costs import (
    OperatingCostPlanCreate,
    OperatingCostPlanResponse,
    OperatingCostPlanUpdate,
    PersonnelCostPlanCreate,
    PersonnelCostPlanResponse,
    PersonnelCostPlanUpdate,
)
from app.schemas.enrollment.enrollment import (
    EnrollmentProjectionRequest,
    EnrollmentProjectionResponse,
)
from app.schemas.insights.kpi import (
    KPICalculationRequest,
    KPICalculationResponse,
)
from app.schemas.investments.investments import (
    CapExPlanCreate,
    CapExPlanResponse,
    CapExPlanUpdate,
    DepreciationCalculationRequest,
    DepreciationCalculationResponse,
)
from app.schemas.revenue.revenue import (
    RevenueCalculationRequest,
    RevenueCalculationResponse,
    RevenuePlanCreate,
    RevenuePlanResponse,
    RevenuePlanUpdate,
)

# DHG schemas - imported from workforce submodule
from app.schemas.workforce.dhg import (
    DHGCalculationRequest,
    DHGCalculationResponse,
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
