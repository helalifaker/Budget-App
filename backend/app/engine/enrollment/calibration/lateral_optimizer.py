"""
Lateral Entry Optimizer Engine

Pure calculation functions for capacity-aware lateral entry optimization.

This engine transforms the enrollment paradigm from "demand projection"
(unreliable due to hyper-growth) to "supply optimization" (class structure
optimization).

Core Algorithm:
    1. Calculate retained students from cohort progression
    2. Determine base class structure from retained count
    3. Calculate fill capacities (to target, to max)
    4. Calculate new class threshold
    5. Make optimization decision to minimize rejections while
       maintaining efficient class structure

Example:
    MS from PS enrollment of 100:
    - Retained: 100 × 0.95 = 95 students
    - Base classes: ceil(95/28) = 4 classes
    - Fill to target: (4 × 25) - 95 = 5 slots
    - Fill to max: (4 × 28) - 95 = 17 slots
    - New class threshold: (5 × 21) - 95 = 10 students

    If demand = 40:
        40 > fill_to_max (17) AND 40 >= threshold (10)
        → NEW_CLASS decision
        → Accept all 40, open 5th class
        → Final: 135 students, 5 classes, 27 avg size
"""

from __future__ import annotations

import math
from decimal import Decimal

from app.engine.enrollment.calibration.optimizer_models import (
    ClassSizeConfig,
    GradeOptimizationInput,
    GradeOptimizationResult,
    NewStudentsSummary,
    NewStudentsSummaryRow,
    OptimizationDecision,
)
from app.engine.enrollment.projection.projection_models import ENTRY_POINT_GRADES

# Grade display names for the summary table
GRADE_DISPLAY_NAMES: dict[str, str] = {
    "PS": "Petite Section",
    "MS": "Moyenne Section",
    "GS": "Grande Section",
    "CP": "CP",
    "CE1": "CE1",
    "CE2": "CE2",
    "CM1": "CM1",
    "CM2": "CM2",
    "6EME": "6ème",
    "5EME": "5ème",
    "4EME": "4ème",
    "3EME": "3ème",
    "2NDE": "2nde",
    "1ERE": "1ère",
    "TLE": "Terminale",
}


def calculate_base_classes(
    retained_students: int,
    max_class_size: int,
) -> int:
    """
    Calculate minimum number of classes needed for retained students.

    Uses ceiling division to ensure all retained students fit.

    Args:
        retained_students: Number of students retained from previous grade
        max_class_size: Maximum students per class

    Returns:
        Number of classes needed (0 if no retained students)
    """
    if retained_students <= 0:
        return 0
    return math.ceil(retained_students / max_class_size)


def calculate_fill_capacities(
    retained_students: int,
    base_classes: int,
    target_class_size: int,
    max_class_size: int,
) -> tuple[int, int]:
    """
    Calculate available slots to fill current class structure.

    Args:
        retained_students: Number of students retained
        base_classes: Number of classes needed for retained
        target_class_size: Target students per class
        max_class_size: Maximum students per class

    Returns:
        Tuple of (fill_to_target_slots, fill_to_max_slots)
    """
    if base_classes == 0:
        return 0, 0

    target_capacity = base_classes * target_class_size
    max_capacity = base_classes * max_class_size

    fill_to_target = max(0, target_capacity - retained_students)
    fill_to_max = max(0, max_capacity - retained_students)

    return fill_to_target, fill_to_max


def calculate_new_class_threshold(
    retained_students: int,
    base_classes: int,
    min_class_size: int,
    max_class_size: int,
) -> int:
    """
    Calculate minimum lateral entry needed to justify opening a new class.

    A new class is justified when:
        (base_classes + 1) × min_class_size ≤ total_students

    Therefore:
        lateral_needed = (base_classes + 1) × min_class_size - retained

    Args:
        retained_students: Number of students retained
        base_classes: Current number of classes
        min_class_size: Minimum students per class
        max_class_size: Maximum students per class

    Returns:
        Minimum lateral entry count to justify new class
    """
    if base_classes == 0:
        # For PS or empty grades, need min_class_size to open first class
        return min_class_size

    # Current capacity with current classes
    current_max_capacity = base_classes * max_class_size

    # If we're not even filling current capacity, threshold is based on
    # filling current + opening new
    new_classes = base_classes + 1
    new_min_total = new_classes * min_class_size

    # Threshold is the lateral count that would bring us to new_min_total
    # But we must first fill current classes to max before opening new
    fill_to_max = max(0, current_max_capacity - retained_students)

    # However, if retained + fill_to_max already exceeds new_min_total,
    # the threshold is simpler
    if current_max_capacity >= new_min_total:
        return fill_to_max + 1  # Just 1 more than fill_to_max to trigger new class

    return max(0, new_min_total - retained_students)


