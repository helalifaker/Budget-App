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

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.data.curriculum_templates import CURRICULUM_TEMPLATES, get_template
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
from app.services.budget_version_service import BudgetVersionService
from app.services.class_size_service import ClassSizeService
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceException,
)
from app.services.fee_structure_service import FeeStructureService
from app.services.reference_data_service import ReferenceDataService
from app.services.subject_hours_service import SubjectHoursService
from app.services.teacher_cost_service import TeacherCostParametersService
from app.services.timetable_constraints_service import TimetableConstraintsService

if TYPE_CHECKING:
    from app.schemas.configuration import (
        SubjectHoursBatchResponse,
        SubjectHoursEntry,
        SubjectHoursMatrixResponse,
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
        self.budget_version_base_service = BaseService(BudgetVersion, session)
        self.class_size_param_service = BaseService(ClassSizeParam, session)
        self.subject_hours_base_service = BaseService(SubjectHoursMatrix, session)
        self.teacher_cost_base_service = BaseService(TeacherCostParam, session)
        self.fee_structure_base_service = BaseService(FeeStructure, session)
        self.timetable_constraint_base_service = BaseService(TimetableConstraint, session)
        # Delegate to specialized services
        self._reference_data = ReferenceDataService(session)
        self._class_size = ClassSizeService(session)
        self._fee_structure = FeeStructureService(session)
        self._timetable_constraints = TimetableConstraintsService(session)
        self._teacher_cost = TeacherCostParametersService(session)
        self._budget_version = BudgetVersionService(session)
        self._subject_hours = SubjectHoursService(session)

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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.get_budget_version(version_id)

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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.get_all_budget_versions(
            fiscal_year=fiscal_year,
            status=status,
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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.get_budget_versions_paginated(
            page=page,
            page_size=page_size,
            fiscal_year=fiscal_year,
            status=status,
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
            name: Version name
            fiscal_year: Fiscal year
            academic_year: Academic year string
            organization_id: Organization UUID this version belongs to
            notes: Optional notes
            parent_version_id: Optional parent version for forecast revisions
            user_id: User ID for audit trail

        Returns:
            Created BudgetVersion instance

        Raises:
            ConflictError: If a working version already exists for the organization and fiscal year

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.create_budget_version(
            name=name,
            fiscal_year=fiscal_year,
            academic_year=academic_year,
            organization_id=organization_id,
            notes=notes,
            parent_version_id=parent_version_id,
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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.submit_budget_version(
            version_id=version_id,
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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.approve_budget_version(
            version_id=version_id,
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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.supersede_budget_version(
            version_id=version_id,
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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        await self._budget_version.delete_budget_version(
            version_id=version_id,
            user_id=user_id,
        )

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

        Note:
            Delegates to BudgetVersionService for centralized version management.
        """
        return await self._budget_version.clone_budget_version(
            source_version_id=source_version_id,
            name=name,
            fiscal_year=fiscal_year,
            academic_year=academic_year,
            clone_configuration=clone_configuration,
            user_id=user_id,
        )

    async def get_academic_cycles(self) -> list[AcademicCycle]:
        """
        Get all academic cycles.

        Returns:
            List of AcademicCycle instances

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_academic_cycles()

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

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_academic_levels(cycle_id=cycle_id)

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

        Note:
            Delegates to ClassSizeService for centralized parameter management.
        """
        return await self._class_size.get_class_size_params(version_id)

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

        Note:
            Delegates to ClassSizeService for centralized parameter management.
        """
        return await self._class_size.upsert_class_size_param(
            version_id=version_id,
            level_id=level_id,
            cycle_id=cycle_id,
            min_class_size=min_class_size,
            target_class_size=target_class_size,
            max_class_size=max_class_size,
            notes=notes,
            user_id=user_id,
        )

    async def get_subjects(self) -> list[Subject]:
        """
        Get all active subjects.

        Returns:
            List of Subject instances

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_subjects(active_only=True)

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

        Note:
            Delegates to SubjectHoursService for centralized matrix management.
        """
        return await self._subject_hours.get_subject_hours_matrix(version_id)

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

        Note:
            Delegates to SubjectHoursService for centralized matrix management.
        """
        return await self._subject_hours.upsert_subject_hours(
            version_id=version_id,
            subject_id=subject_id,
            level_id=level_id,
            hours_per_week=hours_per_week,
            is_split=is_split,
            notes=notes,
            user_id=user_id,
        )

    async def get_teacher_categories(self) -> list[TeacherCategory]:
        """
        Get all teacher categories.

        Returns:
            List of TeacherCategory instances

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_teacher_categories()

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

        Note:
            Delegates to TeacherCostParametersService for centralized cost management.
        """
        return await self._teacher_cost.get_teacher_cost_params(version_id)

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

        Raises:
            ValidationError: If parameters are invalid

        Note:
            Delegates to TeacherCostParametersService for centralized cost management.
        """
        return await self._teacher_cost.upsert_teacher_cost_param(
            version_id=version_id,
            category_id=category_id,
            cycle_id=cycle_id,
            prrd_contribution_eur=prrd_contribution_eur,
            avg_salary_sar=avg_salary_sar,
            social_charges_rate=social_charges_rate,
            benefits_allowance_sar=benefits_allowance_sar,
            hsa_hourly_rate_sar=hsa_hourly_rate_sar,
            max_hsa_hours=max_hsa_hours,
            notes=notes,
            user_id=user_id,
        )

    async def get_fee_categories(self) -> list[FeeCategory]:
        """
        Get all fee categories.

        Returns:
            List of FeeCategory instances

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_fee_categories()

    async def get_nationality_types(self) -> list[NationalityType]:
        """
        Get all nationality types.

        Returns:
            List of NationalityType instances

        Note:
            Delegates to ReferenceDataService for centralized reference data access.
        """
        return await self._reference_data.get_nationality_types()

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

        Note:
            Delegates to FeeStructureService for centralized fee management.
        """
        return await self._fee_structure.get_fee_structure(version_id)

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

        Note:
            Delegates to FeeStructureService for centralized fee management.
        """
        return await self._fee_structure.upsert_fee_structure(
            version_id=version_id,
            level_id=level_id,
            nationality_type_id=nationality_type_id,
            fee_category_id=fee_category_id,
            amount_sar=amount_sar,
            trimester=trimester,
            notes=notes,
            user_id=user_id,
        )

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

        Note:
            Delegates to TimetableConstraintsService for centralized timetable management.
        """
        return await self._timetable_constraints.get_timetable_constraints(version_id)

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

        Note:
            Delegates to TimetableConstraintsService for centralized timetable management.
        """
        return await self._timetable_constraints.upsert_timetable_constraint(
            version_id=version_id,
            level_id=level_id,
            total_hours_per_week=total_hours_per_week,
            max_hours_per_day=max_hours_per_day,
            days_per_week=days_per_week,
            requires_lunch_break=requires_lunch_break,
            min_break_duration_minutes=min_break_duration_minutes,
            notes=notes,
            user_id=user_id,
        )

    # ========================================================================
    # Subject Hours Matrix - Batch Operations & Templates
    # ========================================================================

    async def batch_upsert_subject_hours(
        self,
        version_id: uuid.UUID,
        entries: list[SubjectHoursEntry],
        user_id: uuid.UUID | None = None,
    ) -> SubjectHoursBatchResponse:
        """
        Batch create, update, or delete subject hours entries.

        Entries with hours_per_week=None will be deleted (soft delete).

        Args:
            version_id: Budget version UUID
            entries: List of subject hours entries
            user_id: User ID for audit trail

        Returns:
            SubjectHoursBatchResponse with counts and errors

        Note:
            Delegates to SubjectHoursService for centralized matrix management.
        """
        return await self._subject_hours.batch_upsert_subject_hours(
            version_id=version_id,
            entries=entries,
            user_id=user_id,
        )

    async def get_subject_hours_matrix_by_cycle(
        self,
        version_id: uuid.UUID,
        cycle_code: str | None = None,
    ) -> list[SubjectHoursMatrixResponse]:
        """
        Get subject hours organized as a matrix by cycle.

        Returns all subjects with their hours for each level in the cycle,
        including subjects with no hours configured (empty cells).

        Args:
            version_id: Budget version UUID
            cycle_code: Optional cycle code filter (e.g., 'COLL', 'LYC')

        Returns:
            List of SubjectHoursMatrixResponse (one per cycle)

        Note:
            Delegates to SubjectHoursService for centralized matrix management.
        """
        return await self._subject_hours.get_subject_hours_matrix_by_cycle(
            version_id=version_id,
            cycle_code=cycle_code,
        )

    async def apply_curriculum_template(
        self,
        version_id: uuid.UUID,
        template_code: str,
        cycle_codes: list[str],
        overwrite_existing: bool = False,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Apply a curriculum template to populate subject hours.

        Args:
            version_id: Budget version UUID
            template_code: Template code (e.g., 'AEFE_STANDARD_COLL')
            cycle_codes: Cycles to apply to
            overwrite_existing: Whether to overwrite existing values
            user_id: User ID for audit trail

        Returns:
            Dict with applied_count, skipped_count, template_name

        Raises:
            NotFoundError: If template not found
        """
        template = get_template(template_code)
        if not template:
            raise NotFoundError(f"Template '{template_code}' not found")

        # Get subject code -> id mapping
        subjects = await self.get_subjects()
        subject_lookup = {s.code: s.id for s in subjects}

        # Get level code -> id mapping for requested cycles
        levels_query = (
            select(AcademicLevel)
            .join(AcademicCycle)
            .where(AcademicCycle.code.in_(cycle_codes))
        )
        levels_result = await self.session.execute(levels_query)
        levels = list(levels_result.scalars().all())
        level_lookup = {level.code: level.id for level in levels}

        applied_count = 0
        skipped_count = 0

        for subject_code, level_hours in template["hours"].items():
            subject_id = subject_lookup.get(subject_code)
            if not subject_id:
                continue  # Subject not in database

            is_split = template["split_defaults"].get(subject_code, False)

            for level_code, hours in level_hours.items():
                level_id = level_lookup.get(level_code)
                if not level_id:
                    continue  # Level not in requested cycles

                # Skip if hours is 0
                if hours == Decimal("0.0"):
                    continue

                # Check for existing entry
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

                if existing and not overwrite_existing:
                    skipped_count += 1
                    continue

                data = {
                    "budget_version_id": version_id,
                    "subject_id": subject_id,
                    "level_id": level_id,
                    "hours_per_week": hours,
                    "is_split": is_split,
                    "notes": f"From template: {template['template_name']}",
                }

                if existing:
                    await self.subject_hours_base_service.update(existing.id, data, user_id=user_id)
                else:
                    await self.subject_hours_base_service.create(data, user_id=user_id)

                applied_count += 1

        return {
            "applied_count": applied_count,
            "skipped_count": skipped_count,
            "template_name": template["template_name"],
        }

    async def create_subject(
        self,
        code: str,
        name_fr: str,
        name_en: str,
        category: str,
        user_id: uuid.UUID | None = None,
    ) -> Subject:
        """
        Create a new custom subject.

        Args:
            code: Subject code (2-6 uppercase alphanumeric)
            name_fr: French name
            name_en: English name
            category: Subject category (core, elective, specialty, local)
            user_id: User ID for audit trail

        Returns:
            Created Subject instance

        Raises:
            ConflictError: If subject code already exists
        """
        # Check for existing subject with same code
        query = select(Subject).where(Subject.code == code.upper())
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictError(f"Subject with code '{code}' already exists")

        # Create the subject
        subject = Subject(
            code=code.upper(),
            name_fr=name_fr,
            name_en=name_en,
            category=category,
            is_active=True,
        )
        self.session.add(subject)
        await self.session.flush()
        await self.session.refresh(subject)

        logger.info(
            "Created custom subject",
            subject_code=code,
            category=category,
            user_id=str(user_id) if user_id else None,
        )

        return subject

    def get_available_templates(self) -> list[dict[str, Any]]:
        """
        Get list of available curriculum templates.

        Returns:
            List of template info dicts
        """
        return [
            {
                "code": t["template_code"],
                "name": t["template_name"],
                "description": t["description"],
                "cycle_codes": t["cycle_codes"],
            }
            for t in CURRICULUM_TEMPLATES.values()
        ]
