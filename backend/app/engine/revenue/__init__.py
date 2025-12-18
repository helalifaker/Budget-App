"""
Revenue Module - Tuition and Fee Calculations

This module provides pure calculation functions for tuition revenue,
sibling discounts, and trimester-based revenue recognition.

Key Calculations:
- Tuition fees by level and nationality
- Sibling discounts (25% on 3rd+ child, NOT on DAI/registration fees)
- Trimester distribution (T1: 40%, T2: 30%, T3: 30%)
- Fee categories: French (TTC), Saudi (HT), Other (TTC)

Part of the 10-module engine structure matching frontend.
"""

from app.engine.revenue.calculator import (
    calculate_sibling_discount,
    calculate_total_student_revenue,
    calculate_trimester_distribution,
    calculate_tuition_revenue,
)
from app.engine.revenue.models import (
    FeeCategory,
    SiblingDiscount,
    StudentRevenueResult,
    TrimesterDistribution,
    TuitionInput,
    TuitionRevenue,
)
from app.engine.revenue.validators import (
    validate_sibling_order,
    validate_trimester_percentages,
    validate_tuition_input,
)

__all__ = [
    # Models
    "FeeCategory",
    "SiblingDiscount",
    "StudentRevenueResult",
    "TrimesterDistribution",
    "TuitionInput",
    "TuitionRevenue",
    # Calculator functions
    "calculate_sibling_discount",
    "calculate_total_student_revenue",
    "calculate_trimester_distribution",
    "calculate_tuition_revenue",
    # Validators
    "validate_sibling_order",
    "validate_trimester_percentages",
    "validate_tuition_input",
]
