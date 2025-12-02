"""
KPI Service for calculating and managing Key Performance Indicators.

Implements business logic for:
- KPI calculation (H/E ratio, E/D ratio, cost/revenue per student, margins, etc.)
- KPI trend analysis across budget versions
- AEFE benchmark comparison
- KPI storage and retrieval
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_kpi_dashboard
from app.models.analysis import KPICategory, KPIDefinition, KPIValue
from app.models.configuration import BudgetVersion
from app.services.base import BaseService
from app.services.exceptions import NotFoundError, ValidationError


class KPIService:
    """
    Service for KPI calculations and management.

    Provides methods for calculating educational and financial KPIs,
    comparing to AEFE benchmarks, and analyzing trends across versions.
    """

    # AEFE Benchmark Values
    AEFE_BENCHMARKS = {
        "H_E_PRIMARY": {"min": Decimal("1.0"), "max": Decimal("1.2"), "target": Decimal("1.1")},
        "H_E_SECONDARY": {"min": Decimal("1.8"), "max": Decimal("2.2"), "target": Decimal("2.0")},
        "E_D_PRIMARY": {"min": Decimal("20"), "max": Decimal("25"), "target": Decimal("22.5")},
        "E_D_SECONDARY": {"min": Decimal("24"), "max": Decimal("28"), "target": Decimal("26")},
        "STAFF_COST_PCT": {"min": Decimal("60"), "max": Decimal("75"), "target": Decimal("67.5")},
        "OPERATING_MARGIN": {"min": Decimal("5"), "max": Decimal("10"), "target": Decimal("7.5")},
    }

    def __init__(self, session: AsyncSession):
        """
        Initialize KPI service.

        Args:
            session: Async database session
        """
        self.session = session
        self.kpi_definition_service = BaseService(KPIDefinition, session)
        self.kpi_value_service = BaseService(KPIValue, session)

    async def get_kpi_definition(self, code: str) -> KPIDefinition:
        """
        Get KPI definition by code.

        Args:
            code: KPI code (e.g., 'H_E_RATIO', 'STAFF_COST_PCT')

        Returns:
            KPIDefinition instance

        Raises:
            NotFoundError: If definition not found
        """
        query = select(KPIDefinition).where(
            and_(
                KPIDefinition.code == code,
                KPIDefinition.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError("KPIDefinition", code)

        return definition

    async def get_all_kpi_definitions(
        self,
        category: KPICategory | None = None,
        active_only: bool = True,
    ) -> list[KPIDefinition]:
        """
        Get all KPI definitions.

        Args:
            category: Filter by KPI category
            active_only: Only return active KPIs

        Returns:
            List of KPIDefinition instances
        """
        query = select(KPIDefinition).where(KPIDefinition.deleted_at.is_(None))

        if category:
            query = query.where(KPIDefinition.category == category)

        if active_only:
            query = query.where(KPIDefinition.is_active is True)

        query = query.order_by(KPIDefinition.category, KPIDefinition.code)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    @cache_kpi_dashboard(ttl="5m")
    async def calculate_kpis(
        self,
        budget_version_id: uuid.UUID,
        kpi_codes: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Calculate all KPIs or specific KPIs for a budget version.

        Results are cached for 5 minutes for dashboard performance.

        Args:
            budget_version_id: Budget version UUID (used as cache key)
            kpi_codes: Optional list of specific KPI codes to calculate

        Returns:
            Dictionary mapping KPI codes to calculation results with:
                - calculated_value: The calculated KPI value
                - variance_from_target: Difference from target
                - variance_percent: Percentage variance
                - calculation_inputs: Inputs used in calculation

        Raises:
            NotFoundError: If budget version not found
            ValidationError: If calculation fails
        """
        # Verify budget version exists
        query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        result = await self.session.execute(query)
        version = result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Get aggregated data for calculations
        kpi_data = await self._get_kpi_calculation_data(budget_version_id)

        # Get KPI definitions to calculate
        if kpi_codes:
            definitions = []
            for code in kpi_codes:
                definitions.append(await self.get_kpi_definition(code))
        else:
            definitions = await self.get_all_kpi_definitions(active_only=True)

        # Calculate each KPI
        results = {}
        for definition in definitions:
            try:
                calculation_result = await self._calculate_single_kpi(
                    definition, kpi_data
                )
                results[definition.code] = calculation_result
            except Exception as e:
                raise ValidationError(
                    f"Failed to calculate KPI {definition.code}: {e!s}"
                )

        return results

    async def save_kpi_values(
        self,
        budget_version_id: uuid.UUID,
        kpi_results: dict[str, dict[str, Any]],
    ) -> list[KPIValue]:
        """
        Save calculated KPI values to database.

        Args:
            budget_version_id: Budget version UUID
            kpi_results: KPI calculation results from calculate_kpis()

        Returns:
            List of saved KPIValue instances
        """
        saved_values = []

        for kpi_code, result in kpi_results.items():
            # Get definition
            definition = await self.get_kpi_definition(kpi_code)

            # Check if value already exists
            query = select(KPIValue).where(
                and_(
                    KPIValue.budget_version_id == budget_version_id,
                    KPIValue.kpi_definition_id == definition.id,
                    KPIValue.deleted_at.is_(None),
                )
            )
            existing_result = await self.session.execute(query)
            existing_value = existing_result.scalar_one_or_none()

            if existing_value:
                # Update existing
                existing_value.calculated_value = result["calculated_value"]
                existing_value.variance_from_target = result.get("variance_from_target")
                existing_value.variance_percent = result.get("variance_percent")
                existing_value.calculation_inputs = result["calculation_inputs"]
                existing_value.calculated_at = datetime.utcnow()
                saved_values.append(existing_value)
            else:
                # Create new
                kpi_value = KPIValue(
                    budget_version_id=budget_version_id,
                    kpi_definition_id=definition.id,
                    calculated_value=result["calculated_value"],
                    variance_from_target=result.get("variance_from_target"),
                    variance_percent=result.get("variance_percent"),
                    calculation_inputs=result["calculation_inputs"],
                    calculated_at=datetime.utcnow(),
                )
                self.session.add(kpi_value)
                saved_values.append(kpi_value)

        await self.session.flush()

        # Refresh all to get relationships
        for value in saved_values:
            await self.session.refresh(value)

        return saved_values

    async def get_kpi_by_type(
        self,
        budget_version_id: uuid.UUID,
        kpi_code: str,
    ) -> KPIValue | None:
        """
        Get specific KPI value for a budget version.

        Args:
            budget_version_id: Budget version UUID
            kpi_code: KPI code

        Returns:
            KPIValue instance or None if not found

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads kpi_definition, budget_version, and audit fields
            - Leverages idx_kpi_values_version_def index
        """
        # Get definition first
        definition = await self.get_kpi_definition(kpi_code)

        query = (
            select(KPIValue)
            .where(
                and_(
                    KPIValue.budget_version_id == budget_version_id,
                    KPIValue.kpi_definition_id == definition.id,
                    KPIValue.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(KPIValue.kpi_definition),
                selectinload(KPIValue.budget_version),
                selectinload(KPIValue.created_by),
                selectinload(KPIValue.updated_by),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_kpis(
        self,
        budget_version_id: uuid.UUID,
        category: KPICategory | None = None,
    ) -> list[KPIValue]:
        """
        Get all calculated KPIs for a budget version.

        Args:
            budget_version_id: Budget version UUID
            category: Optional filter by category

        Returns:
            List of KPIValue instances

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads kpi_definition, budget_version, and audit fields
            - Leverages idx_kpi_values_version_def index
        """
        query = (
            select(KPIValue)
            .where(
                and_(
                    KPIValue.budget_version_id == budget_version_id,
                    KPIValue.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(KPIValue.kpi_definition),
                selectinload(KPIValue.budget_version),
                selectinload(KPIValue.created_by),
                selectinload(KPIValue.updated_by),
            )
        )

        if category:
            query = query.join(KPIValue.kpi_definition).where(
                KPIDefinition.category == category
            )

        query = query.order_by(KPIDefinition.category, KPIDefinition.code)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_kpi_trends(
        self,
        version_ids: list[uuid.UUID],
        kpi_code: str,
    ) -> list[dict[str, Any]]:
        """
        Get KPI trend across multiple budget versions.

        Args:
            version_ids: List of budget version UUIDs (chronological order)
            kpi_code: KPI code to analyze

        Returns:
            List of dictionaries with version info and KPI values
        """
        definition = await self.get_kpi_definition(kpi_code)

        trends = []
        for version_id in version_ids:
            # Get version
            version_query = select(BudgetVersion).where(BudgetVersion.id == version_id)
            version_result = await self.session.execute(version_query)
            version = version_result.scalar_one_or_none()

            if not version:
                continue

            # Get KPI value
            kpi_query = (
                select(KPIValue)
                .where(
                    and_(
                        KPIValue.budget_version_id == version_id,
                        KPIValue.kpi_definition_id == definition.id,
                        KPIValue.deleted_at.is_(None),
                    )
                )
                .options(selectinload(KPIValue.kpi_definition))
            )
            kpi_result = await self.session.execute(kpi_query)
            kpi_value = kpi_result.scalar_one_or_none()

            trends.append(
                {
                    "version_id": str(version_id),
                    "version_name": version.name,
                    "fiscal_year": version.fiscal_year,
                    "status": version.status.value,
                    "calculated_value": (
                        float(kpi_value.calculated_value) if kpi_value else None
                    ),
                    "variance_from_target": (
                        float(kpi_value.variance_from_target)
                        if kpi_value and kpi_value.variance_from_target
                        else None
                    ),
                    "calculated_at": (
                        kpi_value.calculated_at.isoformat() if kpi_value else None
                    ),
                }
            )

        return trends

    async def get_benchmark_comparison(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Compare budget version KPIs to AEFE benchmarks.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Dictionary with KPI codes and benchmark comparison data
        """
        # Get all KPIs for version
        kpi_values = await self.get_all_kpis(budget_version_id)

        comparison = {}
        for kpi_value in kpi_values:
            code = kpi_value.kpi_definition.code

            # Get AEFE benchmark if available
            benchmark = self.AEFE_BENCHMARKS.get(code)

            if benchmark:
                value = float(kpi_value.calculated_value)
                target = float(benchmark["target"])
                min_val = float(benchmark["min"])
                max_val = float(benchmark["max"])

                # Determine status
                if min_val <= value <= max_val:
                    status = "within_range"
                elif value < min_val:
                    status = "below_range"
                else:
                    status = "above_range"

                comparison[code] = {
                    "kpi_name": kpi_value.kpi_definition.name_en,
                    "calculated_value": value,
                    "benchmark_target": target,
                    "benchmark_min": min_val,
                    "benchmark_max": max_val,
                    "variance_from_target": value - target,
                    "variance_percent": ((value - target) / target * 100) if target else 0,
                    "status": status,
                    "unit": kpi_value.kpi_definition.unit,
                }
            else:
                # No benchmark available
                comparison[code] = {
                    "kpi_name": kpi_value.kpi_definition.name_en,
                    "calculated_value": float(kpi_value.calculated_value),
                    "benchmark_target": None,
                    "status": "no_benchmark",
                    "unit": kpi_value.kpi_definition.unit,
                }

        return comparison

    async def _get_kpi_calculation_data(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Aggregate data needed for KPI calculations.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Dictionary with aggregated data for calculations
        """
        # This would aggregate data from:
        # - EnrollmentPlan (student counts)
        # - ClassStructure (class counts)
        # - DHGSubjectHours (teaching hours)
        # - TeacherAllocation (FTE counts)
        # - RevenueConsolidation (revenue)
        # - CostConsolidation (costs, personnel costs)

        # For now, return a placeholder structure
        # This will be populated by querying related tables
        return {
            "total_students": 0,
            "primary_students": 0,
            "secondary_students": 0,
            "total_classes": 0,
            "primary_classes": 0,
            "secondary_classes": 0,
            "total_teaching_hours": Decimal("0"),
            "primary_teaching_hours": Decimal("0"),
            "secondary_teaching_hours": Decimal("0"),
            "total_teacher_fte": Decimal("0"),
            "primary_teacher_fte": Decimal("0"),
            "secondary_teacher_fte": Decimal("0"),
            "total_revenue_sar": Decimal("0"),
            "total_costs_sar": Decimal("0"),
            "personnel_costs_sar": Decimal("0"),
            "max_capacity": 1875,
        }

    async def _calculate_single_kpi(
        self,
        definition: KPIDefinition,
        kpi_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate a single KPI value.

        Args:
            definition: KPI definition
            kpi_data: Aggregated data for calculation

        Returns:
            Dictionary with calculation results
        """
        code = definition.code
        calculated_value = Decimal("0")
        calculation_inputs = {}

        # Calculate based on KPI type
        if code == "H_E_PRIMARY":
            # Hours per student - Primary
            if kpi_data["primary_students"] > 0:
                calculated_value = (
                    kpi_data["primary_teaching_hours"] / kpi_data["primary_students"]
                )
            calculation_inputs = {
                "primary_teaching_hours": str(kpi_data["primary_teaching_hours"]),
                "primary_students": kpi_data["primary_students"],
            }

        elif code == "H_E_SECONDARY":
            # Hours per student - Secondary
            if kpi_data["secondary_students"] > 0:
                calculated_value = (
                    kpi_data["secondary_teaching_hours"] / kpi_data["secondary_students"]
                )
            calculation_inputs = {
                "secondary_teaching_hours": str(kpi_data["secondary_teaching_hours"]),
                "secondary_students": kpi_data["secondary_students"],
            }

        elif code == "E_D_PRIMARY":
            # Students per class - Primary
            if kpi_data["primary_classes"] > 0:
                calculated_value = Decimal(str(kpi_data["primary_students"])) / Decimal(
                    str(kpi_data["primary_classes"])
                )
            calculation_inputs = {
                "primary_students": kpi_data["primary_students"],
                "primary_classes": kpi_data["primary_classes"],
            }

        elif code == "E_D_SECONDARY":
            # Students per class - Secondary
            if kpi_data["secondary_classes"] > 0:
                calculated_value = Decimal(
                    str(kpi_data["secondary_students"])
                ) / Decimal(str(kpi_data["secondary_classes"]))
            calculation_inputs = {
                "secondary_students": kpi_data["secondary_students"],
                "secondary_classes": kpi_data["secondary_classes"],
            }

        elif code == "COST_PER_STUDENT":
            # Cost per student
            if kpi_data["total_students"] > 0:
                calculated_value = kpi_data["total_costs_sar"] / Decimal(
                    str(kpi_data["total_students"])
                )
            calculation_inputs = {
                "total_costs_sar": str(kpi_data["total_costs_sar"]),
                "total_students": kpi_data["total_students"],
            }

        elif code == "REVENUE_PER_STUDENT":
            # Revenue per student
            if kpi_data["total_students"] > 0:
                calculated_value = kpi_data["total_revenue_sar"] / Decimal(
                    str(kpi_data["total_students"])
                )
            calculation_inputs = {
                "total_revenue_sar": str(kpi_data["total_revenue_sar"]),
                "total_students": kpi_data["total_students"],
            }

        elif code == "STAFF_COST_PCT":
            # Personnel cost as % of total revenue
            if kpi_data["total_revenue_sar"] > 0:
                calculated_value = (
                    kpi_data["personnel_costs_sar"]
                    / kpi_data["total_revenue_sar"]
                    * 100
                )
            calculation_inputs = {
                "personnel_costs_sar": str(kpi_data["personnel_costs_sar"]),
                "total_revenue_sar": str(kpi_data["total_revenue_sar"]),
            }

        elif code == "OPERATING_MARGIN":
            # Operating margin percentage
            if kpi_data["total_revenue_sar"] > 0:
                margin_sar = kpi_data["total_revenue_sar"] - kpi_data["total_costs_sar"]
                calculated_value = (
                    margin_sar / kpi_data["total_revenue_sar"] * 100
                )
            calculation_inputs = {
                "total_revenue_sar": str(kpi_data["total_revenue_sar"]),
                "total_costs_sar": str(kpi_data["total_costs_sar"]),
            }

        elif code == "CAPACITY_UTILIZATION":
            # Capacity utilization percentage
            if kpi_data["max_capacity"] > 0:
                calculated_value = Decimal(str(kpi_data["total_students"])) / Decimal(
                    str(kpi_data["max_capacity"])
                ) * 100
            calculation_inputs = {
                "total_students": kpi_data["total_students"],
                "max_capacity": kpi_data["max_capacity"],
            }

        # Calculate variance from target
        variance_from_target = None
        variance_percent = None
        if definition.target_value:
            variance_from_target = calculated_value - definition.target_value
            if definition.target_value != 0:
                variance_percent = (
                    variance_from_target / definition.target_value * 100
                )

        return {
            "calculated_value": calculated_value,
            "variance_from_target": variance_from_target,
            "variance_percent": variance_percent,
            "calculation_inputs": calculation_inputs,
        }
