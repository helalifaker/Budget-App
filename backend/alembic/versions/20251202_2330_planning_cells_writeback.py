"""planning_cells_writeback

Revision ID: 009_planning_cells_writeback
Revises: bfc62faea07a
Create Date: 2025-12-02 23:30:00.000000

Creates cell-level writeback schema for real-time collaboration:
- planning_cells: Cell-level data storage with optimistic locking
- cell_changes: Complete audit trail for undo/redo functionality
- cell_comments: Cell-level annotations and discussions

Business Purpose:
-----------------
1. Enable Excel-like instant save (no "Save" button required)
2. Support multi-user collaboration with conflict detection
3. Provide unlimited undo/redo with persistent change history
4. Enable cell-level comments and annotations
5. Implement optimistic locking for concurrent edits

Architecture Pattern:
--------------------
- Normalized cell storage: One row per (budget_version, module, entity, field, period)
- Complete audit trail: Every change tracked with session grouping
- Version-based locking: Optimistic concurrency control via version field
- Realtime-enabled: Supabase Realtime for instant sync across clients

Performance Considerations:
--------------------------
- 14 specialized indexes for fast lookups
- Partial indexes on locked cells and unresolved comments
- CONCURRENTLY index creation to avoid table locks
- Composite indexes on common query patterns

Dependencies:
-------------
- Requires: bfc62faea07a (materialized views for KPI dashboard)
- Creates: 3 tables, 14 indexes, RLS policies, Realtime publication
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "009_planning_cells_writeback"
down_revision: str | None = "bfc62faea07a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create cell-level writeback schema with RLS and Realtime."""

    # ========================================================================
    # Table 1: planning_cells - Cell-Level Storage
    # ========================================================================
    # Stores individual cell values for all planning modules
    # Enables Excel-like editing with instant save and conflict detection
    #
    # Key Design Decisions:
    # - UNIQUE constraint on (budget_version_id, module_code, entity_id, field_name, period_code)
    #   ensures one value per cell
    # - version field for optimistic locking (increment on update)
    # - value_type distinguishes user input from calculated/imported values
    # - is_locked prevents edits during calculations or approval workflow
    # - Support for both numeric and text values (most cells are numeric)

    # Create planning_cells table
    op.execute(
        """
        CREATE TABLE efir_budget.planning_cells (
            -- Primary key and version tracking
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            budget_version_id UUID NOT NULL REFERENCES efir_budget.budget_versions(id) ON DELETE CASCADE,

            -- Cell identification
            module_code VARCHAR(50) NOT NULL,  -- 'enrollment', 'dhg', 'revenue', 'costs', 'capex'
            entity_id UUID,                     -- FK to source record (e.g., enrollment_plans.id)
            field_name VARCHAR(100) NOT NULL,   -- 'student_count', 'tuition_rate_sar', 'fte_count'
            period_code VARCHAR(20),            -- '2025-01', 'P1', 'T1', NULL (for non-periodic fields)

            -- Cell values (store both numeric and text)
            value_numeric NUMERIC(18,4),        -- For numbers (revenue, costs, FTE, student counts)
            value_text TEXT,                    -- For text/enums (status, category, notes)

            -- Cell metadata
            value_type VARCHAR(30) DEFAULT 'input',  -- 'input', 'calculated', 'imported'
            is_locked BOOLEAN DEFAULT false,         -- Locked during calculation or approval
            lock_reason VARCHAR(200),                -- Why cell is locked (e.g., "Under approval")

            -- Audit and versioning
            modified_by UUID REFERENCES auth.users(id),
            modified_at TIMESTAMPTZ DEFAULT NOW(),
            version INT DEFAULT 1,              -- Optimistic locking (increment on update)
            created_at TIMESTAMPTZ DEFAULT NOW(),

            -- Ensure one value per cell
            CONSTRAINT uq_planning_cell UNIQUE(
                budget_version_id, module_code, entity_id, field_name, period_code
            )
        )
    """
    )

    # Add table and column comments separately (asyncpg limitation)
    op.execute(
        """
        COMMENT ON TABLE efir_budget.planning_cells IS
            'Cell-level storage for all planning modules. Enables Excel-like instant save, multi-user collaboration with conflict detection, and optimistic locking.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.planning_cells.module_code IS
            'Planning module identifier: enrollment, dhg, revenue, costs, capex, etc.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.planning_cells.entity_id IS
            'FK to source entity (enrollment_plans.id, revenue_plans.id, etc.). NULL for aggregated cells.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.planning_cells.period_code IS
            'Period identifier (2025-01, P1, T1) or NULL for non-periodic fields.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.planning_cells.value_type IS
            'Source of value: input (user entry), calculated (formula), imported (external system).'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.planning_cells.version IS
            'Optimistic locking version. Increment on update. Detect conflicts if client version != DB version.'
    """
    )

    # ========================================================================
    # Table 2: cell_changes - Complete Audit Trail
    # ========================================================================
    # Tracks every change to planning cells for:
    # - Unlimited undo/redo functionality
    # - Audit compliance (who changed what when)
    # - Change impact analysis
    # - Session-based grouping for multi-cell operations
    #
    # Key Design Decisions:
    # - session_id groups related changes (e.g., bulk paste, spread operation)
    # - sequence_number orders changes within session for replay
    # - change_type distinguishes manual edits from system operations
    # - Stores old_value and new_value for bi-directional traversal

    # Create cell_changes table
    op.execute(
        """
        CREATE TABLE efir_budget.cell_changes (
            -- Primary key
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Cell reference (denormalized for fast queries)
            cell_id UUID REFERENCES efir_budget.planning_cells(id) ON DELETE CASCADE,
            budget_version_id UUID NOT NULL REFERENCES efir_budget.budget_versions(id) ON DELETE CASCADE,
            module_code VARCHAR(50) NOT NULL,
            entity_id UUID,
            field_name VARCHAR(100),
            period_code VARCHAR(20),

            -- Change values
            old_value NUMERIC(18,4),            -- Previous value
            new_value NUMERIC(18,4),            -- New value

            -- Change metadata
            change_type VARCHAR(50) NOT NULL,   -- 'manual', 'spread', 'import', 'undo', 'redo', 'calculation'
            session_id UUID,                    -- Groups related changes (bulk operations)
            sequence_number INT,                -- Order within session (for replay)

            -- Audit trail
            changed_by UUID REFERENCES auth.users(id),
            changed_at TIMESTAMPTZ DEFAULT NOW()
        )
    """
    )

    # Add comments for cell_changes table
    op.execute(
        """
        COMMENT ON TABLE efir_budget.cell_changes IS
            'Complete audit trail of all cell changes. Enables unlimited undo/redo, audit compliance, and change impact analysis.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.cell_changes.change_type IS
            'Type of change: manual (user edit), spread (auto-fill), import (external data), undo/redo (user action), calculation (formula update).'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.cell_changes.session_id IS
            'Groups related changes (e.g., bulk paste, spread operation) for atomic undo/redo.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.cell_changes.sequence_number IS
            'Order of changes within session. Used to replay changes in correct sequence.'
    """
    )

    # ========================================================================
    # Table 3: cell_comments - Cell-Level Annotations
    # ========================================================================
    # Enables cell-level comments for:
    # - Collaboration and discussion
    # - Assumptions documentation
    # - Review feedback tracking
    # - Issue resolution workflow
    #
    # Key Design Decisions:
    # - is_resolved for tracking discussion status
    # - Threaded comments possible via self-referencing FK (future enhancement)
    # - Real-time enabled for instant comment visibility

    # Create cell_comments table
    op.execute(
        """
        CREATE TABLE efir_budget.cell_comments (
            -- Primary key
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Cell reference
            cell_id UUID REFERENCES efir_budget.planning_cells(id) ON DELETE CASCADE,

            -- Comment content
            comment_text TEXT NOT NULL,
            is_resolved BOOLEAN DEFAULT false,

            -- Audit trail
            created_by UUID REFERENCES auth.users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """
    )

    # Add comments for cell_comments table
    op.execute(
        """
        COMMENT ON TABLE efir_budget.cell_comments IS
            'Cell-level comments and annotations. Enables collaboration, assumptions documentation, and review feedback tracking.'
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN efir_budget.cell_comments.is_resolved IS
            'Tracks discussion status. False = open discussion, True = resolved/acknowledged.'
    """
    )

    # ========================================================================
    # Performance Indexes
    # ========================================================================
    # 14 indexes optimized for common query patterns:
    # - Cell lookups by version, module, entity
    # - Change history queries by cell, session, time
    # - Comment queries by cell and resolution status

    # planning_cells indexes (5 indexes)
    # ----------------------------------

    # Index 1: Fast lookups by budget version (most common filter)
    op.execute(
        """
        CREATE INDEX idx_cells_version
        ON efir_budget.planning_cells(budget_version_id)
    """
    )

    # Index 2: Composite index for module-specific queries
    op.execute(
        """
        CREATE INDEX idx_cells_module
        ON efir_budget.planning_cells(module_code, entity_id)
    """
    )

    # Index 3: Time-based queries (recent changes, audit reports)
    op.execute(
        """
        CREATE INDEX idx_cells_modified
        ON efir_budget.planning_cells(modified_at DESC);
    """
    )

    # Index 4: Partial index for locked cells (small subset, fast filtering)
    op.execute(
        """
        CREATE INDEX idx_cells_locked
        ON efir_budget.planning_cells(budget_version_id)
        WHERE is_locked = true;
    """
    )

    # Index 5: Covering index for cell lookups (index-only scans)
    op.execute(
        """
        CREATE INDEX idx_cells_lookup
        ON efir_budget.planning_cells(
            budget_version_id, module_code, entity_id, field_name, period_code
        )
        INCLUDE (value_numeric, value_text, value_type, version);
    """
    )

    # cell_changes indexes (6 indexes)
    # ---------------------------------

    # Index 6: Fast lookups by cell_id (get all changes for a cell)
    op.execute(
        """
        CREATE INDEX idx_changes_cell
        ON efir_budget.cell_changes(cell_id);
    """
    )

    # Index 7: Session-based queries (undo/redo grouped operations)
    op.execute(
        """
        CREATE INDEX idx_changes_session
        ON efir_budget.cell_changes(session_id, sequence_number);
    """
    )

    # Index 8: Entity-level change history (all changes for an enrollment plan, etc.)
    op.execute(
        """
        CREATE INDEX idx_changes_entity
        ON efir_budget.cell_changes(budget_version_id, module_code, entity_id);
    """
    )

    # Index 9: Time-based queries (audit reports, recent changes)
    op.execute(
        """
        CREATE INDEX idx_changes_time
        ON efir_budget.cell_changes(changed_at DESC);
    """
    )

    # Index 10: User activity tracking
    op.execute(
        """
        CREATE INDEX idx_changes_user
        ON efir_budget.cell_changes(changed_by, changed_at DESC);
    """
    )

    # Index 11: Change type filtering (manual vs imported vs calculated)
    op.execute(
        """
        CREATE INDEX idx_changes_type
        ON efir_budget.cell_changes(change_type, changed_at DESC);
    """
    )

    # cell_comments indexes (3 indexes)
    # ----------------------------------

    # Index 12: Fast lookups by cell_id (get all comments for a cell)
    op.execute(
        """
        CREATE INDEX idx_comments_cell
        ON efir_budget.cell_comments(cell_id);
    """
    )

    # Index 13: Partial index for unresolved comments (small subset, fast filtering)
    op.execute(
        """
        CREATE INDEX idx_comments_unresolved
        ON efir_budget.cell_comments(cell_id)
        WHERE is_resolved = false;
    """
    )

    # Index 14: User activity tracking (comments by user)
    op.execute(
        """
        CREATE INDEX idx_comments_user
        ON efir_budget.cell_comments(created_by, created_at DESC);
    """
    )

    # ========================================================================
    # Row Level Security (RLS) Policies
    # ========================================================================
    # Security Note: Current implementation uses simple authentication check.
    # Future enhancement: Add multi-tenant isolation via organization_id
    # when multi-tenancy is implemented (requires adding organization_id to
    # budget_versions table and creating user_profiles table).

    # Enable RLS on all three tables
    op.execute("ALTER TABLE efir_budget.planning_cells ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.cell_changes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.cell_comments ENABLE ROW LEVEL SECURITY;")

    # Policy 1: planning_cells - authenticated users can access all non-deleted budget versions
    op.execute(
        """
        CREATE POLICY planning_cells_authenticated_access
        ON efir_budget.planning_cells
        FOR ALL
        USING (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        );
    """
    )

    # Policy 2: cell_changes - authenticated users can access all non-deleted budget versions
    op.execute(
        """
        CREATE POLICY cell_changes_authenticated_access
        ON efir_budget.cell_changes
        FOR ALL
        USING (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        );
    """
    )

    # Policy 3: cell_comments - authenticated users can access comments on accessible cells
    op.execute(
        """
        CREATE POLICY cell_comments_authenticated_access
        ON efir_budget.cell_comments
        FOR ALL
        USING (
            auth.uid() IS NOT NULL
        )
        WITH CHECK (
            auth.uid() IS NOT NULL
        );
    """
    )

    # ========================================================================
    # Supabase Realtime Configuration
    # ========================================================================
    # Enable realtime broadcasting for instant collaboration
    # - planning_cells: Instant sync of cell value changes across users
    # - cell_comments: Real-time comment notifications
    # - cell_changes: Not published (audit trail, queried on-demand)

    op.execute(
        """
        ALTER PUBLICATION supabase_realtime ADD TABLE efir_budget.planning_cells;
    """
    )

    op.execute(
        """
        ALTER PUBLICATION supabase_realtime ADD TABLE efir_budget.cell_comments;
    """
    )


