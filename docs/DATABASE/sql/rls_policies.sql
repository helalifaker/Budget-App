-- ==============================================================================
-- Row Level Security (RLS) Policies for EFIR Budget Planning Application
-- ==============================================================================
--
-- This script sets up Row Level Security policies for the efir_budget schema.
-- Must be run AFTER the initial migration and AFTER Supabase Auth is configured.
--
-- User Roles (stored in auth.users.raw_user_meta_data->>'role'):
--   - 'admin': Full access to all data
--   - 'manager': Read/write working versions, read-only approved versions
--   - 'viewer': Read-only access to approved versions only
--
-- Policy Pattern:
--   1. Enable RLS on all tables
--   2. Admin gets full access (including soft-deleted records)
--   3. Manager gets conditional access based on version status (non-deleted only)
--   4. Viewer gets read-only access to approved versions (non-deleted only)
--
-- Soft Delete Filtering:
--   All policies (except admin) include: deleted_at IS NULL
--   Admin can see soft-deleted records for audit purposes
--
-- ==============================================================================

-- Enable RLS on all Configuration Layer tables
ALTER TABLE efir_budget.system_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.budget_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.academic_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.academic_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.class_size_params ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.subject_hours_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.teacher_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.teacher_cost_params ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.fee_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.nationality_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.fee_structure ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.timetable_constraints ENABLE ROW LEVEL SECURITY;

-- Enable RLS on all Planning Layer tables
ALTER TABLE efir_budget.enrollment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.class_structures ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.dhg_subject_hours ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.dhg_teacher_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.teacher_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.revenue_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.personnel_cost_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.operating_cost_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.capex_plans ENABLE ROW LEVEL SECURITY;

-- Enable RLS on all Consolidation Layer tables
ALTER TABLE efir_budget.budget_consolidations ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.financial_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.financial_statement_lines ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- Helper Function: Check User Role
-- ==============================================================================

CREATE OR REPLACE FUNCTION efir_budget.current_user_role()
RETURNS TEXT AS $$
BEGIN
  RETURN COALESCE(
    (SELECT raw_user_meta_data->>'role'
     FROM auth.users
     WHERE id = auth.uid()),
    'viewer'  -- Default to viewer if no role set
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==============================================================================
-- Reference Data Tables (Read-Only for All Authenticated Users)
-- ==============================================================================
-- These tables contain master data that all users need to view but only
-- admins should modify.

-- academic_cycles: Read for all, write for admin only
CREATE POLICY "academic_cycles_select" ON efir_budget.academic_cycles
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "academic_cycles_admin_all" ON efir_budget.academic_cycles
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- academic_levels: Read for all, write for admin only
CREATE POLICY "academic_levels_select" ON efir_budget.academic_levels
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "academic_levels_admin_all" ON efir_budget.academic_levels
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- subjects: Read for all, write for admin only
CREATE POLICY "subjects_select" ON efir_budget.subjects
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "subjects_admin_all" ON efir_budget.subjects
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- teacher_categories: Read for all, write for admin only
CREATE POLICY "teacher_categories_select" ON efir_budget.teacher_categories
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "teacher_categories_admin_all" ON efir_budget.teacher_categories
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- fee_categories: Read for all, write for admin only
CREATE POLICY "fee_categories_select" ON efir_budget.fee_categories
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "fee_categories_admin_all" ON efir_budget.fee_categories
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- nationality_types: Read for all, write for admin only
CREATE POLICY "nationality_types_select" ON efir_budget.nationality_types
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "nationality_types_admin_all" ON efir_budget.nationality_types
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- ==============================================================================
-- System Configuration (Admin Only)
-- ==============================================================================

CREATE POLICY "system_configs_admin_all" ON efir_budget.system_configs
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Managers and viewers can read system configs
CREATE POLICY "system_configs_read" ON efir_budget.system_configs
  FOR SELECT
  TO authenticated
  USING (efir_budget.current_user_role() IN ('admin', 'manager', 'viewer'));

-- ==============================================================================
-- Budget Versions (Core Access Control)
-- ==============================================================================
-- This is the most critical table as it controls access to all versioned data.

-- Admin: Full access to all versions
CREATE POLICY "budget_versions_admin_all" ON efir_budget.budget_versions
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Can create new working versions
CREATE POLICY "budget_versions_manager_insert" ON efir_budget.budget_versions
  FOR INSERT
  TO authenticated
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND status = 'working'
  );

