"""
EFIR Budget Planning Application - Database Models

This package contains all SQLAlchemy ORM models organized by module-aligned files:

CANONICAL IMPORTS (use these for new code):
-------------------------------------------
- base: Base classes, mixins, and utilities
- reference: Reference data models (ref_* tables) - 8 models
- settings: System configuration models (settings_* tables) - 12 models
- students: Student/enrollment models (students_* tables) - 16 models
- teachers: Workforce/personnel models (teachers_* tables) - 7 models
- finance: Financial planning models (finance_* tables) - 9 models
- insights: Analytics/dashboard models (insights_* tables) - 8 models
- admin: Administrative models (admin_* tables) - 3 models

BACKWARD COMPATIBILITY:
-----------------------
Old imports from configuration.py, planning.py, personnel.py, consolidation.py,
analysis.py, strategic.py, enrollment_projection.py, enrollment_unified.py,
finance_unified.py, integrations.py, and auth.py continue to work but are
deprecated. Please update to new canonical imports.

Module Architecture (10 Modules):
---------------------------------
| Module       | Route           | Models                                    |
|--------------|-----------------|-------------------------------------------|
| Enrollment   | /enrollment/*   | students.py (16 models)                   |
| Workforce    | /workforce/*    | teachers.py (7 models)                    |
| Revenue      | /revenue/*      | finance.py (FinanceData, type=revenue)    |
| Costs        | /costs/*        | finance.py (FinanceData, type=cost)       |
| Investments  | /investments/*  | finance.py (FinanceData, type=capex)      |
| Consolidation| /consolidation/*| finance.py (4 consolidation models)       |
| Insights     | /insights/*     | insights.py (8 models)                    |
| Strategic    | /strategic/*    | settings.py (4 strategic models)          |
| Settings     | /settings/*     | settings.py (8 settings models)           |
| Admin        | /admin/*        | admin.py (3 models)                       |
"""

# ==============================================================================
# CANONICAL IMPORTS - Use these for new code
# ==============================================================================

# Base classes and utilities
# Admin (admin_* tables)
from app.models.admin import (
    IntegrationLog,
    Organization,
    User,
)
from app.models.base import (
    AuditMixin,
    Base,
    BaseModel,
    PortableJSON,
    ReferenceDataModel,
    SoftDeleteMixin,
    TimestampMixin,
    VersionedMixin,
    get_fk_target,
    get_schema,
    get_table_args,
)

# Finance (finance_* tables)
from app.models.finance import (
    # Active Models
    BudgetConsolidation,
    # Legacy Models (deprecated - Phase 4C)
    CapExPlan,
    # Enums
    ConsolidationCategory,
    FinanceData,
    FinanceDataType,
    FinancialStatement,
    FinancialStatementLine,
    LineType,
    OperatingCostPlan,
    PersonnelCostPlan,
    RevenuePlan,
    StatementFormat,
    StatementType,
)

# Insights (insights_* tables)
from app.models.insights import (
    # Models
    ActualData,
    # Enums
    ActualDataSource,
    BudgetVsActual,
    DashboardConfig,
    DashboardRole,
    DashboardWidget,
    HistoricalActuals,
    HistoricalDataSource,
    HistoricalDimensionType,
    HistoricalModuleCode,
    KPIValue,
    UserPreferences,
    VarianceExplanation,
    VarianceStatus,
    WidgetType,
)

# Reference Data (ref_* tables)
from app.models.reference import (
    # Models
    AcademicCycle,
    AcademicLevel,
    EnrollmentScenario,
    FeeCategory,
    # Enums
    KPICategory,
    KPIDefinition,
    NationalityType,
    Subject,
    TeacherCategory,
)

# Settings (settings_* tables)
from app.models.settings import (
    # Models
    ClassSizeParam,
    FeeStructure,
    # Enums
    InitiativeStatus,
    IntegrationSettings,
    ProjectionCategory,
    ScenarioType,
    StrategicInitiative,
    StrategicPlan,
    StrategicPlanProjection,
    StrategicPlanScenario,
    StrategicScenarioType,
    SubjectHoursMatrix,
    SystemConfig,
    TeacherCostParam,
    TimetableConstraint,
    Version,
    VersionStatus,
)

# Students (students_* tables)
from app.models.students import (
    # Enums
    CalibrationOrigin,
    # Active Models
    ClassStructure,
    DataSourceType,
    # Legacy Models (deprecated - Phase 4A)
    EnrollmentDerivedParameter,
    EnrollmentGlobalOverride,
    EnrollmentGradeOverride,
    EnrollmentLateralEntryDefault,
    EnrollmentLevelOverride,
    EnrollmentParameterOverride,
    EnrollmentPlan,
    EnrollmentProjection,
    EnrollmentProjectionConfig,
    EnrollmentScenarioMultiplier,
    NationalityDistribution,
    OverrideScope,
    StudentsCalibration,
    StudentsConfig,
    StudentsData,
    StudentsOverride,
)

