"""
Curriculum templates for AEFE standard programs.

These templates define standard weekly hours per subject for French education
cycles. They can be applied to quickly populate subject hours configuration.

Reference: French Ministry of Education official programs (Bulletin Officiel)
"""

from decimal import Decimal
from typing import TypedDict


class TemplateHours(TypedDict):
    """Type for hours by level code."""

    pass  # Dynamic keys (level codes)


class CurriculumTemplate(TypedDict):
    """Structure for a curriculum template."""

    template_code: str
    template_name: str
    description: str
    cycle_codes: list[str]
    hours: dict[str, dict[str, Decimal]]  # subject_code -> level_code -> hours
    split_defaults: dict[str, bool]  # subject_code -> is_split


# ==============================================================================
# AEFE Standard - Collège (6ème - 3ème)
# ==============================================================================

AEFE_STANDARD_COLLEGE: CurriculumTemplate = {
    "template_code": "AEFE_STANDARD_COLL",
    "template_name": "AEFE Standard - Collège",
    "description": "Standard French national curriculum hours for middle school (6ème-3ème)",
    "cycle_codes": ["COLL"],
    "hours": {
        # Core subjects
        "FRAN": {
            "6EME": Decimal("4.5"),
            "5EME": Decimal("4.5"),
            "4EME": Decimal("4.5"),
            "3EME": Decimal("4.0"),
        },
        "MATH": {
            "6EME": Decimal("4.5"),
            "5EME": Decimal("3.5"),
            "4EME": Decimal("3.5"),
            "3EME": Decimal("3.5"),
        },
        "HGEO": {
            "6EME": Decimal("3.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.5"),
        },
        "SVT": {
            "6EME": Decimal("1.5"),
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "PHCH": {
            "6EME": Decimal("0.0"),  # Not taught in 6ème
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "TECH": {
            "6EME": Decimal("1.5"),
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "EPS": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
        "ARTS": {
            "6EME": Decimal("1.0"),
            "5EME": Decimal("1.0"),
            "4EME": Decimal("1.0"),
            "3EME": Decimal("1.0"),
        },
        "MUSI": {
            "6EME": Decimal("1.0"),
            "5EME": Decimal("1.0"),
            "4EME": Decimal("1.0"),
            "3EME": Decimal("1.0"),
        },
        "EMC": {
            "6EME": Decimal("0.5"),
            "5EME": Decimal("0.5"),
            "4EME": Decimal("0.5"),
            "3EME": Decimal("0.5"),
        },
        # Languages
        "ANGL": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
        "ARAB": {
            "6EME": Decimal("3.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
        "ESPA": {
            "6EME": Decimal("0.0"),  # LV2 starts in 5ème
            "5EME": Decimal("2.5"),
            "4EME": Decimal("2.5"),
            "3EME": Decimal("2.5"),
        },
    },
    "split_defaults": {
        "ANGL": True,  # Languages typically split
        "ESPA": True,
        "ARAB": True,
        "SVT": True,  # Sciences with lab work
        "PHCH": True,
        "TECH": True,
    },
}

# ==============================================================================
# AEFE Standard - Lycée (2nde - Terminale)
# ==============================================================================

AEFE_STANDARD_LYCEE: CurriculumTemplate = {
    "template_code": "AEFE_STANDARD_LYC",
    "template_name": "AEFE Standard - Lycée",
    "description": "Standard French national curriculum hours for high school (2nde-Terminale)",
    "cycle_codes": ["LYC"],
    "hours": {
        # Core subjects (Tronc commun)
        "FRAN": {
            "2NDE": Decimal("4.0"),
            "1ERE": Decimal("4.0"),
            "TERM": Decimal("2.0"),  # Philosophie replaces part of French
        },
        "PHIL": {
            "2NDE": Decimal("0.0"),  # Not taught in 2nde
            "1ERE": Decimal("0.0"),  # Not taught in 1ère
            "TERM": Decimal("4.0"),
        },
        "HGEO": {
            "2NDE": Decimal("3.0"),
            "1ERE": Decimal("3.0"),
            "TERM": Decimal("3.0"),
        },
        "MATH": {
            "2NDE": Decimal("4.0"),
            "1ERE": Decimal("3.0"),  # Tronc commun (if not specialty)
            "TERM": Decimal("3.0"),
        },
        "SVT": {
            "2NDE": Decimal("1.5"),
            "1ERE": Decimal("0.0"),  # Becomes specialty
            "TERM": Decimal("0.0"),
        },
        "PHCH": {
            "2NDE": Decimal("3.0"),
            "1ERE": Decimal("0.0"),  # Becomes specialty
            "TERM": Decimal("0.0"),
        },
        "EPS": {
            "2NDE": Decimal("2.0"),
            "1ERE": Decimal("2.0"),
            "TERM": Decimal("2.0"),
        },
        "EMC": {
            "2NDE": Decimal("0.5"),
            "1ERE": Decimal("0.5"),
            "TERM": Decimal("0.5"),
        },
        # Languages
        "ANGL": {
            "2NDE": Decimal("3.0"),
            "1ERE": Decimal("2.5"),
            "TERM": Decimal("2.0"),
        },
        "ARAB": {
            "2NDE": Decimal("3.0"),
            "1ERE": Decimal("2.5"),
            "TERM": Decimal("2.0"),
        },
        "ESPA": {
            "2NDE": Decimal("2.5"),
            "1ERE": Decimal("2.0"),
            "TERM": Decimal("2.0"),
        },
        # Sciences numériques
        "SNT": {
            "2NDE": Decimal("1.5"),
            "1ERE": Decimal("0.0"),
            "TERM": Decimal("0.0"),
        },
    },
    "split_defaults": {
        "ANGL": True,
        "ESPA": True,
        "ARAB": True,
        "SVT": True,
        "PHCH": True,
        "SNT": True,
    },
}

# ==============================================================================
# AEFE Reinforced - Extra hours for languages and sciences
# ==============================================================================

AEFE_REINFORCED_COLLEGE: CurriculumTemplate = {
    "template_code": "AEFE_REINFORCED_COLL",
    "template_name": "AEFE Reinforced - Collège",
    "description": "Enhanced curriculum with extra hours for languages and sciences",
    "cycle_codes": ["COLL"],
    "hours": {
        # Core subjects (same as standard)
        "FRAN": {
            "6EME": Decimal("5.0"),
            "5EME": Decimal("5.0"),
            "4EME": Decimal("5.0"),
            "3EME": Decimal("4.5"),
        },
        "MATH": {
            "6EME": Decimal("5.0"),
            "5EME": Decimal("4.0"),
            "4EME": Decimal("4.0"),
            "3EME": Decimal("4.0"),
        },
        "HGEO": {
            "6EME": Decimal("3.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.5"),
        },
        "SVT": {
            "6EME": Decimal("2.0"),
            "5EME": Decimal("2.0"),
            "4EME": Decimal("2.0"),
            "3EME": Decimal("2.0"),
        },
        "PHCH": {
            "6EME": Decimal("0.0"),
            "5EME": Decimal("2.0"),
            "4EME": Decimal("2.0"),
            "3EME": Decimal("2.0"),
        },
        "TECH": {
            "6EME": Decimal("1.5"),
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "EPS": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
        "ARTS": {
            "6EME": Decimal("1.0"),
            "5EME": Decimal("1.0"),
            "4EME": Decimal("1.0"),
            "3EME": Decimal("1.0"),
        },
        "MUSI": {
            "6EME": Decimal("1.0"),
            "5EME": Decimal("1.0"),
            "4EME": Decimal("1.0"),
            "3EME": Decimal("1.0"),
        },
        "EMC": {
            "6EME": Decimal("0.5"),
            "5EME": Decimal("0.5"),
            "4EME": Decimal("0.5"),
            "3EME": Decimal("0.5"),
        },
        # Languages - reinforced
        "ANGL": {
            "6EME": Decimal("5.0"),
            "5EME": Decimal("4.0"),
            "4EME": Decimal("4.0"),
            "3EME": Decimal("4.0"),
        },
        "ARAB": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("4.0"),
            "4EME": Decimal("4.0"),
            "3EME": Decimal("4.0"),
        },
        "ESPA": {
            "6EME": Decimal("0.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
    },
    "split_defaults": {
        "ANGL": True,
        "ESPA": True,
        "ARAB": True,
        "SVT": True,
        "PHCH": True,
        "TECH": True,
    },
}

# ==============================================================================
# Template Registry
# ==============================================================================

CURRICULUM_TEMPLATES: dict[str, CurriculumTemplate] = {
    "AEFE_STANDARD_COLL": AEFE_STANDARD_COLLEGE,
    "AEFE_STANDARD_LYC": AEFE_STANDARD_LYCEE,
    "AEFE_REINFORCED_COLL": AEFE_REINFORCED_COLLEGE,
}


def get_template(template_code: str) -> CurriculumTemplate | None:
    """
    Get a curriculum template by code.

    Args:
        template_code: Template code (e.g., 'AEFE_STANDARD_COLL')

    Returns:
        CurriculumTemplate or None if not found
    """
    return CURRICULUM_TEMPLATES.get(template_code)


def get_template_list() -> list[dict[str, str | list[str]]]:
    """
    Get list of available templates for frontend display.

    Returns:
        List of template info dicts with code, name, description, cycle_codes
    """
    return [
        {
            "code": t["template_code"],
            "name": t["template_name"],
            "description": t["description"],
            "cycle_codes": t["cycle_codes"],
        }
        for t in CURRICULUM_TEMPLATES.values()
    ]
