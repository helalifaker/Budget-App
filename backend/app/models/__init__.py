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
    # Historical Comparison
    HistoricalActuals,
    HistoricalDataSource,
    HistoricalDimensionType,
    HistoricalModuleCode,
    KPICategory,
    KPIDefinition,
    KPIValue,
    UserPreferences,
    VarianceExplanation,
    VarianceStatus,
    WidgetType,
)
from app.models.auth import Organization, User
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
from app.models.enrollment_projection import (
    EnrollmentDerivedParameter,
    EnrollmentGlobalOverride,
    EnrollmentGradeOverride,
    EnrollmentLateralEntryDefault,
    EnrollmentLevelOverride,
    EnrollmentParameterOverride,
    EnrollmentProjection,
    EnrollmentProjectionConfig,
    EnrollmentScenario,
    EnrollmentScenarioMultiplier,
)
from app.models.personnel import (
    # Models
    AEFEPosition,
    # Enums
    AEFEPositionType,
    ContractType,
    Employee,
    EmployeeCategory,
    EmployeeNationality,
    EmployeeSalary,
    EOSProvision,
    TerminationType,
)
from app.models.planning import (
    CapExPlan,
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    EnrollmentPlan,
    NationalityDistribution,
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
    # Personnel Layer (Workforce Module)
    "AEFEPosition",
    "AEFEPositionType",
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
    "ContractType",
    "DHGSubjectHours",
    "DHGTeacherRequirement",
    "DashboardConfig",
    "DashboardRole",
    "DashboardWidget",
    "EOSProvision",
    "Employee",
    "EmployeeCategory",
    "EmployeeNationality",
    "EmployeeSalary",
    # Planning Layer (Modules 7-12)
    "EnrollmentPlan",
    # Enrollment Projection (Module 7 upgrade)
    "EnrollmentScenario",
    "EnrollmentLateralEntryDefault",
    "EnrollmentProjectionConfig",
    "EnrollmentGlobalOverride",
    "EnrollmentLevelOverride",
    "EnrollmentGradeOverride",
    "EnrollmentProjection",
    # Enrollment Settings (Dynamic Lateral Entry)
    "EnrollmentDerivedParameter",
    "EnrollmentParameterOverride",
    "EnrollmentScenarioMultiplier",
    "FeeCategory",
    "FeeStructure",
    "FinancialStatement",
    "FinancialStatementLine",
    # Historical Comparison
    "HistoricalActuals",
    "HistoricalDataSource",
    "HistoricalDimensionType",
    "HistoricalModuleCode",
    "InitiativeStatus",
    # Analysis Layer (Modules 15-17)
    # Enums
    "KPICategory",
    # Models
    "KPIDefinition",
    "KPIValue",
    "LineType",
    "NationalityDistribution",
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
    "TerminationType",
    "TimestampMixin",
    "TimetableConstraint",
    # Auth models
    "Organization",
    "User",
    "UserPreferences",
    "VarianceExplanation",
    "VarianceStatus",
    "VersionedMixin",
    "WidgetType",
]