def make_optimization_decision(
    demand: int,
    fill_to_target: int,
    fill_to_max: int,
    new_class_threshold: int,
    base_classes: int,
    max_divisions: int,
    min_class_size: int,
) -> tuple[OptimizationDecision, int, int]:
    """
    Make optimization decision based on demand and capacities.

    Args:
        demand: Historical lateral entry demand
        fill_to_target: Slots available to reach target size
        fill_to_max: Slots available to reach max size
        new_class_threshold: Lateral needed to justify new class
        base_classes: Current number of classes
        max_divisions: Maximum allowed classes
        min_class_size: Minimum students per class

    Returns:
        Tuple of (decision, accepted, final_classes)
    """
    # Handle zero demand case
    if demand <= 0:
        return OptimizationDecision.ACCEPT_ALL, 0, base_classes

    # Handle zero base classes (first class formation, like PS)
    if base_classes == 0:
        if demand < min_class_size:
            # Not enough to form even one class
            return OptimizationDecision.INSUFFICIENT_DEMAND, demand, 1

        # Calculate how many classes we can form
        classes_possible = min(math.ceil(demand / min_class_size), max_divisions)
        max_capacity = classes_possible * 30  # Use generous max for PS
        accepted = min(demand, max_capacity)
        return OptimizationDecision.NEW_CLASS, accepted, classes_possible

    # Case A: Demand fits within target capacity (comfortable)
    if demand <= fill_to_target:
        return OptimizationDecision.ACCEPT_ALL, demand, base_classes

    # Case B: Demand fits within max capacity (fills classes)
    if demand <= fill_to_max:
        return OptimizationDecision.ACCEPT_FILL_MAX, demand, base_classes

    # Case C & D: Demand exceeds current capacity
    # Check if we can open new classes
    if base_classes >= max_divisions:
        # At ceiling - cannot expand further
        return OptimizationDecision.RESTRICT_AT_CEILING, fill_to_max, base_classes

    # Check if demand justifies new class
    if demand >= new_class_threshold:
        # Calculate how many new classes we can/should open
        new_classes = base_classes
        remaining_demand = demand - fill_to_max  # Demand beyond current capacity

        while remaining_demand > 0 and new_classes < max_divisions:
            new_classes += 1
            # Each new class adds max_class_size capacity
            remaining_demand -= 30  # Use generous max for expansion

        accepted = min(demand, (new_classes * 30))  # Cap at new capacity
        return OptimizationDecision.NEW_CLASS, accepted, new_classes

    # Case C: Awkward middle - demand exceeds max but doesn't justify new class
    return OptimizationDecision.RESTRICT, fill_to_max, base_classes