-- Manager: Can update/delete working versions
CREATE POLICY "budget_versions_manager_working" ON efir_budget.budget_versions
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND status = 'working'
    AND deleted_at IS NULL
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND status = 'working'
    AND deleted_at IS NULL
  );

-- Manager: Can read all non-deleted versions (for comparison)
CREATE POLICY "budget_versions_read_all" ON efir_budget.budget_versions
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
  );

-- Viewer: Read-only access to approved versions
CREATE POLICY "budget_versions_viewer_select" ON efir_budget.budget_versions
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'viewer'
    AND status = 'approved'
    AND deleted_at IS NULL
  );

-- ==============================================================================
-- Versioned Data Tables (Inherit Access from budget_versions)
-- ==============================================================================
-- All tables with budget_version_id inherit permissions from the parent version.

-- class_size_params
CREATE POLICY "class_size_params_admin_all" ON efir_budget.class_size_params
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "class_size_params_manager_working" ON efir_budget.class_size_params
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  );

CREATE POLICY "class_size_params_select" ON efir_budget.class_size_params
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.budget_versions bv
        WHERE bv.id = budget_version_id
        AND bv.status = 'approved'
      )
    )
  );

-- subject_hours_matrix
CREATE POLICY "subject_hours_matrix_admin_all" ON efir_budget.subject_hours_matrix
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "subject_hours_matrix_manager_working" ON efir_budget.subject_hours_matrix
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  );

CREATE POLICY "subject_hours_matrix_select" ON efir_budget.subject_hours_matrix
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.budget_versions bv
        WHERE bv.id = budget_version_id
        AND bv.status = 'approved'
      )
    )
  );

-- teacher_cost_params
CREATE POLICY "teacher_cost_params_admin_all" ON efir_budget.teacher_cost_params
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "teacher_cost_params_manager_working" ON efir_budget.teacher_cost_params
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  );

CREATE POLICY "teacher_cost_params_select" ON efir_budget.teacher_cost_params
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.budget_versions bv
        WHERE bv.id = budget_version_id
        AND bv.status = 'approved'
      )
    )
  );

-- fee_structure
CREATE POLICY "fee_structure_admin_all" ON efir_budget.fee_structure
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "fee_structure_manager_working" ON efir_budget.fee_structure
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  );

CREATE POLICY "fee_structure_select" ON efir_budget.fee_structure
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.budget_versions bv
        WHERE bv.id = budget_version_id
        AND bv.status = 'approved'
      )
    )
  );

-- timetable_constraints
CREATE POLICY "timetable_constraints_admin_all" ON efir_budget.timetable_constraints
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "timetable_constraints_manager_working" ON efir_budget.timetable_constraints
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
    )
  );

CREATE POLICY "timetable_constraints_select" ON efir_budget.timetable_constraints
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.budget_versions bv
        WHERE bv.id = budget_version_id
        AND bv.status = 'approved'
      )
    )
  );

-- ==============================================================================
-- Planning Layer Tables (Modules 7-12)
-- ==============================================================================
-- All Planning Layer tables follow the same pattern as Configuration Layer:
-- - Admin: Full access
-- - Manager: Read/write working versions, read-only others
-- - Viewer: Read-only approved versions

