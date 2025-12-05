"""
Configuration service for managing system settings and budget parameters.

Handles CRUD operations for:
- System configuration
- Budget versions
- Class size parameters
- Subject hours matrix
- Teacher cost parameters
- Fee structure
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
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
from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    ServiceException,
    ValidationError,
)


class ConfigurationService:
    """
    Service for configuration management.

    Provides business logic for system configuration and budget parameters.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize configuration service.

        Args:
            session: Async database session
        """
        self.session = session
        self.system_config_service = BaseService(SystemConfig, session)
        self.budget_version_service = BaseService(BudgetVersion, session)
        self.class_size_param_service = BaseService(ClassSizeParam, session)
        self.subject_hours_service = BaseService(SubjectHoursMatrix, session)
        self.teacher_cost_service = BaseService(TeacherCostParam, session)
        self.fee_structure_service = BaseService(FeeStructure, session)
        self.timetable_constraint_service = BaseService(TimetableConstraint, session)

    async def get_system_config(self, key: str) -> SystemConfig | None:
        """
        Get system configuration by key.

        Args:
            key: Configuration key

        Returns:
            SystemConfig instance or None if not found

        Raises:
            ServiceException: If database operation fails
        """
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.key == key,
                    SystemConfig.deleted_at.is_(None),
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve system configuration",
                key=key,
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve system configuration. Please try again.",
                status_code=500,
                details={"key": key},
            ) from e

    async def get_all_system_configs(self, category: str | None = None) -> list[SystemConfig]:
        """
        Get all system configurations.

        Args:
            category: Optional category filter

        Returns:
            List of SystemConfig instances
        """
        filters = {}
        if category:
            filters["category"] = category

        return await self.system_config_service.get_all(filters=filters)

    async def upsert_system_config(
        self,
        key: str,
        value: dict[str, Any],
        category: str,
        description: str,
        user_id: uuid.UUID | None = None,
    ) -> SystemConfig:
        """
        Create or update system configuration.

        Args:
            key: Configuration key
            value: Configuration value (JSONB)
            category: Configuration category
            description: Configuration description
            user_id: User ID for audit trail

        Returns:
            SystemConfig instance
        """
        existing = await self.get_system_config(key)

        if existing:
            return await self.system_config_service.update(
                existing.id,
                {
                    "value": value,
                    "category": category,
                    "description": description,
                    "is_active": True,
                },
                user_id=user_id,
            )
        else:
            return await self.system_config_service.create(
                {
                    "key": key,
                    "value": value,
                    "category": category,
                    "description": description,
                    "is_active": True,
                },
                user_id=user_id,
            )

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
        return await self.budget_version_service.get_by_id(version_id)

    async def get_all_budget_versions(
        self,
        fiscal_year: int | None = None,
        status: BudgetVersionStatus | None = None,
    ) -> list[BudgetVersion]:
        """
        Get all budget versions.

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

        return await self.budget_version_service.get_all(
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

        return await self.budget_version_service.get_paginated(
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
        notes: str | None = None,
        parent_version_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> BudgetVersion:
        """
        Create a new budget version.

        Args:
            name: Version name
            fiscal_year: Fiscal year
            academic_year: Academic year string
            notes: Optional notes
            parent_version_id: Optional parent version for forecast revisions
            user_id: User ID for audit trail

        Returns:
            Created BudgetVersion instance

        Raises:
            ConflictError: If a working version already exists for the fiscal year
        """
        existing_working = await self.budget_version_service.exists(
            {
                "fiscal_year": fiscal_year,
                "status": BudgetVersionStatus.WORKING,
            }
        )

        if existing_working:
            raise ConflictError(
                f"A working budget version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede the existing version first."
            )

        return await self.budget_version_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
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
            BusinessRuleError: If version is not in working status
        """
        version = await self.get_budget_version(version_id)

        if version.status != BudgetVersionStatus.WORKING:
            raise BusinessRuleError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot submit version with status '{version.status}'. Only working versions can be submitted.",
            )

        return await self.budget_version_service.update(
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
            BusinessRuleError: If version is not in submitted status
        """
        version = await self.get_budget_version(version_id)

        if version.status != BudgetVersionStatus.SUBMITTED:
            raise BusinessRuleError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot approve version with status '{version.status}'. Only submitted versions can be approved.",
            )

        return await self.budget_version_service.update(
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

        Args:
            version_id: Budget version UUID
            user_id: User ID for audit trail

        Returns:
            Updated BudgetVersion instance
        """
        return await self.budget_version_service.update(
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

        Business Rule: Cannot delete approved budget versions - they must be superseded instead
        to maintain audit trail and prevent accidental deletion of approved budgets.

        Args:
            version_id: Budget version UUID
            user_id: User ID performing deletion

        Raises:
            NotFoundError: If version not found
            BusinessRuleError: If version is approved (cannot delete approved budgets)
        """
        version = await self.get_budget_version(version_id)

        # Business rule: Cannot delete approved versions
        if version.status == BudgetVersionStatus.APPROVED:
            raise BusinessRuleError(
                "CANNOT_DELETE_APPROVED",
                "Cannot delete approved budget versions. Please use supersede instead to maintain audit trail.",
            )

        await self.budget_version_service.soft_delete(version_id, user_id=user_id)

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
        Clone a budget version to create a new baseline for the next fiscal year.

        This is the recommended way to create next year's budget based on current year's
        configuration. Clones the budget version metadata and optionally all configuration data.

        Args:
            source_version_id: Source budget version UUID to clone
            name: New version name
            fiscal_year: Target fiscal year
            academic_year: Target academic year
            clone_configuration: Whether to clone configuration data (default: True)
            user_id: User ID for audit trail

        Returns:
            Newly created BudgetVersion instance

        Raises:
            NotFoundError: If source version not found
            ConflictError: If working version exists for target fiscal year
        """
        # 1. Validate source exists
        source_version = await self.get_budget_version(source_version_id)

        # 2. Check for existing working version in target year
        existing_working = await self.budget_version_service.exists(
            {
                "fiscal_year": fiscal_year,
                "status": BudgetVersionStatus.WORKING,
            }
        )

        if existing_working:
            raise ConflictError(
                f"A working budget version already exists for fiscal year {fiscal_year}. "
                "Please submit or supersede it first."
            )

        # 3. Create new version with source as parent
        new_version = await self.budget_version_service.create(
            {
                "name": name,
                "fiscal_year": fiscal_year,
                "academic_year": academic_year,
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

        Copies:
        - Class size parameters (Module 2)
        - Subject hours matrix (Module 3)
        - Teacher cost parameters (Module 4)
        - Fee structure (Module 5)

        Does NOT copy planning data (enrollment, classes, DHG, revenue, costs, capex)
        as these are recalculated from scratch.

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
            await self.class_size_param_service.create(
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
            await self.subject_hours_service.create(
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
            await self.teacher_cost_service.create(
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
            await self.fee_structure_service.create(
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

    async def get_academic_cycles(self) -> list[AcademicCycle]:
        """
        Get all academic cycles.

        Returns:
            List of AcademicCycle instances
        """
        query = select(AcademicCycle).order_by(AcademicCycle.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_academic_levels(
        self,
        cycle_id: uuid.UUID | None = None,
    ) -> list[AcademicLevel]:
        """
        Get all academic levels.

        Args:
            cycle_id: Optional cycle filter

        Returns:
            List of AcademicLevel instances
        """
        query = select(AcademicLevel).options(selectinload(AcademicLevel.cycle))

        if cycle_id:
            query = query.where(AcademicLevel.cycle_id == cycle_id)

        query = query.order_by(AcademicLevel.sort_order)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_class_size_params(
        self,
        version_id: uuid.UUID,
    ) -> list[ClassSizeParam]:
        """
        Get class size parameters for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of ClassSizeParam instances
        """
        return await self.class_size_param_service.get_all(
            filters={"budget_version_id": version_id}
        )

    async def upsert_class_size_param(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID | None,
        cycle_id: uuid.UUID | None,
        min_class_size: int,
        target_class_size: int,
        max_class_size: int,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> ClassSizeParam:
        """
        Create or update class size parameter.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID (None for cycle default)
            cycle_id: Academic cycle UUID (None for level-specific)
            min_class_size: Minimum class size
            target_class_size: Target class size
            max_class_size: Maximum class size
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            ClassSizeParam instance

        Raises:
            ValidationError: If parameters are invalid
        """
        if min_class_size >= target_class_size or target_class_size > max_class_size:
            raise ValidationError(
                "Invalid class size parameters. Must satisfy: min < target <= max"
            )

        if not level_id and not cycle_id:
            raise ValidationError("Either level_id or cycle_id must be provided")

        if level_id and cycle_id:
            raise ValidationError("Cannot specify both level_id and cycle_id")

        query = select(ClassSizeParam).where(
            and_(
                ClassSizeParam.budget_version_id == version_id,
                ClassSizeParam.level_id == level_id if level_id else ClassSizeParam.cycle_id == cycle_id,
                ClassSizeParam.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "level_id": level_id,
            "cycle_id": cycle_id,
            "min_class_size": min_class_size,
            "target_class_size": target_class_size,
            "max_class_size": max_class_size,
            "notes": notes,
        }

        if existing:
            return await self.class_size_param_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.class_size_param_service.create(data, user_id=user_id)

    async def get_subjects(self) -> list[Subject]:
        """
        Get all active subjects.

        Returns:
            List of Subject instances
        """
        query = select(Subject).where(Subject.is_active is True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_subject_hours_matrix(
        self,
        version_id: uuid.UUID,
    ) -> list[SubjectHoursMatrix]:
        """
        Get subject hours matrix for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of SubjectHoursMatrix instances
        """
        query = (
            select(SubjectHoursMatrix)
            .where(
                and_(
                    SubjectHoursMatrix.budget_version_id == version_id,
                    SubjectHoursMatrix.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(SubjectHoursMatrix.subject),
                selectinload(SubjectHoursMatrix.level),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_subject_hours(
        self,
        version_id: uuid.UUID,
        subject_id: uuid.UUID,
        level_id: uuid.UUID,
        hours_per_week: Decimal,
        is_split: bool = False,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> SubjectHoursMatrix:
        """
        Create or update subject hours configuration.

        Args:
            version_id: Budget version UUID
            subject_id: Subject UUID
            level_id: Academic level UUID
            hours_per_week: Hours per week per class
            is_split: Whether classes are split (half-size groups)
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            SubjectHoursMatrix instance

        Raises:
            ValidationError: If hours are invalid
        """
        if hours_per_week <= 0 or hours_per_week > 12:
            raise ValidationError(
                "Hours per week must be between 0 and 12",
                field="hours_per_week",
            )

        query = select(SubjectHoursMatrix).where(
            and_(
                SubjectHoursMatrix.budget_version_id == version_id,
                SubjectHoursMatrix.subject_id == subject_id,
                SubjectHoursMatrix.level_id == level_id,
                SubjectHoursMatrix.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "subject_id": subject_id,
            "level_id": level_id,
            "hours_per_week": hours_per_week,
            "is_split": is_split,
            "notes": notes,
        }

        if existing:
            return await self.subject_hours_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.subject_hours_service.create(data, user_id=user_id)

    async def get_teacher_categories(self) -> list[TeacherCategory]:
        """
        Get all teacher categories.

        Returns:
            List of TeacherCategory instances
        """
        query = select(TeacherCategory)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_teacher_cost_params(
        self,
        version_id: uuid.UUID,
    ) -> list[TeacherCostParam]:
        """
        Get teacher cost parameters for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of TeacherCostParam instances
        """
        query = (
            select(TeacherCostParam)
            .where(
                and_(
                    TeacherCostParam.budget_version_id == version_id,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TeacherCostParam.category),
                selectinload(TeacherCostParam.cycle),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_teacher_cost_param(
        self,
        version_id: uuid.UUID,
        category_id: uuid.UUID,
        cycle_id: uuid.UUID | None,
        prrd_contribution_eur: Decimal | None,
        avg_salary_sar: Decimal | None,
        social_charges_rate: Decimal,
        benefits_allowance_sar: Decimal,
        hsa_hourly_rate_sar: Decimal,
        max_hsa_hours: Decimal,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TeacherCostParam:
        """
        Create or update teacher cost parameter.

        Args:
            version_id: Budget version UUID
            category_id: Teacher category UUID
            cycle_id: Academic cycle UUID (None for all cycles)
            prrd_contribution_eur: PRRD contribution (EUR, for AEFE detached)
            avg_salary_sar: Average salary (SAR/year, for local teachers)
            social_charges_rate: Social charges rate (e.g., 0.21 for 21%)
            benefits_allowance_sar: Benefits/allowances (SAR/year)
            hsa_hourly_rate_sar: HSA hourly rate (SAR)
            max_hsa_hours: Maximum HSA hours per week
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            TeacherCostParam instance
        """
        query = select(TeacherCostParam).where(
            and_(
                TeacherCostParam.budget_version_id == version_id,
                TeacherCostParam.category_id == category_id,
                TeacherCostParam.cycle_id == cycle_id if cycle_id else TeacherCostParam.cycle_id.is_(None),
                TeacherCostParam.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "category_id": category_id,
            "cycle_id": cycle_id,
            "prrd_contribution_eur": prrd_contribution_eur,
            "avg_salary_sar": avg_salary_sar,
            "social_charges_rate": social_charges_rate,
            "benefits_allowance_sar": benefits_allowance_sar,
            "hsa_hourly_rate_sar": hsa_hourly_rate_sar,
            "max_hsa_hours": max_hsa_hours,
            "notes": notes,
        }

        if existing:
            return await self.teacher_cost_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.teacher_cost_service.create(data, user_id=user_id)

    async def get_fee_categories(self) -> list[FeeCategory]:
        """
        Get all fee categories.

        Returns:
            List of FeeCategory instances
        """
        query = select(FeeCategory)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_nationality_types(self) -> list[NationalityType]:
        """
        Get all nationality types.

        Returns:
            List of NationalityType instances
        """
        query = select(NationalityType).order_by(NationalityType.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_fee_structure(
        self,
        version_id: uuid.UUID,
    ) -> list[FeeStructure]:
        """
        Get fee structure for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of FeeStructure instances
        """
        query = (
            select(FeeStructure)
            .where(
                and_(
                    FeeStructure.budget_version_id == version_id,
                    FeeStructure.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(FeeStructure.level),
                selectinload(FeeStructure.nationality_type),
                selectinload(FeeStructure.fee_category),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_fee_structure(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        nationality_type_id: uuid.UUID,
        fee_category_id: uuid.UUID,
        amount_sar: Decimal,
        trimester: int | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> FeeStructure:
        """
        Create or update fee structure entry.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            nationality_type_id: Nationality type UUID
            fee_category_id: Fee category UUID
            amount_sar: Fee amount in SAR
            trimester: Trimester (1-3) for tuition, None for annual fees
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            FeeStructure instance
        """
        query = select(FeeStructure).where(
            and_(
                FeeStructure.budget_version_id == version_id,
                FeeStructure.level_id == level_id,
                FeeStructure.nationality_type_id == nationality_type_id,
                FeeStructure.fee_category_id == fee_category_id,
                FeeStructure.trimester == trimester if trimester else FeeStructure.trimester.is_(None),
                FeeStructure.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "level_id": level_id,
            "nationality_type_id": nationality_type_id,
            "fee_category_id": fee_category_id,
            "amount_sar": amount_sar,
            "trimester": trimester,
            "notes": notes,
        }

        if existing:
            return await self.fee_structure_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.fee_structure_service.create(data, user_id=user_id)

    # ========================================================================
    # Timetable Constraints (Module 6)
    # ========================================================================

    async def get_timetable_constraints(
        self,
        version_id: uuid.UUID,
    ) -> list[TimetableConstraint]:
        """
        Get timetable constraints for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of TimetableConstraint instances
        """
        query = (
            select(TimetableConstraint)
            .where(
                and_(
                    TimetableConstraint.budget_version_id == version_id,
                    TimetableConstraint.deleted_at.is_(None),
                )
            )
            .options(selectinload(TimetableConstraint.level))
            .order_by(TimetableConstraint.level_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_timetable_constraint(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        total_hours_per_week: Decimal,
        max_hours_per_day: Decimal,
        days_per_week: int,
        requires_lunch_break: bool,
        min_break_duration_minutes: int,
        notes: str | None,
        user_id: uuid.UUID,
    ) -> TimetableConstraint:
        """
        Create or update timetable constraint.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            total_hours_per_week: Total student hours per week
            max_hours_per_day: Maximum hours per day
            days_per_week: School days per week (4-6)
            requires_lunch_break: Whether lunch break is required
            min_break_duration_minutes: Minimum break duration (minutes)
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            TimetableConstraint instance

        Raises:
            ValidationError: If max_hours_per_day > total_hours_per_week
        """
        # Validate cross-field constraint
        if max_hours_per_day > total_hours_per_week:
            raise ValidationError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )

        query = select(TimetableConstraint).where(
            and_(
                TimetableConstraint.budget_version_id == version_id,
                TimetableConstraint.level_id == level_id,
                TimetableConstraint.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "level_id": level_id,
            "total_hours_per_week": total_hours_per_week,
            "max_hours_per_day": max_hours_per_day,
            "days_per_week": days_per_week,
            "requires_lunch_break": requires_lunch_break,
            "min_break_duration_minutes": min_break_duration_minutes,
            "notes": notes,
        }

        if existing:
            return await self.timetable_constraint_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.timetable_constraint_service.create(data, user_id=user_id)
