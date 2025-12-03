"""
Revenue Engine - Calculator Functions

Pure calculation functions for tuition revenue and fee calculations.
All functions are stateless with no side effects.

Formulas:
---------
Sibling Discount:
    IF sibling_order >= 3 THEN
        discount = tuition × 0.25
        net_tuition = tuition - discount
    ELSE
        discount = 0
        net_tuition = tuition

Business Rule: Discount ONLY applies to tuition, NOT to DAI or registration fees.

Trimester Distribution:
    T1 = total_revenue × 0.40  (40%)
    T2 = total_revenue × 0.30  (30%)
    T3 = total_revenue × 0.30  (30%)

Total Revenue:
    total = net_tuition + dai + registration
"""

from decimal import Decimal

from app.engine.revenue.models import (
    FeeCategory,
    SiblingDiscount,
    StudentRevenueResult,
    TrimesterDistribution,
    TuitionInput,
    TuitionRevenue,
)

# Sibling discount configuration
SIBLING_DISCOUNT_THRESHOLD = 3  # Discount applies to 3rd+ child
SIBLING_DISCOUNT_RATE = Decimal("0.25")  # 25% discount

# Trimester distribution percentages
TRIMESTER_1_PCT = Decimal("0.40")  # 40%
TRIMESTER_2_PCT = Decimal("0.30")  # 30%
TRIMESTER_3_PCT = Decimal("0.30")  # 30%


def quantize_currency(value: Decimal) -> Decimal:
    """Ensure currency amounts have two decimal places."""
    return value.quantize(Decimal("0.01"))


def calculate_sibling_discount(
    tuition_amount: Decimal,
    sibling_order: int,
) -> SiblingDiscount:
    """
    Calculate sibling discount on tuition.

    Business Rule: 25% discount on tuition for 3rd+ child only.
    NOT applicable to DAI or registration fees.

    Args:
        tuition_amount: Base annual tuition (SAR)
        sibling_order: Student order among siblings (1=eldest, 2=second, etc.)

    Returns:
        SiblingDiscount with discount details

    Example:
        >>> # 1st child: No discount
        >>> discount = calculate_sibling_discount(Decimal("45000"), 1)
        >>> discount.discount_applicable
        False
        >>> discount.net_tuition
        Decimal('45000')
        >>> # 3rd child: 25% discount
        >>> discount = calculate_sibling_discount(Decimal("45000"), 3)
        >>> discount.discount_applicable
        True
        >>> discount.discount_amount
        Decimal('11250.00')  # 45000 × 0.25
        >>> discount.net_tuition
        Decimal('33750.00')  # 45000 - 11250
    """
    # Determine if discount applies (3rd+ child)
    tuition_amount = quantize_currency(tuition_amount)
    discount_applicable = sibling_order >= SIBLING_DISCOUNT_THRESHOLD

    if discount_applicable:
        discount_rate = SIBLING_DISCOUNT_RATE
        discount_amount = tuition_amount * discount_rate
        net_tuition = tuition_amount - discount_amount
    else:
        discount_rate = Decimal("0")
        discount_amount = Decimal("0")
        net_tuition = tuition_amount

    return SiblingDiscount(
        sibling_order=sibling_order,
        discount_applicable=discount_applicable,
        discount_rate=discount_rate,
        base_tuition=tuition_amount,
        discount_amount=discount_amount.quantize(Decimal("0.01")),
        net_tuition=net_tuition.quantize(Decimal("0.01")),
    )


def calculate_tuition_revenue(
    tuition_input: TuitionInput,
) -> TuitionRevenue:
    """
    Calculate tuition revenue for a student.

    Applies sibling discount if applicable and calculates net revenue.

    Args:
        tuition_input: Tuition input with fees and sibling information

    Returns:
        TuitionRevenue with base fees, discounts, and net amounts

    Example:
        >>> from uuid import uuid4
        >>> input_data = TuitionInput(
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     fee_category=FeeCategory.FRENCH_TTC,
        ...     tuition_fee=Decimal("45000"),
        ...     dai_fee=Decimal("2000"),
        ...     registration_fee=Decimal("1000"),
        ...     sibling_order=3  # 3rd child
        ... )
        >>> result = calculate_tuition_revenue(input_data)
        >>> result.sibling_discount_amount
        Decimal('11250.00')
        >>> result.net_tuition
        Decimal('33750.00')
        >>> result.total_revenue
        Decimal('36750.00')  # 33750 + 2000 + 1000
    """
    base_tuition = quantize_currency(tuition_input.tuition_fee)
    base_dai = quantize_currency(tuition_input.dai_fee)
    base_registration = quantize_currency(tuition_input.registration_fee)

    # Calculate sibling discount on tuition ONLY
    sibling_discount = calculate_sibling_discount(
        base_tuition,
        tuition_input.sibling_order,
    )

    # DAI and registration fees are NOT discounted
    net_dai = quantize_currency(base_dai)
    net_registration = quantize_currency(base_registration)

    # Calculate total revenue
    total_revenue = sibling_discount.net_tuition + net_dai + net_registration

    return TuitionRevenue(
        student_id=tuition_input.student_id,
        level_code=tuition_input.level_code,
        fee_category=tuition_input.fee_category,
        base_tuition=base_tuition,
        base_dai=base_dai,
        base_registration=base_registration,
        sibling_discount_amount=sibling_discount.discount_amount,
        sibling_discount_rate=sibling_discount.discount_rate,
        net_tuition=sibling_discount.net_tuition,
        net_dai=net_dai,
        net_registration=net_registration,
        total_revenue=total_revenue.quantize(Decimal("0.01")),
    )


