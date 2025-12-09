"""Seed subjects reference data.

Revision ID: 012_seed_subjects
Revises: 011_seed_reference_data
Create Date: 2025-12-06 14:00:00.000000

Seeds essential subjects for DHG calculations:
- Core subjects (Français, Mathématiques, etc.)
- Languages (Anglais, Espagnol, Allemand, Arabe)
- Sciences (SVT, Physique-Chimie, SES)
- Arts and Physical Education
- Specialties (Philosophie, Options)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "013_seed_subjects"
down_revision = "012_add_audit_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed subjects reference data."""

    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # =========================================================================
    # Seed Subjects for French Education System
    # =========================================================================

    subjects_data = [
        # Core subjects (matières principales)
        {
            "id": uuid.uuid4(),
            "code": "FRAN",
            "name_fr": "Français",
            "name_en": "French",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "MATH",
            "name_fr": "Mathématiques",
            "name_en": "Mathematics",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "HGEO",
            "name_fr": "Histoire-Géographie",
            "name_en": "History-Geography",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Languages (langues)
        {
            "id": uuid.uuid4(),
            "code": "ANGL",
            "name_fr": "Anglais",
            "name_en": "English",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "ESPA",
            "name_fr": "Espagnol",
            "name_en": "Spanish",
            "category": "elective",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "ALLE",
            "name_fr": "Allemand",
            "name_en": "German",
            "category": "elective",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "ARAB",
            "name_fr": "Arabe",
            "name_en": "Arabic",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Sciences
        {
            "id": uuid.uuid4(),
            "code": "SVT",
            "name_fr": "Sciences de la Vie et de la Terre",
            "name_en": "Life and Earth Sciences",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "PHCH",
            "name_fr": "Physique-Chimie",
            "name_en": "Physics-Chemistry",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "TECH",
            "name_fr": "Technologie",
            "name_en": "Technology",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "SES",
            "name_fr": "Sciences Économiques et Sociales",
            "name_en": "Economics and Social Sciences",
            "category": "specialty",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "NSI",
            "name_fr": "Numérique et Sciences Informatiques",
            "name_en": "Computer Science",
            "category": "specialty",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Arts and Physical Education
        {
            "id": uuid.uuid4(),
            "code": "EPS",
            "name_fr": "Éducation Physique et Sportive",
            "name_en": "Physical Education",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "ARTS",
            "name_fr": "Arts Plastiques",
            "name_en": "Visual Arts",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "MUSI",
            "name_fr": "Éducation Musicale",
            "name_en": "Music Education",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Lycée specialties
        {
            "id": uuid.uuid4(),
            "code": "PHIL",
            "name_fr": "Philosophie",
            "name_en": "Philosophy",
            "category": "specialty",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "EMC",
            "name_fr": "Enseignement Moral et Civique",
            "name_en": "Moral and Civic Education",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Primary specific
        {
            "id": uuid.uuid4(),
            "code": "DECO",
            "name_fr": "Découverte du Monde",
            "name_en": "World Discovery",
            "category": "core",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        # Options
        {
            "id": uuid.uuid4(),
            "code": "LATI",
            "name_fr": "Latin",
            "name_en": "Latin",
            "category": "elective",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "GREC",
            "name_fr": "Grec Ancien",
            "name_en": "Ancient Greek",
            "category": "elective",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Insert subjects
    for subject in subjects_data:
        conn.execute(
            sa.text("""
                INSERT INTO efir_budget.subjects
                (id, code, name_fr, name_en, category, is_active, created_at, updated_at)
                VALUES (:id, :code, :name_fr, :name_en, :category, :is_active, :created_at, :updated_at)
                ON CONFLICT (code) DO NOTHING
            """),
            subject,
        )


def downgrade() -> None:
    """Remove seeded subjects (optional - keeps data for safety)."""
    # We don't delete seed data in downgrade as it may be referenced
    # by other tables (subject_hours_matrix) and would require complex cleanup
    pass
