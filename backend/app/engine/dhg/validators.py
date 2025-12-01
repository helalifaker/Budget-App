"""
DHG Engine - Validators

Business rule validators for DHG calculations.
All validators are pure functions that raise exceptions on validation failure.

Business Rules:
---------------
1. Subject hours: 0 to 10 hours per week per subject
2. Class count: 0 to 50 classes per level (reasonable maximum)
3. HSA limits: 2-4 hours maximum per teacher per week
4. Standard hours: 18h/week (secondary), 24h/week (primary)
5. FTE must be non-negative
6. DHG hours must be non-negative
"""

from decimal import Decimal
from typing import List

from app.engine.dhg.models import (
    EducationLevel,
    DHGInput,
    SubjectHours,
    HSAAllocation,
)


class InvalidDHGInputError(Exception):
    """Raised when DHG input data is invalid."""

    pass


class InvalidSubjectHoursError(Exception):
    """Raised when subject hours configuration is invalid."""

    pass


class InvalidHSAAllocationError(Exception):
    """Raised when HSA allocation exceeds limits."""

    pass


def validate_dhg_input(dhg_input: DHGInput) -> None:
    """
    Validate DHG input data for business rules compliance.

    Business Rules:
    1. Number of classes: 0 to 50 (reasonable maximum)
    2. Subject hours list cannot be empty
    3. All subject hours must be for the same level
    4. Subject hours must be within 0-10h per week

    Args:
        dhg_input: DHG input to validate

    Raises:
        InvalidDHGInputError: If input violates business rules

    Example:
        >>> from uuid import uuid4
        >>> valid_input = DHGInput(
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6,
        ...     subject_hours_list=[
        ...         SubjectHours(
        ...             subject_id=uuid4(),
        ...             subject_code="MATH",
        ...             subject_name="Mathématiques",
        ...             level_id=uuid4(),
        ...             level_code="6EME",
        ...             hours_per_week=Decimal("4.5")
        ...         )
        ...     ]
        ... )
        >>> validate_dhg_input(valid_input)  # OK, no exception
    """
    # 1. Validate class count
    if not (0 <= dhg_input.number_of_classes <= 50):
        raise InvalidDHGInputError(
            f"Number of classes must be between 0 and 50, got {dhg_input.number_of_classes}"
        )

    # 2. Validate subject hours list is not empty
    if not dhg_input.subject_hours_list:
        raise InvalidDHGInputError(
            f"Subject hours list cannot be empty for level {dhg_input.level_code}"
        )

    # 3. Validate all subject hours are for the same level
    for subject_hours in dhg_input.subject_hours_list:
        if subject_hours.level_id != dhg_input.level_id:
            raise InvalidDHGInputError(
                f"Subject hours for {subject_hours.subject_code} "
                f"has mismatched level_id (expected {dhg_input.level_id}, "
                f"got {subject_hours.level_id})"
            )

        if subject_hours.level_code != dhg_input.level_code:
            raise InvalidDHGInputError(
                f"Subject hours for {subject_hours.subject_code} "
                f"has mismatched level_code (expected {dhg_input.level_code}, "
                f"got {subject_hours.level_code})"
            )


def validate_subject_hours(subject_hours: SubjectHours) -> None:
    """
    Validate subject hours configuration.

    Business Rule: Hours per week must be between 0 and 10.
    - 0 hours: Subject not taught at this level
    - 1-10 hours: Normal range for subject teaching
    - >10 hours: Unreasonable (single subject taking half the week)

    Args:
        subject_hours: Subject hours to validate

    Raises:
        InvalidSubjectHoursError: If hours are outside valid range

    Example:
        >>> valid_hours = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("4.5")
        ... )
        >>> validate_subject_hours(valid_hours)  # OK
        >>> invalid_hours = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("15.0")  # Too many!
        ... )
        >>> validate_subject_hours(invalid_hours)
        Traceback (most recent call last):
        ...
        InvalidSubjectHoursError: Hours per week for MATH must be between 0 and 10, got 15.0
    """
    if not (Decimal("0") <= subject_hours.hours_per_week <= Decimal("10")):
        raise InvalidSubjectHoursError(
            f"Hours per week for {subject_hours.subject_code} "
            f"must be between 0 and 10, got {subject_hours.hours_per_week}"
        )

    # Validate that hours are reasonable (not negative after validation)
    if subject_hours.hours_per_week < 0:
        raise InvalidSubjectHoursError(
            f"Hours per week for {subject_hours.subject_code} cannot be negative"
        )


