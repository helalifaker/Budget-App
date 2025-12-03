"""
Class Structure Validation.

Validates that class structures conform to class size parameters.

Business Rule (HIGH-4 from Phase 0-3 review):
    avg_class_size must be within the bounds defined in class_size_params table
    for the corresponding level or cycle.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import AcademicLevel, ClassSizeParam
from app.services.exceptions import ValidationError


class ClassStructureValidationError(ValueError):
    """Raised when class structure violates class size constraints."""

    pass


async def validate_class_structure(
    session: AsyncSession,
    level_id: UUID,
    avg_class_size: Decimal,
    number_of_classes: int,
    total_students: int,
) -> None:
    """
    Validate that average class size is within configured bounds.

    Args:
        session: Database session
        level_id: Academic level ID
        avg_class_size: Calculated average class size
        number_of_classes: Number of classes
        total_students: Total number of students

    Raises:
        ClassStructureValidationError: If avg_class_size violates constraints

    Business Rules:
        1. avg_class_size must be >= min_class_size (from class_size_params)
        2. avg_class_size must be <= max_class_size (from class_size_params)
        3. Level-specific parameters override cycle defaults
        4. Validation considers both level-specific and cycle-level parameters

    Example:
        >>> # Level 6ème has min=18, max=30
        >>> await validate_class_structure(
        ...     session=session,
        ...     level_id=sixieme_id,
        ...     avg_class_size=Decimal("25.5"),  # ✅ Valid (18 <= 25.5 <= 30)
        ...     number_of_classes=6,
        ...     total_students=153
        ... )

        >>> await validate_class_structure(
        ...     session=session,
        ...     level_id=sixieme_id,
        ...     avg_class_size=Decimal("35.0"),  # ❌ Invalid (> 30)
        ...     number_of_classes=4,
        ...     total_students=140
        ... )
        ClassStructureValidationError: Average class size 35.0 exceeds maximum 30 for level 6ème
    """
    # First, get the level information to access its cycle
    level_query = select(AcademicLevel).where(AcademicLevel.id == level_id)
    level_result = await session.execute(level_query)
    level = level_result.scalar_one_or_none()

    if not level:
        raise ClassStructureValidationError(
            f"Academic level {level_id} not found"
        )

    # Look for class size parameters
    # Priority 1: Level-specific parameter
    level_param_query = (
        select(ClassSizeParam)
        .where(ClassSizeParam.level_id == level_id)
        .where(ClassSizeParam.deleted_at.is_(None))
    )
    level_param_result = await session.execute(level_param_query)
    level_param = level_param_result.scalar_one_or_none()

    # Priority 2: Cycle-level parameter (if no level-specific param)
    cycle_param: ClassSizeParam | None = None
    if not level_param and level.cycle_id:
        cycle_param_query = (
            select(ClassSizeParam)
            .where(ClassSizeParam.cycle_id == level.cycle_id)
            .where(ClassSizeParam.level_id.is_(None))
            .where(ClassSizeParam.deleted_at.is_(None))
        )
        cycle_param_result = await session.execute(cycle_param_query)
        cycle_param = cycle_param_result.scalar_one_or_none()

    # Use whichever parameter was found (level-specific takes priority)
    param = level_param or cycle_param

    if not param:
        # No constraints defined - allow any class size
        # This is valid for flexible planning scenarios
        return

    # Validate minimum class size
    if avg_class_size < param.min_class_size:
        raise ClassStructureValidationError(
            f"Average class size {avg_class_size} is below minimum "
            f"{param.min_class_size} for level {level.name_en}. "
            f"Current structure: {number_of_classes} classes, "
            f"{total_students} students. "
            f"Consider reducing number of classes."
        )

    # Validate maximum class size
    if avg_class_size > param.max_class_size:
        raise ClassStructureValidationError(
            f"Average class size {avg_class_size} exceeds maximum "
            f"{param.max_class_size} for level {level.name_en}. "
            f"Current structure: {number_of_classes} classes, "
            f"{total_students} students. "
            f"Consider adding more classes."
        )

    # Validation passed
    return


def validate_class_structure_sync(
    min_class_size: int,
    max_class_size: int,
    avg_class_size: Decimal,
    level_name: str,
    number_of_classes: int,
    total_students: int,
) -> None:
    """
    Synchronous validation for class structure (for use in Pydantic validators).

    This is a simpler version that doesn't query the database.
    Use when class size parameters are already known.

    Args:
        min_class_size: Minimum allowed average class size
        max_class_size: Maximum allowed average class size
        avg_class_size: Calculated average class size
        level_name: Name of the academic level (for error messages)
        number_of_classes: Number of classes
        total_students: Total number of students

    Raises:
        ClassStructureValidationError: If avg_class_size violates constraints

    Example:
        >>> validate_class_structure_sync(
        ...     min_class_size=18,
        ...     max_class_size=30,
        ...     avg_class_size=Decimal("25.5"),
        ...     level_name="6ème",
        ...     number_of_classes=6,
        ...     total_students=153
        ... )  # ✅ No error

        >>> validate_class_structure_sync(
        ...     min_class_size=18,
        ...     max_class_size=30,
        ...     avg_class_size=Decimal("35.0"),
        ...     level_name="6ème",
        ...     number_of_classes=4,
        ...     total_students=140
        ... )
        ClassStructureValidationError: Average class size 35.0 exceeds maximum 30 for level 6ème
    """
    # Validate minimum class size
    if avg_class_size < min_class_size:
        raise ClassStructureValidationError(
            f"Average class size {avg_class_size} is below minimum "
            f"{min_class_size} for level {level_name}. "
            f"Current structure: {number_of_classes} classes, "
            f"{total_students} students. "
            f"Consider reducing number of classes."
        )

    # Validate maximum class size
    if avg_class_size > max_class_size:
        raise ClassStructureValidationError(
            f"Average class size {avg_class_size} exceeds maximum "
            f"{max_class_size} for level {level_name}. "
            f"Current structure: {number_of_classes} classes, "
            f"{total_students} students. "
            f"Consider adding more classes."
        )

    # Validation passed
    return


def validate_class_size_params(min_size: int, target_size: int, max_size: int) -> None:
    """
    Validate that class size parameters follow min < target <= max.
    """
    if not (min_size < target_size <= max_size):
        raise ValidationError("Invalid class size parameters: require min < target <= max")


def validate_enrollment_distribution(total_students: int, distributions: dict[str, int]) -> None:
    """
    Validate that enrollment distribution sums to total and has no negatives.
    """
    if any(count < 0 for count in distributions.values()):
        raise ValidationError("Enrollment distribution cannot contain negative values")

    if sum(distributions.values()) != total_students:
        raise ValidationError("Enrollment distribution must equal total students")
