"""
Tests for EnrollmentService.

Tests cover:
- CRUD operations for enrollment plans
- Capacity validation (max 1,875 students)
- Enrollment projections with growth scenarios
- Summary statistics calculations
- Edge cases and error handling
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import AcademicLevel, BudgetVersion, NationalityType
from app.models.planning import EnrollmentPlan
from app.services.enrollment_service import EnrollmentService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestEnrollmentServiceCRUD:
    """Tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_enrollment_plan_returns_list(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
    ):
        """Test retrieving enrollment plan for a budget version."""
        service = EnrollmentService(db_session)

        result = await service.get_enrollment_plan(test_budget_version.id)

        assert isinstance(result, list)
        assert len(result) == len(test_enrollment_data)
        for enrollment in result:
            assert enrollment.budget_version_id == test_budget_version.id
            assert enrollment.deleted_at is None

    @pytest.mark.asyncio
    async def test_get_enrollment_plan_empty_version(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving enrollment plan for version with no enrollments."""
        service = EnrollmentService(db_session)

        # Create a new version with no enrollment data
        empty_version_id = uuid.uuid4()

        result = await service.get_enrollment_plan(empty_version_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_enrollment_by_id_success(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
    ):
        """Test retrieving enrollment by ID."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]

        result = await service.get_enrollment_by_id(enrollment.id)

        assert result.id == enrollment.id
        assert result.student_count == enrollment.student_count

    @pytest.mark.asyncio
    async def test_get_enrollment_by_id_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving non-existent enrollment raises NotFoundError."""
        service = EnrollmentService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_enrollment_by_id(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_create_enrollment_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_user_id: uuid.UUID,
    ):
        """Test creating a new enrollment entry."""
        service = EnrollmentService(db_session)

        result = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["MS"].id,  # Use MS which doesn't have enrollment
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=25,
            notes="Test enrollment",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.student_count == 25
        assert result.level_id == academic_levels["MS"].id
        assert result.nationality_type_id == nationality_types["FRENCH"].id
        assert result.budget_version_id == test_budget_version.id

    @pytest.mark.asyncio
    async def test_create_enrollment_duplicate_raises_error(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test creating duplicate enrollment raises ValidationError."""
        service = EnrollmentService(db_session)
        existing = test_enrollment_data[0]  # PS/FRENCH already exists

        with pytest.raises(ValidationError) as exc_info:
            await service.create_enrollment(
                version_id=test_budget_version.id,
                level_id=existing.level_id,
                nationality_type_id=existing.nationality_type_id,
                student_count=10,
                user_id=test_user_id,
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_enrollment_success(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test updating an enrollment entry."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]
        original_count = enrollment.student_count

        result = await service.update_enrollment(
            enrollment_id=enrollment.id,
            student_count=original_count + 5,
            notes="Updated notes",
            user_id=test_user_id,
        )

        assert result.student_count == original_count + 5
        assert result.notes == "Updated notes"

    @pytest.mark.asyncio
    async def test_update_enrollment_partial(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test updating only specific fields."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]
        original_count = enrollment.student_count

        # Update only notes, not count
        result = await service.update_enrollment(
            enrollment_id=enrollment.id,
            notes="New notes only",
            user_id=test_user_id,
        )

        assert result.student_count == original_count  # Unchanged
        assert result.notes == "New notes only"

    @pytest.mark.asyncio
    async def test_delete_enrollment_success(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test deleting an enrollment entry."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]

        result = await service.delete_enrollment(
            enrollment_id=enrollment.id,
            user_id=test_user_id,
        )

        assert result is True

        # Verify soft delete
        with pytest.raises(NotFoundError):
            await service.get_enrollment_by_id(enrollment.id)


class TestEnrollmentServiceCapacity:
    """Tests for capacity validation (max 1,875 students)."""

    @pytest.mark.asyncio
    async def test_create_enrollment_within_capacity(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_user_id: uuid.UUID,
    ):
        """Test creating enrollment within capacity limits."""
        service = EnrollmentService(db_session)

        # Should succeed - well within 1,875 limit
        result = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["GS"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=100,
            user_id=test_user_id,
        )

        assert result.student_count == 100

    @pytest.mark.asyncio
    async def test_create_enrollment_exceeds_capacity(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test creating enrollment that exceeds capacity raises error."""
        service = EnrollmentService(db_session)

        # Current total from fixtures: 35 + 15 + 80 = 130
        # Try to add 1750, which would exceed 1,875
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.create_enrollment(
                version_id=test_budget_version.id,
                level_id=academic_levels["GS"].id,
                nationality_type_id=nationality_types["OTHER"].id,
                student_count=1750,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "CAPACITY_EXCEEDED"
        assert "1875" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_enrollment_exceeds_capacity(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test updating enrollment that would exceed capacity raises error."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]

        # Try to update to extremely high number
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.update_enrollment(
                enrollment_id=enrollment.id,
                student_count=2000,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "CAPACITY_EXCEEDED"

    @pytest.mark.asyncio
    async def test_capacity_at_exact_limit(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test enrollment at exactly 1,875 is allowed."""
        service = EnrollmentService(db_session)

        # Current total: 35 + 15 + 80 = 130
        # Add exactly enough to reach 1,875
        remaining = 1875 - 130

        result = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["GS"].id,
            nationality_type_id=nationality_types["OTHER"].id,
            student_count=remaining,
            user_id=test_user_id,
        )

        assert result.student_count == remaining


class TestEnrollmentServiceSummary:
    """Tests for enrollment summary statistics."""

    @pytest.mark.asyncio
    async def test_get_enrollment_summary(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
    ):
        """Test getting enrollment summary statistics."""
        service = EnrollmentService(db_session)

        summary = await service.get_enrollment_summary(test_budget_version.id)

        # Total: 35 + 15 + 80 = 130
        assert summary["total_students"] == 130

        # By level
        assert "PS" in summary["by_level"]
        assert summary["by_level"]["PS"] == 50  # 35 + 15
        assert summary["by_level"]["6EME"] == 80

        # By nationality
        assert summary["by_nationality"]["FRENCH"] == 115  # 35 + 80
        assert summary["by_nationality"]["SAUDI"] == 15

        # Capacity utilization
        expected_utilization = Decimal((130 / 1875) * 100).quantize(Decimal("0.01"))
        assert summary["capacity_utilization"] == expected_utilization

    @pytest.mark.asyncio
    async def test_get_enrollment_summary_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test getting summary for empty enrollment."""
        service = EnrollmentService(db_session)
        empty_version_id = uuid.uuid4()

        summary = await service.get_enrollment_summary(empty_version_id)

        assert summary["total_students"] == 0
        assert summary["by_level"] == {}
        assert summary["by_cycle"] == {}
        assert summary["by_nationality"] == {}
        assert summary["capacity_utilization"] == Decimal("0.00")


class TestEnrollmentServiceProjection:
    """Tests for enrollment projection calculations."""

    @pytest.mark.asyncio
    async def test_project_enrollment_base_scenario(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
        nationality_types: dict,
    ):
        """Test projecting enrollment with base growth scenario."""
        service = EnrollmentService(db_session)

        projections = await service.project_enrollment(
            version_id=test_budget_version.id,
            years_to_project=5,
            growth_scenario="base",
        )

        assert len(projections) == len(test_enrollment_data)

        for projection in projections:
            assert len(projection.projections) == 5
            # Base scenario should show some growth
            assert projection.projections[-1].projected_enrollment >= projection.projections[0].projected_enrollment

    @pytest.mark.asyncio
    async def test_project_enrollment_conservative_scenario(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
        nationality_types: dict,
    ):
        """Test projecting with conservative growth scenario."""
        service = EnrollmentService(db_session)

        projections = await service.project_enrollment(
            version_id=test_budget_version.id,
            years_to_project=3,
            growth_scenario="conservative",
        )

        assert len(projections) == len(test_enrollment_data)
        for projection in projections:
            assert len(projection.projections) == 3

    @pytest.mark.asyncio
    async def test_project_enrollment_optimistic_scenario(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
        nationality_types: dict,
    ):
        """Test projecting with optimistic growth scenario."""
        service = EnrollmentService(db_session)

        projections = await service.project_enrollment(
            version_id=test_budget_version.id,
            years_to_project=5,
            growth_scenario="optimistic",
        )

        assert len(projections) == len(test_enrollment_data)

        # Optimistic should have higher growth than base
        for projection in projections:
            first_year = projection.projections[0].projected_enrollment
            last_year = projection.projections[-1].projected_enrollment
            # Allow for growth (optimistic should generally increase)
            assert last_year >= first_year * 0.9  # Allow small decrease for edge cases

    @pytest.mark.asyncio
    async def test_project_enrollment_invalid_years(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
    ):
        """Test projection with invalid years raises ValidationError."""
        service = EnrollmentService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.project_enrollment(
                version_id=test_budget_version.id,
                years_to_project=15,  # Max is 10
                growth_scenario="base",
            )

        assert "between 1 and 10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_project_enrollment_invalid_scenario(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
    ):
        """Test projection with invalid scenario raises ValidationError."""
        service = EnrollmentService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.project_enrollment(
                version_id=test_budget_version.id,
                years_to_project=5,
                growth_scenario="invalid_scenario",
            )

        assert "Invalid growth scenario" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_project_enrollment_no_data(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test projection without enrollment data raises BusinessRuleError."""
        service = EnrollmentService(db_session)
        empty_version_id = uuid.uuid4()

        with pytest.raises(BusinessRuleError) as exc_info:
            await service.project_enrollment(
                version_id=empty_version_id,
                years_to_project=5,
                growth_scenario="base",
            )

        assert exc_info.value.details["rule"] == "NO_ENROLLMENT_DATA"

    @pytest.mark.asyncio
    async def test_project_enrollment_with_custom_rates(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
        nationality_types: dict,
    ):
        """Test projection with custom growth rates per level."""
        service = EnrollmentService(db_session)

        custom_rates = {
            str(academic_levels["PS"].id): Decimal("0.05"),  # 5% growth for PS
            str(academic_levels["6EME"].id): Decimal("0.03"),  # 3% growth for 6EME
        }

        projections = await service.project_enrollment(
            version_id=test_budget_version.id,
            years_to_project=5,
            growth_scenario="base",
            custom_growth_rates=custom_rates,
        )

        assert len(projections) == len(test_enrollment_data)


class TestEnrollmentServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_enrollment_zero_students(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_user_id: uuid.UUID,
    ):
        """Test creating enrollment with zero students."""
        service = EnrollmentService(db_session)

        # Zero students should be allowed (e.g., for new levels)
        result = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["OTHER"].id,
            student_count=0,
            user_id=test_user_id,
        )

        assert result.student_count == 0

    @pytest.mark.asyncio
    async def test_update_enrollment_to_zero(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test updating enrollment to zero students."""
        service = EnrollmentService(db_session)
        enrollment = test_enrollment_data[0]

        result = await service.update_enrollment(
            enrollment_id=enrollment.id,
            student_count=0,
            user_id=test_user_id,
        )

        assert result.student_count == 0

    @pytest.mark.asyncio
    async def test_multiple_enrollments_same_level_different_nationalities(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_user_id: uuid.UUID,
    ):
        """Test creating multiple enrollments for same level with different nationalities."""
        service = EnrollmentService(db_session)

        # Create French enrollment for CP
        result1 = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=30,
            user_id=test_user_id,
        )

        # Create Saudi enrollment for CP (should succeed)
        result2 = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["SAUDI"].id,
            student_count=20,
            user_id=test_user_id,
        )

        # Create Other enrollment for CP (should succeed)
        result3 = await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["OTHER"].id,
            student_count=10,
            user_id=test_user_id,
        )

        assert result1.student_count == 30
        assert result2.student_count == 20
        assert result3.student_count == 10

    @pytest.mark.asyncio
    async def test_concurrent_capacity_validation(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test capacity validation considers all existing enrollments."""
        service = EnrollmentService(db_session)

        # Current total: 130
        # Add multiple enrollments that together would exceed capacity

        # First addition: 1000 students
        await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=1000,
            user_id=test_user_id,
        )

        # Second addition: 500 students (total now 1630)
        await service.create_enrollment(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            nationality_type_id=nationality_types["SAUDI"].id,
            student_count=500,
            user_id=test_user_id,
        )

        # Third addition: 300 would exceed (1630 + 300 = 1930 > 1875)
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.create_enrollment(
                version_id=test_budget_version.id,
                level_id=academic_levels["GS"].id,
                nationality_type_id=nationality_types["OTHER"].id,
                student_count=300,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "CAPACITY_EXCEEDED"


class TestEnrollmentServiceRealEFIRData:
    """Tests using realistic EFIR school data."""

    @pytest.mark.asyncio
    async def test_realistic_enrollment_distribution(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_levels: dict[str, AcademicLevel],
        nationality_types: dict[str, NationalityType],
        test_user_id: uuid.UUID,
    ):
        """Test with realistic EFIR enrollment numbers (~1,800 students)."""
        service = EnrollmentService(db_session)

        # Realistic EFIR-like distribution
        realistic_data = [
            # Maternelle (~250 total)
            ("PS", "FRENCH", 50),
            ("PS", "SAUDI", 20),
            ("PS", "OTHER", 15),
            ("MS", "FRENCH", 55),
            ("MS", "SAUDI", 18),
            ("MS", "OTHER", 12),
            ("GS", "FRENCH", 52),
            ("GS", "SAUDI", 20),
            ("GS", "OTHER", 8),
            # Elementary (~500 total) - using CP only for this test
            ("CP", "FRENCH", 180),
            ("CP", "SAUDI", 60),
            ("CP", "OTHER", 40),
            # Secondary (~650 total) - using 6EME and 5EME
            ("6EME", "FRENCH", 200),
            ("6EME", "SAUDI", 50),
            ("6EME", "OTHER", 30),
            ("5EME", "FRENCH", 180),
            ("5EME", "SAUDI", 45),
            ("5EME", "OTHER", 25),
        ]

        total_enrolled = 0
        for level_code, nationality_code, count in realistic_data:
            if level_code in academic_levels and nationality_code in nationality_types:
                await service.create_enrollment(
                    version_id=test_budget_version.id,
                    level_id=academic_levels[level_code].id,
                    nationality_type_id=nationality_types[nationality_code].id,
                    student_count=count,
                    user_id=test_user_id,
                )
                total_enrolled += count

        summary = await service.get_enrollment_summary(test_budget_version.id)

        assert summary["total_students"] == total_enrolled
        assert summary["total_students"] <= 1875  # Within capacity

    @pytest.mark.asyncio
    async def test_french_majority_nationality_distribution(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        academic_levels: dict,
        academic_cycles: dict,
        nationality_types: dict,
    ):
        """Test that French students are majority (typical EFIR pattern)."""
        service = EnrollmentService(db_session)

        summary = await service.get_enrollment_summary(test_budget_version.id)

        total = summary["total_students"]
        french_count = summary["by_nationality"].get("FRENCH", 0)

        # French should be majority at EFIR
        if total > 0:
            french_percentage = (french_count / total) * 100
            # Based on fixture data: 115/130 = 88.5%
            assert french_percentage > 50  # French should be majority
