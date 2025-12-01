"""
Validation functions for EFIR Budget Planning Application.

This module provides business logic validation that cannot be enforced
at the database level.
"""

from app.validators.class_structure import validate_class_structure

__all__ = ["validate_class_structure"]