def validate_hsa_limits(
    hsa_allocation: HSAAllocation,
) -> None:
    """
    Validate HSA allocation is within business rule limits.

    Business Rule: Max 2-4 hours HSA per teacher per week.
    - If HSA exceeds limit, additional teachers must be hired.

    Args:
        hsa_allocation: HSA allocation to validate

    Raises:
        InvalidHSAAllocationError: If HSA exceeds limits

    Example:
        >>> # Valid: 6 hours needed, 5 teachers → 1.2h per teacher (OK)
        >>> valid_hsa = HSAAllocation(
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     dhg_hours_needed=Decimal("96.0"),
        ...     available_fte=5,
        ...     available_hours=Decimal("90.0"),
        ...     hsa_hours_needed=Decimal("6.0"),
        ...     hsa_within_limit=True,
        ...     max_hsa_per_teacher=Decimal("4.0")
        ... )
        >>> validate_hsa_limits(valid_hsa)  # OK
        >>> # Invalid: 25 hours needed, 5 teachers → 5h per teacher (exceeds 4h limit)
        >>> invalid_hsa = HSAAllocation(
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     dhg_hours_needed=Decimal("115.0"),
        ...     available_fte=5,
        ...     available_hours=Decimal("90.0"),
        ...     hsa_hours_needed=Decimal("25.0"),
        ...     hsa_within_limit=False,
        ...     max_hsa_per_teacher=Decimal("4.0")
        ... )
        >>> validate_hsa_limits(invalid_hsa)
        Traceback (most recent call last):
        ...
        InvalidHSAAllocationError: HSA for MATH exceeds limit...
    """
    if not hsa_allocation.hsa_within_limit:
        if hsa_allocation.available_fte > 0:
            hsa_per_teacher = (
                hsa_allocation.hsa_hours_needed / Decimal(hsa_allocation.available_fte)
            )
            raise InvalidHSAAllocationError(
                f"HSA for {hsa_allocation.subject_code} exceeds limit: "
                f"{hsa_allocation.hsa_hours_needed}h needed across "
                f"{hsa_allocation.available_fte} teachers "
                f"= {hsa_per_teacher:.2f}h per teacher "
                f"(max: {hsa_allocation.max_hsa_per_teacher}h). "
                f"Additional teachers must be hired."
            )
        else:
            raise InvalidHSAAllocationError(
                f"HSA for {hsa_allocation.subject_code} cannot be allocated: "
                f"no available FTE positions"
            )


def validate_max_hsa_per_teacher(max_hsa: Decimal) -> None:
    """
    Validate max HSA per teacher is within allowed range.

    Business Rule: Max HSA must be between 2 and 4 hours per week.

    Args:
        max_hsa: Maximum HSA hours per teacher

    Raises:
        ValueError: If max HSA is outside allowed range

    Example:
        >>> validate_max_hsa_per_teacher(Decimal("4.0"))  # OK
        >>> validate_max_hsa_per_teacher(Decimal("2.0"))  # OK
        >>> validate_max_hsa_per_teacher(Decimal("5.0"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Max HSA per teacher must be between 2 and 4, got 5.0
    """
    if not (Decimal("2.0") <= max_hsa <= Decimal("4.0")):
        raise ValueError(f"Max HSA per teacher must be between 2 and 4, got {max_hsa}")


