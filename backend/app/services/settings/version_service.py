"""
Version service.

Manages budget version lifecycle including creation, workflow transitions,
cloning, and deletion with proper business rules enforcement.

NOTE: Renamed from budget_version_service.py for consistency.
The class name remains BudgetVersion for backward compatibility with SQLAlchemy model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ClassSizeParam,
    FeeStructure,
    ScenarioType,
    SubjectHoursMatrix,
    TeacherCostParam,
    Version,
    VersionStatus,
)
from app.services.base import BaseService
from app.services.exceptions import BusinessRuleError, ConflictError

# Backward compatibility aliases used throughout this file
BudgetVersion = Version
BudgetVersionStatus = VersionStatus

# ==============================================================================
# Workflow Rules by Scenario Type
# ==============================================================================

# Scenario types that can be submitted for approval
CAN_SUBMIT: set[ScenarioType] = {
    ScenarioType.BUDGET,
    ScenarioType.FORECAST,
    ScenarioType.STRATEGIC,
}

# Scenario types that can be approved
CAN_APPROVE: set[ScenarioType] = {
    ScenarioType.ACTUAL,  # Approval = validation/lock of imported data
    ScenarioType.BUDGET,
    ScenarioType.FORECAST,
    ScenarioType.STRATEGIC,
}

# Scenario types that can be rejected (same as can be submitted)
CAN_REJECT: set[ScenarioType] = CAN_SUBMIT


class VersionService:
    """
    Service for managing budget versions.

    Budget versions represent different planning cycles for a fiscal year.
    Each version has a workflow status:
    - WORKING: Active editing state
    - SUBMITTED: Sent for approval
    - APPROVED: Approved by management
    - SUPERSEDED: Replaced by newer version

    Business Rules:
    - Only one WORKING version per fiscal year allowed
    - Cannot delete APPROVED versions (must supersede instead)
    - Status transitions: WORKING → SUBMITTED → APPROVED
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize version service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(BudgetVersion, session)
        # Base services for cloning (direct access, no validation)
        self._class_size_base = BaseService(ClassSizeParam, session)
        self._subject_hours_base = BaseService(SubjectHoursMatrix, session)
        self._teacher_cost_base = BaseService(TeacherCostParam, session)
        self._fee_structure_base = BaseService(FeeStructure, session)

    async def get_version(self, version_id: uuid.UUID) -> BudgetVersion:
        """
        Get version by ID.

        Args:
            version_id: Version UUID

        Returns:
            BudgetVersion instance

        Raises:
            NotFoundError: If version not found
        """
        return await self._base_service.get_by_id(version_id)

    async def get_all_versions(
        self,
        fiscal_year: int | None = None,
        status: BudgetVersionStatus | None = None,
        scenario_type: ScenarioType | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> list[BudgetVersion]:
        """
        Get all versions with optional filters.

        Args:
            fiscal_year: Optional fiscal year filter
            status: Optional status filter
            scenario_type: Optional scenario type filter
            organization_id: Optional organization filter

        Returns:
            List of BudgetVersion instances
        """
        filters = {}
        if fiscal_year:
            filters["fiscal_year"] = fiscal_year
        if status:
            filters["status"] = status
        if scenario_type:
            filters["scenario_type"] = scenario_type
        if organization_id:
            filters["organization_id"] = organization_id

        return await self._base_service.get_all(
            filters=filters,
            order_by="created_at",
        )

    async def get_versions_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        fiscal_year: int | None = None,
        status: BudgetVersionStatus | None = None,
        scenario_type: ScenarioType | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get paginated versions.

        Args:
            page: Page number (1-indexed)
            page_size: Records per page
            fiscal_year: Optional fiscal year filter
            status: Optional status filter
            scenario_type: Optional scenario type filter
            organization_id: Optional organization filter

        Returns:
            Paginated response with items, total, page, page_size, total_pages
        """
        filters = {}
        if fiscal_year:
            filters["fiscal_year"] = fiscal_year
        if status:
            filters["status"] = status
        if scenario_type:
            filters["scenario_type"] = scenario_type
        if organization_id:
            filters["organization_id"] = organization_id

        return await self._base_service.get_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by="created_at",
        )

    async def create_version(
        self,
        name: str,
        fiscal_year: int,
        academic_year: str,
        organization_id: uuid.UUID,
        scenario_type: ScenarioType = ScenarioType.BUDGET,
        notes: str | None = None,
        parent_version_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> BudgetVersion:
        """
        Create a new version.

        Args:
            name: Version name (e.g., "FY2025 Initial Budget")
            fiscal_year: Fiscal year (e.g., 2025)
            academic_year: Academic year string (e.g., "2024-2025")
            organization_id: Organization UUID this version belongs to
            scenario_type: Scenario type (default: BUDGET)
            notes: Optional notes
            parent_version_id: Optional parent version for forecast revisions
            user_id: User ID for audit trail

        Returns:
            Created BudgetVersion instance

        Raises:
            ConflictError: If a working version already exists for the organization and fiscal year

        Business Rules:
            - Only one WORKING version per organization per fiscal year allowed
            - New versions start in WORKING status
        """
        existing_working = await self._base_service.exists(
            {
                "organization_id": organization_id,
                "fiscal_year": fiscal_year,
                "status": BudgetVersionStatus.WORKING,
            }
        )

        if existing_working:
            raise ConflictError(
                f"A working version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede the existing version first."
            )

        return await self._base_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
                "organization_id": organization_id,
                "scenario_type": scenario_type,
                "status": BudgetVersionStatus.WORKING,
                "notes": notes,
                "is_baseline": False,
                "parent_version_id": parent_version_id,
            },
            user_id=user_id,
        )

    async def submit_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Submit version for approval.

        Args:
            version_id: Version UUID
            user_id: User ID submitting the version

        Returns:
            Updated BudgetVersion instance

        Raises:
            BusinessRuleError: If version is not in WORKING status or scenario type cannot be submitted

        Business Rules:
            - Only WORKING versions can be submitted
            - Only BUDGET, FORECAST, and STRATEGIC types can be submitted
            - ACTUAL and WHAT_IF types cannot be submitted
            - Records submission timestamp and user
        """
        version = await self.get_version(version_id)

        # Check scenario type permission
        if version.scenario_type not in CAN_SUBMIT:
            raise BusinessRuleError(
                "SCENARIO_TYPE_CANNOT_SUBMIT",
                f"Versions of type '{version.scenario_type.value}' cannot be submitted. "
                f"Only BUDGET, FORECAST, and STRATEGIC versions can be submitted.",
            )

        if version.status != BudgetVersionStatus.WORKING:
            raise BusinessRuleError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot submit version with status '{version.status}'. "
                "Only working versions can be submitted.",
            )

        return await self._base_service.update(
            version_id,
            {
                "status": BudgetVersionStatus.SUBMITTED,
                "submitted_at": datetime.utcnow(),
                "submitted_by_id": user_id,
            },
            user_id=user_id,
        )

    async def approve_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Approve version.

        Args:
            version_id: Version UUID
            user_id: User ID approving the version (must be manager/admin)

        Returns:
            Updated BudgetVersion instance

        Raises:
            BusinessRuleError: If version cannot be approved based on scenario type or status

        Business Rules:
            - Only ACTUAL, BUDGET, FORECAST, and STRATEGIC types can be approved
            - WHAT_IF types cannot be approved (sandbox only)
            - ACTUAL types: Can be approved directly from WORKING (skip submit step)
            - Other types: Must be in SUBMITTED status to be approved
            - Records approval timestamp and user
        """
        version = await self.get_version(version_id)

        # Check scenario type permission
        if version.scenario_type not in CAN_APPROVE:
            raise BusinessRuleError(
                "SCENARIO_TYPE_CANNOT_APPROVE",
                f"Versions of type '{version.scenario_type.value}' cannot be approved. "
                "WHAT_IF versions are sandbox only and cannot be approved.",
            )

        # ACTUAL versions can be approved directly from WORKING (validation/lock flow)
        # Other types must be SUBMITTED first
        if version.scenario_type == ScenarioType.ACTUAL:
            if version.status not in (BudgetVersionStatus.WORKING, BudgetVersionStatus.SUBMITTED):
                raise BusinessRuleError(
                    "INVALID_STATUS_TRANSITION",
                    f"Cannot approve ACTUAL version with status '{version.status}'. "
                    "ACTUAL versions can be approved from WORKING or SUBMITTED status.",
                )
        elif version.status != BudgetVersionStatus.SUBMITTED:
            raise BusinessRuleError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot approve version with status '{version.status}'. "
                "Only submitted versions can be approved.",
            )

        return await self._base_service.update(
            version_id,
            {
                "status": BudgetVersionStatus.APPROVED,
                "approved_at": datetime.utcnow(),
                "approved_by_id": user_id,
            },
            user_id=user_id,
        )

    async def reject_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str | None = None,
    ) -> BudgetVersion:
        """
        Reject a submitted version, returning it to WORKING status.

        This allows managers to send back a budget for corrections without
        fully approving it.

        Args:
            version_id: Version UUID
            user_id: User ID rejecting the version (must be manager/admin)
            reason: Optional reason for rejection (stored in notes for audit)

        Returns:
            Updated BudgetVersion instance

        Raises:
            BusinessRuleError: If version is not in SUBMITTED status or scenario type cannot be rejected

        Business Rules:
            - Only BUDGET, FORECAST, and STRATEGIC types can be rejected
            - ACTUAL and WHAT_IF types cannot be rejected
            - Only SUBMITTED versions can be rejected
            - Rejection reason is appended to notes for audit trail
            - Clears submission timestamp and submitter
        """
        version = await self.get_version(version_id)

        # Check scenario type permission (same as CAN_SUBMIT - only types that can submit can be rejected)
        if version.scenario_type not in CAN_REJECT:
            raise BusinessRuleError(
                "SCENARIO_TYPE_CANNOT_REJECT",
                f"Versions of type '{version.scenario_type.value}' cannot be rejected. "
                f"Only BUDGET, FORECAST, and STRATEGIC versions can be rejected.",
            )

        if version.status != BudgetVersionStatus.SUBMITTED:
            raise BusinessRuleError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot reject version with status '{version.status}'. "
                "Only submitted versions can be rejected.",
            )

        # Enforce "only one WORKING version per fiscal year" before attempting DB update.
        # Otherwise we may hit the unique partial index and surface a 500 to the client.
        existing_working_result = await self.session.execute(
            select(func.count())
            .select_from(BudgetVersion)
            .where(
                and_(
                    BudgetVersion.fiscal_year == version.fiscal_year,
                    BudgetVersion.status == BudgetVersionStatus.WORKING,
                    BudgetVersion.deleted_at.is_(None),
                    BudgetVersion.id != version_id,
                )
            )
        )
        other_working_count = int(existing_working_result.scalar_one() or 0)
        if other_working_count > 0:
            raise BusinessRuleError(
                "WORKING_VERSION_EXISTS",
                f"Cannot reject this version back to 'working': another working version "
                f"already exists for fiscal year {version.fiscal_year}. "
                "Submit/supersede/delete the other working version first.",
                details={"fiscal_year": version.fiscal_year},
            )

        # Build updated notes with rejection reason for audit trail
        rejection_note = f"[Rejected on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]"
        if reason:
            rejection_note += f" Reason: {reason}"

        existing_notes = version.notes or ""
        updated_notes = f"{existing_notes}\n{rejection_note}".strip()

        return await self._base_service.update(
            version_id,
            {
                "status": BudgetVersionStatus.WORKING,
                "notes": updated_notes,
                # Clear submission info since it's back to working
                "submitted_at": None,
                "submitted_by_id": None,
            },
            user_id=user_id,
        )

    async def supersede_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Mark version as superseded.

        Use this instead of deletion for approved versions to maintain audit trail.

        Args:
            version_id: Version UUID
            user_id: User ID for audit trail

        Returns:
            Updated BudgetVersion instance
        """
        return await self._base_service.update(
            version_id,
            {"status": BudgetVersionStatus.SUPERSEDED},
            user_id=user_id,
        )

    async def delete_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        Delete (soft delete) a version.

        Args:
            version_id: Version UUID
            user_id: User ID performing deletion

        Raises:
            NotFoundError: If version not found
            BusinessRuleError: If version is APPROVED

        Business Rules:
            - Cannot delete APPROVED versions (must supersede instead)
            - This maintains audit trail for approved budgets
        """
        version = await self.get_version(version_id)

        if version.status == BudgetVersionStatus.APPROVED:
            raise BusinessRuleError(
                "CANNOT_DELETE_APPROVED",
                "Cannot delete approved versions. "
                "Please use supersede instead to maintain audit trail.",
            )

        await self._base_service.soft_delete(version_id, user_id=user_id)

    async def clone_version(
        self,
        source_version_id: uuid.UUID,
        name: str,
        fiscal_year: int,
        academic_year: str,
        scenario_type: ScenarioType | None = None,
        clone_configuration: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> BudgetVersion:
        """
        Clone a version to create a new baseline.

        This is the recommended way to create next year's budget based on
        current year's configuration.

        Args:
            source_version_id: Source version UUID to clone
            name: New version name
            fiscal_year: Target fiscal year
            academic_year: Target academic year (e.g., "2025-2026")
            scenario_type: Scenario type for cloned version (default: inherit from source)
            clone_configuration: Whether to clone configuration data (default: True)
            user_id: User ID for audit trail

        Returns:
            Newly created BudgetVersion instance

        Raises:
            NotFoundError: If source version not found
            ConflictError: If working version exists for target fiscal year

        Configuration Data Cloned:
            - Class size parameters (Module 2)
            - Subject hours matrix (Module 3)
            - Teacher cost parameters (Module 4)
            - Fee structure (Module 5)

        NOT Cloned (recalculated from scratch):
            - Enrollment plans
            - Class structures
            - DHG calculations
            - Revenue projections
            - Cost allocations
            - CapEx planning
        """
        # 1. Validate source exists
        source_version = await self.get_version(source_version_id)

        # Use provided scenario_type or inherit from source
        effective_scenario_type = scenario_type if scenario_type is not None else source_version.scenario_type

        # 2. Check for existing working version in target organization and year
        existing_working = await self._base_service.exists(
            {
                "organization_id": source_version.organization_id,
                "fiscal_year": fiscal_year,
                "status": BudgetVersionStatus.WORKING,
            }
        )

        if existing_working:
            raise ConflictError(
                f"A working version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede it first."
            )

        # 3. Create new version with source as parent (inherits organization_id)
        new_version = await self._base_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
                "organization_id": source_version.organization_id,
                "scenario_type": effective_scenario_type,
                "status": BudgetVersionStatus.WORKING,
                "notes": f"Cloned from {source_version.name}",
                "is_baseline": False,
                "parent_version_id": source_version_id,
            },
            user_id=user_id,
        )

        # 4. Clone configuration data if requested
        if clone_configuration:
            await self._clone_configuration_data(
                source_version_id=source_version_id,
                target_version_id=new_version.id,
                user_id=user_id,
            )

        # Refresh to get the complete object
        await self.session.refresh(new_version)
        return new_version

    async def _clone_configuration_data(
        self,
        source_version_id: uuid.UUID,
        target_version_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> None:
        """
        Clone configuration data from source to target version.

        Internal method - bypasses validation since source data is already valid.

        Args:
            source_version_id: Source version ID
            target_version_id: Target version ID
            user_id: User ID for audit trail
        """
        # 1. Clone Class Size Parameters
        source_class_sizes = await self.session.execute(
            select(ClassSizeParam).where(
                and_(
                    ClassSizeParam.version_id == source_version_id,
                    ClassSizeParam.deleted_at.is_(None),
                )
            )
        )
        for source in source_class_sizes.scalars().all():
            await self._class_size_base.create(
                {
                    "version_id": target_version_id,
                    "level_id": source.level_id,
                    "cycle_id": source.cycle_id,
                    "min_class_size": source.min_class_size,
                    "target_class_size": source.target_class_size,
                    "max_class_size": source.max_class_size,
                    "notes": source.notes,
                },
                user_id=user_id,
            )

        # 2. Clone Subject Hours Matrix
        source_subject_hours = await self.session.execute(
            select(SubjectHoursMatrix).where(
                and_(
                    SubjectHoursMatrix.version_id == source_version_id,
                    SubjectHoursMatrix.deleted_at.is_(None),
                )
            )
        )
        for source in source_subject_hours.scalars().all():
            await self._subject_hours_base.create(
                {
                    "version_id": target_version_id,
                    "level_id": source.level_id,
                    "subject_id": source.subject_id,
                    "hours_per_week": source.hours_per_week,
                    "is_split": source.is_split,
                    "notes": source.notes,
                },
                user_id=user_id,
            )

        # 3. Clone Teacher Cost Parameters
        source_teacher_costs = await self.session.execute(
            select(TeacherCostParam).where(
                and_(
                    TeacherCostParam.version_id == source_version_id,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
        )
        for source in source_teacher_costs.scalars().all():
            await self._teacher_cost_base.create(
                {
                    "version_id": target_version_id,
                    "category_id": source.category_id,
                    "cycle_id": source.cycle_id,
                    "prrd_contribution_eur": source.prrd_contribution_eur,
                    "avg_salary_sar": source.avg_salary_sar,
                    "social_charges_rate": source.social_charges_rate,
                    "benefits_allowance_sar": source.benefits_allowance_sar,
                    "hsa_hourly_rate_sar": source.hsa_hourly_rate_sar,
                    "max_hsa_hours": source.max_hsa_hours,
                    "notes": source.notes,
                },
                user_id=user_id,
            )

        # 4. Clone Fee Structure
        source_fees = await self.session.execute(
            select(FeeStructure).where(
                and_(
                    FeeStructure.version_id == source_version_id,
                    FeeStructure.deleted_at.is_(None),
                )
            )
        )
        for source in source_fees.scalars().all():
            await self._fee_structure_base.create(
                {
                    "version_id": target_version_id,
                    "level_id": source.level_id,
                    "nationality_type_id": source.nationality_type_id,
                    "fee_category_id": source.fee_category_id,
                    "amount_sar": source.amount_sar,
                    "trimester": source.trimester,
                    "notes": source.notes,
                },
                user_id=user_id,
            )


# Backward compatibility alias - will be removed in future version
BudgetVersionService = VersionService
