"""
EFIR Budget Services Layer

Domain Modules (aligned with canonical 10 modules):
- enrollment: Projections, class structure, capacity
- workforce: DHG, employees, AEFE positions
- revenue: Tuition, subsidies, other revenue
- costs: Personnel costs, operating expenses
- investments: CapEx, projects
- consolidation: Budget rollup, financial statements
- insights: KPIs, dashboards, analytics
- settings: Configuration, versions, parameters
- admin: Writeback, imports, cascade operations

Shared:
- base: BaseService ORM abstraction
- exceptions: Service exception hierarchy
"""

from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    CellLockedError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceException,
    UnauthorizedError,
    ValidationError,
    VersionConflictError,
)

__all__ = [
    "BaseService",
    "BusinessRuleError",
    "CellLockedError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "ServiceException",
    "UnauthorizedError",
    "ValidationError",
    "VersionConflictError",
]
