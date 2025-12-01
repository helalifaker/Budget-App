"""
Revenue Engine - Tuition and Fee Calculations (Module 10)

This module provides pure calculation functions for tuition revenue,
sibling discounts, and trimester-based revenue recognition.

Key Calculations:
- Tuition fees by level and nationality
- Sibling discounts (25% on 3rd+ child, NOT on DAI/registration fees)
- Trimester distribution (T1: 40%, T2: 30%, T3: 30%)
- Fee categories: French (TTC), Saudi (HT), Other (TTC)
"""

from app.engine.revenue.calculator import (
    calculate_tuition_revenue,
    calculate_sibling_discount,
    calculate_trimester_distribution,
    calculate_total_student_revenue,
)
from app.engine.revenue.models import (
    FeeCategory,
    TuitionInput,
    TuitionRevenue,
    SiblingDiscount,
    TrimesterDistribution,
    StudentRevenueResult,
)
from app.engine.revenue.validators import (
    validate_tuition_input,
    validate_sibling_order,
    validate_trimester_percentages,
)

__all__ = [
    # Models
    "FeeCategory",
    "TuitionInput",
    "TuitionRevenue",
    "SiblingDiscount",
    "TrimesterDistribution",
    "StudentRevenueResult",
    # Calculator functions
    "calculate_tuition_revenue",
    "calculate_sibling_discount",
    "calculate_trimester_distribution",
    "calculate_total_student_revenue",
    # Validators
    "validate_tuition_input",
    "validate_sibling_order",
    "validate_trimester_percentages",
]
