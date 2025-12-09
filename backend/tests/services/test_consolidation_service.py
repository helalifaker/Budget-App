"""
Tests for ConsolidationService.

Tests cover:
- Budget consolidation across all planning modules
- Approval workflow (WORKING → SUBMITTED → APPROVED → SUPERSEDED)
- Version validation and completeness checks
- Line item rollup calculations
- Business rule validation
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.models.planning import (
    ClassStructure,
    EnrollmentPlan,
    OperatingCostPlan,
    PersonnelCostPlan,
    RevenuePlan,
)
from app.services.consolidation_service import ConsolidationService
from app.services.exceptions import BusinessRuleError, NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession


class TestConsolidationServiceGetConsolidation:
    """Tests for retrieving consolidated budget."""

    @pytest.mark.asyncio
    async def test_get_consolidation_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving empty consolidation."""
        service = ConsolidationService(db_session)

        result = await service.get_consolidation(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_consolidation_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving consolidation for non-existent version."""
        service = ConsolidationService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_consolidation(uuid.uuid4())


class TestConsolidationServiceConsolidate:
    """Tests for budget consolidation calculation."""

    @pytest.mark.asyncio
    async def test_consolidate_budget_with_revenue(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test consolidating budget with revenue entries."""
        # Create revenue entries
        revenue1 = RevenuePlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="70110",
            description="Tuition T1",
            category="tuition",
            amount_sar=Decimal("2000000.00"),
            trimester=1,
            created_by_id=test_user_id,
        )
        revenue2 = RevenuePlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="70120",
            description="Tuition T2",
            category="tuition",
            amount_sar=Decimal("1500000.00"),
            trimester=2,
            created_by_id=test_user_id,
        )
        db_session.add_all([revenue1, revenue2])
        await db_session.flush()

        service = ConsolidationService(db_session)
        result = await service.consolidate_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        assert len(result) >= 2  # At least 2 revenue entries
        revenue_entries = [e for e in result if e.is_revenue]
        assert len(revenue_entries) == 2

    @pytest.mark.asyncio
    async def test_consolidate_budget_with_personnel_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test consolidating budget with personnel cost entries."""
        # Create personnel cost entries
        cost1 = PersonnelCostPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="64110",
            description="Teaching Staff",
            fte_count=Decimal("20"),
            unit_cost_sar=Decimal("180000.00"),
            total_cost_sar=Decimal("3600000.00"),
            created_by_id=test_user_id,
        )
        db_session.add(cost1)
        await db_session.flush()

        service = ConsolidationService(db_session)
        result = await service.consolidate_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        cost_entries = [e for e in result if not e.is_revenue]
        assert len(cost_entries) >= 1

    @pytest.mark.asyncio
    async def test_consolidate_budget_replaces_existing(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that consolidation replaces existing entries."""
        # Create initial revenue
        revenue = RevenuePlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="70110",
            description="Tuition",
            category="tuition",
            amount_sar=Decimal("1000000.00"),
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = ConsolidationService(db_session)

        # First consolidation
        await service.consolidate_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        # Update revenue and consolidate again
        revenue.amount_sar = Decimal("1500000.00")
        await db_session.flush()

        await service.consolidate_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        # Should have replaced, not duplicated
        all_entries = await service.get_consolidation(test_budget_version.id)
        tuition_entries = [e for e in all_entries if e.account_code == "70110"]
        assert len(tuition_entries) == 1