# Teachers (teachers_* tables)
from app.models.teachers import (
    # Legacy Models (deprecated - Phase 4B)
    AEFEPosition,
    # Enums
    AEFEPositionType,
    ContractType,
    # Active Models
    DHGSubjectHours,
    DHGTeacherRequirement,
    Employee,
    EmployeeCategory,
    EmployeeNationality,
    EmployeeSalary,
    EOSProvision,
    TeacherAllocation,
    TerminationType,
)

# ==============================================================================
# BACKWARD COMPATIBILITY ALIASES
# These aliases maintain compatibility with old import paths.
# Please update to canonical imports above for new code.
# ==============================================================================

# Version aliases (old names → new names)
BudgetVersion = Version
BudgetVersionStatus = VersionStatus

# Mixin alias (was in enrollment_unified, now not needed as separate export)
LineageMixin = VersionedMixin  # Lineage columns are now part of models directly

# ==============================================================================
# ALL EXPORTS
# ==============================================================================

__all__ = [
    # =========================================================================
    # Base Classes & Utilities
    # =========================================================================
    "Base",
    "BaseModel",
    "ReferenceDataModel",
    "AuditMixin",
    "SoftDeleteMixin",
    "TimestampMixin",
    "VersionedMixin",
    "PortableJSON",
    "get_fk_target",
    "get_schema",
    "get_table_args",
    # =========================================================================
    # Reference Data (ref_* - 8 models)
    # =========================================================================
    "AcademicCycle",
    "AcademicLevel",
    "Subject",
    "TeacherCategory",
    "FeeCategory",
    "NationalityType",
    "EnrollmentScenario",
    "KPIDefinition",
    # Reference Enums
    "KPICategory",
    # =========================================================================
    # Settings (settings_* - 12 models)
    # =========================================================================
    "SystemConfig",
    "Version",
    "ClassSizeParam",
    "SubjectHoursMatrix",
    "TeacherCostParam",
    "FeeStructure",
    "TimetableConstraint",
    "IntegrationSettings",
    "StrategicPlan",
    "StrategicPlanScenario",
    "StrategicPlanProjection",
    "StrategicInitiative",
    # Settings Enums
    "VersionStatus",
    "ScenarioType",
    "StrategicScenarioType",
    "InitiativeStatus",
    "ProjectionCategory",
    # =========================================================================
    # Students (students_* - 16 models)
    # =========================================================================
    # Active Models (9)
    "EnrollmentPlan",
    "NationalityDistribution",
    "ClassStructure",
    "EnrollmentLateralEntryDefault",
    "EnrollmentProjection",
    "StudentsConfig",
    "StudentsData",
    "StudentsOverride",
    "StudentsCalibration",
    # Legacy Models - Deprecated (7)
    "EnrollmentProjectionConfig",
    "EnrollmentGlobalOverride",
    "EnrollmentLevelOverride",
    "EnrollmentGradeOverride",
    "EnrollmentDerivedParameter",
    "EnrollmentParameterOverride",
    "EnrollmentScenarioMultiplier",
    # Students Enums
    "OverrideScope",
    "CalibrationOrigin",
    "DataSourceType",
    # =========================================================================
    # Teachers (teachers_* - 7 models)
    # =========================================================================
    # Active Models (5)
    "Employee",
    "EOSProvision",
    "DHGSubjectHours",
    "DHGTeacherRequirement",
    "TeacherAllocation",
    # Legacy Models - Deprecated (2)
    "EmployeeSalary",
    "AEFEPosition",
    # Teachers Enums
    "EmployeeCategory",
    "EmployeeNationality",
    "ContractType",
    "TerminationType",
    "AEFEPositionType",
    # =========================================================================
    # Finance (finance_* - 9 models)
    # =========================================================================
    # Active Models (4)
    "FinanceData",
    "BudgetConsolidation",
    "FinancialStatement",
    "FinancialStatementLine",
    # Legacy Models - Deprecated (4)
    "RevenuePlan",
    "PersonnelCostPlan",
    "OperatingCostPlan",
    "CapExPlan",
    # Finance Enums
    "FinanceDataType",
    "ConsolidationCategory",
    "StatementType",
    "StatementFormat",
    "LineType",
    # =========================================================================
    # Insights (insights_* - 8 models)
    # =========================================================================
    "KPIValue",
    "DashboardConfig",
    "DashboardWidget",
    "UserPreferences",
    "ActualData",
    "BudgetVsActual",
    "VarianceExplanation",
    "HistoricalActuals",
    # Insights Enums
    "WidgetType",
    "DashboardRole",
    "VarianceStatus",
    "ActualDataSource",
    "HistoricalModuleCode",
    "HistoricalDimensionType",
    "HistoricalDataSource",
    # =========================================================================
    # Admin (admin_* - 3 models)
    # =========================================================================
    "User",
    "Organization",
    "IntegrationLog",
    # =========================================================================
    # Backward Compatibility Aliases
    # =========================================================================
    "BudgetVersion",  # → Version
    "BudgetVersionStatus",  # → VersionStatus
    "LineageMixin",  # → VersionedMixin
]
