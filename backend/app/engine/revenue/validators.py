"""
Revenue Engine - Validators

Business rule validators for revenue calculations.
All validators are pure functions that raise exceptions on validation failure.

Business Rules:
---------------
1. Fees: All fees must be non-negative
2. Sibling order: Must be between 1 and 10 (reasonable maximum)
3. Trimester percentages: Must sum to 100% (1.00)
4. Fee categories: Must match allowed nationalities
5. Discount: Only applies to tuition, not DAI or registration
"""

from decimal import Decimal

from app.engine.revenue.models import (
    FeeCategory,
    TrimesterDistribution,
    TuitionInput,
)


class InvalidTuitionInputError(Exception):
    """Raised when tuition input data is invalid."""

    pass


class InvalidSiblingOrderError(Exception):
    """Raised when sibling order is outside valid range."""

    pass


class InvalidTrimesterPercentagesError(Exception):
    """Raised when trimester percentages don't sum to 100%."""

    pass


def validate_tuition_input(tuition_input: TuitionInput) -> None:
    """
    Validate tuition input data for business rules compliance.

    Business Rules:
    1. All fees must be non-negative
    2. Sibling order must be 1-10
    3. Tuition fee should be reasonable (> 0 for enrolled students)

    Args:
        tuition_input: Tuition input to validate

    Raises:
        InvalidTuitionInputError: If input violates business rules

    Example:
        >>> from uuid import uuid4
        >>> valid_input = TuitionInput(
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     fee_category=FeeCategory.FRENCH_TTC,
        ...     tuition_fee=Decimal("45000"),
        ...     dai_fee=Decimal("2000"),
        ...     registration_fee=Decimal("1000"),
        ...     sibling_order=1
        ... )
        >>> validate_tuition_input(valid_input)  # OK, no exception
    """
    # 1. Validate fees are non-negative
    if tuition_input.tuition_fee < 0:
        raise InvalidTuitionInputError(
            f"Tuition fee cannot be negative, got {tuition_input.tuition_fee}"
        )

    if tuition_input.dai_fee < 0:
        raise InvalidTuitionInputError(
            f"DAI fee cannot be negative, got {tuition_input.dai_fee}"
        )

    if tuition_input.registration_fee < 0:
        raise InvalidTuitionInputError(
            f"Registration fee cannot be negative, got {tuition_input.registration_fee}"
        )

    # 2. Validate sibling order
    validate_sibling_order(tuition_input.sibling_order)


def validate_sibling_order(sibling_order: int) -> None:
    """
    Validate sibling order is within reasonable range.

    Business Rule: Sibling order must be between 1 and 10.
    - 1: Eldest child
    - 2: Second child
    - 3+: Eligible for sibling discount
    - 10: Maximum (rare to have 10+ children)

    Args:
        sibling_order: Student order among siblings

    Raises:
        InvalidSiblingOrderError: If sibling order is outside valid range

    Example:
        >>> validate_sibling_order(1)  # OK - eldest
        >>> validate_sibling_order(3)  # OK - 3rd child (discount eligible)
        >>> validate_sibling_order(10)  # OK - maximum
        >>> validate_sibling_order(0)  # Raises - invalid
        Traceback (most recent call last):
        ...
        InvalidSiblingOrderError: Sibling order must be between 1 and 10, got 0
        >>> validate_sibling_order(15)  # Raises - too high
        Traceback (most recent call last):
        ...
        InvalidSiblingOrderError: Sibling order must be between 1 and 10, got 15
    """
    if not (1 <= sibling_order <= 10):
        raise InvalidSiblingOrderError(
            f"Sibling order must be between 1 and 10, got {sibling_order}"
        )


