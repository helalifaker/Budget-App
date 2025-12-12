"""
Planning Progress Service.

Service for tracking and validating budget planning progress across all 6 planning steps.
Dynamically calculates completion status by querying existing planning data.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import BudgetVersion
from app.models.planning import (
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    EnrollmentPlan,
    TeacherAllocation,
)
from app.schemas.planning_progress import (
    PlanningProgressResponse,
    StepBlocker,
    StepProgress,
    StepValidation,
)
from app.services.enrollment_capacity import get_effective_capacity


class PlanningProgressService:
    """
    Service for tracking planning progress and validation.

    Analyzes existing planning data to determine completion status for each
    of the 6 planning steps (enrollment, class_structure, dhg, revenue, costs, capex).
    """

    # Constants (capacity is per-version via enrollment_projection_configs)
    MIN_RECOMMENDED_STUDENTS = 500  # Minimum recommended enrollment
    OPTIMAL_MIN = 1000  # Optimal range minimum
    OPTIMAL_MAX = 1700  # Optimal range maximum
    MIN_REVENUE_PER_STUDENT = 10000  # SAR - minimum expected revenue per student
    ENROLLMENT_MATCH_TOLERANCE = 0.05  # 5% tolerance for class structure match
    ALLOCATION_IN_PROGRESS_THRESHOLD = 0.50  # 50% - marks DHG as in_progress
    ALLOCATION_COMPLETE_THRESHOLD = 0.90  # 90% - marks DHG as completed
    PERSONNEL_COST_MIN_RATIO = 0.60  # 60% - typical personnel cost ratio

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def get_planning_progress(
        self, budget_version_id: UUID
    ) -> PlanningProgressResponse:
        """
        Get comprehensive planning progress for a budget version.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            PlanningProgressResponse with progress for all 6 steps
        """
        # Validate budget version exists
        await self._get_budget_version(budget_version_id)

        # Validate all 6 steps
        enrollment_progress = await self._validate_enrollment_step(budget_version_id)
        class_structure_progress = await self._validate_class_structure_step(
            budget_version_id, enrollment_progress
        )
        dhg_progress = await self._validate_dhg_step(
            budget_version_id, class_structure_progress
        )
        revenue_progress = await self._validate_revenue_step(
            budget_version_id, enrollment_progress
        )
        costs_progress = await self._validate_costs_step(
            budget_version_id, dhg_progress
        )
        capex_progress = await self._validate_capex_step(budget_version_id)

        # Collect all steps
        steps = [
            enrollment_progress,
            class_structure_progress,
            dhg_progress,
            revenue_progress,
            costs_progress,
            capex_progress,
        ]

        # Calculate overall progress
        completed_steps = sum(1 for step in steps if step.status == "completed")
        overall_progress = (completed_steps / len(steps)) * 100

        return PlanningProgressResponse(
            budget_version_id=budget_version_id,
            overall_progress=overall_progress,
            completed_steps=completed_steps,
            total_steps=len(steps),
            steps=steps,
        )

    async def _get_budget_version(self, budget_version_id: UUID) -> BudgetVersion:
        """Get budget version or raise NotFoundError."""
        result = await self.db.execute(
            select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        )
        budget_version = result.scalar_one_or_none()
        if not budget_version:
            from app.services.exceptions import NotFoundError

            raise NotFoundError(f"Budget version {budget_version_id} not found")
        return budget_version

    # ==========================================================================
    # Step 1: Enrollment Planning
    # ==========================================================================

    async def _validate_enrollment_step(
        self, budget_version_id: UUID
    ) -> StepProgress:
        """
        Validate enrollment planning step.

        Checks:
        - enrollment_exists: At least 1 enrollment record exists
        - capacity_check: Total students <= 1,875 (max capacity)
        - capacity_warning: Total students < 500 (underutilized)
        - capacity_optimal: 1,000 <= total <= 1,700 (optimal range)
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # Get enrollment count and total students
        result = await self.db.execute(
            select(
                func.count(EnrollmentPlan.id), func.sum(EnrollmentPlan.student_count)
            ).where(EnrollmentPlan.budget_version_id == budget_version_id)
        )
        enrollment_count, total_students = result.one()
        total_students = int(total_students or 0)
        effective_capacity = await get_effective_capacity(self.db, budget_version_id)

        # Check: enrollment exists
        if enrollment_count == 0:
            validation.append(
                StepValidation(
                    check_id="enrollment_exists",
                    status="failed",
                    message="No enrollment data entered. Add at least one enrollment entry.",
                )
            )
            status = "not_started"
            progress_percentage = 0.0
        else:
            validation.append(
                StepValidation(
                    check_id="enrollment_exists",
                    status="passed",
                    message=f"Enrollment data exists ({enrollment_count} entries).",
                )
            )

            # Check: capacity limits
            if total_students > effective_capacity:
                validation.append(
                    StepValidation(
                        check_id="capacity_check",
                        status="failed",
                        message=f"Over capacity! Total enrollment {total_students} exceeds maximum {effective_capacity}.",
                        details={"total_students": total_students, "capacity": effective_capacity},
                    )
                )
                status = "error"
                progress_percentage = 50.0
            else:
                validation.append(
                    StepValidation(
                        check_id="capacity_check",
                        status="passed",
                        message=f"Enrollment within capacity ({total_students}/{effective_capacity}).",
                    )
                )

                # Warning: low enrollment
                if total_students < self.MIN_RECOMMENDED_STUDENTS:
                    validation.append(
                        StepValidation(
                            check_id="capacity_warning",
                            status="warning",
                            message=f"Low enrollment ({total_students}). Consider if this is financially viable.",
                            details={"total_students": total_students},
                        )
                    )

                # Info: optimal range
                if self.OPTIMAL_MIN <= total_students <= self.OPTIMAL_MAX:
                    validation.append(
                        StepValidation(
                            check_id="capacity_optimal",
                            status="info",
                            message=f"Enrollment within optimal range ({total_students} students).",
                        )
                    )

                status = "completed"
                progress_percentage = 100.0

        return StepProgress(
            step_id="enrollment",
            step_number=1,
            status=status,
            progress_percentage=progress_percentage,
            validation=validation,
            blockers=blockers,
            metrics={"total_students": total_students, "enrollment_count": enrollment_count},
        )

    # ==========================================================================
    # Step 2: Class Structure
    # ==========================================================================

    async def _validate_class_structure_step(
        self, budget_version_id: UUID, enrollment_progress: StepProgress
    ) -> StepProgress:
        """
        Validate class structure step.

        Checks:
        - enrollment_prerequisite: Enrollment step must be completed
        - class_structure_exists: Class structure records exist
        - enrollment_match: Total students matches enrollment (within 5% tolerance)
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # Check prerequisite: enrollment must be completed
        if enrollment_progress.status != "completed":
            blockers.append(
                StepBlocker(
                    message="Enrollment Planning must be completed first.",
                    resolution="Go to Enrollment Planning and enter student enrollment data.",
                )
            )
            validation.append(
                StepValidation(
                    check_id="enrollment_prerequisite",
                    status="failed",
                    message="Complete Enrollment Planning first.",
                )
            )
            return StepProgress(
                step_id="class_structure",
                step_number=2,
                status="blocked",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="enrollment_prerequisite",
                status="passed",
                message="Enrollment Planning completed.",
            )
        )

        # Get class structure data
        result = await self.db.execute(
            select(
                func.count(ClassStructure.id),
                func.sum(ClassStructure.total_students),
                func.sum(ClassStructure.number_of_classes),
            ).where(ClassStructure.budget_version_id == budget_version_id)
        )
        class_count, total_students_in_classes, total_classes = result.one()
        total_students_in_classes = int(total_students_in_classes or 0)
        total_classes = int(total_classes or 0)

        # Check: class structure exists
        if class_count == 0:
            validation.append(
                StepValidation(
                    check_id="class_structure_exists",
                    status="failed",
                    message="No class structure calculated. Click 'Calculate from Enrollment'.",
                )
            )
            return StepProgress(
                step_id="class_structure",
                step_number=2,
                status="not_started",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="class_structure_exists",
                status="passed",
                message=f"Class structure calculated ({total_classes} classes).",
            )
        )

        # Check: enrollment match (within 5% tolerance)
        enrollment_total = enrollment_progress.metrics.get("total_students", 0)
        if enrollment_total > 0:
            diff_percentage = abs(total_students_in_classes - enrollment_total) / enrollment_total
            if diff_percentage > self.ENROLLMENT_MATCH_TOLERANCE:
                validation.append(
                    StepValidation(
                        check_id="enrollment_match",
                        status="failed",
                        message=f"Total students in classes ({total_students_in_classes}) doesn't match enrollment ({enrollment_total}). Difference: {diff_percentage*100:.1f}%",
                        details={
                            "total_students_in_classes": total_students_in_classes,
                            "enrollment_total": enrollment_total,
                        },
                    )
                )
                status = "error"
                progress_percentage = 75.0
            else:
                validation.append(
                    StepValidation(
                        check_id="enrollment_match",
                        status="passed",
                        message=f"Total students matches enrollment (within {self.ENROLLMENT_MATCH_TOLERANCE*100:.0f}% tolerance).",
                    )
                )
                status = "completed"
                progress_percentage = 100.0
        else:
            status = "completed"
            progress_percentage = 100.0

        return StepProgress(
            step_id="class_structure",
            step_number=2,
            status=status,
            progress_percentage=progress_percentage,
            validation=validation,
            blockers=blockers,
            metrics={
                "total_classes": total_classes,
                "total_students_in_classes": total_students_in_classes,
            },
        )

    # ==========================================================================
    # Step 3: DHG Workforce Planning
    # ==========================================================================

    async def _validate_dhg_step(
        self, budget_version_id: UUID, class_structure_progress: StepProgress
    ) -> StepProgress:
        """
        Validate DHG workforce planning step.

        Checks:
        - class_structure_prerequisite: Class structure must be completed
        - subject_hours_calculated: DHG subject hours records exist
        - fte_calculated: Teacher FTE requirements calculated
        - allocations_entered: TRMD allocations entered (AEFE + Local)
        - allocations_complete: >= 90% of FTE allocated
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # Check prerequisite: class structure must be completed
        if class_structure_progress.status != "completed":
            blockers.append(
                StepBlocker(
                    message="Class Structure must be completed first.",
                    resolution="Go to Class Structure and calculate classes from enrollment.",
                )
            )
            validation.append(
                StepValidation(
                    check_id="class_structure_prerequisite",
                    status="failed",
                    message="Complete Class Structure first.",
                )
            )
            return StepProgress(
                step_id="dhg",
                step_number=3,
                status="blocked",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="class_structure_prerequisite",
                status="passed",
                message="Class Structure completed.",
            )
        )

        # Get DHG subject hours count
        subject_hours_result = await self.db.execute(
            select(func.count(DHGSubjectHours.id)).where(
                DHGSubjectHours.budget_version_id == budget_version_id
            )
        )
        subject_hours_count = subject_hours_result.scalar_one()

        if subject_hours_count == 0:
            validation.append(
                StepValidation(
                    check_id="subject_hours_calculated",
                    status="failed",
                    message="Subject hours not calculated. Click 'Calculate FTE'.",
                )
            )
            return StepProgress(
                step_id="dhg",
                step_number=3,
                status="not_started",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="subject_hours_calculated",
                status="passed",
                message=f"Subject hours calculated ({subject_hours_count} entries).",
            )
        )

        # Get teacher FTE requirements
        fte_result = await self.db.execute(
            select(
                func.count(DHGTeacherRequirement.id),
                func.sum(DHGTeacherRequirement.fte_required),
            ).where(DHGTeacherRequirement.budget_version_id == budget_version_id)
        )
        fte_count, total_fte_required = fte_result.one()
        total_fte_required = float(total_fte_required or 0.0)

        if fte_count == 0:
            validation.append(
                StepValidation(
                    check_id="fte_calculated",
                    status="failed",
                    message="Teacher FTE not calculated.",
                )
            )
            return StepProgress(
                step_id="dhg",
                step_number=3,
                status="in_progress",
                progress_percentage=25.0,
                validation=validation,
                blockers=blockers,
                metrics={"subject_hours_count": subject_hours_count},
            )

        validation.append(
            StepValidation(
                check_id="fte_calculated",
                status="passed",
                message=f"Teacher FTE calculated ({total_fte_required:.1f} FTE required).",
            )
        )

        # Get TRMD allocations
        allocations_result = await self.db.execute(
            select(func.sum(TeacherAllocation.fte_count)).where(
                TeacherAllocation.budget_version_id == budget_version_id
            )
        )
        total_allocated = float(allocations_result.scalar_one() or 0.0)

        # Calculate allocation percentage
        allocation_percentage = (
            (total_allocated / total_fte_required * 100) if total_fte_required > 0 else 0
        )

        if allocation_percentage < self.ALLOCATION_IN_PROGRESS_THRESHOLD * 100:
            validation.append(
                StepValidation(
                    check_id="allocations_entered",
                    status="warning",
                    message=f"TRMD allocations incomplete ({allocation_percentage:.0f}%). Enter AEFE and Local staff.",
                    details={
                        "allocated_fte": total_allocated,
                        "required_fte": total_fte_required,
                    },
                )
            )
            status = "in_progress"
            progress_percentage = 50.0
        elif allocation_percentage < self.ALLOCATION_COMPLETE_THRESHOLD * 100:
            validation.append(
                StepValidation(
                    check_id="allocations_entered",
                    status="info",
                    message=f"TRMD allocations in progress ({allocation_percentage:.0f}%).",
                    details={
                        "allocated_fte": total_allocated,
                        "required_fte": total_fte_required,
                    },
                )
            )
            status = "in_progress"
            progress_percentage = 75.0
        else:
            validation.append(
                StepValidation(
                    check_id="allocations_complete",
                    status="passed",
                    message=f"TRMD allocations complete ({allocation_percentage:.0f}%).",
                    details={
                        "allocated_fte": total_allocated,
                        "required_fte": total_fte_required,
                    },
                )
            )
            status = "completed"
            progress_percentage = 100.0

        return StepProgress(
            step_id="dhg",
            step_number=3,
            status=status,
            progress_percentage=progress_percentage,
            validation=validation,
            blockers=blockers,
            metrics={
                "subject_hours_count": subject_hours_count,
                "total_fte_required": total_fte_required,
                "total_allocated": total_allocated,
                "allocation_percentage": allocation_percentage,
            },
        )

    # ==========================================================================
    # Step 4: Revenue Planning
    # ==========================================================================

    async def _validate_revenue_step(
        self, budget_version_id: UUID, enrollment_progress: StepProgress
    ) -> StepProgress:
        """
        Validate revenue planning step.

        Checks:
        - enrollment_prerequisite: Enrollment must be completed
        - revenue_exists: Revenue records exist
        - revenue_positive: Total revenue > 0
        - revenue_low_warning: Revenue >= (enrollment × 10,000 SAR)
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # Check prerequisite: enrollment must be completed
        if enrollment_progress.status != "completed":
            blockers.append(
                StepBlocker(
                    message="Enrollment Planning must be completed first.",
                    resolution="Go to Enrollment Planning and enter student enrollment data.",
                )
            )
            validation.append(
                StepValidation(
                    check_id="enrollment_prerequisite",
                    status="failed",
                    message="Complete Enrollment Planning first.",
                )
            )
            return StepProgress(
                step_id="revenue",
                step_number=4,
                status="blocked",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="enrollment_prerequisite",
                status="passed",
                message="Enrollment Planning completed.",
            )
        )

        # Note: Revenue data would come from a Revenue model (not yet implemented)
        # For now, we'll return a placeholder indicating revenue step is pending implementation
        validation.append(
            StepValidation(
                check_id="revenue_exists",
                status="info",
                message="Revenue planning validation pending (Revenue model not yet implemented).",
            )
        )

        return StepProgress(
            step_id="revenue",
            step_number=4,
            status="not_started",
            progress_percentage=0.0,
            validation=validation,
            blockers=blockers,
            metrics={},
        )

    # ==========================================================================
    # Step 5: Cost Planning
    # ==========================================================================

    async def _validate_costs_step(
        self, budget_version_id: UUID, dhg_progress: StepProgress
    ) -> StepProgress:
        """
        Validate cost planning step.

        Checks:
        - dhg_prerequisite: DHG must be completed (for personnel costs)
        - personnel_costs_calculated: Personnel cost records exist
        - operating_costs_entered: Operating cost records exist
        - cost_ratio_check: Personnel costs >= 60% of total (typical ratio)
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # Check prerequisite: DHG must be completed
        if dhg_progress.status != "completed":
            blockers.append(
                StepBlocker(
                    message="DHG Workforce Planning must be completed first for personnel costs.",
                    resolution="Go to DHG and complete teacher FTE calculation and TRMD allocations.",
                )
            )
            validation.append(
                StepValidation(
                    check_id="dhg_prerequisite",
                    status="failed",
                    message="Complete DHG Workforce Planning first.",
                )
            )
            return StepProgress(
                step_id="costs",
                step_number=5,
                status="blocked",
                progress_percentage=0.0,
                validation=validation,
                blockers=blockers,
                metrics={},
            )

        validation.append(
            StepValidation(
                check_id="dhg_prerequisite",
                status="passed",
                message="DHG Workforce Planning completed.",
            )
        )

        # Note: Cost data would come from Cost models (not yet fully implemented)
        # For now, we'll return a placeholder
        validation.append(
            StepValidation(
                check_id="personnel_costs_calculated",
                status="info",
                message="Cost planning validation pending (Cost models not yet fully implemented).",
            )
        )

        return StepProgress(
            step_id="costs",
            step_number=5,
            status="not_started",
            progress_percentage=0.0,
            validation=validation,
            blockers=blockers,
            metrics={},
        )

    # ==========================================================================
    # Step 6: CapEx Planning
    # ==========================================================================

    async def _validate_capex_step(self, budget_version_id: UUID) -> StepProgress:
        """
        Validate CapEx planning step.

        Checks:
        - capex_optional: CapEx is optional (always info status)
        - capex_exists: CapEx records exist
        - depreciation_calculated: All CapEx items have depreciation
        """
        validation: list[StepValidation] = []
        blockers: list[StepBlocker] = []

        # CapEx is optional
        validation.append(
            StepValidation(
                check_id="capex_optional",
                status="info",
                message="CapEx planning is optional for budget completion.",
            )
        )

        # Note: CapEx data would come from CapEx model (not yet implemented)
        # For now, we'll return not_started
        return StepProgress(
            step_id="capex",
            step_number=6,
            status="not_started",
            progress_percentage=0.0,
            validation=validation,
            blockers=blockers,
            metrics={},
        )
