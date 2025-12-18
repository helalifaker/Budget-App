"""Phase 3B: Table prefixes and scenario_type enum

Revision ID: 025_phase_3b_table_prefixes
Revises: 024_rename_budget_version_id
Create Date: 2025-12-15 04:00:00.000000

Implements DB_golden_rules.md Section 9.2 table prefix convention:
- ref_*      : Reference/static lookup tables
- settings_* : Configuration and versioning tables
- students_* : Enrollment and class structure tables
- teachers_* : Personnel and DHG tables
- finance_*  : Revenue, costs, financial statements
- insights_* : KPIs, dashboards, variance analysis
- admin_*    : Organizations, audit, system admin

Also adds scenario_type enum to settings_versions table.

CRITICAL: This migration renames 61 tables. Ensure backups before running.
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "025_phase_3b_table_prefixes"
down_revision: str | None = "024_rename_budget_version_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ============================================================================
# TABLE RENAME MAPPING
# ============================================================================
# Format: (old_name, new_name)

REFERENCE_TABLES = [
    ("academic_cycles", "ref_academic_cycles"),
    ("academic_levels", "ref_academic_levels"),
    ("subjects", "ref_subjects"),
    ("teacher_categories", "ref_teacher_categories"),
    ("fee_categories", "ref_fee_categories"),
    ("nationality_types", "ref_nationality_types"),
    ("kpi_definitions", "ref_kpi_definitions"),
    ("enrollment_scenarios", "ref_enrollment_scenarios"),
]

SETTINGS_TABLES = [
    ("budget_versions", "settings_versions"),
    ("system_configs", "settings_system_configs"),
    ("class_size_params", "settings_class_size_params"),
    ("subject_hours_matrix", "settings_subject_hours_matrix"),
    ("teacher_cost_params", "settings_teacher_cost_params"),
    ("fee_structure", "settings_fee_structure"),
    ("timetable_constraints", "settings_timetable_constraints"),
    ("integration_settings", "settings_integration"),
    ("strategic_plans", "settings_strategic_plans"),
    ("strategic_plan_scenarios", "settings_strategic_scenarios"),
    ("strategic_plan_projections", "settings_strategic_projections"),
    ("strategic_initiatives", "settings_strategic_initiatives"),
]

STUDENTS_TABLES = [
    ("enrollment_plans", "students_enrollment_plans"),
    ("enrollment_projections", "students_enrollment_projections"),
    ("enrollment_projection_configs", "students_projection_configs"),
    ("enrollment_global_overrides", "students_global_overrides"),
    ("enrollment_level_overrides", "students_level_overrides"),
    ("enrollment_grade_overrides", "students_grade_overrides"),
    ("enrollment_lateral_entry_defaults", "students_lateral_entry_defaults"),
    ("enrollment_scenario_multipliers", "students_scenario_multipliers"),
    ("enrollment_derived_parameters", "students_derived_parameters"),
    ("enrollment_parameter_overrides", "students_parameter_overrides"),
    ("class_structures", "students_class_structures"),
    ("nationality_distributions", "students_nationality_distributions"),
    ("enrollment_calibration_overrides", "students_calibration_overrides"),
]

TEACHERS_TABLES = [
    ("employees", "teachers_employees"),
    ("employee_salaries", "teachers_employee_salaries"),
    ("aefe_positions", "teachers_aefe_positions"),
    ("eos_provisions", "teachers_eos_provisions"),
    ("dhg_subject_hours", "teachers_dhg_subject_hours"),
    ("dhg_teacher_requirements", "teachers_dhg_requirements"),
    ("teacher_allocations", "teachers_allocations"),
]

FINANCE_TABLES = [
    ("revenue_plans", "finance_revenue_plans"),
    ("personnel_cost_plans", "finance_personnel_cost_plans"),
    ("operating_cost_plans", "finance_operating_cost_plans"),
    ("capex_plans", "finance_capex_plans"),
    ("budget_consolidations", "finance_consolidations"),
    ("financial_statements", "finance_statements"),
    ("financial_statement_lines", "finance_statement_lines"),
]

INSIGHTS_TABLES = [
    ("kpi_values", "insights_kpi_values"),
    ("dashboard_configs", "insights_dashboard_configs"),
    ("dashboard_widgets", "insights_dashboard_widgets"),
    ("user_preferences", "insights_user_preferences"),
    ("actual_data", "insights_actual_data"),
    ("budget_vs_actual", "insights_budget_vs_actual"),
    ("variance_explanations", "insights_variance_explanations"),
    ("historical_actuals", "insights_historical_actuals"),
]

ADMIN_TABLES = [
    ("organizations", "admin_organizations"),
    ("integration_logs", "admin_integration_logs"),
    ("planning_cells", "admin_planning_cells"),
    ("cell_changes", "admin_cell_changes"),
    ("cell_comments", "admin_cell_comments"),
    ("historical_comparison_runs", "admin_historical_comparison_runs"),
]

# Combine all renames
ALL_RENAMES = (
    REFERENCE_TABLES
    + SETTINGS_TABLES
    + STUDENTS_TABLES
    + TEACHERS_TABLES
    + FINANCE_TABLES
    + INSIGHTS_TABLES
    + ADMIN_TABLES
)


def upgrade() -> None:
    """Apply table prefix convention and add scenario_type enum."""

    # ========================================================================
    # STEP 1: Create scenario_type enum
    # ========================================================================
    op.execute("""
        CREATE TYPE efir_budget.scenario_type AS ENUM (
            'ACTUAL',      -- Historical actuals (locked, immutable)
            'BUDGET',      -- Official approved budget
            'FORECAST',    -- Mid-year forecast revisions
            'STRATEGIC',   -- 5-year strategic planning
            'WHAT_IF'      -- Scenario analysis (sandboxed)
        );
    """)

    # ========================================================================
    # STEP 2: Rename all tables (PostgreSQL auto-updates FK references)
    # ========================================================================
    for old_name, new_name in ALL_RENAMES:
        # Check if table exists before renaming (some tables may not exist in all environments)
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'efir_budget' AND table_name = '{old_name}'
                ) THEN
                    ALTER TABLE efir_budget.{old_name} RENAME TO {new_name};
                END IF;
            END $$;
        """)

    # ========================================================================
    # STEP 3: Add scenario_type column to settings_versions
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        ADD COLUMN IF NOT EXISTS scenario_type efir_budget.scenario_type
        NOT NULL DEFAULT 'BUDGET';
    """)

    # ========================================================================
    # STEP 4: Update FK constraint names to reflect new table names
    # ========================================================================
    # Note: PostgreSQL doesn't auto-rename FK constraints, so we need to do it manually
    # This is a subset of the most important constraints

    fk_renames = [
        # settings_versions FKs (formerly budget_versions)
        ("enrollment_projection_configs_version_id_fkey", "students_projection_configs_version_id_fkey", "students_projection_configs"),
        ("class_structures_version_id_fkey", "students_class_structures_version_id_fkey", "students_class_structures"),
        ("enrollment_plans_version_id_fkey", "students_enrollment_plans_version_id_fkey", "students_enrollment_plans"),
        ("dhg_subject_hours_version_id_fkey", "teachers_dhg_subject_hours_version_id_fkey", "teachers_dhg_subject_hours"),
        ("dhg_teacher_requirements_version_id_fkey", "teachers_dhg_requirements_version_id_fkey", "teachers_dhg_requirements"),
        ("employees_version_id_fkey", "teachers_employees_version_id_fkey", "teachers_employees"),
        ("revenue_plans_version_id_fkey", "finance_revenue_plans_version_id_fkey", "finance_revenue_plans"),
        ("personnel_cost_plans_version_id_fkey", "finance_personnel_cost_plans_version_id_fkey", "finance_personnel_cost_plans"),
        ("operating_cost_plans_version_id_fkey", "finance_operating_cost_plans_version_id_fkey", "finance_operating_cost_plans"),
        ("capex_plans_version_id_fkey", "finance_capex_plans_version_id_fkey", "finance_capex_plans"),
        ("budget_consolidations_version_id_fkey", "finance_consolidations_version_id_fkey", "finance_consolidations"),
        ("financial_statements_version_id_fkey", "finance_statements_version_id_fkey", "finance_statements"),
        ("kpi_values_version_id_fkey", "insights_kpi_values_version_id_fkey", "insights_kpi_values"),
        ("budget_vs_actual_version_id_fkey", "insights_budget_vs_actual_version_id_fkey", "insights_budget_vs_actual"),
    ]

    for old_fk, new_fk, table in fk_renames:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = '{old_fk}'
                    AND table_schema = 'efir_budget'
                ) THEN
                    ALTER TABLE efir_budget.{table}
                    RENAME CONSTRAINT {old_fk} TO {new_fk};
                END IF;
            END $$;
        """)

    # ========================================================================
    # STEP 5: Update RLS policies if they exist
    # ========================================================================
    # RLS policies that reference old table names need to be recreated
    # This is handled by dropping and recreating policies with new names

    # Example: settings_versions RLS (formerly budget_versions)
    op.execute("""
        DO $$
        BEGIN
            -- Drop old policies if they exist
            DROP POLICY IF EXISTS budget_versions_org_isolation ON efir_budget.settings_versions;

            -- Create new policy with correct name
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'settings_versions'
                AND policyname = 'settings_versions_org_isolation'
            ) THEN
                CREATE POLICY settings_versions_org_isolation ON efir_budget.settings_versions
                FOR ALL
                USING (
                    organization_id IN (
                        SELECT organization_id FROM efir_budget.admin_organizations
                        WHERE id = organization_id
                    )
                );
            END IF;
        EXCEPTION
            WHEN undefined_table THEN
                NULL; -- Table doesn't exist, skip
        END $$;
    """)

    # ========================================================================
    # STEP 6: Update materialized view references if needed
    # ========================================================================
    # Materialized views may reference old table names - recreate if necessary
    # NOTE: Each SQL statement must be in its own op.execute() due to asyncpg limitation

    # Drop existing materialized view
    op.execute("""
        DROP MATERIALIZED VIEW IF EXISTS efir_budget.kpi_dashboard_summary CASCADE
    """)

    # Create materialized view with new table names
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS efir_budget.kpi_dashboard_summary AS
        SELECT
            v.id as version_id,
            v.name as version_name,
            v.fiscal_year,
            v.status as version_status,
            v.scenario_type,
            COUNT(DISTINCT kv.id) as kpi_count,
            COUNT(DISTINCT CASE WHEN kd.category = 'educational' THEN kv.id END) as educational_kpis,
            COUNT(DISTINCT CASE WHEN kd.category = 'financial' THEN kv.id END) as financial_kpis
        FROM efir_budget.settings_versions v
        LEFT JOIN efir_budget.insights_kpi_values kv ON kv.version_id = v.id AND kv.deleted_at IS NULL
        LEFT JOIN efir_budget.ref_kpi_definitions kd ON kd.id = kv.kpi_definition_id
        WHERE v.deleted_at IS NULL
        GROUP BY v.id, v.name, v.fiscal_year, v.status, v.scenario_type
    """)

    # Create index on the materialized view
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_kpi_dashboard_summary_version
        ON efir_budget.kpi_dashboard_summary(version_id)
    """)