def optimize_grade_lateral_entry(
    grade_input: GradeOptimizationInput,
) -> GradeOptimizationResult:
    """
    Optimize lateral entry for a single grade.

    This is the main entry point for grade-level optimization.

    Args:
        grade_input: Input containing retained students, demand, and config

    Returns:
        GradeOptimizationResult with decision and final structure
    """
    config = grade_input.class_size_config
    retained = grade_input.retained_students
    demand = grade_input.historical_demand

    # Step 1: Calculate base class structure
    base_classes = calculate_base_classes(retained, config.max_class_size)

    # Step 2: Calculate fill capacities
    fill_to_target, fill_to_max = calculate_fill_capacities(
        retained,
        base_classes,
        config.target_class_size,
        config.max_class_size,
    )

    # Step 3: Calculate new class threshold
    new_class_threshold = calculate_new_class_threshold(
        retained,
        base_classes,
        config.min_class_size,
        config.max_class_size,
    )

    # Step 4: Make optimization decision
    decision, accepted, final_classes = make_optimization_decision(
        demand=demand,
        fill_to_target=fill_to_target,
        fill_to_max=fill_to_max,
        new_class_threshold=new_class_threshold,
        base_classes=base_classes,
        max_divisions=config.max_divisions,
        min_class_size=config.min_class_size,
    )

    # Step 5: Calculate final metrics
    rejected = max(0, demand - accepted)
    final_students = retained + accepted

    if final_classes > 0:
        avg_class_size = Decimal(final_students / final_classes).quantize(
            Decimal("0.1")
        )
        # Utilization: percentage of target capacity
        target_capacity = final_classes * config.target_class_size
        utilization_pct = (
            Decimal(final_students) / Decimal(target_capacity) * 100
        ).quantize(Decimal("0.1"))
    else:
        avg_class_size = Decimal("0.0")
        utilization_pct = Decimal("0.0")

    # Acceptance rate: percentage of demand accepted
    if demand > 0:
        acceptance_rate = (Decimal(accepted) / Decimal(demand) * 100).quantize(
            Decimal("0.1")
        )
    else:
        acceptance_rate = Decimal("100.0")

    return GradeOptimizationResult(
        grade_code=grade_input.grade_code,
        cycle_code=grade_input.cycle_code,
        is_entry_point=grade_input.is_entry_point,
        retained_students=retained,
        historical_demand=demand,
        base_classes=base_classes,
        fill_to_target=fill_to_target,
        fill_to_max=fill_to_max,
        new_class_threshold=new_class_threshold,
        decision=decision,
        accepted=accepted,
        rejected=rejected,
        final_classes=final_classes,
        final_students=final_students,
        avg_class_size=avg_class_size,
        utilization_pct=utilization_pct,
        acceptance_rate=acceptance_rate,
    )


def optimize_ps_entry(
    ps_demand: int,
    class_size_config: ClassSizeConfig,
) -> GradeOptimizationResult:
    """
    Optimize PS (Petite Section) entry.

    PS is a special case with no retention from a previous grade.
    All students are new entries.

    Args:
        ps_demand: Expected PS enrollment (from scenario ps_entry + growth)
        class_size_config: Class size parameters for PS

    Returns:
        GradeOptimizationResult for PS
    """
    config = class_size_config

    # PS has no retention - all are new students

    # Calculate how many classes we can form
    if ps_demand < config.min_class_size:
        # Not enough for even one class
        decision = OptimizationDecision.INSUFFICIENT_DEMAND
        accepted = ps_demand
        final_classes = 1  # We'd still open 1 class
    else:
        # Calculate optimal number of classes
        # Target: each class has ~target_class_size students
        optimal_classes = math.ceil(ps_demand / config.target_class_size)
        final_classes = min(optimal_classes, config.max_divisions)

        # Calculate capacity
        max_capacity = final_classes * config.max_class_size
        accepted = min(ps_demand, max_capacity)

        if accepted == ps_demand:
            decision = OptimizationDecision.ACCEPT_ALL
        elif final_classes >= config.max_divisions:
            decision = OptimizationDecision.RESTRICT_AT_CEILING
        else:
            decision = OptimizationDecision.ACCEPT_FILL_MAX

    rejected = max(0, ps_demand - accepted)
    final_students = accepted

    if final_classes > 0:
        avg_class_size = Decimal(final_students / final_classes).quantize(
            Decimal("0.1")
        )
        # Utilization: percentage of target capacity
        target_capacity = final_classes * config.target_class_size
        utilization_pct = (
            Decimal(final_students) / Decimal(target_capacity) * 100
        ).quantize(Decimal("0.1"))
    else:
        avg_class_size = Decimal("0.0")
        utilization_pct = Decimal("0.0")

    # Acceptance rate: percentage of demand accepted
    if ps_demand > 0:
        acceptance_rate = (Decimal(accepted) / Decimal(ps_demand) * 100).quantize(
            Decimal("0.1")
        )
    else:
        acceptance_rate = Decimal("100.0")

    return GradeOptimizationResult(
        grade_code="PS",
        cycle_code="MAT",
        is_entry_point=True,
        retained_students=0,
        historical_demand=ps_demand,
        base_classes=0,
        fill_to_target=0,
        fill_to_max=0,
        new_class_threshold=config.min_class_size,
        decision=decision,
        accepted=accepted,
        rejected=rejected,
        final_classes=final_classes,
        final_students=final_students,
        avg_class_size=avg_class_size,
        utilization_pct=utilization_pct,
        acceptance_rate=acceptance_rate,
    )


