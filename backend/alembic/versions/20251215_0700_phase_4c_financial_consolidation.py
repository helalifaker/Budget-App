"""Phase 4C: Financial Module Consolidation

Revision ID: 028_phase_4c_financial_consolidation
Revises: 027_phase_4b_personnel_consolidation
Create Date: 2025-12-15

Consolidates financial planning tables from 4 → 1 unified fact table + views:

OLD TABLES:
- finance_revenue_plans (15 cols) - VERSION-LINKED → merge into finance_data
- finance_operating_cost_plans (14 cols) - VERSION-LINKED → merge into finance_data
- finance_personnel_cost_plans (17 cols) - VERSION-LINKED → merge into finance_data
- finance_capex_plans (16 cols) - VERSION-LINKED → merge into finance_data

NEW STRUCTURE:
- finance_data - Unified fact table with data_type discriminator
- vw_finance_revenue - View filtering data_type='revenue'
- vw_finance_operating_costs - View filtering data_type='operating_cost'
- vw_finance_personnel_costs - View filtering data_type='personnel_cost'
- vw_finance_capex - View filtering data_type='capex'

OUTPUT tables get lineage columns:
- finance_consolidations - Add lineage columns
- finance_statements - Add lineage columns
- finance_statement_lines - Add lineage columns

This migration:
1. Creates finance_data_type ENUM
2. Creates finance_data unified table
3. Migrates data from all 4 source tables
4. Creates backward-compatible views
5. Adds lineage columns to OUTPUT tables
6. Marks old tables as deprecated (not dropped for safety)
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "028_phase_4c_financial_consolidation"
down_revision: str | None = "027_phase_4b_personnel_consolidation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Consolidate financial planning tables."""

    # ========================================================================
    # STEP 1: Create finance_data_type ENUM
    # ========================================================================
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE efir_budget.finance_data_type AS ENUM (
                'revenue',
                'operating_cost',
                'personnel_cost',
                'capex'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ========================================================================
    # STEP 2: Create unified finance_data table
    # ========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS efir_budget.finance_data (
            -- Primary key
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Version FK (VERSION-LINKED table)
            version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,

            -- Discriminator column
            data_type efir_budget.finance_data_type NOT NULL,

            -- Common columns (all data types)
            account_code VARCHAR(20) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            amount_sar NUMERIC(15, 2) NOT NULL,
            is_calculated BOOLEAN NOT NULL DEFAULT FALSE,
            calculation_driver VARCHAR(100),
            notes TEXT,

            -- Revenue-specific columns (nullable, only for data_type='revenue')
            trimester INTEGER CHECK (trimester IS NULL OR trimester BETWEEN 1 AND 3),

            -- Personnel-specific columns (nullable, only for data_type='personnel_cost')
            category_id UUID REFERENCES efir_budget.ref_teacher_categories(id),
            cycle_id UUID REFERENCES efir_budget.ref_academic_cycles(id),
            fte_count NUMERIC(8, 2),
            unit_cost_sar NUMERIC(12, 2),

            -- CapEx-specific columns (nullable, only for data_type='capex')
            quantity INTEGER,
            acquisition_date DATE,
            useful_life_years INTEGER,

            -- Lineage columns for OUTPUT tracking
            computed_at TIMESTAMP WITH TIME ZONE,
            computed_by UUID,
            run_id UUID,
            inputs_hash VARCHAR(64),

            -- Audit columns
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by_id UUID,
            updated_by_id UUID,
            deleted_at TIMESTAMP WITH TIME ZONE
        );

        -- Add comments
        COMMENT ON TABLE efir_budget.finance_data IS 'Unified financial planning data (Phase 4C consolidation)';
        COMMENT ON COLUMN efir_budget.finance_data.data_type IS 'Discriminator: revenue, operating_cost, personnel_cost, capex';
        COMMENT ON COLUMN efir_budget.finance_data.trimester IS 'Revenue only: which trimester (1, 2, or 3)';
        COMMENT ON COLUMN efir_budget.finance_data.category_id IS 'Personnel only: teacher category FK';
        COMMENT ON COLUMN efir_budget.finance_data.cycle_id IS 'Personnel only: academic cycle FK';
        COMMENT ON COLUMN efir_budget.finance_data.fte_count IS 'Personnel only: FTE count';
        COMMENT ON COLUMN efir_budget.finance_data.unit_cost_sar IS 'Personnel/CapEx: unit cost';
        COMMENT ON COLUMN efir_budget.finance_data.quantity IS 'CapEx only: quantity of items';
        COMMENT ON COLUMN efir_budget.finance_data.acquisition_date IS 'CapEx only: when acquired';
        COMMENT ON COLUMN efir_budget.finance_data.useful_life_years IS 'CapEx only: depreciation period';
    """)

    # ========================================================================
    # STEP 3: Create indexes on finance_data
    # ========================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_finance_data_version_id
            ON efir_budget.finance_data(version_id);
        CREATE INDEX IF NOT EXISTS ix_finance_data_data_type
            ON efir_budget.finance_data(data_type);
        CREATE INDEX IF NOT EXISTS ix_finance_data_account_code
            ON efir_budget.finance_data(account_code);
        CREATE INDEX IF NOT EXISTS ix_finance_data_category
            ON efir_budget.finance_data(category);
        CREATE INDEX IF NOT EXISTS ix_finance_data_version_type
            ON efir_budget.finance_data(version_id, data_type);
    """)

    # ========================================================================
    # STEP 4: Migrate data from finance_revenue_plans
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.finance_data (
            id, version_id, data_type, account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes, trimester,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            id, version_id, 'revenue'::efir_budget.finance_data_type,
            account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes, trimester,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_revenue_plans
        ON CONFLICT (id) DO NOTHING;
    """)

    # ========================================================================
    # STEP 5: Migrate data from finance_operating_cost_plans
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.finance_data (
            id, version_id, data_type, account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            id, version_id, 'operating_cost'::efir_budget.finance_data_type,
            account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_operating_cost_plans
        ON CONFLICT (id) DO NOTHING;
    """)

    # ========================================================================
    # STEP 6: Migrate data from finance_personnel_cost_plans
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.finance_data (
            id, version_id, data_type, account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes,
            category_id, cycle_id, fte_count, unit_cost_sar,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            id, version_id, 'personnel_cost'::efir_budget.finance_data_type,
            account_code, description,
            COALESCE(
                (SELECT name_en FROM efir_budget.ref_teacher_categories WHERE id = category_id),
                'Uncategorized'
            ) as category,
            total_cost_sar, is_calculated, calculation_driver, notes,
            category_id, cycle_id, fte_count, unit_cost_sar,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_personnel_cost_plans
        ON CONFLICT (id) DO NOTHING;
    """)

    # ========================================================================
    # STEP 7: Migrate data from finance_capex_plans
    # ========================================================================
    op.execute("""
        INSERT INTO efir_budget.finance_data (
            id, version_id, data_type, account_code, description, category,
            amount_sar, is_calculated, notes,
            quantity, unit_cost_sar, acquisition_date, useful_life_years,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        )
        SELECT
            id, version_id, 'capex'::efir_budget.finance_data_type,
            account_code, description, category,
            total_cost_sar, FALSE, notes,
            quantity, unit_cost_sar, acquisition_date, useful_life_years,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_capex_plans
        ON CONFLICT (id) DO NOTHING;
    """)

    # ========================================================================
    # STEP 8: Create backward-compatible views
    # ========================================================================
    op.execute("""
        -- Revenue view
        CREATE OR REPLACE VIEW efir_budget.vw_finance_revenue AS
        SELECT
            id, version_id, account_code, description, category,
            amount_sar, is_calculated, calculation_driver, trimester, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_data
        WHERE data_type = 'revenue' AND deleted_at IS NULL;

        COMMENT ON VIEW efir_budget.vw_finance_revenue IS
            'Backward-compatible view for finance_revenue_plans (Phase 4C)';

        -- Operating costs view
        CREATE OR REPLACE VIEW efir_budget.vw_finance_operating_costs AS
        SELECT
            id, version_id, account_code, description, category,
            amount_sar, is_calculated, calculation_driver, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_data
        WHERE data_type = 'operating_cost' AND deleted_at IS NULL;

        COMMENT ON VIEW efir_budget.vw_finance_operating_costs IS
            'Backward-compatible view for finance_operating_cost_plans (Phase 4C)';

        -- Personnel costs view
        CREATE OR REPLACE VIEW efir_budget.vw_finance_personnel_costs AS
        SELECT
            id, version_id, account_code, description,
            category_id, cycle_id, fte_count, unit_cost_sar,
            amount_sar as total_cost_sar, is_calculated, calculation_driver, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_data
        WHERE data_type = 'personnel_cost' AND deleted_at IS NULL;

        COMMENT ON VIEW efir_budget.vw_finance_personnel_costs IS
            'Backward-compatible view for finance_personnel_cost_plans (Phase 4C)';

        -- CapEx view
        CREATE OR REPLACE VIEW efir_budget.vw_finance_capex AS
        SELECT
            id, version_id, account_code, description, category,
            quantity, unit_cost_sar, amount_sar as total_cost_sar,
            acquisition_date, useful_life_years, notes,
            created_at, updated_at, created_by_id, updated_by_id, deleted_at
        FROM efir_budget.finance_data
        WHERE data_type = 'capex' AND deleted_at IS NULL;

        COMMENT ON VIEW efir_budget.vw_finance_capex IS
            'Backward-compatible view for finance_capex_plans (Phase 4C)';
    """)

    # ========================================================================
    # STEP 9: Add lineage columns to OUTPUT tables
    # ========================================================================
    op.execute("""
        -- Add lineage columns to finance_consolidations
        ALTER TABLE efir_budget.finance_consolidations
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64);

        COMMENT ON COLUMN efir_budget.finance_consolidations.computed_at IS 'When this output was computed';
        COMMENT ON COLUMN efir_budget.finance_consolidations.computed_by IS 'User who triggered computation';
        COMMENT ON COLUMN efir_budget.finance_consolidations.run_id IS 'Unique computation run ID';
        COMMENT ON COLUMN efir_budget.finance_consolidations.inputs_hash IS 'SHA-256 hash of inputs';
    """)

    op.execute("""
        -- Add lineage columns to finance_statements
        ALTER TABLE efir_budget.finance_statements
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64);

        COMMENT ON COLUMN efir_budget.finance_statements.computed_at IS 'When this output was computed';
        COMMENT ON COLUMN efir_budget.finance_statements.computed_by IS 'User who triggered computation';
        COMMENT ON COLUMN efir_budget.finance_statements.run_id IS 'Unique computation run ID';
        COMMENT ON COLUMN efir_budget.finance_statements.inputs_hash IS 'SHA-256 hash of inputs';
    """)

    op.execute("""
        -- Add lineage columns to finance_statement_lines
        ALTER TABLE efir_budget.finance_statement_lines
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64);

        COMMENT ON COLUMN efir_budget.finance_statement_lines.computed_at IS 'When this output was computed';
        COMMENT ON COLUMN efir_budget.finance_statement_lines.computed_by IS 'User who triggered computation';
        COMMENT ON COLUMN efir_budget.finance_statement_lines.run_id IS 'Unique computation run ID';
        COMMENT ON COLUMN efir_budget.finance_statement_lines.inputs_hash IS 'SHA-256 hash of inputs';
    """)

    # ========================================================================
    # STEP 10: Mark old tables as deprecated (comments only, not dropped)
    # ========================================================================
    op.execute("""
        COMMENT ON TABLE efir_budget.finance_revenue_plans IS
            'DEPRECATED (Phase 4C): Use efir_budget.finance_data WHERE data_type=''revenue'' or vw_finance_revenue';
        COMMENT ON TABLE efir_budget.finance_operating_cost_plans IS
            'DEPRECATED (Phase 4C): Use efir_budget.finance_data WHERE data_type=''operating_cost'' or vw_finance_operating_costs';
        COMMENT ON TABLE efir_budget.finance_personnel_cost_plans IS
            'DEPRECATED (Phase 4C): Use efir_budget.finance_data WHERE data_type=''personnel_cost'' or vw_finance_personnel_costs';
        COMMENT ON TABLE efir_budget.finance_capex_plans IS
            'DEPRECATED (Phase 4C): Use efir_budget.finance_data WHERE data_type=''capex'' or vw_finance_capex';
    """)

    # ========================================================================
    # STEP 11: Enable RLS on finance_data
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.finance_data ENABLE ROW LEVEL SECURITY;

        -- RLS policy: Users can access data for versions they have access to
        DROP POLICY IF EXISTS finance_data_org_isolation ON efir_budget.finance_data;
        CREATE POLICY finance_data_org_isolation ON efir_budget.finance_data
            FOR ALL
            USING (
                version_id IN (
                    SELECT v.id FROM efir_budget.settings_versions v
                    WHERE v.organization_id IN (
                        SELECT uo.organization_id FROM efir_budget.user_organizations uo
                        WHERE uo.user_id = auth.uid()
                    )
                )
            );
    """)