def downgrade() -> None:
    """Revert table prefix convention and remove scenario_type enum."""

    # ========================================================================
    # STEP 1: Reverse all table renames
    # ========================================================================
    for old_name, new_name in reversed(ALL_RENAMES):
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'efir_budget' AND table_name = '{new_name}'
                ) THEN
                    ALTER TABLE efir_budget.{new_name} RENAME TO {old_name};
                END IF;
            END $$;
        """)

    # ========================================================================
    # STEP 2: Remove scenario_type column from budget_versions
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.budget_versions
        DROP COLUMN IF EXISTS scenario_type;
    """)

    # ========================================================================
    # STEP 3: Drop scenario_type enum
    # ========================================================================
    op.execute("""
        DROP TYPE IF EXISTS efir_budget.scenario_type;
    """)

    # ========================================================================
    # STEP 4: Recreate materialized views with old table names
    # ========================================================================
    # NOTE: Each SQL statement must be in its own op.execute() due to asyncpg limitation

    op.execute("""
        DROP MATERIALIZED VIEW IF EXISTS efir_budget.kpi_dashboard_summary CASCADE
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS efir_budget.kpi_dashboard_summary AS
        SELECT
            v.id as version_id,
            v.name as version_name,
            v.fiscal_year,
            v.status as version_status,
            COUNT(DISTINCT kv.id) as kpi_count,
            COUNT(DISTINCT CASE WHEN kd.category = 'educational' THEN kv.id END) as educational_kpis,
            COUNT(DISTINCT CASE WHEN kd.category = 'financial' THEN kv.id END) as financial_kpis
        FROM efir_budget.budget_versions v
        LEFT JOIN efir_budget.kpi_values kv ON kv.version_id = v.id AND kv.deleted_at IS NULL
        LEFT JOIN efir_budget.kpi_definitions kd ON kd.id = kv.kpi_definition_id
        WHERE v.deleted_at IS NULL
        GROUP BY v.id, v.name, v.fiscal_year, v.status
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_kpi_dashboard_summary_version
        ON efir_budget.kpi_dashboard_summary(version_id)
    """)
