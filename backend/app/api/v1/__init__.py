"""API v1 package."""

from app.api.v1.admin import router as admin_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.calculations import router as calculations_router
from app.api.v1.configuration import router as configuration_router
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.costs import router as costs_router
from app.api.v1.enrollment_settings import router as enrollment_settings_router
from app.api.v1.export import router as export_router
from app.api.v1.historical import router as historical_router
from app.api.v1.organization import router as organization_router
from app.api.v1.planning import router as planning_router
from app.api.v1.strategic import router as strategic_router
from app.api.v1.workforce import router as workforce_router
from app.api.v1.writeback import router as writeback_router

__all__ = [
    "admin_router",
    "analysis_router",
    "calculations_router",
    "configuration_router",
    "consolidation_router",
    "costs_router",
    "enrollment_settings_router",
    "export_router",
    "historical_router",
    "organization_router",
    "planning_router",
    "strategic_router",
    "workforce_router",
    "writeback_router",
]
