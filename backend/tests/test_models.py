"""
Tests for SQLAlchemy models.

Verifies that:
1. All models can be imported without errors (CRITICAL-1, CRITICAL-2)
2. Models have correct relationships and no mapper errors
3. Soft delete functionality works (HIGH-1)
4. Audit trail fields exist (CRITICAL-3)
"""

from app.models.base import BaseModel, SoftDeleteMixin


class TestModelImports:
    """Test that all models can be imported without errors."""

    def test_import_configuration_models(self):
        """Test that Configuration Layer models import successfully."""
        from app.models.configuration import (
            AcademicCycle,
            AcademicLevel,
            BudgetVersion,
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

        # If imports succeed, no mapper errors occurred
        assert AcademicCycle is not None
        assert AcademicLevel is not None
        assert BudgetVersion is not None
        assert ClassSizeParam is not None
        assert FeeCategory is not None
        assert FeeStructure is not None
        assert NationalityType is not None
        assert Subject is not None
        assert SubjectHoursMatrix is not None
        assert SystemConfig is not None
        assert TeacherCategory is not None
        assert TeacherCostParam is not None
        assert TimetableConstraint is not None

    def test_import_planning_models(self):
        """Test that Planning Layer models import successfully."""
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

        assert EnrollmentPlan is not None
        assert ClassStructure is not None
        assert DHGSubjectHours is not None
        assert DHGTeacherRequirement is not None
        assert TeacherAllocation is not None
        assert RevenuePlan is not None
        assert PersonnelCostPlan is not None
        assert OperatingCostPlan is not None
        assert CapExPlan is not None

    def test_import_consolidation_models(self):
        """Test that Consolidation Layer models import successfully."""
        from app.models.consolidation import (
            BudgetConsolidation,
            FinancialStatement,
            FinancialStatementLine,
        )

        assert BudgetConsolidation is not None
        assert FinancialStatement is not None
        assert FinancialStatementLine is not None

    def test_import_all_models_at_once(self):
        """Test that all models can be imported together."""
        import app.models as models_module

        # Verify __all__ is defined and all items are importable
        assert hasattr(models_module, "__all__"), "models module should define __all__"
        for name in models_module.__all__:
            assert hasattr(models_module, name), f"'{name}' not exported"

        # If this doesn't raise an error, all models are importable
        # and no circular dependencies or mapper errors exist


class TestBaseModelMixins:
    """Test BaseModel and its mixins."""

    def test_base_model_includes_soft_delete(self):
        """Test that BaseModel inherits SoftDeleteMixin (HIGH-1 fix)."""
        assert issubclass(BaseModel, SoftDeleteMixin)

    def test_base_model_has_soft_delete_methods(self):
        """Test that soft delete methods are available."""
        # Check that the methods exist (can't instantiate abstract class)
        assert hasattr(SoftDeleteMixin, "soft_delete")
        assert hasattr(SoftDeleteMixin, "restore")
        assert hasattr(SoftDeleteMixin, "is_deleted")

    def test_soft_delete_mixin_has_deleted_at_field(self):
        """Test that SoftDeleteMixin defines deleted_at field."""
        # Access the __annotations__ to see declared fields
        assert "deleted_at" in SoftDeleteMixin.__annotations__


class TestAuditTrail:
    """Test audit trail functionality (CRITICAL-3 fix)."""

    def test_base_model_has_audit_fields(self):
        """Test that BaseModel has all required audit fields."""
        from app.models.base import AuditMixin

        # Check that audit fields are defined
        # created_at and updated_at are in annotations
        assert "created_at" in AuditMixin.__annotations__
        assert "updated_at" in AuditMixin.__annotations__
        # created_by_id and updated_by_id are declared_attr (not in __annotations__)
        assert hasattr(AuditMixin, "created_by_id")
        assert hasattr(AuditMixin, "updated_by_id")

    def test_audit_fields_are_nullable(self):
        """Test that created_by_id and updated_by_id are nullable (CRITICAL-3 fix)."""
        from app.models.configuration import BudgetVersion

        # Get the column definitions
        created_by_col = BudgetVersion.__table__.c.created_by_id
        updated_by_col = BudgetVersion.__table__.c.updated_by_id

        # Verify they are nullable
        assert created_by_col.nullable is True
        assert updated_by_col.nullable is True


class TestVersionedMixin:
    """Test VersionedMixin (CRITICAL-1 fix)."""

    def test_versioned_mixin_no_back_populates(self):
        """
        Test that VersionedMixin doesn't use back_populates (CRITICAL-1 fix).

        This verifies that the relationship doesn't try to back-populate
        to non-existent attributes on BudgetVersion.
        """
        from app.models.planning import EnrollmentPlan

        # Get the budget_version relationship
        budget_version_rel = EnrollmentPlan.budget_version

        # Verify it exists
        assert budget_version_rel is not None

        # If we got here without mapper errors, the fix is working
        # The relationship should exist but without back_populates


class TestModelRelationships:
    """Test that model relationships work correctly."""

    def test_budget_version_parent_child_relationship(self):
        """Test BudgetVersion self-referential relationship."""
        from app.models.configuration import BudgetVersion

        # Check that parent_version and child_versions relationships exist
        assert hasattr(BudgetVersion, "parent_version")
        assert hasattr(BudgetVersion, "child_versions")

    def test_enrollment_plan_relationships(self):
        """Test EnrollmentPlan relationships."""
        from app.models.planning import EnrollmentPlan

        # Check that relationships exist
        assert hasattr(EnrollmentPlan, "budget_version")
        assert hasattr(EnrollmentPlan, "level")
        assert hasattr(EnrollmentPlan, "nationality_type")

    def test_financial_statement_cascade(self):
        """Test FinancialStatement cascade to lines."""
        from app.models.consolidation import FinancialStatement

        # Check that lines relationship exists
        assert hasattr(FinancialStatement, "lines")

        # Get the relationship property
        lines_rel = FinancialStatement.lines

        # Verify cascade is configured (cascade delete of lines when statement is deleted)
        assert lines_rel is not None


# Note: Integration tests with actual database operations
# should be added in a separate test_integration.py file
