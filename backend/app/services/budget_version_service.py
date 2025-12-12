"""
Budget Version service.

Manages budget version lifecycle including creation, workflow transitions,
cloning, and deletion with proper business rules enforcement.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    BudgetVersion,
    BudgetVersionStatus,
    ClassSizeParam,
    FeeStructure,
    SubjectHoursMatrix,
    TeacherCostParam,
)
from app.services.base import BaseService
from app.services.exceptions import BusinessRuleError, ConflictError


class BudgetVersionService:
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
        Initialize budget version service.

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

    async def get_budget_version(self, version_id: uuid.UUID) -> BudgetVersion:
        """
        Get budget version by ID.

        Args:
            version_id: Budget version UUID

        Returns:
            BudgetVersion instance

        Raises:
            NotFoundError: If version not found
        """
        return await self._base_service.get_by_id(version_id)

    async def get_all_budget_versions(
        self,
        fiscal_year: int | None = None,
        status: BudgetVersionStatus | None = None,
    ) -> list[BudgetVersion]:
        """
        Get all budget versions with optional filters.

        Args:
            fiscal_year: Optional fiscal year filter
            status: Optional status filter

        Returns:
            List of BudgetVersion instances
        """
        filters = {}
        if fiscal_year:
            filters["fiscal_year"] = fiscal_year
        if status:
            filters["status"] = status

        return await self._base_service.get_all(
            filters=filters,
            order_by="created_at",
        )

    async def get_budget_versions_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        fiscal_year: int | None = None,
        status: BudgetVersionStatus | None = None,
    ) -> dict[str, Any]:
        """
        Get paginated budget versions.

        Args:
            page: Page number (1-indexed)
            page_size: Records per page
            fiscal_year: Optional fiscal year filter
            status: Optional status filter

        Returns:
            Paginated response with items, total, page, page_size, total_pages
        """
        filters = {}
        if fiscal_year:
            filters["fiscal_year"] = fiscal_year
        if status:
            filters["status"] = status

        return await self._base_service.get_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by="created_at",
        )

    async def create_budget_version(
        self,
        name: str,
        fiscal_year: int,
        academic_year: str,
        organization_id: uuid.UUID,
        notes: str | None = None,
        parent_version_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> BudgetVersion:
        """
        Create a new budget version.

        Args:
            name: Version name (e.g., "FY2025 Initial Budget")
            fiscal_year: Fiscal year (e.g., 2025)
            academic_year: Academic year string (e.g., "2024-2025")
            organization_id: Organization UUID this version belongs to
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
                f"A working budget version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede the existing version first."
            )

        return await self._base_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
                "organization_id": organization_id,
                "status": BudgetVersionStatus.WORKING,
                "notes": notes,
                "is_baseline": False,
                "parent_version_id": parent_version_id,
            },
            user_id=user_id,
        )

    async def submit_budget_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Submit budget version for approval.

        Args:
            version_id: Budget version UUID
            user_id: User ID submitting the version

        Returns:
            Updated BudgetVersion instance

        Raises:
            BusinessRuleError: If version is not in WORKING status

        Business Rules:
            - Only WORKING versions can be submitted
            - Records submission timestamp and user
        """
        version = await self.get_budget_version(version_id)

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

    async def approve_budget_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Approve budget version.

        Args:
            version_id: Budget version UUID
            user_id: User ID approving the version (must be manager/admin)

        Returns:
            Updated BudgetVersion instance

        Raises:
            BusinessRuleError: If version is not in SUBMITTED status

        Business Rules:
            - Only SUBMITTED versions can be approved
            - Records approval timestamp and user
        """
        version = await self.get_budget_version(version_id)

        if version.status != BudgetVersionStatus.SUBMITTED:
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

    async def supersede_budget_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> BudgetVersion:
        """
        Mark budget version as superseded.

        Use this instead of deletion for approved versions to maintain audit trail.

        Args:
            version_id: Budget version UUID
            user_id: User ID for audit trail

        Returns:
            Updated BudgetVersion instance
        """
        return await self._base_service.update(
            version_id,
            {"status": BudgetVersionStatus.SUPERSEDED},
            user_id=user_id,
        )

    async def delete_budget_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        Delete (soft delete) a budget version.

        Args:
            version_id: Budget version UUID
            user_id: User ID performing deletion

        Raises:
            NotFoundError: If version not found
            BusinessRuleError: If version is APPROVED

        Business Rules:
            - Cannot delete APPROVED versions (must supersede instead)
            - This maintains audit trail for approved budgets
        """
        version = await self.get_budget_version(version_id)

        if version.status == BudgetVersionStatus.APPROVED:
            raise BusinessRuleError(
                "CANNOT_DELETE_APPROVED",
                "Cannot delete approved budget versions. "
                "Please use supersede instead to maintain audit trail.",
            )

        await self._base_service.soft_delete(version_id, user_id=user_id)

    async def clone_budget_version(
        self,
        source_version_id: uuid.UUID,
        name: str,
        fiscal_year: int,
        academic_year: str,
        clone_configuration: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> BudgetVersion:
        """
        Clone a budget version to create a new baseline.

        This is the recommended way to create next year's budget based on
        current year's configuration.

        Args:
            source_version_id: Source budget version UUID to clone
            name: New version name
            fiscal_year: Target fiscal year
            academic_year: Target academic year (e.g., "2025-2026")
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
        source_version = await self.get_budget_version(source_version_id)

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
                f"A working budget version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede it first."
            )

        # 3. Create new version with source as parent (inherits organization_id)
        new_version = await self._base_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
                "organization_id": source_version.organization_id,
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
                    ClassSizeParam.budget_version_id == source_version_id,
                    ClassSizeParam.deleted_at.is_(None),
                )
            )
        )
        for source in source_class_sizes.scalars().all():
            await self._class_size_base.create(
                {
                    "budget_version_id": target_version_id,
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
                    SubjectHoursMatrix.budget_version_id == source_version_id,
                    SubjectHoursMatrix.deleted_at.is_(None),
                )
            )
        )
        for source in source_subject_hours.scalars().all():
            await self._subject_hours_base.create(
                {
                    "budget_version_id": target_version_id,
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
                    TeacherCostParam.budget_version_id == source_version_id,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
        )
        for source in source_teacher_costs.scalars().all():
            await self._teacher_cost_base.create(
                {
                    "budget_version_id": target_version_id,
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
                    FeeStructure.budget_version_id == source_version_id,
                    FeeStructure.deleted_at.is_(None),
                )
            )
        )
        for source in source_fees.scalars().all():
            await self._fee_structure_base.create(
                {
                    "budget_version_id": target_version_id,
                    "level_id": source.level_id,
                    "nationality_type_id": source.nationality_type_id,
                    "fee_category_id": source.fee_category_id,
                    "amount_sar": source.amount_sar,
                    "trimester": source.trimester,
                    "notes": source.notes,
                },
                user_id=user_id,
            )
