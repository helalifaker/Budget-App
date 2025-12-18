"""
Consolidation service for budget consolidation operations.

Handles budget consolidation across all planning modules, approval workflow,
version management, validation, and line item rollup calculations.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models import (
    BudgetConsolidation,
    CapExPlan,
    ConsolidationCategory,
    OperatingCostPlan,
    PersonnelCostPlan,
    RevenuePlan,
    Version,
    VersionStatus,
)
from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    ServiceException,
)

# Backward compatibility aliases
BudgetVersion = Version
BudgetVersionStatus = VersionStatus


class ConsolidationService:
    """
    Service for budget consolidation operations.

    Provides business logic for:
    - Budget consolidation across all modules
    - Approval workflow management
    - Version validation and completeness checks
    - Line item rollup and calculations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize consolidation service.

        Args:
            session: Async database session
        """
        self.session = session
        self.consolidation_service = BaseService(BudgetConsolidation, session)
        self.version_service = BaseService(Version, session)

    async def get_consolidation(
        self,
        version_id: uuid.UUID,
    ) -> list[BudgetConsolidation]:
        """
        Get consolidated budget for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of BudgetConsolidation instances with all line items

        Raises:
            NotFoundError: If budget version not found

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads version and audit fields
            - Leverages idx_consolidation_version_account index
        """
        # Verify version exists
        await self.version_service.get_by_id(version_id)

        # Get all consolidation entries with eager loading
        query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.version_id == version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(BudgetConsolidation.version),
                # Note: created_by and updated_by are FKs, not relationships
            )
            .order_by(
                BudgetConsolidation.is_revenue.desc(),
                BudgetConsolidation.consolidation_category,
                BudgetConsolidation.account_code,
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def consolidate_budget(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> list[BudgetConsolidation]:
        """
        Calculate consolidated budget by aggregating all planning modules.

        This is the core consolidation operation that:
        1. Aggregates revenue from RevenuePlan
        2. Aggregates personnel costs from PersonnelCostPlan
        3. Aggregates operating costs from OperatingCostPlan
        4. Aggregates CapEx from CapExPlan
        5. Creates/updates BudgetConsolidation entries

        Args:
            version_id: Budget version UUID
            user_id: User ID for audit trail

        Returns:
            List of created/updated BudgetConsolidation instances

        Raises:
            NotFoundError: If budget version not found
            ValidationError: If consolidation fails
            ServiceException: If database operations fail
        """
        try:
            # Verify version exists
            await self.version_service.get_by_id(version_id)

            # Delete existing consolidation entries for this version
            await self._delete_existing_consolidation(version_id)

            # Calculate line items from all sources
            consolidation_entries = await self.calculate_line_items(version_id)

            # Create consolidation entries
            created_entries = []
            for entry_data in consolidation_entries:
                entry = await self.consolidation_service.create(
                    entry_data,
                    user_id=user_id,
                )
                created_entries.append(entry)

            # Commit the session
            await self.session.flush()

            logger.info(
                "Budget consolidation completed successfully",
                version_id=str(version_id),
                entries_created=len(created_entries),
            )

            return created_entries
        except SQLAlchemyError as e:
            logger.error(
                "Failed to consolidate budget",
                version_id=str(version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to consolidate budget. Please try again.",
                status_code=500,
                details={"version_id": str(version_id)},
            ) from e

    async def submit_for_approval(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Submit budget version for approval.

        Business Rules:
        - Can only submit if status is WORKING
        - Must validate completeness before submission

        Args:
            version_id: Budget version UUID
            user_id: User ID submitting the budget

        Returns:
            Updated BudgetVersion instance

        Raises:
            NotFoundError: If budget version not found
            BusinessRuleError: If budget cannot be submitted
        """
        # Get version
        version = await self.version_service.get_by_id(version_id)

        # Validate status
        if version.status != VersionStatus.WORKING:
            raise BusinessRuleError(
                rule="SUBMIT_WORKFLOW",
                message=f"Cannot submit budget with status '{version.status.value}'. "
                f"Only WORKING budgets can be submitted.",
                details={"current_status": version.status.value},
            )

        # Validate completeness
        validation = await self.validate_completeness(version_id)
        if not validation["is_complete"]:
            raise BusinessRuleError(
                rule="SUBMIT_COMPLETENESS",
                message="Cannot submit incomplete budget. Missing modules: "
                f"{', '.join(validation['missing_modules'])}",
                details=validation,
            )

        # Update status
        updated = await self.version_service.update(
            version_id,
            {
                "status": VersionStatus.SUBMITTED,
                "submitted_at": datetime.utcnow(),
                "submitted_by_id": user_id,
            },
            user_id=user_id,
        )

        return updated

    async def approve_budget(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Approve budget version.

        Business Rules:
        - Can only approve if status is SUBMITTED
        - Approved budgets become APPROVED (can optionally set as BASELINE)
        - Previous APPROVED versions should be marked as SUPERSEDED

        Args:
            version_id: Budget version UUID
            user_id: User ID approving the budget

        Returns:
            Updated BudgetVersion instance

        Raises:
            NotFoundError: If budget version not found
            BusinessRuleError: If budget cannot be approved
        """
        # Get version
        version = await self.version_service.get_by_id(version_id)

        # Validate status
        if version.status != VersionStatus.SUBMITTED:
            raise BusinessRuleError(
                rule="APPROVE_WORKFLOW",
                message=f"Cannot approve budget with status '{version.status.value}'. "
                f"Only SUBMITTED budgets can be approved.",
                details={"current_status": version.status.value},
            )

        # Mark previous approved versions for the same fiscal year as superseded
        await self._supersede_previous_versions(
            version.fiscal_year,
            version_id,
        )

        # Update status
        updated = await self.version_service.update(
            version_id,
            {
                "status": VersionStatus.APPROVED,
                "approved_at": datetime.utcnow(),
                "approved_by_id": user_id,
                "is_baseline": True,  # Newly approved becomes baseline
            },
            user_id=user_id,
        )

        return updated

    async def calculate_line_items(
        self,
        version_id: uuid.UUID,
    ) -> list[dict]:
        """
        Calculate all consolidated line items by aggregating from source tables.

        Aggregates:
        1. Revenue from finance_revenue_plans (account_code, category)
        2. Personnel costs from finance_personnel_cost_plans (account_code, category)
        3. Operating costs from finance_operating_cost_plans (account_code, category)
        4. CapEx from finance_capex_plans (account_code, category)

        Args:
            version_id: Budget version UUID

        Returns:
            List of dictionaries with consolidation data ready for creation
        """
        consolidation_data = []

        # 1. Aggregate Revenue
        revenue_items = await self._aggregate_revenue(version_id)
        consolidation_data.extend(revenue_items)

        # 2. Aggregate Personnel Costs
        personnel_items = await self._aggregate_personnel_costs(version_id)
        consolidation_data.extend(personnel_items)

        # 3. Aggregate Operating Costs
        operating_items = await self._aggregate_operating_costs(version_id)
        consolidation_data.extend(operating_items)

        # 4. Aggregate CapEx
        capex_items = await self._aggregate_capex(version_id)
        consolidation_data.extend(capex_items)

        return consolidation_data

    async def validate_completeness(
        self,
        version_id: uuid.UUID,
    ) -> dict[str, any]:
        """
        Validate that all required modules are complete for budget version.

        Checks:
        - Enrollment planning exists
        - Class structure exists
        - Revenue planning exists
        - Personnel costs exist
        - Operating costs exist

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with validation results:
            {
                "is_complete": bool,
                "missing_modules": list[str],
                "warnings": list[str],
                "module_counts": dict[str, int]
            }
        """
        missing_modules = []
        warnings = []
        module_counts = {}

        # Check enrollment
        enrollment_count = await self._count_records("students_enrollment_plans", version_id)
        module_counts["enrollment"] = enrollment_count
        if enrollment_count == 0:
            missing_modules.append("enrollment")

        # Check class structure
        class_count = await self._count_records("students_class_structures", version_id)
        module_counts["class_structure"] = class_count
        if class_count == 0:
            missing_modules.append("class_structure")

        # Check revenue
        revenue_count = await self._count_records("finance_revenue_plans", version_id)
        module_counts["revenue"] = revenue_count
        if revenue_count == 0:
            warnings.append("No revenue entries found")

        # Check personnel costs
        personnel_count = await self._count_records("finance_personnel_cost_plans", version_id)
        module_counts["personnel_costs"] = personnel_count
        if personnel_count == 0:
            warnings.append("No personnel cost entries found")

        # Check operating costs
        operating_count = await self._count_records("finance_operating_cost_plans", version_id)
        module_counts["operating_costs"] = operating_count
        if operating_count == 0:
            warnings.append("No operating cost entries found")

        # Check CapEx (optional, so just count)
        capex_count = await self._count_records("finance_capex_plans", version_id)
        module_counts["capex"] = capex_count

        return {
            "is_complete": len(missing_modules) == 0,
            "missing_modules": missing_modules,
            "warnings": warnings,
            "module_counts": module_counts,
        }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _delete_existing_consolidation(
        self,
        version_id: uuid.UUID,
    ) -> None:
        """Delete all existing consolidation entries for a version."""
        existing = await self.consolidation_service.get_all(
            filters={"version_id": version_id}
        )
        for entry in existing:
            await self.consolidation_service.delete(entry.id)

    async def _supersede_previous_versions(
        self,
        fiscal_year: int,
        exclude_version_id: uuid.UUID,
    ) -> None:
        """Mark previous approved versions as superseded."""
        query = (
            select(BudgetVersion)
            .where(
                and_(
                    BudgetVersion.fiscal_year == fiscal_year,
                    BudgetVersion.id != exclude_version_id,
                    BudgetVersion.status == BudgetVersionStatus.APPROVED,
                    BudgetVersion.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(query)
        previous_versions = result.scalars().all()

        for prev_version in previous_versions:
            await self.version_service.update(
                prev_version.id,
                {
                    "status": VersionStatus.SUPERSEDED,
                    "is_baseline": False,
                },
            )

    async def _count_records(
        self,
        table_name: str,
        version_id: uuid.UUID,
    ) -> int:
        """Count records in a planning table for a budget version."""
        # Map table names to model classes (uses new prefixed table names)
        from app.models import (
            CapExPlan,
            ClassStructure,
            EnrollmentPlan,
            OperatingCostPlan,
            PersonnelCostPlan,
            RevenuePlan,
        )

        model_map = {
            "students_enrollment_plans": EnrollmentPlan,
            "students_class_structures": ClassStructure,
            "finance_revenue_plans": RevenuePlan,
            "finance_personnel_cost_plans": PersonnelCostPlan,
            "finance_operating_cost_plans": OperatingCostPlan,
            "finance_capex_plans": CapExPlan,
        }

        # Get the model class
        model_class = model_map[table_name]

        # Count records
        query = select(func.count()).select_from(model_class).where(
            and_(
                model_class.version_id == version_id,
                model_class.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def _aggregate_revenue(
        self,
        version_id: uuid.UUID,
    ) -> list[dict]:
        """Aggregate revenue from finance_revenue_plans."""
        query = (
            select(
                RevenuePlan.account_code,
                RevenuePlan.description,
                RevenuePlan.category,
                func.sum(RevenuePlan.amount_sar).label("total_amount"),
                func.count(RevenuePlan.id).label("source_count"),
            )
            .where(
                and_(
                    RevenuePlan.version_id == version_id,
                    RevenuePlan.deleted_at.is_(None),
                )
            )
            .group_by(
                RevenuePlan.account_code,
                RevenuePlan.description,
                RevenuePlan.category,
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        consolidation_data = []
        for row in rows:
            # Map revenue category to consolidation category
            consolidation_category = self._map_revenue_to_consolidation_category(
                row.account_code,
                row.category,
            )

            consolidation_data.append({
                "version_id": version_id,
                "account_code": row.account_code,
                "account_name": row.description,
                "consolidation_category": consolidation_category,
                "is_revenue": True,
                "amount_sar": row.total_amount or Decimal("0.00"),
                "source_table": "finance_revenue_plans",
                "source_count": row.source_count,
                "is_calculated": True,
            })

        return consolidation_data

    async def _aggregate_personnel_costs(
        self,
        version_id: uuid.UUID,
    ) -> list[dict]:
        """Aggregate personnel costs from finance_personnel_cost_plans."""
        query = (
            select(
                PersonnelCostPlan.account_code,
                PersonnelCostPlan.description,
                func.sum(PersonnelCostPlan.total_cost_sar).label("total_amount"),
                func.count(PersonnelCostPlan.id).label("source_count"),
            )
            .where(
                and_(
                    PersonnelCostPlan.version_id == version_id,
                    PersonnelCostPlan.deleted_at.is_(None),
                )
            )
            .group_by(
                PersonnelCostPlan.account_code,
                PersonnelCostPlan.description,
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        consolidation_data = []
        for row in rows:
            # Map personnel category to consolidation category
            consolidation_category = self._map_personnel_to_consolidation_category(
                row.account_code,
            )

            consolidation_data.append({
                "version_id": version_id,
                "account_code": row.account_code,
                "account_name": row.description,
                "consolidation_category": consolidation_category,
                "is_revenue": False,
                "amount_sar": row.total_amount or Decimal("0.00"),
                "source_table": "finance_personnel_cost_plans",
                "source_count": row.source_count,
                "is_calculated": True,
            })

        return consolidation_data

    async def _aggregate_operating_costs(
        self,
        version_id: uuid.UUID,
    ) -> list[dict]:
        """Aggregate operating costs from finance_operating_cost_plans."""
        query = (
            select(
                OperatingCostPlan.account_code,
                OperatingCostPlan.description,
                OperatingCostPlan.category,
                func.sum(OperatingCostPlan.amount_sar).label("total_amount"),
                func.count(OperatingCostPlan.id).label("source_count"),
            )
            .where(
                and_(
                    OperatingCostPlan.version_id == version_id,
                    OperatingCostPlan.deleted_at.is_(None),
                )
            )
            .group_by(
                OperatingCostPlan.account_code,
                OperatingCostPlan.description,
                OperatingCostPlan.category,
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        consolidation_data = []
        for row in rows:
            # Map operating category to consolidation category
            consolidation_category = self._map_operating_to_consolidation_category(
                row.account_code,
                row.category,
            )

            consolidation_data.append({
                "version_id": version_id,
                "account_code": row.account_code,
                "account_name": row.description,
                "consolidation_category": consolidation_category,
                "is_revenue": False,
                "amount_sar": row.total_amount or Decimal("0.00"),
                "source_table": "finance_operating_cost_plans",
                "source_count": row.source_count,
                "is_calculated": True,
            })

        return consolidation_data

    async def _aggregate_capex(
        self,
        version_id: uuid.UUID,
    ) -> list[dict]:
        """Aggregate CapEx from finance_capex_plans."""
        query = (
            select(
                CapExPlan.account_code,
                CapExPlan.description,
                CapExPlan.category,
                func.sum(CapExPlan.total_cost_sar).label("total_amount"),
                func.count(CapExPlan.id).label("source_count"),
            )
            .where(
                and_(
                    CapExPlan.version_id == version_id,
                    CapExPlan.deleted_at.is_(None),
                )
            )
            .group_by(
                CapExPlan.account_code,
                CapExPlan.description,
                CapExPlan.category,
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        consolidation_data = []
        for row in rows:
            # Map CapEx category to consolidation category
            consolidation_category = self._map_capex_to_consolidation_category(
                row.account_code,
                row.category,
            )

            consolidation_data.append({
                "version_id": version_id,
                "account_code": row.account_code,
                "account_name": row.description,
                "consolidation_category": consolidation_category,
                "is_revenue": False,
                "amount_sar": row.total_amount or Decimal("0.00"),
                "source_table": "finance_capex_plans",
                "source_count": row.source_count,
                "is_calculated": True,
            })

        return consolidation_data

    def _map_revenue_to_consolidation_category(
        self,
        account_code: str,
        category: str,
    ) -> ConsolidationCategory:
        """Map revenue account code and category to consolidation category."""
        # Tuition (701xx)
        if account_code.startswith("701"):
            return ConsolidationCategory.REVENUE_TUITION
        # Fees (702xx-709xx)
        elif account_code.startswith("702") or account_code.startswith("703"):
            return ConsolidationCategory.REVENUE_FEES
        # Other revenue (75xxx-77xxx)
        else:
            return ConsolidationCategory.REVENUE_OTHER

    def _map_personnel_to_consolidation_category(
        self,
        account_code: str,
    ) -> ConsolidationCategory:
        """Map personnel account code and category to consolidation category."""
        # Teaching staff (64110-64119)
        if account_code.startswith("6411"):
            return ConsolidationCategory.PERSONNEL_TEACHING
        # Admin staff (64120-64129)
        elif account_code.startswith("6412"):
            return ConsolidationCategory.PERSONNEL_ADMIN
        # Support staff (64130-64139)
        elif account_code.startswith("6413"):
            return ConsolidationCategory.PERSONNEL_SUPPORT
        # Social charges (645xx)
        elif account_code.startswith("645"):
            return ConsolidationCategory.PERSONNEL_SOCIAL
        # Default to teaching
        else:
            return ConsolidationCategory.PERSONNEL_TEACHING

    def _map_operating_to_consolidation_category(
        self,
        account_code: str,
        category: str,
    ) -> ConsolidationCategory:
        """Map operating cost account code and category to consolidation category."""
        # Supplies (606xx)
        if account_code.startswith("606"):
            return ConsolidationCategory.OPERATING_SUPPLIES
        # Utilities (6061x)
        elif account_code.startswith("6061"):
            return ConsolidationCategory.OPERATING_UTILITIES
        # Maintenance (615xx)
        elif account_code.startswith("615"):
            return ConsolidationCategory.OPERATING_MAINTENANCE
        # Insurance (616xx)
        elif account_code.startswith("616"):
            return ConsolidationCategory.OPERATING_INSURANCE
        # Other operating
        else:
            return ConsolidationCategory.OPERATING_OTHER

    def _map_capex_to_consolidation_category(
        self,
        account_code: str,
        category: str,
    ) -> ConsolidationCategory:
        """Map CapEx account code and category to consolidation category."""
        # Equipment (2154x)
        if account_code.startswith("2154"):
            return ConsolidationCategory.CAPEX_EQUIPMENT
        # IT (2183x)
        elif account_code.startswith("2183"):
            return ConsolidationCategory.CAPEX_IT
        # Furniture (2184x)
        elif account_code.startswith("2184"):
            return ConsolidationCategory.CAPEX_FURNITURE
        # Building (213xx)
        elif account_code.startswith("213"):
            return ConsolidationCategory.CAPEX_BUILDING
        # Software (205xx)
        elif account_code.startswith("205"):
            return ConsolidationCategory.CAPEX_SOFTWARE
        # Default to equipment
        else:
            return ConsolidationCategory.CAPEX_EQUIPMENT
