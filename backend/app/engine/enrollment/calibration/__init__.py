"""
Enrollment Calibration Engine - Historical Rate Derivation

Pure calculation functions for deriving enrollment projection rates
from historical data using weighted analysis.

Key concepts:
- Weighted progression: 70% N-1 + 30% N-2 (configurable)
- Cycle-based retention: MAT/ELEM 96%, COLL 97%, LYC 93%
- Lateral rate = weighted_progression - retention_rate
- All grades use percentage-based lateral (unified model)

Part of the Enrollment module.
"""

from app.engine.enrollment.calibration.calibration_engine import (
    CalibrationResult,
    GradeCalibrationResult,
    GradeProgressionData,
    HistoricalEnrollmentYear,
    calculate_grade_progression,
    calculate_weighted_progression,
    calibrate_from_historical,
    calibrate_grade,
    compare_with_defaults,
    derive_lateral_rate,
    get_default_effective_rates,
)
from app.engine.enrollment.calibration.lateral_optimizer import (
    GRADE_DISPLAY_NAMES,
    build_new_students_summary,
    calculate_base_classes,
    calculate_fill_capacities,
    calculate_new_class_threshold,
    is_entry_point_grade,
    make_optimization_decision,
    optimize_grade_lateral_entry,
    optimize_ps_entry,
)
from app.engine.enrollment.calibration.optimizer_models import (
    ClassSizeConfig,
    GradeOptimizationInput,
    GradeOptimizationResult,
    NewStudentsSummary,
    NewStudentsSummaryRow,
    OptimizationDecision,
)

__all__ = [
    # Constants
    "GRADE_DISPLAY_NAMES",
    # Models - Calibration
    "CalibrationResult",
    # Models - Optimization
    "ClassSizeConfig",
    "GradeCalibrationResult",
    "GradeOptimizationInput",
    "GradeOptimizationResult",
    "GradeProgressionData",
    "HistoricalEnrollmentYear",
    "NewStudentsSummary",
    "NewStudentsSummaryRow",
    "OptimizationDecision",
    # Optimization functions
    "build_new_students_summary",
    "calculate_base_classes",
    "calculate_fill_capacities",
    "calculate_grade_progression",
    "calculate_new_class_threshold",
    "calculate_weighted_progression",
    # Calibration functions
    "calibrate_from_historical",
    "calibrate_grade",
    "compare_with_defaults",
    "derive_lateral_rate",
    "get_default_effective_rates",
    "is_entry_point_grade",
    "make_optimization_decision",
    "optimize_grade_lateral_entry",
    "optimize_ps_entry",
]