-- MACRO: Apply standard versioned data policies to all Planning Layer tables
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT unnest(ARRAY[
            'enrollment_plans',
            'class_structures',
            'dhg_subject_hours',
            'dhg_teacher_requirements',
            'teacher_allocations',
            'revenue_plans',
            'personnel_cost_plans',
            'operating_cost_plans',
            'capex_plans'
        ])
    LOOP
        -- Admin: Full access
        EXECUTE format('
            CREATE POLICY "%s_admin_all" ON efir_budget.%s
              FOR ALL
              TO authenticated
              USING (efir_budget.current_user_role() = ''admin'')
              WITH CHECK (efir_budget.current_user_role() = ''admin'')
        ', tbl, tbl);

        -- Manager: Read/write working versions (non-deleted only)
        EXECUTE format('
            CREATE POLICY "%s_manager_working" ON efir_budget.%s
              FOR ALL
              TO authenticated
              USING (
                efir_budget.current_user_role() = ''manager''
                AND deleted_at IS NULL
                AND EXISTS (
                  SELECT 1 FROM efir_budget.budget_versions bv
                  WHERE bv.id = budget_version_id
                  AND bv.status = ''working''
                  AND bv.deleted_at IS NULL
                )
              )
              WITH CHECK (
                efir_budget.current_user_role() = ''manager''
                AND deleted_at IS NULL
                AND EXISTS (
                  SELECT 1 FROM efir_budget.budget_versions bv
                  WHERE bv.id = budget_version_id
                  AND bv.status = ''working''
                  AND bv.deleted_at IS NULL
                )
              )
        ', tbl, tbl);

        -- All authenticated: Read access with version constraints (non-deleted only)
        EXECUTE format('
            CREATE POLICY "%s_select" ON efir_budget.%s
              FOR SELECT
              TO authenticated
              USING (
                deleted_at IS NULL
                AND (
                  efir_budget.current_user_role() IN (''admin'', ''manager'')
                  OR (
                    efir_budget.current_user_role() = ''viewer''
                    AND EXISTS (
                      SELECT 1 FROM efir_budget.budget_versions bv
                      WHERE bv.id = budget_version_id
                      AND bv.status = ''approved''
                      AND bv.deleted_at IS NULL
                    )
                  )
                )
              )
        ', tbl, tbl);
    END LOOP;
END $$;

-- ==============================================================================
-- Consolidation Layer Tables (Modules 13-14)
-- ==============================================================================
-- All Consolidation Layer tables follow the same pattern as Planning Layer:
-- - Admin: Full access
-- - Manager: Read/write working versions, read-only others
-- - Viewer: Read-only approved versions

-- MACRO: Apply standard versioned data policies to all Consolidation Layer tables
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT unnest(ARRAY[
            'budget_consolidations',
            'financial_statements'
        ])
    LOOP
        -- Admin: Full access
        EXECUTE format('
            CREATE POLICY "%s_admin_all" ON efir_budget.%s
              FOR ALL
              TO authenticated
              USING (efir_budget.current_user_role() = ''admin'')
              WITH CHECK (efir_budget.current_user_role() = ''admin'')
        ', tbl, tbl);

        -- Manager: Read/write working versions (non-deleted only)
        EXECUTE format('
            CREATE POLICY "%s_manager_working" ON efir_budget.%s
              FOR ALL
              TO authenticated
              USING (
                efir_budget.current_user_role() = ''manager''
                AND deleted_at IS NULL
                AND EXISTS (
                  SELECT 1 FROM efir_budget.budget_versions bv
                  WHERE bv.id = budget_version_id
                  AND bv.status = ''working''
                  AND bv.deleted_at IS NULL
                )
              )
              WITH CHECK (
                efir_budget.current_user_role() = ''manager''
                AND deleted_at IS NULL
                AND EXISTS (
                  SELECT 1 FROM efir_budget.budget_versions bv
                  WHERE bv.id = budget_version_id
                  AND bv.status = ''working''
                  AND bv.deleted_at IS NULL
                )
              )
        ', tbl, tbl);

        -- All authenticated: Read access with version constraints (non-deleted only)
        EXECUTE format('
            CREATE POLICY "%s_select" ON efir_budget.%s
              FOR SELECT
              TO authenticated
              USING (
                deleted_at IS NULL
                AND (
                  efir_budget.current_user_role() IN (''admin'', ''manager'')
                  OR (
                    efir_budget.current_user_role() = ''viewer''
                    AND EXISTS (
                      SELECT 1 FROM efir_budget.budget_versions bv
                      WHERE bv.id = budget_version_id
                      AND bv.status = ''approved''
                      AND bv.deleted_at IS NULL
                    )
                  )
                )
              )
        ', tbl, tbl);
    END LOOP;
END $$;

-- Financial Statement Lines (child table - inherits access from parent)
-- Admin: Full access
CREATE POLICY "financial_statement_lines_admin_all" ON efir_budget.financial_statement_lines
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Read/write working versions (via parent statement, non-deleted only)
CREATE POLICY "financial_statement_lines_manager_working" ON efir_budget.financial_statement_lines
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.financial_statements fs
      JOIN efir_budget.budget_versions bv ON fs.budget_version_id = bv.id
      WHERE fs.id = statement_id
      AND bv.status = 'working'
      AND fs.deleted_at IS NULL
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.financial_statements fs
      JOIN efir_budget.budget_versions bv ON fs.budget_version_id = bv.id
      WHERE fs.id = statement_id
      AND bv.status = 'working'
      AND fs.deleted_at IS NULL
      AND bv.deleted_at IS NULL
    )
  );

-- All authenticated: Read access with version constraints (via parent statement, non-deleted only)
CREATE POLICY "financial_statement_lines_select" ON efir_budget.financial_statement_lines
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.financial_statements fs
          JOIN efir_budget.budget_versions bv ON fs.budget_version_id = bv.id
          WHERE fs.id = statement_id
          AND bv.status = 'approved'
          AND fs.deleted_at IS NULL
          AND bv.deleted_at IS NULL
        )
      )
    )
  );