def calculate_trimester_distribution(
    total_revenue: Decimal,
    t1_pct: Decimal = TRIMESTER_1_PCT,
    t2_pct: Decimal = TRIMESTER_2_PCT,
    t3_pct: Decimal = TRIMESTER_3_PCT,
) -> TrimesterDistribution:
    """
    Calculate trimester-based revenue distribution.

    Business Rule: T1: 40%, T2: 30%, T3: 30%

    Args:
        total_revenue: Total annual revenue (SAR)
        t1_pct: Trimester 1 percentage (default: 40%)
        t2_pct: Trimester 2 percentage (default: 30%)
        t3_pct: Trimester 3 percentage (default: 30%)

    Returns:
        TrimesterDistribution with revenue split by trimester

    Example:
        >>> distribution = calculate_trimester_distribution(Decimal("45000"))
        >>> distribution.trimester_1
        Decimal('18000.00')  # 45000 × 0.40
        >>> distribution.trimester_2
        Decimal('13500.00')  # 45000 × 0.30
        >>> distribution.trimester_3
        Decimal('13500.00')  # 45000 × 0.30
    """
    # Validate percentages sum to 100%
    total_pct = t1_pct + t2_pct + t3_pct
    if abs(total_pct - Decimal("1.00")) > Decimal("0.001"):
        raise ValueError(
            f"Trimester percentages must sum to 1.00, got {total_pct} "
            f"({t1_pct} + {t2_pct} + {t3_pct})"
        )

    # Calculate trimester amounts
    trimester_1 = (total_revenue * t1_pct).quantize(Decimal("0.01"))
    trimester_2 = (total_revenue * t2_pct).quantize(Decimal("0.01"))
    trimester_3 = (total_revenue * t3_pct).quantize(Decimal("0.01"))

    return TrimesterDistribution(
        total_revenue=total_revenue,
        trimester_1=trimester_1,
        trimester_2=trimester_2,
        trimester_3=trimester_3,
        t1_percentage=t1_pct,
        t2_percentage=t2_pct,
        t3_percentage=t3_pct,
    )


def calculate_total_student_revenue(
    tuition_input: TuitionInput,
) -> StudentRevenueResult:
    """
    Calculate complete student revenue with tuition and trimester distribution.

    Combines tuition calculation with trimester-based revenue recognition.

    Args:
        tuition_input: Tuition input with fees and sibling information

    Returns:
        StudentRevenueResult with complete revenue breakdown

    Example:
        >>> from uuid import uuid4
        >>> input_data = TuitionInput(
        ...     student_id=uuid4(),
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     fee_category=FeeCategory.FRENCH_TTC,
        ...     tuition_fee=Decimal("45000"),
        ...     dai_fee=Decimal("2000"),
        ...     registration_fee=Decimal("1000"),
        ...     sibling_order=3
        ... )
        >>> result = calculate_total_student_revenue(input_data)
        >>> result.total_annual_revenue
        Decimal('36750.00')
        >>> result.sibling_discount_applied
        True
        >>> result.trimester_distribution.trimester_1
        Decimal('14700.00')  # 36750 × 0.40
    """
    # Calculate tuition revenue with discounts
    tuition_revenue = calculate_tuition_revenue(tuition_input)

    # Calculate trimester distribution
    trimester_distribution = calculate_trimester_distribution(
        tuition_revenue.total_revenue
    )

    # Determine if sibling discount was applied
    sibling_discount_applied = tuition_revenue.sibling_discount_amount > 0

    return StudentRevenueResult(
        student_id=tuition_input.student_id,
        level_code=tuition_input.level_code,
        fee_category=tuition_input.fee_category,
        tuition_revenue=tuition_revenue,
        trimester_distribution=trimester_distribution,
        total_annual_revenue=tuition_revenue.total_revenue,
        sibling_discount_applied=sibling_discount_applied,
    )


