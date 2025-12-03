"""
KPI Engine - Calculator Functions

Pure calculation functions for key performance indicators.
All functions are stateless with no side effects.

Formulas:
---------
Student-Teacher Ratio:
    ratio = total_students ÷ total_teacher_fte
    Target: ~12.0 (EFIR benchmark)

H/E Ratio (Heures/Élève - Secondary):
    ratio = dhg_hours_total ÷ secondary_students
    Target: ~1.35 (French system benchmark)

Revenue per Student:
    revenue_per_student = total_revenue ÷ total_students
    Target: ~45,000 SAR (EFIR average)

Cost per Student:
    cost_per_student = total_costs ÷ total_students

Margin Percentage:
    margin = (total_revenue - total_costs) ÷ total_revenue × 100
    Target: ~10% (EFIR financial goal)

Staff Cost Ratio:
    ratio = personnel_costs ÷ total_costs × 100
    Target: ~70% (typical for education)

Capacity Utilization:
    utilization = current_students ÷ max_capacity × 100
    Target: 90-95% (optimal range)
"""

from decimal import Decimal

from app.engine.kpi.models import (
    KPICalculationResult,
    KPIInput,
    KPIResult,
    KPIType,
)

# Target values for EFIR school (from specifications)
TARGET_STUDENT_TEACHER_RATIO = Decimal("12.0")
TARGET_HE_RATIO_SECONDARY = Decimal("1.35")
TARGET_REVENUE_PER_STUDENT = Decimal("45000")  # SAR
TARGET_MARGIN_PERCENTAGE = Decimal("10.0")  # %
TARGET_STAFF_COST_RATIO = Decimal("70.0")  # %
TARGET_CAPACITY_UTILIZATION_MIN = Decimal("90.0")  # %
TARGET_CAPACITY_UTILIZATION_MAX = Decimal("95.0")  # %