-- ==============================================================================
-- Analysis Layer Tables (Modules 15-17)
-- ==============================================================================
-- Analysis Layer tables have mixed patterns:
-- - Reference data (kpi_definitions): Read for all, write for admin
-- - Versioned data (kpi_values, budget_vs_actual): Standard version-based access
-- - Ownership-based (dashboard_configs, user_preferences): Owner + admin access
-- - Public data (actual_data): Admin write, all read
-- - Child tables (dashboard_widgets, variance_explanations): Inherit from parent

-- Enable RLS on all Analysis Layer tables
ALTER TABLE efir_budget.kpi_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.kpi_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.dashboard_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.dashboard_widgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.actual_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.budget_vs_actual ENABLE ROW LEVEL SECURITY;
ALTER TABLE efir_budget.variance_explanations ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- kpi_definitions: Reference Data (Read for all, write for admin only)
-- ------------------------------------------------------------------------------

-- All authenticated users can read KPI definitions
CREATE POLICY "kpi_definitions_select" ON efir_budget.kpi_definitions
  FOR SELECT
  TO authenticated
  USING (deleted_at IS NULL);

-- Admin: Full access to KPI definitions
CREATE POLICY "kpi_definitions_admin_all" ON efir_budget.kpi_definitions
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- ------------------------------------------------------------------------------
-- kpi_values: Versioned Data (Standard version-based access pattern)
-- ------------------------------------------------------------------------------

-- Admin: Full access
CREATE POLICY "kpi_values_admin_all" ON efir_budget.kpi_values
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Read/write working versions (non-deleted only)
CREATE POLICY "kpi_values_manager_working" ON efir_budget.kpi_values
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  );

-- All authenticated: Read access with version constraints (non-deleted only)
CREATE POLICY "kpi_values_select" ON efir_budget.kpi_values
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.budget_versions bv
          WHERE bv.id = budget_version_id
          AND bv.status = 'approved'
          AND bv.deleted_at IS NULL
        )
      )
    )
  );

-- ------------------------------------------------------------------------------
-- dashboard_configs: Ownership-based access + system templates
-- ------------------------------------------------------------------------------
-- Dashboard configs can be:
--   1. System templates (dashboard_role IS NOT NULL, owner_user_id IS NULL)
--   2. User-created dashboards (owner_user_id IS NOT NULL)

-- Admin: Full access to all dashboards
CREATE POLICY "dashboard_configs_admin_all" ON efir_budget.dashboard_configs
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Owner: Full access to own dashboards (non-deleted only)
CREATE POLICY "dashboard_configs_owner_all" ON efir_budget.dashboard_configs
  FOR ALL
  TO authenticated
  USING (
    deleted_at IS NULL
    AND owner_user_id = auth.uid()
  )
  WITH CHECK (
    deleted_at IS NULL
    AND owner_user_id = auth.uid()
  );

-- All authenticated: Read system templates (public dashboards, non-deleted)
CREATE POLICY "dashboard_configs_template_select" ON efir_budget.dashboard_configs
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND dashboard_role IS NOT NULL
    AND owner_user_id IS NULL
  );

-- Manager: Can create system templates
CREATE POLICY "dashboard_configs_manager_templates" ON efir_budget.dashboard_configs
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND dashboard_role IS NOT NULL
    AND owner_user_id IS NULL
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND dashboard_role IS NOT NULL
    AND owner_user_id IS NULL
  );

-- ------------------------------------------------------------------------------
-- dashboard_widgets: Child table inheriting access from dashboard_configs
-- ------------------------------------------------------------------------------