def build_new_students_summary(
    optimization_results: list[GradeOptimizationResult],
) -> NewStudentsSummary:
    """
    Build the new students summary table from optimization results.

    Args:
        optimization_results: List of optimization results for all grades

    Returns:
        NewStudentsSummary with complete breakdown
    """
    rows: list[NewStudentsSummaryRow] = []
    total_demand = 0
    total_available = 0
    total_accepted = 0
    total_rejected = 0

    entry_point_demand = 0
    entry_point_accepted = 0
    incidental_demand = 0
    incidental_accepted = 0

    grades_accept_all: list[str] = []
    grades_fill_max: list[str] = []
    grades_restricted: list[str] = []
    grades_new_class: list[str] = []
    grades_at_ceiling: list[str] = []

    for result in optimization_results:
        total_demand += result.historical_demand
        total_available += result.fill_to_max
        total_accepted += result.accepted
        total_rejected += result.rejected

        if result.is_entry_point:
            entry_point_demand += result.historical_demand
            entry_point_accepted += result.accepted
        else:
            incidental_demand += result.historical_demand
            incidental_accepted += result.accepted

        # Categorize by decision
        if result.decision == OptimizationDecision.ACCEPT_ALL:
            grades_accept_all.append(result.grade_code)
        elif result.decision == OptimizationDecision.ACCEPT_FILL_MAX:
            grades_fill_max.append(result.grade_code)
        elif result.decision == OptimizationDecision.RESTRICT:
            grades_restricted.append(result.grade_code)
        elif result.decision == OptimizationDecision.NEW_CLASS:
            grades_new_class.append(result.grade_code)
        elif result.decision == OptimizationDecision.RESTRICT_AT_CEILING:
            grades_at_ceiling.append(result.grade_code)

    # Build rows with pct_of_total_intake
    for result in optimization_results:
        if total_accepted > 0:
            pct_of_total = Decimal(result.accepted / total_accepted * 100).quantize(
                Decimal("0.1")
            )
        else:
            pct_of_total = Decimal("0.0")

        if result.historical_demand > 0:
            acceptance_rate = Decimal(
                result.accepted / result.historical_demand * 100
            ).quantize(Decimal("0.1"))
        else:
            acceptance_rate = Decimal("100.0")

        row = NewStudentsSummaryRow(
            grade_code=result.grade_code,
            grade_name=GRADE_DISPLAY_NAMES.get(result.grade_code, result.grade_code),
            cycle_code=result.cycle_code,
            is_entry_point=result.is_entry_point,
            historical_demand=result.historical_demand,
            available_slots=result.fill_to_max,
            accepted=result.accepted,
            rejected=result.rejected,
            acceptance_rate=acceptance_rate,
            pct_of_total_intake=pct_of_total,
            decision=result.decision,
        )
        rows.append(row)

    # Overall acceptance rate
    if total_demand > 0:
        overall_acceptance_rate = Decimal(total_accepted / total_demand * 100).quantize(
            Decimal("0.1")
        )
    else:
        overall_acceptance_rate = Decimal("100.0")

    return NewStudentsSummary(
        total_demand=total_demand,
        total_available=total_available,
        total_accepted=total_accepted,
        total_rejected=total_rejected,
        overall_acceptance_rate=overall_acceptance_rate,
        by_grade=rows,
        entry_point_demand=entry_point_demand,
        entry_point_accepted=entry_point_accepted,
        incidental_demand=incidental_demand,
        incidental_accepted=incidental_accepted,
        grades_accept_all=grades_accept_all,
        grades_fill_max=grades_fill_max,
        grades_restricted=grades_restricted,
        grades_new_class=grades_new_class,
        grades_at_ceiling=grades_at_ceiling,
    )


def is_entry_point_grade(grade_code: str) -> bool:
    """Check if a grade is an entry point (uses percentage-based lateral)."""
    return grade_code in ENTRY_POINT_GRADES or grade_code == "PS"
