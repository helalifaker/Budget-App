"""API v1 package."""

from app.api.v1.analysis import router as analysis_router
from app.api.v1.calculations import router as calculations_router
from app.api.v1.configuration import router as configuration_router
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.costs import router as costs_router
from app.api.v1.export import router as export_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.planning import router as planning_router
from app.api.v1.writeback import router as writeback_router

__all__ = [
    "analysis_router",
    "calculations_router",
    "configuration_router",
    "consolidation_router",
    "costs_router",
    "export_router",
    "integrations_router",
    "planning_router",
    "writeback_router",
]