def validate_education_level_standard_hours(
    education_level: EducationLevel,
    expected_hours: Decimal,
) -> None:
    """
    Validate that standard hours match education level.

    Business Rule:
    - Primary: 24 hours/week
    - Secondary: 18 hours/week

    Args:
        education_level: Education level
        expected_hours: Expected standard hours for this level

    Raises:
        ValueError: If standard hours don't match education level

    Example:
        >>> validate_education_level_standard_hours(
        ...     EducationLevel.SECONDARY,
        ...     Decimal("18.0")
        ... )  # OK
        >>> validate_education_level_standard_hours(
        ...     EducationLevel.SECONDARY,
        ...     Decimal("24.0")
        ... )  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Secondary education should have 18 hours/week, got 24.0
    """
    if education_level == EducationLevel.PRIMARY:
        if expected_hours != Decimal("24.0"):
            raise ValueError(
                f"Primary education should have 24 hours/week, got {expected_hours}"
            )
    elif education_level == EducationLevel.SECONDARY:
        if expected_hours != Decimal("18.0"):
            raise ValueError(
                f"Secondary education should have 18 hours/week, got {expected_hours}"
            )


def validate_fte_non_negative(fte: Decimal) -> None:
    """
    Validate FTE is non-negative.

    Args:
        fte: FTE value to validate

    Raises:
        ValueError: If FTE is negative

    Example:
        >>> validate_fte_non_negative(Decimal("5.33"))  # OK
        >>> validate_fte_non_negative(Decimal("-1.0"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: FTE cannot be negative, got -1.0
    """
    if fte < 0:
        raise ValueError(f"FTE cannot be negative, got {fte}")


def validate_dhg_hours_non_negative(dhg_hours: Decimal) -> None:
    """
    Validate DHG hours are non-negative.

    Args:
        dhg_hours: DHG hours value to validate

    Raises:
        ValueError: If DHG hours are negative

    Example:
        >>> validate_dhg_hours_non_negative(Decimal("96.0"))  # OK
        >>> validate_dhg_hours_non_negative(Decimal("-10.0"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: DHG hours cannot be negative, got -10.0
    """
    if dhg_hours < 0:
        raise ValueError(f"DHG hours cannot be negative, got {dhg_hours}")


def validate_subject_hours_list_consistency(
    subject_hours_list: List[SubjectHours],
) -> None:
    """
    Validate that subject hours list is consistent.

    Business Rules:
    1. List must not be empty
    2. All subject hours must be for the same level
    3. No duplicate subjects

    Args:
        subject_hours_list: List of subject hours to validate

    Raises:
        InvalidSubjectHoursError: If list is inconsistent

    Example:
        >>> subject1 = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("4.5")
        ... )
        >>> subject2 = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="FRAN",
        ...     subject_name="Français",
        ...     level_id=subject1.level_id,  # Same level
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("5.0")
        ... )
        >>> validate_subject_hours_list_consistency([subject1, subject2])  # OK
    """
    # 1. List must not be empty
    if not subject_hours_list:
        raise InvalidSubjectHoursError("Subject hours list cannot be empty")

    # 2. All subject hours must be for the same level
    first_level_id = subject_hours_list[0].level_id
    first_level_code = subject_hours_list[0].level_code

    for subject_hours in subject_hours_list:
        if subject_hours.level_id != first_level_id:
            raise InvalidSubjectHoursError(
                f"All subject hours must have the same level_id "
                f"(expected {first_level_id}, got {subject_hours.level_id} "
                f"for {subject_hours.subject_code})"
            )

        if subject_hours.level_code != first_level_code:
            raise InvalidSubjectHoursError(
                f"All subject hours must have the same level_code "
                f"(expected {first_level_code}, got {subject_hours.level_code} "
                f"for {subject_hours.subject_code})"
            )

    # 3. No duplicate subjects
    subject_codes = [sh.subject_code for sh in subject_hours_list]
    if len(subject_codes) != len(set(subject_codes)):
        duplicates = [code for code in subject_codes if subject_codes.count(code) > 1]
        raise InvalidSubjectHoursError(
            f"Duplicate subjects found: {set(duplicates)}"
        )