def validate_trimester_percentages(
    t1_pct: Decimal,
    t2_pct: Decimal,
    t3_pct: Decimal,
    tolerance: Decimal = Decimal("0.001"),
) -> None:
    """
    Validate that trimester percentages sum to 100% (1.00).

    Business Rule: Trimester percentages must sum to exactly 1.00 (100%).
    Standard distribution: T1: 40%, T2: 30%, T3: 30%

    Args:
        t1_pct: Trimester 1 percentage
        t2_pct: Trimester 2 percentage
        t3_pct: Trimester 3 percentage
        tolerance: Allowed tolerance for rounding (default: 0.001)

    Raises:
        InvalidTrimesterPercentagesError: If percentages don't sum to 1.00

    Example:
        >>> validate_trimester_percentages(
        ...     Decimal("0.40"), Decimal("0.30"), Decimal("0.30")
        ... )  # OK - standard distribution
        >>> validate_trimester_percentages(
        ...     Decimal("0.50"), Decimal("0.25"), Decimal("0.25")
        ... )  # OK - custom distribution
        >>> validate_trimester_percentages(
        ...     Decimal("0.40"), Decimal("0.40"), Decimal("0.40")
        ... )  # Raises - sums to 1.20
        Traceback (most recent call last):
        ...
        InvalidTrimesterPercentagesError: Trimester percentages must sum to 1.00, got 1.20
    """
    total_pct = t1_pct + t2_pct + t3_pct

    if abs(total_pct - Decimal("1.00")) > tolerance:
        raise InvalidTrimesterPercentagesError(
            f"Trimester percentages must sum to 1.00, got {total_pct} "
            f"({t1_pct} + {t2_pct} + {t3_pct})"
        )


def validate_trimester_distribution(
    distribution: TrimesterDistribution,
) -> None:
    """
    Validate trimester distribution is consistent.

    Checks that:
    1. Percentages sum to 100%
    2. Trimester amounts match percentages of total
    3. All amounts are non-negative

    Args:
        distribution: Trimester distribution to validate

    Raises:
        InvalidTrimesterPercentagesError: If distribution is inconsistent

    Example:
        >>> distribution = TrimesterDistribution(
        ...     total_revenue=Decimal("45000"),
        ...     trimester_1=Decimal("18000"),
        ...     trimester_2=Decimal("13500"),
        ...     trimester_3=Decimal("13500"),
        ...     t1_percentage=Decimal("0.40"),
        ...     t2_percentage=Decimal("0.30"),
        ...     t3_percentage=Decimal("0.30")
        ... )
        >>> validate_trimester_distribution(distribution)  # OK
    """
    # 1. Validate percentages sum to 100%
    validate_trimester_percentages(
        distribution.t1_percentage,
        distribution.t2_percentage,
        distribution.t3_percentage,
    )

    # 2. Validate trimester amounts are non-negative
    if distribution.trimester_1 < 0:
        raise InvalidTrimesterPercentagesError(
            f"Trimester 1 amount cannot be negative, got {distribution.trimester_1}"
        )

    if distribution.trimester_2 < 0:
        raise InvalidTrimesterPercentagesError(
            f"Trimester 2 amount cannot be negative, got {distribution.trimester_2}"
        )

    if distribution.trimester_3 < 0:
        raise InvalidTrimesterPercentagesError(
            f"Trimester 3 amount cannot be negative, got {distribution.trimester_3}"
        )

    # 3. Validate trimester amounts roughly match percentages (allow 1 SAR tolerance for rounding)
    expected_t1 = distribution.total_revenue * distribution.t1_percentage
    expected_t2 = distribution.total_revenue * distribution.t2_percentage
    expected_t3 = distribution.total_revenue * distribution.t3_percentage

    if abs(distribution.trimester_1 - expected_t1) > Decimal("1.0"):
        raise InvalidTrimesterPercentagesError(
            f"Trimester 1 amount {distribution.trimester_1} doesn't match "
            f"expected {expected_t1:.2f} (total × {distribution.t1_percentage})"
        )

    if abs(distribution.trimester_2 - expected_t2) > Decimal("1.0"):
        raise InvalidTrimesterPercentagesError(
            f"Trimester 2 amount {distribution.trimester_2} doesn't match "
            f"expected {expected_t2:.2f} (total × {distribution.t2_percentage})"
        )

    if abs(distribution.trimester_3 - expected_t3) > Decimal("1.0"):
        raise InvalidTrimesterPercentagesError(
            f"Trimester 3 amount {distribution.trimester_3} doesn't match "
            f"expected {expected_t3:.2f} (total × {distribution.t3_percentage})"
        )


