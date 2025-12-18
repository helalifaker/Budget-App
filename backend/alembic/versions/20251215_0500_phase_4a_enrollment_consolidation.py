"""Phase 4A: Enrollment Module Consolidation

Revision ID: 026_phase_4a_enrollment_consolidation
Revises: 025_phase_3b_table_prefixes
Create Date: 2025-12-15

Consolidates enrollment tables from 12 → 6:

OLD TABLES (to be merged):
- students_projection_configs + students_scenario_multipliers → students_configs
- students_enrollment_plans + students_nationality_distributions → students_data (separate migration)
- students_global/level/grade_overrides + lateral_entry_defaults → students_overrides
- students_derived_parameters + students_parameter_overrides → students_calibration

KEEP (add lineage columns):
- students_enrollment_projections
- students_class_structures

This migration creates the new unified tables and migrates data.
Old tables are kept for validation and dropped in a subsequent migration.
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "026_phase_4a_enrollment_consolidation"
down_revision: str | None = "025_phase_3b_table_prefixes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create unified enrollment tables and migrate data."""

    # ========================================================================
    # STEP 1: Create ENUM types
    # ========================================================================
    op.execute("""
        CREATE TYPE efir_budget.override_scope AS ENUM ('global', 'cycle', 'level')
    """)

    op.execute("""
        CREATE TYPE efir_budget.calibration_origin AS ENUM ('calculated', 'manual_override')
    """)

    op.execute("""
        CREATE TYPE efir_budget.data_source_type AS ENUM ('manual', 'projected', 'actual', 'imported')
    """)

    # ========================================================================
    # STEP 2: Create students_configs (merge projection_configs + scenario_multipliers)
    # ========================================================================
    op.execute("""
        CREATE TABLE efir_budget.students_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,
            scenario_code VARCHAR(20) NOT NULL DEFAULT 'base',

            -- From projection_configs
            base_year INTEGER NOT NULL,
            projection_years INTEGER NOT NULL DEFAULT 5,
            school_max_capacity INTEGER NOT NULL DEFAULT 1850,
            default_class_size INTEGER NOT NULL DEFAULT 25,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            validated_at TIMESTAMPTZ,
            validated_by UUID,

            -- From scenario_multipliers
            lateral_multiplier NUMERIC(5,2) NOT NULL DEFAULT 1.00,

            -- Audit columns
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by_id UUID,
            updated_by_id UUID,
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX ix_students_configs_version_scenario
        ON efir_budget.students_configs(version_id, scenario_code)
        WHERE deleted_at IS NULL
    """)

    # ========================================================================
    # STEP 3: Create students_data (unified enrollment data)
    # ========================================================================
    op.execute("""
        CREATE TABLE efir_budget.students_data (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,
            fiscal_year INTEGER NOT NULL,
            level_id UUID NOT NULL REFERENCES efir_budget.ref_academic_levels(id),

            -- Enrollment counts
            student_count INTEGER NOT NULL DEFAULT 0,
            number_of_classes INTEGER,
            avg_class_size NUMERIC(5,2),

            -- Nationality breakdown (from nationality_distributions)
            french_pct NUMERIC(5,2) DEFAULT 0,
            saudi_pct NUMERIC(5,2) DEFAULT 0,
            other_pct NUMERIC(5,2) DEFAULT 0,

            -- Nationality type (for backward compatibility)
            nationality_type_id UUID REFERENCES efir_budget.ref_nationality_types(id),

            -- Data source tracking
            data_source efir_budget.data_source_type NOT NULL DEFAULT 'manual',

            -- Audit columns
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by_id UUID,
            updated_by_id UUID,
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE INDEX ix_students_data_version_year
        ON efir_budget.students_data(version_id, fiscal_year)
    """)

    op.execute("""
        CREATE INDEX ix_students_data_level
        ON efir_budget.students_data(level_id)
    """)

    # ========================================================================
    # STEP 4: Create students_overrides (unified override layers)
    # ========================================================================
    op.execute("""
        CREATE TABLE efir_budget.students_overrides (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            config_id UUID NOT NULL REFERENCES efir_budget.students_configs(id) ON DELETE CASCADE,

            -- Scope definition
            scope_type efir_budget.override_scope NOT NULL,
            scope_id UUID,

            -- Override values
            ps_entry_adjustment INTEGER,
            retention_adjustment NUMERIC(5,4),
            retention_rate NUMERIC(5,4),
            lateral_entry INTEGER,
            lateral_multiplier_override NUMERIC(5,2),

            -- Class size constraints
            min_class_size INTEGER,
            max_class_size INTEGER,
            target_class_size INTEGER,
            max_divisions INTEGER,
            class_size_ceiling INTEGER,

            -- Audit
            override_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by_id UUID,
            updated_by_id UUID,
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX ix_students_overrides_config_scope
        ON efir_budget.students_overrides(config_id, scope_type, scope_id)
        WHERE deleted_at IS NULL
    """)

    # ========================================================================
    # STEP 5: Create students_calibration (unified calibration parameters)
    # ========================================================================
    op.execute("""
        CREATE TABLE efir_budget.students_calibration (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
            grade_code VARCHAR(10) NOT NULL,

            -- Data origin tracking
            data_origin efir_budget.calibration_origin NOT NULL DEFAULT 'calculated',

            -- Derived parameters
            progression_rate NUMERIC(5,4),
            lateral_entry_rate NUMERIC(5,4),
            retention_rate NUMERIC(5,4),
            confidence VARCHAR(20) DEFAULT 'low',
            std_deviation NUMERIC(10,6),
            years_used INTEGER DEFAULT 0,
            source_years JSONB DEFAULT '[]'::jsonb,
            calculated_at TIMESTAMPTZ DEFAULT now(),

            -- Manual overrides
            override_lateral_rate BOOLEAN DEFAULT FALSE,
            manual_lateral_rate NUMERIC(5,4),
            override_retention_rate BOOLEAN DEFAULT FALSE,
            manual_retention_rate NUMERIC(5,4),
            override_fixed_lateral BOOLEAN DEFAULT FALSE,
            manual_fixed_lateral INTEGER,
            override_reason TEXT,

            -- Audit columns
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by_id UUID,
            updated_by_id UUID,
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX ix_students_calibration_org_grade
        ON efir_budget.students_calibration(organization_id, grade_code)
        WHERE deleted_at IS NULL
    """)

    # ========================================================================
    # STEP 6: Add lineage columns to OUTPUT tables
    # ========================================================================
    # Add to students_enrollment_projections
    op.execute("""
        ALTER TABLE efir_budget.students_enrollment_projections
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64)
    """)

    # Add to students_class_structures
    op.execute("""
        ALTER TABLE efir_budget.students_class_structures
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64)
    """)

    # ========================================================================
    # STEP 7: Migrate data - projection_configs → students_configs
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.students_configs (
            id, version_id, scenario_code, base_year, projection_years,
            school_max_capacity, default_class_size, status, validated_at, validated_by,
            lateral_multiplier, created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            pc.id,
            pc.version_id,
            COALESCE(es.code, 'base') as scenario_code,
            pc.base_year,
            pc.projection_years,
            pc.school_max_capacity,
            pc.default_class_size,
            pc.status,
            pc.validated_at,
            pc.validated_by,
            COALESCE(
                (SELECT sm.lateral_multiplier
                 FROM efir_budget.students_scenario_multipliers sm
                 WHERE sm.scenario_code = COALESCE(es.code, 'base')
                 LIMIT 1),
                1.00
            ) as lateral_multiplier,
            pc.created_at,
            pc.updated_at,
            pc.created_by_id,
            pc.updated_by_id,
            pc.deleted_at
        FROM efir_budget.students_projection_configs pc
        LEFT JOIN efir_budget.ref_enrollment_scenarios es ON es.id = pc.scenario_id
        ON CONFLICT DO NOTHING
    """)

    # ========================================================================
    # STEP 8: Migrate data - enrollment_plans → students_data
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.students_data (
            version_id, fiscal_year, level_id, student_count,
            nationality_type_id, data_source, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            ep.version_id,
            EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER as fiscal_year,
            ep.level_id,
            ep.student_count,
            ep.nationality_type_id,
            'manual'::efir_budget.data_source_type,
            ep.notes,
            ep.created_at,
            ep.updated_at,
            ep.created_by_id,
            ep.updated_by_id,
            ep.deleted_at
        FROM efir_budget.students_enrollment_plans ep
        ON CONFLICT DO NOTHING
    """)

    # Update with nationality distributions
    op.execute("""
        UPDATE efir_budget.students_data sd
        SET
            french_pct = nd.french_pct,
            saudi_pct = nd.saudi_pct,
            other_pct = nd.other_pct
        FROM efir_budget.students_nationality_distributions nd
        WHERE sd.version_id = nd.version_id
          AND sd.level_id = nd.level_id
    """)

    # ========================================================================
    # STEP 9: Migrate data - overrides → students_overrides
    # ========================================================================
    # Global overrides
    op.execute("""
        INSERT INTO efir_budget.students_overrides (
            config_id, scope_type, scope_id,
            ps_entry_adjustment, retention_adjustment, lateral_multiplier_override, max_class_size,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            go.projection_config_id,
            'global'::efir_budget.override_scope,
            NULL,
            go.ps_entry_adjustment,
            go.retention_adjustment,
            go.lateral_multiplier_override,
            go.class_size_override,
            go.created_at,
            go.updated_at,
            go.created_by_id,
            go.updated_by_id,
            go.deleted_at
        FROM efir_budget.students_global_overrides go
        WHERE EXISTS (
            SELECT 1 FROM efir_budget.students_configs sc
            WHERE sc.id = go.projection_config_id
        )
        ON CONFLICT DO NOTHING
    """)

    # Level (cycle) overrides
    op.execute("""
        INSERT INTO efir_budget.students_overrides (
            config_id, scope_type, scope_id,
            class_size_ceiling, max_divisions,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            lo.projection_config_id,
            'cycle'::efir_budget.override_scope,
            lo.cycle_id,
            lo.class_size_ceiling,
            lo.max_divisions,
            lo.created_at,
            lo.updated_at,
            lo.created_by_id,
            lo.updated_by_id,
            lo.deleted_at
        FROM efir_budget.students_level_overrides lo
        WHERE EXISTS (
            SELECT 1 FROM efir_budget.students_configs sc
            WHERE sc.id = lo.projection_config_id
        )
        ON CONFLICT DO NOTHING
    """)

    # Grade (level) overrides
    op.execute("""
        INSERT INTO efir_budget.students_overrides (
            config_id, scope_type, scope_id,
            retention_rate, lateral_entry, max_divisions, class_size_ceiling,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            gro.projection_config_id,
            'level'::efir_budget.override_scope,
            gro.level_id,
            gro.retention_rate,
            gro.lateral_entry,
            gro.max_divisions,
            gro.class_size_ceiling,
            gro.created_at,
            gro.updated_at,
            gro.created_by_id,
            gro.updated_by_id,
            gro.deleted_at
        FROM efir_budget.students_grade_overrides gro
        WHERE EXISTS (
            SELECT 1 FROM efir_budget.students_configs sc
            WHERE sc.id = gro.projection_config_id
        )
        ON CONFLICT DO NOTHING
    """)

    # ========================================================================
    # STEP 10: Migrate data - calibration parameters → students_calibration
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.students_calibration (
            organization_id, grade_code, data_origin,
            progression_rate, lateral_entry_rate, retention_rate, confidence, std_deviation,
            years_used, source_years, calculated_at,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            dp.organization_id,
            dp.grade_code,
            'calculated'::efir_budget.calibration_origin,
            dp.progression_rate,
            dp.lateral_entry_rate,
            dp.retention_rate,
            dp.confidence,
            dp.std_deviation,
            dp.years_used,
            dp.source_years,
            dp.calculated_at,
            dp.created_at,
            dp.updated_at,
            dp.created_by_id,
            dp.updated_by_id,
            dp.deleted_at
        FROM efir_budget.students_derived_parameters dp
        ON CONFLICT DO NOTHING
    """)

    # Update with manual overrides from students_parameter_overrides
    op.execute("""
        UPDATE efir_budget.students_calibration c
        SET
            data_origin = CASE
                WHEN po.override_lateral_rate OR po.override_retention_rate OR po.override_fixed_lateral
                THEN 'manual_override'::efir_budget.calibration_origin
                ELSE c.data_origin
            END,
            override_lateral_rate = COALESCE(po.override_lateral_rate, FALSE),
            manual_lateral_rate = po.manual_lateral_rate,
            override_retention_rate = COALESCE(po.override_retention_rate, FALSE),
            manual_retention_rate = po.manual_retention_rate,
            override_fixed_lateral = COALESCE(po.override_fixed_lateral, FALSE),
            manual_fixed_lateral = po.manual_fixed_lateral,
            override_reason = po.override_reason,
            updated_at = po.updated_at
        FROM efir_budget.students_parameter_overrides po
        WHERE po.organization_id = c.organization_id
          AND po.grade_code = c.grade_code
    """)

    # Insert calibration records that only exist in parameter_overrides
    op.execute("""
        INSERT INTO efir_budget.students_calibration (
            organization_id, grade_code, data_origin,
            override_lateral_rate, manual_lateral_rate,
            override_retention_rate, manual_retention_rate,
            override_fixed_lateral, manual_fixed_lateral,
            override_reason, created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            po.organization_id,
            po.grade_code,
            'manual_override'::efir_budget.calibration_origin,
            po.override_lateral_rate,
            po.manual_lateral_rate,
            po.override_retention_rate,
            po.manual_retention_rate,
            po.override_fixed_lateral,
            po.manual_fixed_lateral,
            po.override_reason,
            po.created_at,
            po.updated_at,
            po.created_by_id,
            po.updated_by_id,
            po.deleted_at
        FROM efir_budget.students_parameter_overrides po
        WHERE NOT EXISTS (
            SELECT 1 FROM efir_budget.students_calibration c
            WHERE c.organization_id = po.organization_id
              AND c.grade_code = po.grade_code
        )
        ON CONFLICT DO NOTHING
    """)

    # ========================================================================
    # STEP 11: Create RLS policies for new tables
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.students_configs ENABLE ROW LEVEL SECURITY
    """)

    op.execute("""
        ALTER TABLE efir_budget.students_data ENABLE ROW LEVEL SECURITY
    """)

    op.execute("""
        ALTER TABLE efir_budget.students_overrides ENABLE ROW LEVEL SECURITY
    """)

    op.execute("""
        ALTER TABLE efir_budget.students_calibration ENABLE ROW LEVEL SECURITY
    """)


def downgrade() -> None:
    """Remove unified enrollment tables."""

    # Drop new tables
    op.execute("DROP TABLE IF EXISTS efir_budget.students_calibration CASCADE")
    op.execute("DROP TABLE IF EXISTS efir_budget.students_overrides CASCADE")
    op.execute("DROP TABLE IF EXISTS efir_budget.students_data CASCADE")
    op.execute("DROP TABLE IF EXISTS efir_budget.students_configs CASCADE")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS efir_budget.data_source_type CASCADE")
    op.execute("DROP TYPE IF EXISTS efir_budget.calibration_origin CASCADE")
    op.execute("DROP TYPE IF EXISTS efir_budget.override_scope CASCADE")

    # Remove lineage columns from OUTPUT tables
    op.execute("""
        ALTER TABLE efir_budget.students_enrollment_projections
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash
    """)

    op.execute("""
        ALTER TABLE efir_budget.students_class_structures
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash
    """)