-- Admin: Full access to all widgets
CREATE POLICY "dashboard_widgets_admin_all" ON efir_budget.dashboard_widgets
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Owner: Full access to widgets in owned dashboards (non-deleted only)
CREATE POLICY "dashboard_widgets_owner_via_dashboard" ON efir_budget.dashboard_widgets
  FOR ALL
  TO authenticated
      USING (
        deleted_at IS NULL
        AND EXISTS (
          SELECT 1 FROM efir_budget.dashboard_configs dc
          WHERE dc.id = dashboard_config_id
          AND dc.owner_user_id = auth.uid()
          AND dc.deleted_at IS NULL
        )
      )
      WITH CHECK (
        deleted_at IS NULL
        AND EXISTS (
          SELECT 1 FROM efir_budget.dashboard_configs dc
          WHERE dc.id = dashboard_config_id
          AND dc.owner_user_id = auth.uid()
          AND dc.deleted_at IS NULL
        )
      );

-- All authenticated: Read widgets from accessible dashboards (non-deleted only)
CREATE POLICY "dashboard_widgets_select_via_dashboard" ON efir_budget.dashboard_widgets
  FOR SELECT
  TO authenticated
  USING (
        deleted_at IS NULL
        AND EXISTS (
          SELECT 1 FROM efir_budget.dashboard_configs dc
          WHERE dc.id = dashboard_config_id
          AND dc.deleted_at IS NULL
          AND (
            dc.owner_user_id = auth.uid()  -- Own dashboard
            OR (dc.dashboard_role IS NOT NULL AND dc.owner_user_id IS NULL)  -- System template
            OR efir_budget.current_user_role() = 'admin'  -- Admin sees all
          )
        )
      );

-- Manager: Can modify system template widgets
CREATE POLICY "dashboard_widgets_manager_templates" ON efir_budget.dashboard_widgets
  FOR ALL
  TO authenticated
  USING (
        efir_budget.current_user_role() = 'manager'
        AND deleted_at IS NULL
        AND EXISTS (
          SELECT 1 FROM efir_budget.dashboard_configs dc
          WHERE dc.id = dashboard_config_id
          AND dc.dashboard_role IS NOT NULL
          AND dc.owner_user_id IS NULL
          AND dc.deleted_at IS NULL
        )
      )
      WITH CHECK (
        efir_budget.current_user_role() = 'manager'
        AND deleted_at IS NULL
        AND EXISTS (
          SELECT 1 FROM efir_budget.dashboard_configs dc
          WHERE dc.id = dashboard_config_id
          AND dc.dashboard_role IS NOT NULL
          AND dc.owner_user_id IS NULL
          AND dc.deleted_at IS NULL
        )
      );

-- ------------------------------------------------------------------------------
-- user_preferences: Self-only access (each user manages own preferences)
-- ------------------------------------------------------------------------------

-- Admin: Full access to all user preferences
CREATE POLICY "user_preferences_admin_all" ON efir_budget.user_preferences
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Self: Full access to own preferences (non-deleted only)
CREATE POLICY "user_preferences_self_all" ON efir_budget.user_preferences
  FOR ALL
  TO authenticated
  USING (
    deleted_at IS NULL
    AND user_id = auth.uid()
  )
  WITH CHECK (
    deleted_at IS NULL
    AND user_id = auth.uid()
  );

-- Self: Read own preferences
CREATE POLICY "user_preferences_select_self" ON efir_budget.user_preferences
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND user_id = auth.uid()
  );

-- ------------------------------------------------------------------------------
-- actual_data: Admin/Manager write, all authenticated read
-- ------------------------------------------------------------------------------
-- Actual data imported from Odoo or manually entered
-- All users need to read actuals for variance analysis

-- Admin: Full access
CREATE POLICY "actual_data_admin_all" ON efir_budget.actual_data
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Can insert and update actual data (non-deleted only)
CREATE POLICY "actual_data_manager_insert_update" ON efir_budget.actual_data
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
  );

-- All authenticated: Read access to actual data (non-deleted only)
CREATE POLICY "actual_data_select_all" ON efir_budget.actual_data
  FOR SELECT
  TO authenticated
  USING (deleted_at IS NULL);

-- ------------------------------------------------------------------------------
-- budget_vs_actual: Versioned Data (Standard version-based access pattern)
-- ------------------------------------------------------------------------------

-- Admin: Full access
CREATE POLICY "budget_vs_actual_admin_all" ON efir_budget.budget_vs_actual
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Read/write working versions (non-deleted only)
CREATE POLICY "budget_vs_actual_manager_working" ON efir_budget.budget_vs_actual
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  );

