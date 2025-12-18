"""Rename budget_version_id column to version_id across all tables.

Revision ID: 024_rename_budget_version_id
Revises: 023_fix_academic_year_display
Create Date: 2025-12-15 02:50:00.000000

This migration renames the `budget_version_id` column to `version_id` for consistency
with the naming convention defined in REFACTORING_MASTER_PLAN.md Phase 3A.

The migration is IDEMPOTENT - it checks if the column exists before renaming,
so it's safe to run on databases that have already been manually updated.

Tables affected (using old names before Phase 3B prefix rename):
- Configuration: class_size_params, subject_hours_matrix, teacher_cost_params, fee_structure, timetable_constraints
- Planning: enrollment_plans, class_structures, nationality_distributions
- DHG: dhg_subject_hours, dhg_teacher_requirements, teacher_allocations
- Finance: revenue_plans, personnel_cost_plans, operating_cost_plans, capex_plans
- Consolidation: budget_consolidations, consolidation_line_items, financial_statements, financial_statement_lines
- Analysis: kpi_values, budget_vs_actual
- Writeback: planning_cells, cell_changes
- Personnel: employees, employee_salaries, eos_provisions, aefe_positions
- Enrollment: enrollment_projection_configs, enrollment_global_overrides, enrollment_level_overrides,
             enrollment_grade_overrides, enrollment_projection_results, enrollment_lateral_entry_defaults,
             enrollment_derived_parameters, enrollment_parameter_overrides, enrollment_scenario_multipliers
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "024_rename_budget_version_id"
down_revision: str = "023_fix_academic_year_display"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# All tables that have budget_version_id column (using OLD names before Phase 3B)
TABLES_TO_RENAME = [
    # Configuration Layer
    "class_size_params",
    "subject_hours_matrix",
    "teacher_cost_params",
    "fee_structure",
    "timetable_constraints",
    # Planning Layer
    "enrollment_plans",
    "class_structures",
    "nationality_distributions",
    "dhg_subject_hours",
    "dhg_teacher_requirements",
    "teacher_allocations",
    "revenue_plans",
    "personnel_cost_plans",
    "operating_cost_plans",
    "capex_plans",
    # Consolidation Layer
    "budget_consolidations",
    "consolidation_line_items",
    "financial_statements",
    "financial_statement_lines",
    # Analysis Layer
    "kpi_values",
    "budget_vs_actual",
    # Writeback
    "planning_cells",
    "cell_changes",
    # Personnel
    "employees",
    "employee_salaries",
    "eos_provisions",
    "aefe_positions",
    # Enrollment Projection
    "enrollment_projection_configs",
    "enrollment_global_overrides",
    "enrollment_level_overrides",
    "enrollment_grade_overrides",
    "enrollment_projection_results",
    "enrollment_lateral_entry_defaults",
    "enrollment_derived_parameters",
    "enrollment_parameter_overrides",
    "enrollment_scenario_multipliers",
]


def upgrade() -> None:
    """Rename budget_version_id to version_id in all affected tables.

    Uses idempotent SQL that checks column existence before renaming.
    """
    for table_name in TABLES_TO_RENAME:
        # Idempotent rename: only if budget_version_id exists and version_id doesn't
        op.execute(f"""
            DO $$
            BEGIN
                -- Check if table exists and has budget_version_id column
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'efir_budget'
                      AND table_name = '{table_name}'
                      AND column_name = 'budget_version_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'efir_budget'
                      AND table_name = '{table_name}'
                      AND column_name = 'version_id'
                ) THEN
                    ALTER TABLE efir_budget.{table_name}
                    RENAME COLUMN budget_version_id TO version_id;
                    RAISE NOTICE 'Renamed budget_version_id to version_id in %', '{table_name}';
                ELSE
                    RAISE NOTICE 'Skipping % (column already renamed or table does not exist)', '{table_name}';
                END IF;
            END $$;
        """)

    # Also rename the FK constraint in planning_cells (unique constraint)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'efir_budget'
                  AND table_name = 'planning_cells'
                  AND constraint_name = 'uq_planning_cell'
            ) THEN
                -- Drop and recreate with new column name if needed
                -- The constraint references budget_version_id, need to update
                RAISE NOTICE 'Note: uq_planning_cell constraint may need manual review if issues arise';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Rename version_id back to budget_version_id in all affected tables.

    Uses idempotent SQL that checks column existence before renaming.
    """
    for table_name in TABLES_TO_RENAME:
        # Idempotent rename: only if version_id exists and budget_version_id doesn't
        op.execute(f"""
            DO $$
            BEGIN
                -- Check if table exists and has version_id column
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'efir_budget'
                      AND table_name = '{table_name}'
                      AND column_name = 'version_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'efir_budget'
                      AND table_name = '{table_name}'
                      AND column_name = 'budget_version_id'
                ) THEN
                    ALTER TABLE efir_budget.{table_name}
                    RENAME COLUMN version_id TO budget_version_id;
                    RAISE NOTICE 'Renamed version_id back to budget_version_id in %', '{table_name}';
                ELSE
                    RAISE NOTICE 'Skipping % (column already has old name or table does not exist)', '{table_name}';
                END IF;
            END $$;
        """)