class TestConsolidationServiceApprovalWorkflow:
    """Tests for budget approval workflow."""

    @pytest.mark.asyncio
    async def test_submit_for_approval_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
        test_user_id: uuid.UUID,
    ):
        """Test submitting budget for approval."""
        service = ConsolidationService(db_session)

        result = await service.submit_for_approval(
            test_budget_version.id,
            user_id=test_user_id,
        )

        assert result.status == BudgetVersionStatus.SUBMITTED
        assert result.submitted_at is not None
        assert result.submitted_by_id == test_user_id

    @pytest.mark.asyncio
    async def test_submit_for_approval_wrong_status(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
        test_user_id: uuid.UUID,
    ):
        """Test cannot submit if not WORKING status."""
        service = ConsolidationService(db_session)

        # First submit
        await service.submit_for_approval(
            test_budget_version.id,
            user_id=test_user_id,
        )

        # Try to submit again (now SUBMITTED)
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.submit_for_approval(
                test_budget_version.id,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "SUBMIT_WORKFLOW"
        assert "Only WORKING" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_for_approval_incomplete(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test cannot submit incomplete budget."""
        service = ConsolidationService(db_session)

        # No enrollment or class structure
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.submit_for_approval(
                test_budget_version.id,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "SUBMIT_COMPLETENESS"
        assert "enrollment" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_budget_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
        test_user_id: uuid.UUID,
    ):
        """Test approving submitted budget."""
        service = ConsolidationService(db_session)

        # First submit
        await service.submit_for_approval(
            test_budget_version.id,
            user_id=test_user_id,
        )

        # Then approve
        result = await service.approve_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        assert result.status == BudgetVersionStatus.APPROVED
        assert result.approved_at is not None
        assert result.approved_by_id == test_user_id
        assert result.is_baseline is True

    @pytest.mark.asyncio
    async def test_approve_budget_wrong_status(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test cannot approve if not SUBMITTED status."""
        service = ConsolidationService(db_session)

        # Try to approve WORKING budget
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.approve_budget(
                test_budget_version.id,
                user_id=test_user_id,
            )

        assert exc_info.value.details["rule"] == "APPROVE_WORKFLOW"
        assert "Only SUBMITTED" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_supersedes_previous(
        self,
        db_session: AsyncSession,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
        test_user_id: uuid.UUID,
    ):
        """Test approving new budget supersedes previous approved."""
        service = ConsolidationService(db_session)

        # Create first budget version and approve
        version1 = BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Budget v1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        db_session.add(version1)
        await db_session.flush()

        # Add enrollment and class structure for version1
        enrollment1 = EnrollmentPlan(
            id=uuid.uuid4(),
            budget_version_id=version1.id,
            level_id=test_enrollment_data[0].level_id,
            nationality_type_id=test_enrollment_data[0].nationality_type_id,
            student_count=50,
            created_by_id=test_user_id,
        )
        class1 = ClassStructure(
            id=uuid.uuid4(),
            budget_version_id=version1.id,
            level_id=test_enrollment_data[0].level_id,
            total_students=50,
            number_of_classes=2,
            avg_class_size=Decimal("25"),
            created_by_id=test_user_id,
        )
        db_session.add_all([enrollment1, class1])
        await db_session.flush()

        # Submit and approve version1
        await service.submit_for_approval(version1.id, test_user_id)
        await service.approve_budget(version1.id, test_user_id)

        # Create second budget version
        version2 = BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Budget v2",
            fiscal_year=2025,  # Same fiscal year
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        db_session.add(version2)
        await db_session.flush()

        # Add enrollment and class structure for version2
        enrollment2 = EnrollmentPlan(
            id=uuid.uuid4(),
            budget_version_id=version2.id,
            level_id=test_enrollment_data[0].level_id,
            nationality_type_id=test_enrollment_data[0].nationality_type_id,
            student_count=60,
            created_by_id=test_user_id,
        )
        class2 = ClassStructure(
            id=uuid.uuid4(),
            budget_version_id=version2.id,
            level_id=test_enrollment_data[0].level_id,
            total_students=60,
            number_of_classes=2,
            avg_class_size=Decimal("30"),
            created_by_id=test_user_id,
        )
        db_session.add_all([enrollment2, class2])
        await db_session.flush()

        # Submit and approve version2
        await service.submit_for_approval(version2.id, test_user_id)
        await service.approve_budget(version2.id, test_user_id)

        # Refresh version1
        await db_session.refresh(version1)

        # version1 should be superseded
        assert version1.status == BudgetVersionStatus.SUPERSEDED
        assert version1.is_baseline is False


class TestConsolidationServiceValidation:
    """Tests for validation methods."""

    @pytest.mark.asyncio
    async def test_validate_completeness_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test validation with no planning data."""
        service = ConsolidationService(db_session)

        result = await service.validate_completeness(test_budget_version.id)

        assert result["is_complete"] is False
        assert "enrollment" in result["missing_modules"]
        assert "class_structure" in result["missing_modules"]

    @pytest.mark.asyncio
    async def test_validate_completeness_with_enrollment(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
    ):
        """Test validation with enrollment only."""
        service = ConsolidationService(db_session)

        result = await service.validate_completeness(test_budget_version.id)

        assert "enrollment" not in result["missing_modules"]
        assert "class_structure" in result["missing_modules"]
        assert result["module_counts"]["enrollment"] == len(test_enrollment_data)

    @pytest.mark.asyncio
    async def test_validate_completeness_complete(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
    ):
        """Test validation with complete required modules."""
        service = ConsolidationService(db_session)

        result = await service.validate_completeness(test_budget_version.id)

        assert result["is_complete"] is True
        assert result["missing_modules"] == []
        assert result["module_counts"]["enrollment"] > 0
        assert result["module_counts"]["class_structure"] > 0

    @pytest.mark.asyncio
    async def test_validate_completeness_warnings(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
    ):
        """Test validation returns warnings for optional missing data."""
        service = ConsolidationService(db_session)

        result = await service.validate_completeness(test_budget_version.id)

        # Should have warnings for missing revenue, costs (optional but warned)
        assert len(result["warnings"]) > 0
        assert result["module_counts"]["revenue"] == 0
        assert result["module_counts"]["personnel_costs"] == 0


class TestConsolidationServiceLineItems:
    """Tests for line item calculations."""

    @pytest.mark.asyncio
    async def test_calculate_line_items_revenue(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test revenue line item calculation."""
        # Create revenue entries
        revenues = [
            RevenuePlan(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                account_code="70110",
                description="Tuition T1",
                category="tuition",
                amount_sar=Decimal("1000000"),
                created_by_id=test_user_id,
            ),
            RevenuePlan(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                account_code="70120",
                description="Tuition T2",
                category="tuition",
                amount_sar=Decimal("750000"),
                created_by_id=test_user_id,
            ),
            RevenuePlan(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                account_code="70200",
                description="DAI",
                category="fees",
                amount_sar=Decimal("250000"),
                created_by_id=test_user_id,
            ),
        ]
        db_session.add_all(revenues)
        await db_session.flush()

        service = ConsolidationService(db_session)
        line_items = await service.calculate_line_items(test_budget_version.id)

        revenue_items = [item for item in line_items if item["is_revenue"]]
        assert len(revenue_items) == 3

        total_revenue = sum(item["amount_sar"] for item in revenue_items)
        assert total_revenue == Decimal("2000000")

    @pytest.mark.asyncio
    async def test_calculate_line_items_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test cost line item calculation."""
        # Create cost entries
        personnel = PersonnelCostPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="64110",
            description="Teaching Staff",
            fte_count=Decimal("10"),
            unit_cost_sar=Decimal("180000"),
            total_cost_sar=Decimal("1800000"),
            created_by_id=test_user_id,
        )
        operating = OperatingCostPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="60610",
            description="Supplies",
            category="supplies",
            amount_sar=Decimal("200000"),
            created_by_id=test_user_id,
        )
        db_session.add_all([personnel, operating])
        await db_session.flush()

        service = ConsolidationService(db_session)
        line_items = await service.calculate_line_items(test_budget_version.id)

        cost_items = [item for item in line_items if not item["is_revenue"]]
        assert len(cost_items) == 2

        total_cost = sum(item["amount_sar"] for item in cost_items)
        assert total_cost == Decimal("2000000")


class TestConsolidationServiceRealEFIRData:
    """Tests using realistic EFIR budget data."""

    @pytest.mark.asyncio
    async def test_full_budget_consolidation(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_class_structure: list[ClassStructure],
        test_user_id: uuid.UUID,
    ):
        """Test full budget consolidation with realistic data."""
        # Create realistic revenue (54M SAR tuition)
        for trimester, pct in [(1, "0.40"), (2, "0.30"), (3, "0.30")]:
            revenue = RevenuePlan(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                account_code=f"7011{trimester}",
                description=f"Scolarité T{trimester}",
                category="tuition",
                amount_sar=Decimal("54000000") * Decimal(pct),
                trimester=trimester,
                created_by_id=test_user_id,
            )
            db_session.add(revenue)

        # DAI revenue (5.4M SAR)
        dai = RevenuePlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="70200",
            description="DAI",
            category="fees",
            amount_sar=Decimal("5400000"),
            created_by_id=test_user_id,
        )
        db_session.add(dai)

        # Personnel costs (30M SAR)
        personnel = PersonnelCostPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="64110",
            description="Teaching Staff",
            fte_count=Decimal("100"),
            unit_cost_sar=Decimal("300000"),
            total_cost_sar=Decimal("30000000"),
            created_by_id=test_user_id,
        )
        db_session.add(personnel)

        # Operating costs (5M SAR)
        operating = OperatingCostPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="60610",
            description="Operating Expenses",
            category="supplies",
            amount_sar=Decimal("5000000"),
            created_by_id=test_user_id,
        )
        db_session.add(operating)

        await db_session.flush()

        service = ConsolidationService(db_session)
        result = await service.consolidate_budget(
            test_budget_version.id,
            user_id=test_user_id,
        )

        # Verify consolidation
        revenue_items = [e for e in result if e.is_revenue]
        cost_items = [e for e in result if not e.is_revenue]

        total_revenue = sum(e.amount_sar for e in revenue_items)
        total_cost = sum(e.amount_sar for e in cost_items)

        # Revenue: 54M + 5.4M = 59.4M
        assert total_revenue == Decimal("59400000")

        # Costs: 30M + 5M = 35M
        assert total_cost == Decimal("35000000")

        # Net surplus: 59.4M - 35M = 24.4M
        net = total_revenue - total_cost
        assert net == Decimal("24400000")