-- All authenticated: Read access with version constraints (non-deleted only)
CREATE POLICY "budget_vs_actual_select" ON efir_budget.budget_vs_actual
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.budget_versions bv
          WHERE bv.id = budget_version_id
          AND bv.status = 'approved'
          AND bv.deleted_at IS NULL
        )
      )
    )
  );

-- ------------------------------------------------------------------------------
-- variance_explanations: Child table inheriting access from budget_vs_actual
-- ------------------------------------------------------------------------------

-- Admin: Full access
CREATE POLICY "variance_explanations_admin_all" ON efir_budget.variance_explanations
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Read/write for working versions (via parent, non-deleted only)
CREATE POLICY "variance_explanations_manager_working" ON efir_budget.variance_explanations
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_vs_actual bva
      JOIN efir_budget.budget_versions bv ON bva.budget_version_id = bv.id
      WHERE bva.id = budget_vs_actual_id
      AND bv.status = 'working'
      AND bva.deleted_at IS NULL
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.budget_vs_actual bva
      JOIN efir_budget.budget_versions bv ON bva.budget_version_id = bv.id
      WHERE bva.id = budget_vs_actual_id
      AND bv.status = 'working'
      AND bva.deleted_at IS NULL
      AND bv.deleted_at IS NULL
    )
  );

-- All authenticated: Read access with version constraints (via parent, non-deleted only)
CREATE POLICY "variance_explanations_select" ON efir_budget.variance_explanations
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.budget_vs_actual bva
          JOIN efir_budget.budget_versions bv ON bva.budget_version_id = bv.id
          WHERE bva.id = budget_vs_actual_id
          AND bv.status = 'approved'
          AND bva.deleted_at IS NULL
          AND bv.deleted_at IS NULL
        )
      )
    )
  );

-- ==============================================================================
-- Verification Queries
-- ==============================================================================
-- Run these to verify RLS policies are working correctly

-- View all policies
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies
-- WHERE schemaname = 'efir_budget'
-- ORDER BY tablename, policyname;

-- Test access as different roles (requires test users)
-- SET ROLE test_admin;
-- SET ROLE test_manager;
-- SET ROLE test_viewer;

-- ##############################################################################
-- MODULE 18: STRATEGIC PLANNING LAYER - RLS POLICIES
-- ##############################################################################
-- Strategic planning tables for 5-year strategic plans with scenario modeling
-- Access pattern: Admin/Manager full access, Viewer read-only for approved plans

-- ==============================================================================
-- strategic_plans: 5-year strategic plan headers
-- ==============================================================================

-- Enable RLS
ALTER TABLE efir_budget.strategic_plans ENABLE ROW LEVEL SECURITY;

-- Admin: Full access to all strategic plans
CREATE POLICY "strategic_plans_admin_all" ON efir_budget.strategic_plans
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Full access to all strategic plans (strategic planning is manager-level)
CREATE POLICY "strategic_plans_manager_all" ON efir_budget.strategic_plans
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
  );

-- Viewer: Read-only for approved plans
CREATE POLICY "strategic_plans_viewer_select" ON efir_budget.strategic_plans
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'viewer'
    AND deleted_at IS NULL
    AND status = 'approved'
  );

-- All authenticated: General read access with status constraints
CREATE POLICY "strategic_plans_select" ON efir_budget.strategic_plans
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND status = 'approved'
      )
    )
  );

-- ==============================================================================
-- strategic_plan_scenarios: Growth scenarios within strategic plans
-- ==============================================================================

-- Enable RLS
ALTER TABLE efir_budget.strategic_plan_scenarios ENABLE ROW LEVEL SECURITY;

-- Admin: Full access to all scenarios
CREATE POLICY "strategic_plan_scenarios_admin_all" ON efir_budget.strategic_plan_scenarios
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Full access to scenarios (via parent plan access)
CREATE POLICY "strategic_plan_scenarios_manager_all" ON efir_budget.strategic_plan_scenarios
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.deleted_at IS NULL
    )
  );

-- Viewer: Read-only for scenarios in approved plans
CREATE POLICY "strategic_plan_scenarios_viewer_select" ON efir_budget.strategic_plan_scenarios
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'viewer'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.status = 'approved'
      AND sp.deleted_at IS NULL
    )
  );

