"""API v1 package."""

from app.api.v1.admin import router as admin_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.calculations import router as calculations_router
from app.api.v1.capex import router as capex_router
from app.api.v1.class_structure import router as class_structure_router
from app.api.v1.configuration import router as configuration_router
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.costs import router as costs_router
from app.api.v1.dhg import router as dhg_router
from app.api.v1.dhg import router as dhg_router
from app.api.v1.distributions import router as distributions_router
from app.api.v1.enrollment import router as enrollment_router
from app.api.v1.enrollment_projection import router as enrollment_projection_router
from app.api.v1.enrollment_settings import router as enrollment_settings_router
from app.api.v1.export import router as export_router
from app.api.v1.historical import router as historical_router
from app.api.v1.impact import router as impact_router
from app.api.v1.orchestration import router as orchestration_router
from app.api.v1.organization import router as organization_router
from app.api.v1.revenue import router as revenue_router
from app.api.v1.strategic import router as strategic_router
from app.api.v1.workforce import router as workforce_router
from app.api.v1.writeback import router as writeback_router

__all__ = [
    "admin_router",
    "analysis_router",
    "calculations_router",
    "capex_router",
    "class_structure_router",
    "configuration_router",
    "consolidation_router",
    "costs_router",
    "dhg_router",
    "distributions_router",
    "enrollment_router",
    "enrollment_projection_router",
    "enrollment_settings_router",
    "export_router",
    "historical_router",
    "impact_router",
    "orchestration_router",
    "organization_router",
    "revenue_router",
    "strategic_router",
    "workforce_router",
    "writeback_router",
]