def downgrade() -> None:
    """Reverse financial consolidation - remove finance_data and views."""

    # Drop RLS policy
    op.execute("""
        DROP POLICY IF EXISTS finance_data_org_isolation ON efir_budget.finance_data;
    """)

    # Drop views
    op.execute("""
        DROP VIEW IF EXISTS efir_budget.vw_finance_capex;
        DROP VIEW IF EXISTS efir_budget.vw_finance_personnel_costs;
        DROP VIEW IF EXISTS efir_budget.vw_finance_operating_costs;
        DROP VIEW IF EXISTS efir_budget.vw_finance_revenue;
    """)

    # Remove lineage columns from OUTPUT tables
    op.execute("""
        ALTER TABLE efir_budget.finance_statement_lines
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash;
    """)

    op.execute("""
        ALTER TABLE efir_budget.finance_statements
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash;
    """)

    op.execute("""
        ALTER TABLE efir_budget.finance_consolidations
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash;
    """)

    # Drop unified table
    op.execute("DROP TABLE IF EXISTS efir_budget.finance_data;")

    # Drop ENUM
    op.execute("DROP TYPE IF EXISTS efir_budget.finance_data_type;")

    # Remove deprecation comments from old tables
    op.execute("""
        COMMENT ON TABLE efir_budget.finance_revenue_plans IS 'Revenue planning data';
        COMMENT ON TABLE efir_budget.finance_operating_cost_plans IS 'Operating cost planning data';
        COMMENT ON TABLE efir_budget.finance_personnel_cost_plans IS 'Personnel cost planning data';
        COMMENT ON TABLE efir_budget.finance_capex_plans IS 'Capital expenditure planning data';
    """)