-- All authenticated: Read access via parent plan constraints
CREATE POLICY "strategic_plan_scenarios_select" ON efir_budget.strategic_plan_scenarios
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.strategic_plans sp
          WHERE sp.id = strategic_plan_id
          AND sp.status = 'approved'
          AND sp.deleted_at IS NULL
        )
      )
    )
  );

-- ==============================================================================
-- strategic_plan_projections: Multi-year financial projections
-- ==============================================================================

-- Enable RLS
ALTER TABLE efir_budget.strategic_plan_projections ENABLE ROW LEVEL SECURITY;

-- Admin: Full access to all projections
CREATE POLICY "strategic_plan_projections_admin_all" ON efir_budget.strategic_plan_projections
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Full access to projections (via parent scenario → plan)
CREATE POLICY "strategic_plan_projections_manager_all" ON efir_budget.strategic_plan_projections
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plan_scenarios sps
      JOIN efir_budget.strategic_plans sp ON sps.strategic_plan_id = sp.id
      WHERE sps.id = strategic_plan_scenario_id
      AND sps.deleted_at IS NULL
      AND sp.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plan_scenarios sps
      JOIN efir_budget.strategic_plans sp ON sps.strategic_plan_id = sp.id
      WHERE sps.id = strategic_plan_scenario_id
      AND sps.deleted_at IS NULL
      AND sp.deleted_at IS NULL
    )
  );

-- Viewer: Read-only for projections in approved plans
CREATE POLICY "strategic_plan_projections_viewer_select" ON efir_budget.strategic_plan_projections
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'viewer'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plan_scenarios sps
      JOIN efir_budget.strategic_plans sp ON sps.strategic_plan_id = sp.id
      WHERE sps.id = strategic_plan_scenario_id
      AND sp.status = 'approved'
      AND sps.deleted_at IS NULL
      AND sp.deleted_at IS NULL
    )
  );

-- All authenticated: Read access via parent scenario → plan constraints
CREATE POLICY "strategic_plan_projections_select" ON efir_budget.strategic_plan_projections
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.strategic_plan_scenarios sps
          JOIN efir_budget.strategic_plans sp ON sps.strategic_plan_id = sp.id
          WHERE sps.id = strategic_plan_scenario_id
          AND sp.status = 'approved'
          AND sps.deleted_at IS NULL
          AND sp.deleted_at IS NULL
        )
      )
    )
  );

-- ==============================================================================
-- strategic_initiatives: Major projects and capital investments
-- ==============================================================================

-- Enable RLS
ALTER TABLE efir_budget.strategic_initiatives ENABLE ROW LEVEL SECURITY;

-- Admin: Full access to all initiatives
CREATE POLICY "strategic_initiatives_admin_all" ON efir_budget.strategic_initiatives
  FOR ALL
  TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

-- Manager: Full access to initiatives (via parent plan)
CREATE POLICY "strategic_initiatives_manager_all" ON efir_budget.strategic_initiatives
  FOR ALL
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.deleted_at IS NULL
    )
  )
  WITH CHECK (
    efir_budget.current_user_role() = 'manager'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.deleted_at IS NULL
    )
  );

-- Viewer: Read-only for initiatives in approved plans
CREATE POLICY "strategic_initiatives_viewer_select" ON efir_budget.strategic_initiatives
  FOR SELECT
  TO authenticated
  USING (
    efir_budget.current_user_role() = 'viewer'
    AND deleted_at IS NULL
    AND EXISTS (
      SELECT 1 FROM efir_budget.strategic_plans sp
      WHERE sp.id = strategic_plan_id
      AND sp.status = 'approved'
      AND sp.deleted_at IS NULL
    )
  );

-- All authenticated: Read access via parent plan constraints
CREATE POLICY "strategic_initiatives_select" ON efir_budget.strategic_initiatives
  FOR SELECT
  TO authenticated
  USING (
    deleted_at IS NULL
    AND (
      efir_budget.current_user_role() IN ('admin', 'manager')
      OR (
        efir_budget.current_user_role() = 'viewer'
        AND EXISTS (
          SELECT 1 FROM efir_budget.strategic_plans sp
          WHERE sp.id = strategic_plan_id
          AND sp.status = 'approved'
          AND sp.deleted_at IS NULL
        )
      )
    )
  );

-- ==============================================================================
-- END OF MODULE 18 RLS POLICIES
-- ==============================================================================