def calculate_aggregate_revenue(
    student_revenues: list[TuitionRevenue],
) -> Decimal:
    """
    Calculate total aggregated revenue across all students.

    Args:
        student_revenues: List of student tuition revenue results

    Returns:
        Total revenue across all students

    Example:
        >>> student1 = TuitionRevenue(
        ...     level_code="6EME",
        ...     fee_category=FeeCategory.FRENCH_TTC,
        ...     base_tuition=Decimal("45000"),
        ...     base_dai=Decimal("2000"),
        ...     base_registration=Decimal("1000"),
        ...     net_tuition=Decimal("45000"),
        ...     net_dai=Decimal("2000"),
        ...     net_registration=Decimal("1000"),
        ...     total_revenue=Decimal("48000")
        ... )
        >>> student2 = TuitionRevenue(
        ...     level_code="5EME",
        ...     fee_category=FeeCategory.FRENCH_TTC,
        ...     base_tuition=Decimal("45000"),
        ...     base_dai=Decimal("2000"),
        ...     base_registration=Decimal("1000"),
        ...     net_tuition=Decimal("33750"),  # With sibling discount
        ...     net_dai=Decimal("2000"),
        ...     net_registration=Decimal("1000"),
        ...     total_revenue=Decimal("36750")
        ... )
        >>> total = calculate_aggregate_revenue([student1, student2])
        >>> total
        Decimal('84750')  # 48000 + 36750
    """
    total = Decimal("0")
    for revenue in student_revenues:
        total += revenue.total_revenue
    return total


def calculate_revenue_by_level(
    student_revenues: list[TuitionRevenue],
) -> dict[str, Decimal]:
    """
    Calculate revenue aggregated by level.

    Args:
        student_revenues: List of student tuition revenue results

    Returns:
        Dictionary mapping level_code to total revenue

    Example:
        >>> revenues = [
        ...     TuitionRevenue(
        ...         level_code="6EME", fee_category=FeeCategory.FRENCH_TTC,
        ...         base_tuition=Decimal("45000"), base_dai=Decimal("2000"),
        ...         base_registration=Decimal("1000"), net_tuition=Decimal("45000"),
        ...         net_dai=Decimal("2000"), net_registration=Decimal("1000"),
        ...         total_revenue=Decimal("48000")
        ...     ),
        ...     TuitionRevenue(
        ...         level_code="6EME", fee_category=FeeCategory.FRENCH_TTC,
        ...         base_tuition=Decimal("45000"), base_dai=Decimal("2000"),
        ...         base_registration=Decimal("1000"), net_tuition=Decimal("45000"),
        ...         net_dai=Decimal("2000"), net_registration=Decimal("1000"),
        ...         total_revenue=Decimal("48000")
        ...     )
        ... ]
        >>> by_level = calculate_revenue_by_level(revenues)
        >>> by_level["6EME"]
        Decimal('96000')  # 48000 + 48000
    """
    revenue_by_level: dict[str, Decimal] = {}

    for revenue in student_revenues:
        if revenue.level_code not in revenue_by_level:
            revenue_by_level[revenue.level_code] = Decimal("0")
        revenue_by_level[revenue.level_code] += revenue.total_revenue

    return revenue_by_level


def calculate_revenue_by_category(
    student_revenues: list[TuitionRevenue],
) -> dict[FeeCategory, Decimal]:
    """
    Calculate revenue aggregated by fee category.

    Args:
        student_revenues: List of student tuition revenue results

    Returns:
        Dictionary mapping FeeCategory to total revenue

    Example:
        >>> revenues = [
        ...     TuitionRevenue(
        ...         level_code="6EME", fee_category=FeeCategory.FRENCH_TTC,
        ...         base_tuition=Decimal("45000"), base_dai=Decimal("2000"),
        ...         base_registration=Decimal("1000"), net_tuition=Decimal("45000"),
        ...         net_dai=Decimal("2000"), net_registration=Decimal("1000"),
        ...         total_revenue=Decimal("48000")
        ...     ),
        ...     TuitionRevenue(
        ...         level_code="6EME", fee_category=FeeCategory.SAUDI_HT,
        ...         base_tuition=Decimal("40000"), base_dai=Decimal("2000"),
        ...         base_registration=Decimal("1000"), net_tuition=Decimal("40000"),
        ...         net_dai=Decimal("2000"), net_registration=Decimal("1000"),
        ...         total_revenue=Decimal("43000")
        ...     )
        ... ]
        >>> by_category = calculate_revenue_by_category(revenues)
        >>> by_category[FeeCategory.FRENCH_TTC]
        Decimal('48000')
        >>> by_category[FeeCategory.SAUDI_HT]
        Decimal('43000')
    """
    revenue_by_category: dict[FeeCategory, Decimal] = {}

    for revenue in student_revenues:
        if revenue.fee_category not in revenue_by_category:
            revenue_by_category[revenue.fee_category] = Decimal("0")
        revenue_by_category[revenue.fee_category] += revenue.total_revenue

    return revenue_by_category
