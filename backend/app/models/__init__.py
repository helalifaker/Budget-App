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

from app.models.analysis import (
    # Models
    ActualData,
    # Enums
    ActualDataSource,
    BudgetVsActual,
    DashboardConfig,
    DashboardRole,
    DashboardWidget,
    KPICategory,
    KPIDefinition,
    KPIValue,
    UserPreferences,
    VarianceExplanation,
    VarianceStatus,
    WidgetType,
)
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
from app.models.consolidation import (
    BudgetConsolidation,
    ConsolidationCategory,
    FinancialStatement,
    FinancialStatementLine,
    LineType,
    StatementFormat,
    StatementType,
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
    "AcademicCycle",
    "AcademicLevel",
    "ActualData",
    "ActualDataSource",
    "AuditMixin",
    # Base classes
    "Base",
    "BaseModel",
    # Consolidation Layer (Modules 13-14)
    "BudgetConsolidation",
    "BudgetVersion",
    "BudgetVersionStatus",
    "BudgetVsActual",
    "CapExPlan",
    "ClassSizeParam",
    "ClassStructure",
    "ConsolidationCategory",
    "DHGSubjectHours",
    "DHGTeacherRequirement",
    "DashboardConfig",
    "DashboardRole",
    "DashboardWidget",
    # Planning Layer (Modules 7-12)
    "EnrollmentPlan",
    "FeeCategory",
    "FeeStructure",
    "FinancialStatement",
    "FinancialStatementLine",
    "InitiativeStatus",
    # Analysis Layer (Modules 15-17)
    # Enums
    "KPICategory",
    # Models
    "KPIDefinition",
    "KPIValue",
    "LineType",
    "NationalityType",
    "OperatingCostPlan",
    "PersonnelCostPlan",
    "ProjectionCategory",
    "ReferenceDataModel",
    "RevenuePlan",
    # Strategic Layer (Module 18)
    # Enums
    "ScenarioType",
    "SoftDeleteMixin",
    "StatementFormat",
    "StatementType",
    "StrategicInitiative",
    # Models
    "StrategicPlan",
    "StrategicPlanProjection",
    "StrategicPlanScenario",
    "Subject",
    "SubjectHoursMatrix",
    # Configuration Layer (Modules 1-6)
    "SystemConfig",
    "TeacherAllocation",
    "TeacherCategory",
    "TeacherCostParam",
    "TimestampMixin",
    "TimetableConstraint",
    "UserPreferences",
    "VarianceExplanation",
    "VarianceStatus",
    "VersionedMixin",
    "WidgetType",
]