def calculate_student_teacher_ratio(
    total_students: int,
    total_teacher_fte: Decimal,
    target: Decimal = TARGET_STUDENT_TEACHER_RATIO,
) -> KPIResult:
    """
    Calculate student-to-teacher ratio.

    Formula:
        ratio = total_students ÷ total_teacher_fte

    Args:
        total_students: Total enrolled students
        total_teacher_fte: Total teacher FTE (full-time equivalent)
        target: Target ratio (default: 12.0)

    Returns:
        KPIResult with calculated ratio and variance from target

    Example:
        >>> calculate_student_teacher_ratio(1850, Decimal("154.2"))
        KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("12.00"),
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("0.00"),
            performance_status="on_target"
        )
    """
    if total_teacher_fte <= 0:
        raise ValueError(f"Teacher FTE must be positive, got {total_teacher_fte}")

    ratio = Decimal(total_students) / total_teacher_fte
    variance = ratio - target

    # Determine performance status (within ±0.5 is on target)
    if abs(variance) <= Decimal("0.5"):
        status = "on_target"
    elif variance > 0:
        status = "above_target"  # More students per teacher (worse)
    else:
        status = "below_target"  # Fewer students per teacher (better)

    return KPIResult(
        kpi_type=KPIType.STUDENT_TEACHER_RATIO,
        value=ratio.quantize(Decimal("0.01")),
        target_value=target,
        unit="ratio",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_he_ratio_secondary(
    dhg_hours_total: Decimal,
    secondary_students: int,
    target: Decimal = TARGET_HE_RATIO_SECONDARY,
) -> KPIResult:
    """
    Calculate H/E ratio (Heures/Élève) for secondary education.

    Formula:
        ratio = dhg_hours_total ÷ secondary_students

    The H/E ratio is a French education system metric measuring
    the teaching hours allocated per student.

    Args:
        dhg_hours_total: Total DHG hours for secondary (Collège + Lycée)
        secondary_students: Total secondary students
        target: Target H/E ratio (default: 1.35)

    Returns:
        KPIResult with calculated ratio and variance from target

    Example:
        >>> calculate_he_ratio_secondary(Decimal("877.5"), 650)
        KPIResult(
            kpi_type=KPIType.HE_RATIO_SECONDARY,
            value=Decimal("1.35"),
            target_value=Decimal("1.35"),
            unit="ratio",
            variance_from_target=Decimal("0.00"),
            performance_status="on_target"
        )
    """
    if dhg_hours_total <= 0:
        raise ValueError("DHG hours total must be positive")

    if secondary_students <= 0:
        raise ValueError(f"Secondary students must be positive, got {secondary_students}")

    ratio = dhg_hours_total / Decimal(secondary_students)
    variance = ratio - target

    # Within ±0.05 is on target
    if abs(variance) <= Decimal("0.05"):
        status = "on_target"
    elif variance > 0:
        status = "above_target"  # More hours per student (better quality)
    else:
        status = "below_target"  # Fewer hours per student (lower quality)

    return KPIResult(
        kpi_type=KPIType.HE_RATIO_SECONDARY,
        value=ratio.quantize(Decimal("0.01")),
        target_value=target,
        unit="ratio",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_revenue_per_student(
    total_revenue: Decimal,
    total_students: int,
    target: Decimal = TARGET_REVENUE_PER_STUDENT,
) -> KPIResult:
    """
    Calculate revenue per student.

    Formula:
        revenue_per_student = total_revenue ÷ total_students

    Args:
        total_revenue: Total revenue in SAR
        total_students: Total enrolled students
        target: Target revenue per student (default: 45,000 SAR)

    Returns:
        KPIResult with calculated revenue per student

    Example:
        >>> calculate_revenue_per_student(Decimal("83272500"), 1850)
        KPIResult(
            kpi_type=KPIType.REVENUE_PER_STUDENT,
            value=Decimal("45012.16"),
            target_value=Decimal("45000"),
            unit="SAR",
            variance_from_target=Decimal("12.16"),
            performance_status="on_target"
        )
    """
    if total_students <= 0:
        raise ValueError(f"Total students must be positive, got {total_students}")

    revenue_per_student = total_revenue / Decimal(total_students)
    variance = revenue_per_student - target

    # Within ±1,000 SAR is on target
    if abs(variance) <= Decimal("1000"):
        status = "on_target"
    elif variance > 0:
        status = "above_target"  # Higher revenue per student (better)
    else:
        status = "below_target"  # Lower revenue per student (worse)

    return KPIResult(
        kpi_type=KPIType.REVENUE_PER_STUDENT,
        value=revenue_per_student.quantize(Decimal("0.01")),
        target_value=target,
        unit="SAR",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_cost_per_student(
    total_costs: Decimal,
    total_students: int,
) -> KPIResult:
    """
    Calculate cost per student.

    Formula:
        cost_per_student = total_costs ÷ total_students

    No target is set for this KPI as it varies by service level.
    Lower is generally better, but must maintain quality.

    Args:
        total_costs: Total costs in SAR
        total_students: Total enrolled students

    Returns:
        KPIResult with calculated cost per student (no target)

    Example:
        >>> calculate_cost_per_student(Decimal("74945250"), 1850)
        KPIResult(
            kpi_type=KPIType.COST_PER_STUDENT,
            value=Decimal("40510.95"),
            target_value=None,
            unit="SAR",
            variance_from_target=None,
            performance_status=None
        )
    """
    if total_students <= 0:
        raise ValueError(f"Total students must be positive, got {total_students}")

    cost_per_student = total_costs / Decimal(total_students)

    return KPIResult(
        kpi_type=KPIType.COST_PER_STUDENT,
        value=cost_per_student.quantize(Decimal("0.01")),
        target_value=None,
        unit="SAR",
        variance_from_target=None,
        performance_status=None,
    )


def calculate_margin_percentage(
    total_revenue: Decimal,
    total_costs: Decimal,
    target: Decimal = TARGET_MARGIN_PERCENTAGE,
) -> KPIResult:
    """
    Calculate profit margin percentage.

    Formula:
        margin = (total_revenue - total_costs) ÷ total_revenue × 100

    Args:
        total_revenue: Total revenue in SAR
        total_costs: Total costs in SAR
        target: Target margin percentage (default: 10%)

    Returns:
        KPIResult with calculated margin percentage

    Example:
        >>> calculate_margin_percentage(Decimal("83272500"), Decimal("74945250"))
        KPIResult(
            kpi_type=KPIType.MARGIN_PERCENTAGE,
            value=Decimal("10.00"),
            target_value=Decimal("10.0"),
            unit="%",
            variance_from_target=Decimal("0.00"),
            performance_status="on_target"
        )
    """
    if total_revenue <= 0:
        raise ValueError(f"Total revenue must be positive, got {total_revenue}")

    margin = ((total_revenue - total_costs) / total_revenue) * Decimal("100")
    variance = margin - target

    # Within ±1% is on target
    if abs(variance) <= Decimal("1.0"):
        status = "on_target"
    elif variance > 0:
        status = "above_target"  # Higher margin (better)
    else:
        status = "below_target"  # Lower margin (worse)

    return KPIResult(
        kpi_type=KPIType.MARGIN_PERCENTAGE,
        value=margin.quantize(Decimal("0.01")),
        target_value=target,
        unit="%",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_staff_cost_ratio(
    personnel_costs: Decimal,
    total_costs: Decimal,
    target: Decimal = TARGET_STAFF_COST_RATIO,
) -> KPIResult:
    """
    Calculate personnel costs as percentage of total costs.

    Formula:
        ratio = (personnel_costs ÷ total_costs) × 100

    Args:
        personnel_costs: Total personnel costs in SAR
        total_costs: Total costs in SAR
        target: Target staff cost ratio (default: 70%)

    Returns:
        KPIResult with calculated staff cost ratio

    Example:
        >>> calculate_staff_cost_ratio(Decimal("52461675"), Decimal("74945250"))
        KPIResult(
            kpi_type=KPIType.STAFF_COST_RATIO,
            value=Decimal("70.00"),
            target_value=Decimal("70.0"),
            unit="%",
            variance_from_target=Decimal("0.00"),
            performance_status="on_target"
        )
    """
    if total_costs <= 0:
        raise ValueError(f"Total costs must be positive, got {total_costs}")

    ratio = (personnel_costs / total_costs) * Decimal("100")
    variance = ratio - target

    # Within ±5% is on target
    if abs(variance) <= Decimal("5.0"):
        status = "on_target"
    elif variance > 0:
        status = "above_target"  # Higher personnel ratio (may indicate inefficiency)
    else:
        status = "below_target"  # Lower personnel ratio (may indicate understaffing)

    return KPIResult(
        kpi_type=KPIType.STAFF_COST_RATIO,
        value=ratio.quantize(Decimal("0.01")),
        target_value=target,
        unit="%",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_capacity_utilization(
    current_students: int,
    max_capacity: int,
) -> KPIResult:
    """
    Calculate school capacity utilization percentage.

    Formula:
        utilization = (current_students ÷ max_capacity) × 100

    Target range: 90-95% (optimal utilization without overcrowding)

    Args:
        current_students: Current enrolled students
        max_capacity: Maximum school capacity
        target: Target utilization midpoint (default: 92.5%)

    Returns:
        KPIResult with calculated capacity utilization

    Example:
        >>> calculate_capacity_utilization(1850, 1875)
        KPIResult(
            kpi_type=KPIType.CAPACITY_UTILIZATION,
            value=Decimal("98.67"),
            target_value=Decimal("92.5"),
            unit="%",
            variance_from_target=Decimal("6.17"),
            performance_status="above_target"
        )
    """
    if max_capacity <= 0:
        raise ValueError(f"Max capacity must be positive, got {max_capacity}")

    utilization = (Decimal(current_students) / Decimal(max_capacity)) * Decimal("100")

    # Target is the midpoint of 90-95% range
    target_midpoint = (TARGET_CAPACITY_UTILIZATION_MIN + TARGET_CAPACITY_UTILIZATION_MAX) / Decimal(
        "2"
    )
    variance = utilization - target_midpoint

    # Within the 90-95% range is on target
    if TARGET_CAPACITY_UTILIZATION_MIN <= utilization <= TARGET_CAPACITY_UTILIZATION_MAX:
        status = "on_target"
    elif utilization > TARGET_CAPACITY_UTILIZATION_MAX:
        status = "above_target"  # Over capacity (overcrowding risk)
    else:
        status = "below_target"  # Under capacity (underutilized)

    return KPIResult(
        kpi_type=KPIType.CAPACITY_UTILIZATION,
        value=utilization.quantize(Decimal("0.01")),
        target_value=target_midpoint.quantize(Decimal("0.01")),
        unit="%",
        variance_from_target=variance.quantize(Decimal("0.01")),
        performance_status=status,
    )


def calculate_all_kpis(kpi_input: KPIInput) -> KPICalculationResult:
    """
    Calculate all KPIs from a single input dataset.

    Convenience function that calculates all available KPIs
    and returns them in a structured result.

    Args:
        kpi_input: Complete KPI input data

    Returns:
        KPICalculationResult with all calculated KPIs

    Example:
        >>> from datetime import datetime
        >>> input_data = KPIInput(
        ...     total_students=1850,
        ...     secondary_students=650,
        ...     max_capacity=1875,
        ...     total_teacher_fte=Decimal("154.2"),
        ...     dhg_hours_total=Decimal("877.5"),
        ...     total_revenue=Decimal("83272500"),
        ...     total_costs=Decimal("74945250"),
        ...     personnel_costs=Decimal("52461675")
        ... )
        >>> result = calculate_all_kpis(input_data)
        >>> result.student_teacher_ratio.value
        Decimal("12.00")
        >>> result.margin_percentage.value
        Decimal("10.00")
    """
    from datetime import UTC, datetime

    # Educational KPIs
    student_teacher_ratio = calculate_student_teacher_ratio(
        kpi_input.total_students, kpi_input.total_teacher_fte
    )

    he_ratio_secondary: KPIResult | None = None
    if kpi_input.dhg_hours_total is not None and kpi_input.secondary_students > 0:
        he_ratio_secondary = calculate_he_ratio_secondary(
            kpi_input.dhg_hours_total, kpi_input.secondary_students
        )

    capacity_utilization = calculate_capacity_utilization(
        kpi_input.total_students, kpi_input.max_capacity
    )

    # Financial KPIs
    revenue_per_student = calculate_revenue_per_student(
        kpi_input.total_revenue, kpi_input.total_students
    )

    cost_per_student = calculate_cost_per_student(
        kpi_input.total_costs, kpi_input.total_students
    )

    # Handle zero revenue case gracefully
    if kpi_input.total_revenue == 0:
        # Zero revenue means 100% loss
        margin_percentage = KPIResult(
            kpi_type=KPIType.MARGIN_PERCENTAGE,
            value=Decimal("-100.00") if kpi_input.total_costs > 0 else Decimal("0.00"),
            target_value=TARGET_MARGIN_PERCENTAGE,
            unit="%",
            variance_from_target=Decimal("-110.00") if kpi_input.total_costs > 0 else Decimal("-10.00"),
            performance_status="below_target",
        )
    else:
        margin_percentage = calculate_margin_percentage(
            kpi_input.total_revenue, kpi_input.total_costs
        )

    staff_cost_ratio = calculate_staff_cost_ratio(
        kpi_input.personnel_costs, kpi_input.total_costs
    )

    return KPICalculationResult(
        budget_id=kpi_input.budget_id,
        calculation_date=datetime.now(UTC),
        student_teacher_ratio=student_teacher_ratio,
        he_ratio_secondary=he_ratio_secondary,
        capacity_utilization=capacity_utilization,
        revenue_per_student=revenue_per_student,
        cost_per_student=cost_per_student,
        margin_percentage=margin_percentage,
        staff_cost_ratio=staff_cost_ratio,
    )
