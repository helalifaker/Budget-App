"""Seed reference data and create nationality_distributions table.

Revision ID: 011_seed_reference_data
Revises: 010_planning_cells_writeback
Create Date: 2025-12-05 12:00:00.000000

Seeds essential reference data:
- Academic cycles (4): MAT, ELEM, COLL, LYC
- Academic levels (15): PS through Terminale
- Nationality types (3): FRENCH, SAUDI, OTHER

Creates nationality_distributions table for per-level percentage tracking.
"""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_seed_reference_data"
down_revision = "010_planning_cells_writeback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed reference data and create nationality_distributions table."""

    # Get connection for raw SQL inserts
    conn = op.get_bind()

    # =========================================================================
    # Seed Academic Cycles (4 records)
    # =========================================================================

    # Generate UUIDs for cycles (so we can reference them in levels)
    cycle_mat_id = uuid.uuid4()
    cycle_elem_id = uuid.uuid4()
    cycle_coll_id = uuid.uuid4()
    cycle_lyc_id = uuid.uuid4()

    now = datetime.now(UTC)

    cycles_data = [
        {
            "id": cycle_mat_id,
            "code": "MAT",
            "name_fr": "Maternelle",
            "name_en": "Preschool",
            "sort_order": 1,
            "requires_atsem": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": cycle_elem_id,
            "code": "ELEM",
            "name_fr": "Élémentaire",
            "name_en": "Elementary",
            "sort_order": 2,
            "requires_atsem": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": cycle_coll_id,
            "code": "COLL",
            "name_fr": "Collège",
            "name_en": "Middle School",
            "sort_order": 3,
            "requires_atsem": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": cycle_lyc_id,
            "code": "LYC",
            "name_fr": "Lycée",
            "name_en": "High School",
            "sort_order": 4,
            "requires_atsem": False,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Insert cycles
    for cycle in cycles_data:
        conn.execute(
            sa.text("""
                INSERT INTO efir_budget.academic_cycles
                (id, code, name_fr, name_en, sort_order, requires_atsem, created_at, updated_at)
                VALUES (:id, :code, :name_fr, :name_en, :sort_order, :requires_atsem, :created_at, :updated_at)
                ON CONFLICT (code) DO NOTHING
            """),
            cycle,
        )

    # =========================================================================
    # Seed Academic Levels (15 records)
    # =========================================================================

    levels_data = [
        # Maternelle (3 levels)
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_mat_id,
            "code": "PS",
            "name_fr": "Petite Section",
            "name_en": "Preschool - Small Section",
            "sort_order": 1,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_mat_id,
            "code": "MS",
            "name_fr": "Moyenne Section",
            "name_en": "Preschool - Medium Section",
            "sort_order": 2,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_mat_id,
            "code": "GS",
            "name_fr": "Grande Section",
            "name_en": "Preschool - Large Section",
            "sort_order": 3,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        # Élémentaire (5 levels)
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_elem_id,
            "code": "CP",
            "name_fr": "CP",
            "name_en": "Elementary - 1st Grade",
            "sort_order": 4,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_elem_id,
            "code": "CE1",
            "name_fr": "CE1",
            "name_en": "Elementary - 2nd Grade",
            "sort_order": 5,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_elem_id,
            "code": "CE2",
            "name_fr": "CE2",
            "name_en": "Elementary - 3rd Grade",
            "sort_order": 6,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_elem_id,
            "code": "CM1",
            "name_fr": "CM1",
            "name_en": "Elementary - 4th Grade",
            "sort_order": 7,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_elem_id,
            "code": "CM2",
            "name_fr": "CM2",
            "name_en": "Elementary - 5th Grade",
            "sort_order": 8,
            "is_secondary": False,
            "created_at": now,
            "updated_at": now,
        },
        # Collège (4 levels)
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_coll_id,
            "code": "6EME",
            "name_fr": "Sixième",
            "name_en": "Middle School - 6th Grade",
            "sort_order": 9,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_coll_id,
            "code": "5EME",
            "name_fr": "Cinquième",
            "name_en": "Middle School - 7th Grade",
            "sort_order": 10,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_coll_id,
            "code": "4EME",
            "name_fr": "Quatrième",
            "name_en": "Middle School - 8th Grade",
            "sort_order": 11,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_coll_id,
            "code": "3EME",
            "name_fr": "Troisième",
            "name_en": "Middle School - 9th Grade",
            "sort_order": 12,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        # Lycée (3 levels)
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_lyc_id,
            "code": "2NDE",
            "name_fr": "Seconde",
            "name_en": "High School - 10th Grade",
            "sort_order": 13,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_lyc_id,
            "code": "1ERE",
            "name_fr": "Première",
            "name_en": "High School - 11th Grade",
            "sort_order": 14,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "cycle_id": cycle_lyc_id,
            "code": "TLE",
            "name_fr": "Terminale",
            "name_en": "High School - 12th Grade",
            "sort_order": 15,
            "is_secondary": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Insert levels
    for level in levels_data:
        conn.execute(
            sa.text("""
                INSERT INTO efir_budget.academic_levels
                (id, cycle_id, code, name_fr, name_en, sort_order, is_secondary, created_at, updated_at)
                VALUES (:id, :cycle_id, :code, :name_fr, :name_en, :sort_order, :is_secondary, :created_at, :updated_at)
                ON CONFLICT (code) DO NOTHING
            """),
            level,
        )

    # =========================================================================
    # Seed Nationality Types (3 records)
    # =========================================================================

    nationality_types_data = [
        {
            "id": uuid.uuid4(),
            "code": "FRENCH",
            "name_fr": "Français",
            "name_en": "French",
            "vat_applicable": False,  # French nationals: HT in Saudi context
            "sort_order": 1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "SAUDI",
            "name_fr": "Saoudien",
            "name_en": "Saudi",
            "vat_applicable": False,  # Saudi nationals: HT (no VAT)
            "sort_order": 2,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "code": "OTHER",
            "name_fr": "Autre",
            "name_en": "Other",
            "vat_applicable": True,  # Other nationals: TTC (with VAT)
            "sort_order": 3,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Insert nationality types
    for nat_type in nationality_types_data:
        conn.execute(
            sa.text("""
                INSERT INTO efir_budget.nationality_types
                (id, code, name_fr, name_en, vat_applicable, sort_order, created_at, updated_at)
                VALUES (:id, :code, :name_fr, :name_en, :vat_applicable, :sort_order, :created_at, :updated_at)
                ON CONFLICT (code) DO NOTHING
            """),
            nat_type,
        )

    # =========================================================================
    # Create nationality_distributions table
    # =========================================================================

    op.create_table(
        "nationality_distributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Budget version this distribution belongs to",
        ),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_levels.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Academic level (per-level distribution)",
        ),
        sa.Column(
            "french_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
            comment="French nationality percentage (0-100)",
        ),
        sa.Column(
            "saudi_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
            comment="Saudi nationality percentage (0-100)",
        ),
        sa.Column(
            "other_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
            comment="Other nationalities percentage (0-100)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.UniqueConstraint(
            "budget_version_id", "level_id", name="uk_distribution_version_level"
        ),
        sa.CheckConstraint(
            "french_pct >= 0 AND french_pct <= 100", name="ck_distribution_french_range"
        ),
        sa.CheckConstraint(
            "saudi_pct >= 0 AND saudi_pct <= 100", name="ck_distribution_saudi_range"
        ),
        sa.CheckConstraint(
            "other_pct >= 0 AND other_pct <= 100", name="ck_distribution_other_range"
        ),
        sa.CheckConstraint(
            "french_pct + saudi_pct + other_pct = 100",
            name="ck_distribution_sum_100",
        ),
        schema="efir_budget",
        comment="Per-level nationality distribution percentages for enrollment planning",
    )

    # Create index for efficient lookups
    op.create_index(
        "ix_nationality_distributions_version_id",
        "nationality_distributions",
        ["budget_version_id"],
        schema="efir_budget",
    )


def downgrade() -> None:
    """Remove nationality_distributions table and seed data."""

    # Drop nationality_distributions table
    op.drop_index(
        "ix_nationality_distributions_version_id",
        table_name="nationality_distributions",
        schema="efir_budget",
    )
    op.drop_table("nationality_distributions", schema="efir_budget")

    # Note: We don't delete seed data in downgrade as it may be referenced
    # by other tables and would require a more complex cleanup
