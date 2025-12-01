"""
Tests for validation functions.

Tests the class structure validation logic (HIGH-4 from Phase 0-3 review).
"""

from decimal import Decimal

import pytest

from app.validators.class_structure import (
    ClassStructureValidationError,
    validate_class_structure_sync,
)


class TestClassStructureValidationSync:
    """Test synchronous class structure validation."""

    def test_valid_class_size_within_bounds(self):
        """Test that valid class size passes validation."""
        # avg_class_size = 25.5 is within bounds [18, 30]
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.5"),
            level_name="6ème",
            number_of_classes=6,
            total_students=153,
        )
        # Should not raise any exception

    def test_valid_class_size_at_minimum(self):
        """Test that avg_class_size exactly at minimum is valid."""
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("18.0"),
            level_name="6ème",
            number_of_classes=8,
            total_students=144,
        )
        # Should not raise any exception

    def test_valid_class_size_at_maximum(self):
        """Test that avg_class_size exactly at maximum is valid."""
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("30.0"),
            level_name="6ème",
            number_of_classes=5,
            total_students=150,
        )
        # Should not raise any exception

    def test_invalid_class_size_below_minimum(self):
        """Test that avg_class_size below minimum raises error."""
        with pytest.raises(
            ClassStructureValidationError,
            match=r"Average class size .* is below minimum 18 for level 6ème",
        ):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("15.0"),
                level_name="6ème",
                number_of_classes=10,
                total_students=150,
            )

    def test_invalid_class_size_above_maximum(self):
        """Test that avg_class_size above maximum raises error."""
        with pytest.raises(
            ClassStructureValidationError,
            match=r"Average class size .* exceeds maximum 30 for level 6ème",
        ):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("35.0"),
                level_name="6ème",
                number_of_classes=4,
                total_students=140,
            )

    def test_error_message_includes_helpful_details(self):
        """Test that error messages include actionable information."""
        with pytest.raises(ClassStructureValidationError) as exc_info:
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("35.0"),
                level_name="6ème",
                number_of_classes=4,
                total_students=140,
            )

        error_message = str(exc_info.value)
        assert "35.0" in error_message  # avg_class_size
        assert "30" in error_message  # max_class_size
        assert "6ème" in error_message  # level_name
        assert "4" in error_message  # number_of_classes
        assert "140" in error_message  # total_students
        assert "adding more classes" in error_message.lower()  # suggestion

    def test_error_message_for_too_small_classes(self):
        """Test that error for small classes suggests reducing classes."""
        with pytest.raises(ClassStructureValidationError) as exc_info:
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("15.0"),
                level_name="CM2",
                number_of_classes=10,
                total_students=150,
            )

        error_message = str(exc_info.value)
        assert "reducing number of classes" in error_message.lower()

    def test_realistic_scenario_college_sixieme(self):
        """
        Test realistic scenario for Collège 6ème.

        Real EFIR data: 6ème typically has 5-6 classes, avg ~25 students/class
        """
        # Scenario 1: 153 students → 6 classes → avg 25.5 students ✅
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.5"),
            level_name="6ème",
            number_of_classes=6,
            total_students=153,
        )

        # Scenario 2: 153 students → 5 classes → avg 30.6 students ❌
        with pytest.raises(ClassStructureValidationError):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("30.6"),
                level_name="6ème",
                number_of_classes=5,
                total_students=153,
            )

    def test_realistic_scenario_maternelle_ps(self):
        """
        Test realistic scenario for Maternelle PS (Petite Section).

        Maternelle typically has smaller class sizes: min=15, target=22, max=25
        """
        # Scenario 1: 66 students → 3 classes → avg 22 students ✅
        validate_class_structure_sync(
            min_class_size=15,
            max_class_size=25,
            avg_class_size=Decimal("22.0"),
            level_name="PS",
            number_of_classes=3,
            total_students=66,
        )

        # Scenario 2: 66 students → 2 classes → avg 33 students ❌
        with pytest.raises(ClassStructureValidationError):
            validate_class_structure_sync(
                min_class_size=15,
                max_class_size=25,
                avg_class_size=Decimal("33.0"),
                level_name="PS",
                number_of_classes=2,
                total_students=66,
            )

    def test_edge_case_single_class(self):
        """Test edge case with single class."""
        # 25 students in 1 class → avg 25 ✅
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.0"),
            level_name="Terminale",
            number_of_classes=1,
            total_students=25,
        )

    def test_edge_case_very_small_level(self):
        """Test edge case with very small enrollment."""
        # 12 students in 1 class → avg 12 (below min 18) ❌
        with pytest.raises(ClassStructureValidationError):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("12.0"),
                level_name="Terminale Option Rare",
                number_of_classes=1,
                total_students=12,
            )

    def test_decimal_precision(self):
        """Test that decimal precision is handled correctly."""
        # 100 students / 4 classes = 25.0 exactly
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.0"),
            level_name="5ème",
            number_of_classes=4,
            total_students=100,
        )

        # 101 students / 4 classes = 25.25
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.25"),
            level_name="5ème",
            number_of_classes=4,
            total_students=101,
        )


# Note: Async version tests would require database fixtures
# These tests can be added when the full service layer is implemented
# For now, the sync version provides comprehensive coverage of the validation logic