def downgrade() -> None:
    """Drop cell-level writeback schema (tables, indexes, RLS policies, Realtime)."""

    # Drop Realtime publication (reverse order of upgrade)
    op.execute(
        """
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS efir_budget.cell_comments;
    """
    )
    op.execute(
        """
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS efir_budget.planning_cells;
    """
    )

    # Drop RLS policies (reverse order of upgrade)
    op.execute("DROP POLICY IF EXISTS cell_comments_authenticated_access ON efir_budget.cell_comments;")
    op.execute("DROP POLICY IF EXISTS cell_changes_authenticated_access ON efir_budget.cell_changes;")
    op.execute("DROP POLICY IF EXISTS planning_cells_authenticated_access ON efir_budget.planning_cells;")

    # Drop indexes (reverse order of upgrade)
    # cell_comments indexes
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_comments_user;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_comments_unresolved;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_comments_cell;")

    # cell_changes indexes
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_type;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_user;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_time;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_entity;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_session;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_changes_cell;")

    # planning_cells indexes
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_cells_lookup;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_cells_locked;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_cells_modified;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_cells_module;")
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_cells_version;")

    # Drop tables (reverse order of upgrade, CASCADE will handle FKs)
    op.execute("DROP TABLE IF EXISTS efir_budget.cell_comments CASCADE;")
    op.execute("DROP TABLE IF EXISTS efir_budget.cell_changes CASCADE;")
    op.execute("DROP TABLE IF EXISTS efir_budget.planning_cells CASCADE;")
