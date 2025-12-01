"""
Revenue Engine - Pydantic Models

Input/output models for tuition and revenue calculations.
All models use Pydantic for validation and type safety.

EFIR Fee Structure Context:
- Tuition (Scolarité): Main teaching fee
- DAI (Droit Annuel d'Inscription): Annual enrollment fee
- Registration (Frais d'Inscription): One-time registration fee
- Fee Categories: French (TTC), Saudi (HT), Other (TTC)
- Sibling Discount: 25% on tuition for 3rd+ child (NOT on DAI/registration)
"""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeeCategory(str, Enum):
    """Fee category by nationality for tax treatment."""

    FRENCH_TTC = "french_ttc"  # French nationals: Prix TTC (tax included)
    SAUDI_HT = "saudi_ht"  # Saudi nationals: Prix HT (tax excluded)
    OTHER_TTC = "other_ttc"  # Other nationalities: Prix TTC


class TuitionInput(BaseModel):
    """
    Input data for tuition revenue calculation.

    Contains student enrollment details and fee structure.
    """

    student_id: UUID | None = Field(None, description="Student UUID (optional)")
    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code (e.g., '6EME', 'TERMINALE')")
    fee_category: FeeCategory = Field(..., description="Fee category by nationality")

    # Fees in SAR
    tuition_fee: Decimal = Field(..., ge=Decimal("0"), description="Annual tuition fee (SAR)")
    dai_fee: Decimal = Field(
        ..., ge=Decimal("0"), description="Droit Annuel d'Inscription (SAR)"
    )
    registration_fee: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        description="One-time registration fee (SAR)",
    )

    # Sibling information
    sibling_order: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Student order among siblings (1=eldest, 2=second, etc.)",
    )

    @field_validator("tuition_fee", "dai_fee", "registration_fee")
    @classmethod
    def validate_fees_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure fees are non-negative."""
        if v < 0:
            raise ValueError(f"Fee cannot be negative, got {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "123e4567-e89b-12d3-a456-426614174000",
                "level_id": "123e4567-e89b-12d3-a456-426614174001",
                "level_code": "6EME",
                "fee_category": "french_ttc",
                "tuition_fee": 45000,
                "dai_fee": 2000,
                "registration_fee": 1000,
                "sibling_order": 1,
            }
        }


class TuitionRevenue(BaseModel):
    """
    Tuition revenue calculation result.

    Contains base tuition, discounts applied, and net tuition.
    """

    student_id: UUID | None = Field(None, description="Student UUID")
    level_code: str = Field(..., description="Level code")
    fee_category: FeeCategory = Field(..., description="Fee category")

    # Base fees
    base_tuition: Decimal = Field(..., description="Base annual tuition (SAR)")
    base_dai: Decimal = Field(..., description="Base DAI fee (SAR)")
    base_registration: Decimal = Field(..., description="Base registration fee (SAR)")

    # Discounts
    sibling_discount_amount: Decimal = Field(
        default=Decimal("0"), description="Sibling discount applied (SAR)"
    )
    sibling_discount_rate: Decimal = Field(
        default=Decimal("0"), description="Sibling discount rate (0.00 to 0.25)"
    )

    # Net amounts
    net_tuition: Decimal = Field(..., description="Tuition after discounts (SAR)")
    net_dai: Decimal = Field(..., description="DAI after discounts (SAR, no discount)")
    net_registration: Decimal = Field(
        ..., description="Registration after discounts (SAR, no discount)"
    )
    total_revenue: Decimal = Field(..., description="Total revenue per student (SAR)")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "123e4567-e89b-12d3-a456-426614174000",
                "level_code": "6EME",
                "fee_category": "french_ttc",
                "base_tuition": 45000,
                "base_dai": 2000,
                "base_registration": 1000,
                "sibling_discount_amount": 11250,
                "sibling_discount_rate": 0.25,
                "net_tuition": 33750,
                "net_dai": 2000,
                "net_registration": 1000,
                "total_revenue": 36750,
            }
        }


class SiblingDiscount(BaseModel):
    """
    Sibling discount calculation.

    Business Rule: 25% discount on tuition for 3rd+ child.
    NOT applicable to DAI or registration fees.
    """

    sibling_order: int = Field(..., description="Student order among siblings")
    discount_applicable: bool = Field(..., description="Whether discount applies (3rd+ child)")
    discount_rate: Decimal = Field(..., description="Discount rate (0.25 for 3rd+ child)")
    base_tuition: Decimal = Field(..., description="Base tuition before discount (SAR)")
    discount_amount: Decimal = Field(..., description="Discount amount (SAR)")
    net_tuition: Decimal = Field(..., description="Tuition after discount (SAR)")

    class Config:
        json_schema_extra = {
            "example": {
                "sibling_order": 3,
                "discount_applicable": True,
                "discount_rate": 0.25,
                "base_tuition": 45000,
                "discount_amount": 11250,
                "net_tuition": 33750,
            }
        }


class TrimesterDistribution(BaseModel):
    """
    Trimester-based revenue distribution.

    Business Rule: T1: 40%, T2: 30%, T3: 30%
    """

    total_revenue: Decimal = Field(..., description="Total annual revenue (SAR)")
    trimester_1: Decimal = Field(..., description="T1 revenue (40%)")
    trimester_2: Decimal = Field(..., description="T2 revenue (30%)")
    trimester_3: Decimal = Field(..., description="T3 revenue (30%)")

    # Percentages
    t1_percentage: Decimal = Field(default=Decimal("0.40"), description="T1 percentage (40%)")
    t2_percentage: Decimal = Field(default=Decimal("0.30"), description="T2 percentage (30%)")
    t3_percentage: Decimal = Field(default=Decimal("0.30"), description="T3 percentage (30%)")

    @field_validator("t1_percentage", "t2_percentage", "t3_percentage")
    @classmethod
    def validate_percentage_range(cls, v: Decimal) -> Decimal:
        """Ensure percentages are between 0 and 1."""
        if not (Decimal("0") <= v <= Decimal("1")):
            raise ValueError(f"Percentage must be between 0 and 1, got {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "total_revenue": 45000,
                "trimester_1": 18000,
                "trimester_2": 13500,
                "trimester_3": 13500,
                "t1_percentage": 0.40,
                "t2_percentage": 0.30,
                "t3_percentage": 0.30,
            }
        }


class StudentRevenueResult(BaseModel):
    """
    Complete student revenue calculation result.

    Combines tuition calculation with trimester distribution.
    """

    student_id: UUID | None = Field(None, description="Student UUID")
    level_code: str = Field(..., description="Level code")
    fee_category: FeeCategory = Field(..., description="Fee category")

    # Revenue breakdown
    tuition_revenue: TuitionRevenue = Field(..., description="Tuition calculation details")
    trimester_distribution: TrimesterDistribution = Field(
        ..., description="Trimester revenue distribution"
    )

    # Summary
    total_annual_revenue: Decimal = Field(..., description="Total annual revenue (SAR)")
    sibling_discount_applied: bool = Field(..., description="Whether sibling discount applied")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "123e4567-e89b-12d3-a456-426614174000",
                "level_code": "6EME",
                "fee_category": "french_ttc",
                "tuition_revenue": {
                    "level_code": "6EME",
                    "fee_category": "french_ttc",
                    "base_tuition": 45000,
                    "base_dai": 2000,
                    "base_registration": 1000,
                    "sibling_discount_amount": 11250,
                    "sibling_discount_rate": 0.25,
                    "net_tuition": 33750,
                    "net_dai": 2000,
                    "net_registration": 1000,
                    "total_revenue": 36750,
                },
                "trimester_distribution": {
                    "total_revenue": 36750,
                    "trimester_1": 14700,
                    "trimester_2": 11025,
                    "trimester_3": 11025,
                },
                "total_annual_revenue": 36750,
                "sibling_discount_applied": True,
            }
        }
