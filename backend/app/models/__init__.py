"""
EFIR Budget Planning Application - Database Models

This package contains all SQLAlchemy ORM models organized by layer:
- base: Base classes and mixins
- configuration: Configuration Layer (Modules 1-6)
- planning: Planning Layer (Modules 7-12)
- consolidation: Consolidation Layer (Modules 13-14)
- analysis: Analysis Layer (Modules 15-17)
- strategic: Strategic Layer (Module 18)
"""

from app.models.base import (
    AuditMixin,
    Base,
    BaseModel,
    ReferenceDataModel,
    SoftDeleteMixin,
    TimestampMixin,
    VersionedMixin,
)
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    BudgetVersion,
    BudgetVersionStatus,
    ClassSizeParam,
    FeeCategory,
    FeeStructure,
    NationalityType,
    Subject,
    SubjectHoursMatrix,
    SystemConfig,
    TeacherCategory,
    TeacherCostParam,
    TimetableConstraint,
)
from app.models.planning import (
    CapExPlan,
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    EnrollmentPlan,
    OperatingCostPlan,
    PersonnelCostPlan,
    RevenuePlan,
    TeacherAllocation,
)
from app.models.consolidation import (
    BudgetConsolidation,
    ConsolidationCategory,
    FinancialStatement,
    FinancialStatementLine,
    LineType,
    StatementFormat,
    StatementType,
)
from app.models.analysis import (
    # Enums
    ActualDataSource,
    DashboardRole,
    KPICategory,
    VarianceStatus,
    WidgetType,
    # Models
    ActualData,
    BudgetVsActual,
    DashboardConfig,
    DashboardWidget,
    KPIDefinition,
    KPIValue,
    UserPreferences,
    VarianceExplanation,
)
from app.models.strategic import (
    # Enums
    InitiativeStatus,
    ProjectionCategory,
    ScenarioType,
    # Models
    StrategicInitiative,
    StrategicPlan,
    StrategicPlanProjection,
    StrategicPlanScenario,
)

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "ReferenceDataModel",
    "AuditMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "VersionedMixin",
    # Configuration Layer (Modules 1-6)
    "SystemConfig",
    "BudgetVersion",
    "BudgetVersionStatus",
    "AcademicCycle",
    "AcademicLevel",
    "ClassSizeParam",
    "Subject",
    "SubjectHoursMatrix",
    "TeacherCategory",
    "TeacherCostParam",
    "FeeCategory",
    "NationalityType",
    "FeeStructure",
    "TimetableConstraint",
    # Planning Layer (Modules 7-12)
    "EnrollmentPlan",
    "ClassStructure",
    "DHGSubjectHours",
    "DHGTeacherRequirement",
    "TeacherAllocation",
    "RevenuePlan",
    "PersonnelCostPlan",
    "OperatingCostPlan",
    "CapExPlan",
    # Consolidation Layer (Modules 13-14)
    "BudgetConsolidation",
    "ConsolidationCategory",
    "FinancialStatement",
    "FinancialStatementLine",
    "StatementType",
    "StatementFormat",
    "LineType",
    # Analysis Layer (Modules 15-17)
    # Enums
    "KPICategory",
    "WidgetType",
    "DashboardRole",
    "VarianceStatus",
    "ActualDataSource",
    # Models
    "KPIDefinition",
    "KPIValue",
    "DashboardConfig",
    "DashboardWidget",
    "UserPreferences",
    "ActualData",
    "BudgetVsActual",
    "VarianceExplanation",
    # Strategic Layer (Module 18)
    # Enums
    "ScenarioType",
    "InitiativeStatus",
    "ProjectionCategory",
    # Models
    "StrategicPlan",
    "StrategicPlanScenario",
    "StrategicPlanProjection",
    "StrategicInitiative",
]