def validate_fee_non_negative(fee_amount: Decimal, fee_name: str = "Fee") -> None:
    """
    Validate that a fee amount is non-negative.

    Args:
        fee_amount: Fee amount to validate
        fee_name: Name of the fee (for error message)

    Raises:
        ValueError: If fee is negative

    Example:
        >>> validate_fee_non_negative(Decimal("45000"), "Tuition")  # OK
        >>> validate_fee_non_negative(Decimal("-1000"), "DAI")  # Raises
        Traceback (most recent call last):
        ...
        ValueError: DAI cannot be negative, got -1000
    """
    if fee_amount < 0:
        raise ValueError(f"{fee_name} cannot be negative, got {fee_amount}")


def validate_fee_category(
    fee_category: FeeCategory,
    allowed_categories: list[FeeCategory] | None = None,
) -> None:
    """
    Validate fee category is allowed.

    Args:
        fee_category: Fee category to validate
        allowed_categories: List of allowed categories (None = all allowed)

    Raises:
        ValueError: If fee category is not in allowed list

    Example:
        >>> validate_fee_category(FeeCategory.FRENCH_TTC)  # OK (all allowed)
        >>> validate_fee_category(
        ...     FeeCategory.FRENCH_TTC,
        ...     [FeeCategory.FRENCH_TTC, FeeCategory.OTHER_TTC]
        ... )  # OK
        >>> validate_fee_category(
        ...     FeeCategory.SAUDI_HT,
        ...     [FeeCategory.FRENCH_TTC, FeeCategory.OTHER_TTC]
        ... )  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Fee category saudi_ht is not in allowed list...
    """
    if allowed_categories is not None:
        if fee_category not in allowed_categories:
            allowed_str = ", ".join([cat.value for cat in allowed_categories])
            raise ValueError(
                f"Fee category {fee_category.value} is not in allowed list: {allowed_str}"
            )


def validate_discount_rate(discount_rate: Decimal) -> None:
    """
    Validate discount rate is within reasonable range.

    Business Rule: Discount rate must be between 0% and 50%.
    - 0%: No discount
    - 25%: Standard sibling discount
    - 50%: Maximum (more than 50% would be unusual)

    Args:
        discount_rate: Discount rate (0.00 to 0.50)

    Raises:
        ValueError: If discount rate is outside range

    Example:
        >>> validate_discount_rate(Decimal("0.00"))  # OK - no discount
        >>> validate_discount_rate(Decimal("0.25"))  # OK - standard sibling
        >>> validate_discount_rate(Decimal("0.50"))  # OK - maximum
        >>> validate_discount_rate(Decimal("0.75"))  # Raises - too high
        Traceback (most recent call last):
        ...
        ValueError: Discount rate must be between 0 and 0.50, got 0.75
    """
    if not (Decimal("0.00") <= discount_rate <= Decimal("0.50")):
        raise ValueError(
            f"Discount rate must be between 0 and 0.50, got {discount_rate}"
        )


def validate_revenue_positive(revenue: Decimal) -> None:
    """
    Validate that revenue is positive.

    While fees can be zero, total revenue for an enrolled student should be positive.

    Args:
        revenue: Revenue amount to validate

    Raises:
        ValueError: If revenue is not positive

    Example:
        >>> validate_revenue_positive(Decimal("45000"))  # OK
        >>> validate_revenue_positive(Decimal("0"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Revenue must be positive, got 0
    """
    if revenue <= 0:
        raise ValueError(f"Revenue must be positive, got {revenue}")
